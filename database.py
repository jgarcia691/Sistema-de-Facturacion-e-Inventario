"""
=============================================================================
MÓDULO DE BASE DE DATOS Y PERSISTENCIA (SQLite)
=============================================================================
Este módulo administra la capa de persistencia de datos del sistema utilizando
SQLite como motor relacional empaquetado ('inventory_system.db').

Responsabilidades clave:
1. Conectividad y configuración de SQLite:
   - Detección dinámica del directorio base (compatible con ejecutables de PyInstaller).
   - Activación obligatoria de integridad referencial mediante claves foráneas (PRAGMA foreign_keys = ON).
   - Uso de sqlite3.Row para acceso asociativo a columnas.
2. Estructura y esquemas relacionales:
   - 'cliente': Directorio de clientes con cédula/RIF único.
   - 'productos': Catálogo de artículos con control de inventario (stock) y precios en USD.
   - 'factura': Encabezados de facturación (fecha, cliente, método de pago, tasa, IVA, totales).
   - 'factura_productos': Renglones o partidas de cada factura con respaldo histórico de precio unitario.
   - 'negocio_config': Datos fiscales de la empresa (nombre, RIF, dirección, teléfono).
3. Migraciones y consistencia:
   - Verificación de esquema en tiempo de ejecución (adición dinámica de 'precio_unitario').
4. Servicios externos y analítica:
   - Consulta automatizada de la tasa oficial del BCV a través de DolarApi.
   - Consultas agregadas para el dashboard ejecutivo y gráficas estadísticas.
=============================================================================
"""

import sqlite3
import os
import sys
import urllib.request
import json
from datetime import datetime, timedelta


def get_app_dir():
    """
    Retorna la ruta absoluta al directorio base de la aplicación.
    
    Proporciona soporte transparente tanto en ejecución estándar (script .py)
    como en ejecutables portables congelados con PyInstaller (sys.frozen),
    asegurando que la base de datos se guarde siempre junto al ejecutable.

    Returns:
        str: Ruta absoluta del directorio raíz de la aplicación.
    """
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


# Ruta absoluta del archivo de base de datos SQLite
DB_NAME = os.path.join(get_app_dir(), "inventory_system.db")


