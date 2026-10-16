# 📦 Sistema de Inventario y Facturación Native Desktop

Aplicación nativa de escritorio para Windows desarrollada en **Python** con una interfaz moderna y fluida basada en **CustomTkinter**, base de datos relacional local **SQLite3**, generación de gráficos con **Matplotlib** y exportación avanzada de reportes en **OpenPyXL**.

> 📘 **Documentación Técnica Adicional**: Para un análisis detallado de la arquitectura de software, diagramas MER de la base de datos, flujo de arranque y diseño modular, consulte el [Manual Técnico y de Arquitectura](README_TECNICO.md).

---

## 🌟 Características Principales

### 1. ⚙️ Tuerca de Opciones y Configuración del Negocio
- **Acceso Directo**: Botón con ícono de tuerca `⚙️` en la cabecera superior y botón dedicado `⚙️ Datos del Negocio` en la barra lateral.
- **Formulario Emergente (Modal)** para configurar los datos fiscales:
  - 🏢 **Nombre del Negocio / Razón Social**
  - 📄 **RIF (Registro de Información Fiscal)**
  - 📍 **Dirección Fiscal / Comercial**
  - 📞 **Teléfono de Contacto**
- **Sincronización Total**: Al guardar, los datos se actualizan instantáneamente en el título de la ventana, el Dashboard, los encabezados de facturas, los reportes en Excel y la base de datos de forma persistente.

### 2. 👋 Dashboard de Bienvenida Minimalista
- Pantalla de inicio limpia, moderna y libre de saturación visual.
- Saludo personalizado con el nombre comercial de la empresa, RIF y dirección fiscal.
- Indicador de estado en tiempo real (`🟢 Sistema en línea`) con fecha y hora actual.
- Acceso directo a la configuración de la empresa y guía de navegación rápida.

### 3. 📄 Módulo de Nueva Factura de Venta
- **Autocompletado de Clientes**: Búsqueda instantánea al escribir la Cédula/ID. Si el cliente no existe, se registran sus datos (Nombre y Teléfono) directamente en la misma pantalla.
- **Búsqueda Dinámica de Productos**: Búsqueda por código ID o nombre, o selección directa en menú desplegable.
- **Control de Stock en Tiempo Real**: Validación automática de unidades disponibles antes de permitir añadir al carrito.
- **Tasa BCV Oficial en Vivo**: Consulta automática en segundo plano de la tasa oficial del Banco Central de Venezuela a través de la API pública (`dolarapi.com`), con indicador animado y botón de recarga manual.
- **Cálculo Automático**: Desglose instantáneo de Subtotal, IVA (16% configurable mediante casilla de verificación) y Totales tanto en **Dólares ($)** como en **Bolívares (Bs.)**.
- **Múltiples Métodos de Pago**: Efectivo, Transferencia Bancaria, Pago Móvil y Tarjeta de Débito/Crédito.
- **Descuento de Stock Inmediato**: Al procesar la factura, el inventario se actualiza automáticamente en la base de datos.

### 4. 📜 Historial de Facturas y Auditoría
- Registro cronológico detallado de todas las ventas emitidas (`FAC-0001`, `FAC-0002`, etc.).
- Filtro de búsqueda en tiempo real por número de factura, cédula o nombre del cliente.
- **Modal de Detalle de Factura**: Muestra el membrete completo del negocio, fecha, método de pago, tasa aplicada y el desglose de productos con cantidades, precios unitarios y subtotales.
- **Exportación Inteligente a Excel**: Genera reportes organizados por Año y Mes (`YYYY-MM.xlsx`) con pestañas separadas por cada día (`Día 01`, `Día 02`, etc.). Si se vuelve a exportar el mismo día, actualiza la hoja correspondiente sin perder las demás.
- Botón directo para abrir la carpeta `reportes/` en el explorador de Windows.

### 5. 📦 Control de Inventario y Productos
- Catálogo interactivo con ID, Nombre del Producto, Unidades en Stock y Precio Unitario en USD ($).
- **Alertas Visuales de Stock Bajo**: Indicador destacado cuando el inventario sea menor o igual a 5 unidades.
- Filtro de búsqueda en tiempo real por ID o nombre.
- **Operaciones CRUD**:
  - ➕ Agregar nuevo producto con validación de precios y existencias.
  - ✏️ Modificar nombre, cantidad y precio de productos existentes.
  - 🗑️ Eliminar productos del catálogo.
- **Exportación a Excel**: Genera `Inventario_Productos.xlsx` con KPIs (unidades totales, valor económico del inventario) y formato condicional de stock bajo.

### 6. 👥 Directorio y Gestión de Clientes
- Registro centralizado de clientes con Cédula, Nombre Completo y Teléfono de contacto.
- Búsqueda en tiempo real por número de documento o nombre.
- Formulario modal para registrar y editar información de clientes.
- Consulta del total de facturas emitidas y compras acumuladas por cada cliente.
- Exportación del directorio completo a archivo Excel.

### 7. 📈 Estadísticas y Gráficos Financieros
- Tarjetas financieras con Facturación Total en USD ($), Facturación Total en Bs. y Conteo de Productos.
- **Gráficos Nativos con Matplotlib** adaptados a la estética oscura:
  - 🏆 **Top 5 Productos Más Vendidos** (gráfico de barras horizontales con etiquetas de cantidades).
  - 📅 **Tendencia de Ventas por Día** (gráfico cronológico de ingresos diarios en USD).

---

## 🖥️ Adaptabilidad de Pantalla y Resoluciones