def get_connection():
    """
    Crea y retorna una nueva conexión a la base de datos SQLite.
    
    Configura row_factory = sqlite3.Row para permitir el acceso a las
    columnas tanto por índice numérico como por nombre de campo tipo diccionario.

    Returns:
        sqlite3.Connection: Conexión activa a la base de datos.
    """
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """
    Inicializa la base de datos creando las tablas requeridas si aún no existen.
    
    Procedimiento:
    1. Habilita el cumplimiento de claves foráneas mediante PRAGMA foreign_keys = ON.
    2. Crea las tablas relacionales: cliente, productos, factura, factura_productos, negocio_config.
    3. Ejecuta migraciones de esquema automáticas (como la columna precio_unitario).
    4. Inserta el registro inicial por defecto de configuración del negocio si la tabla está vacía.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # Activar validación de claves foráneas
    cursor.execute("PRAGMA foreign_keys = ON;")
    
    # 1. Tabla cliente (cedula como clave primaria, nombre, telefono)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cliente (
            cedula TEXT PRIMARY KEY,
            nombre TEXT NOT NULL,
            telefono TEXT
        )
    """)

    # 2. Tabla productos (id autoincremental, nombre, stock cant, precio en USD)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS productos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            cant INTEGER NOT NULL DEFAULT 0,
            precio REAL NOT NULL DEFAULT 0.0
        )
    """)

    # 3. Tabla factura (id, fecha/hora, cedula_cliente, método de pago, totales, tasa de cambio e IVA)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS factura (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT NOT NULL,
            cedula_cliente TEXT NOT NULL,
            metodo_pago TEXT NOT NULL,
            total_dolar REAL NOT NULL DEFAULT 0.0,
            total_bs REAL NOT NULL DEFAULT 0.0,
            tasa REAL NOT NULL DEFAULT 0.0,
            iva REAL NOT NULL DEFAULT 0.0,
            FOREIGN KEY (cedula_cliente) REFERENCES cliente (cedula) ON DELETE CASCADE
        )
    """)

    # 4. Tabla factura_productos (relación muchos a muchos con cantidad y precio unitario congelado)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS factura_productos (
            id_factura INTEGER NOT NULL,
            id_producto INTEGER NOT NULL,
            cantidad INTEGER NOT NULL,
            precio_unitario REAL NOT NULL DEFAULT 0.0,
            FOREIGN KEY (id_factura) REFERENCES factura (id) ON DELETE CASCADE,
            FOREIGN KEY (id_producto) REFERENCES productos (id)
        )
    """)

    # Migración de esquema: asegurar que exista precio_unitario en instalaciones previas
    cursor.execute("PRAGMA table_info(factura_productos);")
    column_names = [col[1] for col in cursor.fetchall()]
    if "precio_unitario" not in column_names:
        cursor.execute("ALTER TABLE factura_productos ADD COLUMN precio_unitario REAL NOT NULL DEFAULT 0.0;")
        # Respaldar precio de facturas antiguas con el precio actual del producto
        cursor.execute("""
            UPDATE factura_productos
            SET precio_unitario = COALESCE((SELECT precio FROM productos WHERE productos.id = factura_productos.id_producto), 0.0)
            WHERE precio_unitario IS NULL OR precio_unitario = 0.0;
        """)

    # 5. Tabla negocio_config (registro único id=1 con datos fiscales del comercio)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS negocio_config (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            nombre TEXT NOT NULL DEFAULT 'Mi Negocio',
            rif TEXT NOT NULL DEFAULT 'J-00000000-0',
            direccion TEXT NOT NULL DEFAULT 'Ciudad, Venezuela',
            telefono TEXT DEFAULT ''
        )
    """)
    cursor.execute("SELECT COUNT(*) FROM negocio_config WHERE id = 1;")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
            INSERT INTO negocio_config (id, nombre, rif, direccion, telefono)
            VALUES (1, 'Mi Negocio', 'J-00000000-0', 'Ciudad, Venezuela', '')
        """)

    conn.commit()
    conn.close()


def get_negocio_config():
    """
    Obtiene los datos de configuración del negocio (nombre, RIF, dirección, teléfono).

    Returns:
        dict: Diccionario con los campos 'nombre', 'rif', 'direccion' y 'telefono'.
              Si no existe registro, retorna valores predeterminados de fábrica.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT nombre, rif, direccion, telefono FROM negocio_config WHERE id = 1")
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(row)
    return {
        "nombre": "Mi Negocio",
        "rif": "J-00000000-0",
        "direccion": "Ciudad, Venezuela",
        "telefono": ""
    }


def update_negocio_config(nombre, rif, direccion, telefono=""):
    """
    Actualiza la configuración fiscal e institucional del negocio en la base de datos.

    Args:
        nombre (str): Nombre comercial de la empresa.
        rif (str): Registro de Información Fiscal (RIF).
        direccion (str): Dirección fiscal del establecimiento.
        telefono (str, opcional): Teléfono corporativo.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE negocio_config
        SET nombre = ?, rif = ?, direccion = ?, telefono = ?
        WHERE id = 1
    """, (nombre.strip(), rif.strip(), direccion.strip(), telefono.strip()))
    if cursor.rowcount == 0:
        cursor.execute("""
            INSERT INTO negocio_config (id, nombre, rif, direccion, telefono)
            VALUES (1, ?, ?, ?, ?)
        """, (nombre.strip(), rif.strip(), direccion.strip(), telefono.strip()))
    conn.commit()
    conn.close()


def clear_database():
    """
    Vacía por completo todas las tablas operativas de la base de datos (mantenimiento/reinicio).
    
    Procedimiento:
    1. Desactiva temporalmente las claves foráneas para evitar violaciones de restricción.
    2. Elimina registros de factura_productos, factura, productos y cliente.
    3. Reinicia los contadores autoincrementales en sqlite_sequence.
    4. Reactiva las claves foráneas y guarda los cambios.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = OFF;")
    cursor.execute("DELETE FROM factura_productos;")
    cursor.execute("DELETE FROM factura;")
    cursor.execute("DELETE FROM productos;")
    cursor.execute("DELETE FROM cliente;")
    cursor.execute("DELETE FROM sqlite_sequence;")
    cursor.execute("PRAGMA foreign_keys = ON;")
    conn.commit()
    conn.close()


def get_bcv_rate():
    """
    Consulta en tiempo real la tasa oficial de cambio del Banco Central de Venezuela (BCV)
    utilizando el servicio de DolarApi (https://ve.dolarapi.com/v1/dolares/oficial).

    Returns:
        float: Tasa de cambio oficial en Bolívares por Dólar (ej. 36.50).
               En caso de error de conexión o tiempo de espera agotado, retorna 36.50 como valor de contingencia.
    """
    try:
        url = "https://ve.dolarapi.com/v1/dolares/oficial"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode('utf-8'))
            compra = data.get("compra")
            if compra is not None and float(compra) > 0:
                return float(compra)
            promedio = data.get("promedio")
            if promedio is not None and float(promedio) > 0:
                return float(promedio)
    except Exception as e:
        print(f"Error obteniendo tasa de dolarapi.com: {e}")
    return 36.50


# =============================================================================
# OPERACIONES CRUD - PRODUCTOS
# =============================================================================

def get_all_products(search_term=""):
    """
    Obtiene la lista de productos registrados, con filtro opcional de búsqueda.

    Args:
        search_term (str, opcional): Texto para filtrar por ID o por nombre de producto.

    Returns:
        list[sqlite3.Row]: Lista de filas de productos ordenados alfabéticamente por nombre.
    """
    conn = get_connection()
    cursor = conn.cursor()
    if search_term:
        term = f"%{search_term}%"
        cursor.execute("""
            SELECT * FROM productos 
            WHERE CAST(id AS TEXT) LIKE ? OR nombre LIKE ?
            ORDER BY nombre ASC
        """, (term, term))
    else:
        cursor.execute("SELECT * FROM productos ORDER BY nombre ASC")
    rows = cursor.fetchall()
    conn.close()
    return rows


def get_product_by_id(product_id):
    """
    Busca y retorna un producto específico por su identificador primario.

    Args:
        product_id (int): ID del producto.

    Returns:
        sqlite3.Row or None: Registro del producto si existe, de lo contrario None.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM productos WHERE id = ?", (product_id,))
    row = cursor.fetchone()
    conn.close()
    return row


def add_product(nombre, cant, precio):
    """
    Inserta un nuevo producto en el inventario.

    Args:
        nombre (str): Nombre o descripción del artículo.
        cant (int): Cantidad inicial en stock.
        precio (float): Precio unitario en dólares estadounidenses ($).

    Returns:
        int: Identificador único (ID autoincremental) asignado al nuevo producto.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO productos (nombre, cant, precio)
        VALUES (?, ?, ?)
    """, (nombre, cant, precio))
    conn.commit()
    prod_id = cursor.lastrowid
    conn.close()
    return prod_id


def update_product(product_id, nombre, cant, precio):
    """
    Actualiza la información de un producto existente.

    Args:
        product_id (int): ID del producto a modificar.
        nombre (str): Nuevo nombre del producto.
        cant (int): Nueva cantidad en stock disponible.
        precio (float): Nuevo precio unitario en dólares ($).
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE productos 
        SET nombre = ?, cant = ?, precio = ?
        WHERE id = ?
    """, (nombre, cant, precio, product_id))
    conn.commit()
    conn.close()


def delete_product(product_id):
    """
    Elimina un producto del catálogo mediante su identificador.

    Args:
        product_id (int): ID del producto a suprimir.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM productos WHERE id = ?", (product_id,))
    conn.commit()
    conn.close()


# =============================================================================
# OPERACIONES CRUD - CLIENTES
# =============================================================================

def get_all_clients(search_term=""):
    """
    Consulta todos los clientes registrados, con soporte para filtrado.

    Args:
        search_term (str, opcional): Cadena para buscar por cédula, nombre o teléfono.

    Returns:
        list[sqlite3.Row]: Lista de clientes ordenados alfabéticamente por nombre.
    """
    conn = get_connection()
    cursor = conn.cursor()
    if search_term:
        term = f"%{search_term}%"
        cursor.execute("""
            SELECT * FROM cliente 
            WHERE cedula LIKE ? OR nombre LIKE ? OR telefono LIKE ?
            ORDER BY nombre ASC
        """, (term, term, term))
    else:
        cursor.execute("SELECT * FROM cliente ORDER BY nombre ASC")
    rows = cursor.fetchall()
    conn.close()
    return rows


def get_client_by_cedula(cedula):
    """
    Busca un cliente por su número de cédula o RIF (sin distinción de mayúsculas o espacios).

    Args:
        cedula (str): Cédula o identificación del cliente.

    Returns:
        sqlite3.Row or None: Registro del cliente si se encuentra, o None.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM cliente WHERE UPPER(TRIM(cedula)) = UPPER(TRIM(?))", (cedula,))
    row = cursor.fetchone()
    conn.close()
    return row