El sistema está optimizado para funcionar en múltiples resoluciones de pantalla:
- **Rango soportado**: Desde **1280×720** (laptops estándar / 720p) hasta **1920×1080** (Full HD) y resoluciones superiores.
- **Tamaño Mínimo Seguro**: `1024×600` para garantizar que no existan desbordamientos de interfaz.
- **Inicio Automático Maximizado**: La ventana se maximiza automáticamente al arrancar (`state("zoomed")`) ocupando toda la pantalla disponible.
- **Componentes con Scroll Responsivo**: Las tablas y formularios cuentan con contenedores desplazables para adaptarse a pantallas con distintas escalas de DPI (100%, 125%, 150%).

---

## 🛠️ Requisitos Técnicos y Dependencias

- **Sistema Operativo**: Windows 7, 8, 8.1, 10 u 11.
- **Python**: Versión 3.10 o superior (para ejecución en desarrollo).
- **Librerías Requeridas**:
  - `customtkinter` (interfaz gráfica moderna)
  - `pillow` (manejo de imágenes y assets)
  - `matplotlib` (renderizado de gráficos estadísticos)
  - `openpyxl` (creación y formateo de libros Excel)
  - `pyinstaller` (compilación a ejecutable nativo)

Instalación de dependencias:
```bash
pip install customtkinter pillow matplotlib openpyxl pyinstaller
```

---

## 💻 Ejecución en Modo Desarrollo

Para iniciar la aplicación directamente desde la consola:

```bash
python main.py
```

---

## 📦 Compilación a Ejecutable para Windows (.exe)

El proyecto incluye un script de compilación automatizado con **PyInstaller**: [`build_exe.py`](build_exe.py).

Para generar el ejecutable, ejecuta:

```bash
python build_exe.py
```

### Características del Ejecutable Generado:
- **Archivo Único (`--onefile`)**: Se genera un único archivo ejecutable en la carpeta `dist/`:
  📁 **`dist/SistemaInventario.exe`**
- **Sin Consola Negra (`--windowed`)**: Inicia directamente como una aplicación de ventanas nativa.
- **Portabilidad Automática**: El programa detecta automáticamente si está empaquetado y almacena la base de datos `inventory_system.db` y los archivos exportados en la carpeta `reportes/` **junto al ejecutable**, evitando pérdidas en carpetas temporales de Windows.

---

## 🛡️ Guía de Compatibilidad (Windows 7 / 10 / 11 y 32 / 64 Bits)

| Sistema Operativo | Arquitectura | Ejecutable Actual (`dist/SistemaInventario.exe`) | Ejecutable Universal (32-bit Python 3.8) |
| :--- | :---: | :---: | :---: |
| **Windows 11** | 64-bit | ✅ **Compatible al 100%** | ✅ Compatible |
| **Windows 10** | 64-bit | ✅ **Compatible al 100%** | ✅ Compatible |
| **Windows 10** | 32-bit | ❌ Requiere binario x86 | ✅ Compatible |
| **Windows 7 / 8 / 8.1** | 32-bit / 64-bit | ⚠️ Requiere Python 3.8 | ✅ Compatible |

### 📌 Notas Importantes sobre Compatibilidad:
1. **Regla de Arquitecturas**: Los binarios de 64 bits solo funcionan en sistemas de 64 bits. Un binario compilado en **32 bits (x86)** funciona tanto en sistemas de 32 bits como en sistemas de 64 bits (mediante la capa nativa WOW64 de Windows).
2. **Compatibilidad con Windows 7**: Microsoft y Python descontinuaron el soporte oficial para Windows 7 a partir de Python 3.9. La última versión compatible con Windows 7 SP1 es **Python 3.8.10**.
3. **Para generar un único ejecutable universal que funcione en cualquier Windows (7, 8, 10, 11 en 32 y 64 bits)**:
   - Instale **Python 3.8 (32 bits)**.
   - Instale las dependencias con `pip`.
   - Ejecute `python build_exe.py`.
   - El ejecutable resultante podrá ser distribuido en cualquier equipo.

---

## 📁 Estructura del Proyecto

```text
Sistema de inventario/
│
├── main.py                 # Ventana principal, barra lateral, navegación y control de temas
├── database.py             # Capa de base de datos SQLite3 (modelos, consultas y migración)
├── excel_exporter.py       # Motor de exportación a Excel con estilos corporativos
├── animations.py           # Componentes de animación (LoadingSpinner y transiciones)
├── build_exe.py            # Script automatizado de compilación con PyInstaller
├── README.md               # Documentación general del sistema
│
├── views/                  # Módulos de vista de la aplicación
│   ├── dashboard_view.py   # Pantalla principal de bienvenida
│   ├── invoice_view.py     # Generación de nuevas facturas y consulta de tasa BCV
│   ├── history_view.py     # Historial de facturas y visualizador de detalles
│   ├── inventory_view.py   # Control de productos, stock y alertas
│   ├── client_view.py      # Directorio y gestión de clientes
│   ├── statistics_view.py  # Gráficos de tendencias y productos más vendidos
│   └── settings_modal.py   # Diálogo modal para editar datos del negocio (⚙️)
│
├── reportes/               # Carpeta generada automáticamente con reportes Excel (.xlsx)
├── dist/                   # Carpeta donde se genera el ejecutable SistemaInventario.exe
└── inventory_system.db     # Base de datos SQLite local (autocreable)
```

---

## 🎨 Apariencia y Modos de Color

La aplicación cuenta con un selector de apariencia en la parte inferior de la barra lateral:
- 🌙 **Modo Oscuro (Dark)**: Paleta moderna inspirada en temas oscuros profesionales.
- ☀️ **Modo Claro (Light)**: Esquema de alto contraste para ambientes iluminados.
- 💻 **Modo Sistema (System)**: Se adapta automáticamente a la configuración visual de Windows.

---

## 📄 Licencia

Desarrollado como sistema de escritorio para gestión comercial, facturación y control de inventarios. Libre para uso comercial y personal.