def save_or_update_client(cedula, nombre, telefono):
    """
    Guarda o actualiza un cliente (operación Upsert).
    
    Si la cédula ya existe en la base de datos, actualiza el nombre y teléfono;
    en caso contrario, inserta un nuevo registro.

    Args:
        cedula (str): Cédula o RIF único del cliente.
        nombre (str): Nombre completo del cliente.
        telefono (str): Teléfono de contacto.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT cedula FROM cliente WHERE UPPER(TRIM(cedula)) = UPPER(TRIM(?))", (cedula,))
    if cursor.fetchone():
        cursor.execute("""
            UPDATE cliente 
            SET nombre = ?, telefono = ?
            WHERE UPPER(TRIM(cedula)) = UPPER(TRIM(?))
        """, (nombre, telefono, cedula))
    else:
        cursor.execute("""
            INSERT INTO cliente (cedula, nombre, telefono)
            VALUES (?, ?, ?)
        """, (cedula, nombre, telefono))
    conn.commit()
    conn.close()


def add_client(cedula, nombre, telefono):
    """
    Inserta un nuevo cliente en el directorio.

    Args:
        cedula (str): Cédula o RIF del cliente.
        nombre (str): Nombre completo.
        telefono (str): Número telefónico.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO cliente (cedula, nombre, telefono)
        VALUES (?, ?, ?)
    """, (cedula, nombre, telefono))
    conn.commit()
    conn.close()


def update_client(cedula, nombre, telefono):
    """
    Modifica los datos de un cliente existente.

    Args:
        cedula (str): Cédula del cliente (clave primaria).
        nombre (str): Nuevo nombre completo.
        telefono (str): Nuevo teléfono.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE cliente 
        SET nombre = ?, telefono = ?
        WHERE cedula = ?
    """, (nombre, telefono, cedula))
    conn.commit()
    conn.close()


def delete_client(cedula):
    """
    Elimina un cliente y, por cascada referencial, sus registros asociados.

    Args:
        cedula (str): Cédula del cliente a eliminar.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM cliente WHERE cedula = ?", (cedula,))
    conn.commit()
    conn.close()


# =============================================================================
# OPERACIONES DE FACTURACIÓN Y TRANSACCIONES
# =============================================================================

def save_invoice(cedula_cliente, nombre_cliente, telefono_cliente, metodo_pago, tasa, iva_monto, items):
    """
    Guarda una factura completa de forma atómica y actualiza el inventario.
    
    Procedimiento transaccional:
    1. Asegura que el cliente exista en la tabla 'cliente'. Si existe, actualiza
       nombre y teléfono si fueron provistos; si no existe, lo inserta de inmediato.
    2. Calcula subtotal en USD sumando (cantidad * precio_unitario) de los renglones.
    3. Calcula total en USD sumando el IVA, y total en Bs aplicando la tasa de cambio oficial.
    4. Inserta el registro maestro en la tabla 'factura'.
    5. Itera cada artículo en 'items', registrándolo en 'factura_productos' con su
       precio unitario exacto en ese momento.
    6. Descuenta automáticamente la cantidad vendida del stock en la tabla 'productos'.
    7. Confirma la transacción (commit).

    Args:
        cedula_cliente (str): Cédula o RIF del cliente.
        nombre_cliente (str): Nombre del cliente.
        telefono_cliente (str): Teléfono del cliente.
        metodo_pago (str): Método de pago seleccionado (Efectivo $, Pago Móvil, etc.).
        tasa (float): Tasa de cambio BCV utilizada (Bs/$).
        iva_monto (float): Monto calculado del IVA en dólares.
        items (list[dict]): Lista de diccionarios con claves:
                            'id_producto' (int), 'cantidad' (int), 'precio' (float).

    Returns:
        int: Identificador de la nueva factura generada (ID autoincremental).
    """
    conn = get_connection()
    cursor = conn.cursor()

    # 1. Asegurar la existencia o actualización del cliente
    cursor.execute("SELECT cedula FROM cliente WHERE UPPER(TRIM(cedula)) = UPPER(TRIM(?))", (cedula_cliente,))
    if cursor.fetchone():
        if nombre_cliente or telefono_cliente:
            cursor.execute("""
                UPDATE cliente SET nombre = COALESCE(NULLIF(?, ''), nombre), 
                                  telefono = COALESCE(NULLIF(?, ''), telefono)
                WHERE UPPER(TRIM(cedula)) = UPPER(TRIM(?))
            """, (nombre_cliente, telefono_cliente, cedula_cliente))
    else:
        cursor.execute("""
            INSERT INTO cliente (cedula, nombre, telefono)
            VALUES (?, ?, ?)
        """, (cedula_cliente, nombre_cliente or "Cliente Contado", telefono_cliente or ""))

    # 2. Fecha y hora actual del sistema
    date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 3. Cálculos monetarios
    subtotal_dolar = sum(item['cantidad'] * float(item.get('precio', item.get('precio_unitario', 0.0))) for item in items)
    total_dolar = round(subtotal_dolar + iva_monto, 2)
    total_bs = round(total_dolar * tasa, 2)

    # 4. Inserción del encabezado de factura
    cursor.execute("""
        INSERT INTO factura (fecha, cedula_cliente, metodo_pago, total_dolar, total_bs, tasa, iva)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (date_str, cedula_cliente, metodo_pago, total_dolar, total_bs, tasa, round(iva_monto, 2)))

    invoice_id = cursor.lastrowid

    # 5. Inserción de renglones y descuento de inventario
    for item in items:
        unit_price = float(item.get('precio', item.get('precio_unitario', 0.0)))
        cursor.execute("""
            INSERT INTO factura_productos (id_factura, id_producto, cantidad, precio_unitario)
            VALUES (?, ?, ?, ?)
        """, (invoice_id, item['id_producto'], item['cantidad'], round(unit_price, 2)))

        # Reducir stock del producto
        cursor.execute("UPDATE productos SET cant = cant - ? WHERE id = ?", (item['cantidad'], item['id_producto']))

    conn.commit()
    conn.close()
    return invoice_id


def get_all_invoices(search_term=""):
    """
    Consulta todas las facturas emitidas ordenadas cronológicamente de forma descendente.
    
    Incluye un JOIN con la tabla de clientes para obtener el nombre y teléfono del comprador.
    Soporta filtrado por número de factura, cédula o nombre del cliente.

    Args:
        search_term (str, opcional): Término de búsqueda.

    Returns:
        list[sqlite3.Row]: Lista de facturas encontradas.
    """
    conn = get_connection()
    cursor = conn.cursor()

    query = """
        SELECT f.*, c.nombre as cliente_nombre, c.telefono as cliente_telefono
        FROM factura f
        LEFT JOIN cliente c ON f.cedula_cliente = c.cedula
        WHERE 1=1
    """
    params = []

    if search_term:
        query += " AND (CAST(f.id AS TEXT) LIKE ? OR f.cedula_cliente LIKE ? OR c.nombre LIKE ?)"
        term = f"%{search_term}%"
        params.extend([term, term, term])

    query += " ORDER BY f.fecha DESC"

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return rows


def get_invoice_details(invoice_id):
    """
    Obtiene el encabezado completo de una factura y la lista desglosada de sus productos.

    Args:
        invoice_id (int): Identificador de la factura.

    Returns:
        tuple[sqlite3.Row or None, list[sqlite3.Row]]: 
            (registro_factura, lista_items_factura).
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # Consulta de cabecera de factura y cliente
    cursor.execute("""
        SELECT f.*, c.nombre as cliente_nombre, c.telefono as cliente_telefono
        FROM factura f
        LEFT JOIN cliente c ON f.cedula_cliente = c.cedula
        WHERE f.id = ?
    """, (invoice_id,))
    invoice = cursor.fetchone()

    # Consulta de partidas de la factura con descripción del producto y precio congelado
    cursor.execute("""
        SELECT fp.*, 
               COALESCE(p.nombre, 'Producto no disponible') as producto_nombre, 
               COALESCE(NULLIF(fp.precio_unitario, 0.0), p.precio, 0.0) as producto_precio,
               COALESCE(NULLIF(fp.precio_unitario, 0.0), p.precio, 0.0) as precio_unitario
        FROM factura_productos fp
        LEFT JOIN productos p ON fp.id_producto = p.id
        WHERE fp.id_factura = ?
    """, (invoice_id,))
    items = cursor.fetchall()

    conn.close()
    return invoice, items


# =============================================================================
# DASHBOARD Y REPORTES ESTADÍSTICOS
# =============================================================================

def get_dashboard_summary():
    """
    Genera un consolidado de métricas operativas globales para la pantalla principal (Dashboard).

    Returns:
        dict: Diccionario que contiene:
            - 'total_sales_dolar': Ventas acumuladas en USD.
            - 'total_sales_bs': Ventas acumuladas en Bolívares.
            - 'total_products': Cantidad total de productos registrados.
            - 'total_clients': Total de clientes registrados.
            - 'low_stock_count': Cantidad de productos con stock crítico (<= 5).
            - 'low_stock_items': Lista de los 5 productos con menor existencia.
            - 'recent_invoices': Lista de las 5 facturas más recientes.
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Total de ventas acumuladas ($ y Bs)
    cursor.execute("SELECT COALESCE(SUM(total_dolar), 0), COALESCE(SUM(total_bs), 0) FROM factura")
    row_sales = cursor.fetchone()
    total_sales_dolar = row_sales[0]
    total_sales_bs = row_sales[1]

    # Total de productos en catálogo
    cursor.execute("SELECT COUNT(*) FROM productos")
    total_products = cursor.fetchone()[0]

    # Total de clientes registrados
    cursor.execute("SELECT COUNT(*) FROM cliente")
    total_clients = cursor.fetchone()[0]

    # Conteo y lista de productos con inventario crítico (stock <= 5)
    cursor.execute("SELECT COUNT(*) FROM productos WHERE cant <= 5")
    low_stock_count = cursor.fetchone()[0]

    cursor.execute("SELECT id, nombre, cant, precio FROM productos WHERE cant <= 5 ORDER BY cant ASC LIMIT 5")
    low_stock_items = cursor.fetchall()

    # Facturas más recientes (últimas 5)
    cursor.execute("""
        SELECT f.*, c.nombre as cliente_nombre 
        FROM factura f 
        LEFT JOIN cliente c ON f.cedula_cliente = c.cedula 
        ORDER BY f.fecha DESC LIMIT 5
    """)
    recent_invoices = cursor.fetchall()

    conn.close()

    return {
        "total_sales_dolar": total_sales_dolar,
        "total_sales_bs": total_sales_bs,
        "total_products": total_products,
        "total_clients": total_clients,
        "low_stock_count": low_stock_count,
        "low_stock_items": low_stock_items,
        "recent_invoices": recent_invoices
    }


def get_statistics_data():
    """
    Calcula los datos analíticos para la visualización de gráficos estadísticos (Matplotlib).

    Returns:
        dict: Diccionario que contiene:
            - 'top_products': Los 5 productos más vendidos agrupados por suma de unidades vendidas.
            - 'sales_by_day': Montos totales diarios de ventas en dólares de los últimos 10 días registrados.
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Top 5 productos más vendidos por volumen
    cursor.execute("""
        SELECT p.nombre as producto_nombre, SUM(fp.cantidad) as total_qty
        FROM factura_productos fp
        JOIN productos p ON fp.id_producto = p.id
        GROUP BY p.id
        ORDER BY total_qty DESC
        LIMIT 5
    """)
    top_products = cursor.fetchall()

    # Histórico de ventas agrupadas por fecha (últimos 10 días activos)
    cursor.execute("""
        SELECT strftime('%Y-%m-%d', fecha) as day, SUM(total_dolar) as total
        FROM factura
        GROUP BY day
        ORDER BY day ASC
        LIMIT 10
    """)
    sales_by_day = cursor.fetchall()

    conn.close()
    return {
        "top_products": top_products,
        "sales_by_day": sales_by_day
    }
