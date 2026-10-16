"""
Módulo de Facturación y Emisión de Ventas (invoice_view.py)
===========================================================
Gestiona el proceso completo de emisión de facturas:
- Búsqueda y autocompletado de datos del cliente por Cédula / ID.
- Registro inmediato de clientes no existentes sin salir del formulario.
- Búsqueda dinámica y selección de productos con validación de stock disponible.
- Consulta asíncrona de la tasa oficial del Banco Central de Venezuela (BCV) en tiempo real.
- Cálculo automático de subtotal, IVA (16% configurable) y totales en USD y Bs.
- Registro en base de datos mediante transacción segura y descuento inmediato de stock.
"""

import customtkinter as ctk
from tkinter import messagebox
import threading
import database
from animations import LoadingSpinner

class InvoiceView(ctk.CTkFrame):
    """
    Vista de Facturación y Creación de Nuevas Ventas.
    
    Hereda de `ctk.CTkFrame` para alojarse en el contenedor de vistas de la aplicación.
    
    Parámetros:
    - parent: Contenedor principal de vistas (`main_container`).
    - nav_callback: Callback para navegar entre vistas del sistema.
    """
    def __init__(self, parent, nav_callback):
        super().__init__(parent, fg_color="transparent")
        self.nav_callback = nav_callback

        # Lista de renglones agregados al carrito actual
        # Cada renglón contiene: id_producto, nombre, cantidad, precio, subtotal
        self.current_items = []
        self.all_products = []
        self.selected_product_id = None

        # Configuración de proporciones de columnas:
        # Columna 0: Cliente y selector de productos (peso 2)
        # Columna 1: Tasa de cambio, método de pago y resumen de totales (peso 1)
        self.grid_columnconfigure(0, weight=2)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.build_ui()
        self.load_data()
        self.fetch_bcv_rate_async()

    def build_ui(self):
        """
        Construye la interfaz de facturación en dos columnas responsivas:
        - Barra superior con título y membrete del negocio emisor.
        - Columna izquierda: formulario del cliente, buscador de productos y lista de renglones.
        - Columna derecha: método de pago, tasa BCV, cálculo de impuestos y botón de procesar.
        """
        # 1. Barra de Encabezado Superior
        top_frame = ctk.CTkFrame(self, fg_color=("white", "#1e1e2e"), corner_radius=12)
        top_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=15, pady=(15, 10))
        top_frame.grid_columnconfigure(1, weight=1)

        title_lbl = ctk.CTkLabel(
            top_frame,
            text="📝 Generar Nueva Factura de Venta",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_lbl.grid(row=0, column=0, sticky="w", padx=20, pady=15)

        # Membrete del emisor obtenido de la base de datos
        negocio = database.get_negocio_config()
        self.lbl_inv_biz = ctk.CTkLabel(
            top_frame,
            text=f"🏢 Emisor: {negocio['nombre']}  |  RIF: {negocio['rif']}",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=("#2563eb", "#60a5fa")
        )
        self.lbl_inv_biz.grid(row=0, column=1, sticky="e", padx=20, pady=15)

        # 2. Columna Izquierda: Datos del Cliente y Constructor de Renglones
        left_frame = ctk.CTkFrame(self, fg_color=("white", "#1e1e2e"), corner_radius=12)
        left_frame.grid(row=1, column=0, sticky="nsew", padx=(15, 5), pady=(0, 15))
        left_frame.grid_columnconfigure(1, weight=1)

        # --- SECCIÓN CLIENTE ---
        ctk.CTkLabel(left_frame, text="👤 Datos del Cliente", font=ctk.CTkFont(size=14, weight="bold")).grid(row=0, column=0, columnspan=2, sticky="w", padx=15, pady=(15, 5))

        # Cédula del cliente (Disparador de búsqueda reactiva)
        ctk.CTkLabel(left_frame, text="Cédula / ID:").grid(row=1, column=0, sticky="w", padx=15, pady=5)
        self.ent_cedula = ctk.CTkEntry(left_frame, placeholder_text="Escriba la cédula (Ej: V-12345678)")
        self.ent_cedula.grid(row=1, column=1, sticky="ew", padx=15, pady=5)
        self.ent_cedula.bind("<KeyRelease>", self.on_cedula_change)

        # Etiqueta indicadora de estado del cliente (Registrado / Nuevo)
        self.lbl_client_status = ctk.CTkLabel(
            left_frame,
            text="",
            font=ctk.CTkFont(size=11, weight="bold"),
            anchor="w"
        )
        self.lbl_client_status.grid(row=2, column=1, sticky="w", padx=15, pady=(0, 5))

        # Nombre del cliente
        ctk.CTkLabel(left_frame, text="Nombre Cliente:").grid(row=3, column=0, sticky="w", padx=15, pady=5)
        self.ent_nombre_cliente = ctk.CTkEntry(left_frame, placeholder_text="Nombre completo del cliente")
        self.ent_nombre_cliente.grid(row=3, column=1, sticky="ew", padx=15, pady=5)

        # Teléfono del cliente
        ctk.CTkLabel(left_frame, text="Teléfono:").grid(row=4, column=0, sticky="w", padx=15, pady=5)
        self.ent_telefono = ctk.CTkEntry(left_frame, placeholder_text="Ej: 0414-1234567")
        self.ent_telefono.grid(row=4, column=1, sticky="ew", padx=15, pady=5)

        # Divisor sutil
        ctk.CTkFrame(left_frame, height=2, fg_color=("gray85", "#333344")).grid(row=5, column=0, columnspan=2, sticky="ew", padx=15, pady=12)

        # --- SECCIÓN AGREGAR PRODUCTO ---
        ctk.CTkLabel(left_frame, text="🛒 Buscar / Agregar Producto", font=ctk.CTkFont(size=14, weight="bold")).grid(row=6, column=0, columnspan=2, sticky="w", padx=15, pady=(0, 5))

        item_builder = ctk.CTkFrame(left_frame, fg_color=("gray92", "#2b2b36"), corner_radius=8)
        item_builder.grid(row=7, column=0, columnspan=2, sticky="ew", padx=15, pady=5)
        item_builder.grid_columnconfigure(1, weight=1)

        # Búsqueda rápida de producto por ID o Nombre
        ctk.CTkLabel(item_builder, text="Buscar ID/Nombre:").grid(row=0, column=0, sticky="w", padx=10, pady=6)
        self.ent_prod_search = ctk.CTkEntry(item_builder, placeholder_text="Escriba ID o Nombre del producto...")
        self.ent_prod_search.grid(row=0, column=1, columnspan=2, sticky="ew", padx=10, pady=6)
        self.ent_prod_search.bind("<KeyRelease>", self.on_product_search_change)

        # Selector desplegable de productos
        ctk.CTkLabel(item_builder, text="O seleccionar:").grid(row=1, column=0, sticky="w", padx=10, pady=6)
        self.cmb_product = ctk.CTkOptionMenu(
            item_builder,
            values=["Cargando productos..."],
            command=self.on_product_dropdown_select
        )
        self.cmb_product.grid(row=1, column=1, columnspan=2, sticky="ew", padx=10, pady=6)

        # Etiqueta indicadora del estado del producto
        self.lbl_prod_status = ctk.CTkLabel(
            item_builder,
            text="",
            font=ctk.CTkFont(size=11, weight="bold"),
            anchor="w"
        )
        self.lbl_prod_status.grid(row=2, column=1, columnspan=2, sticky="w", padx=10, pady=(0, 4))

        # Nombre del producto seleccionado
        ctk.CTkLabel(item_builder, text="Producto:").grid(row=3, column=0, sticky="w", padx=10, pady=6)
        self.ent_prod_name = ctk.CTkEntry(item_builder, placeholder_text="Nombre del producto")
        self.ent_prod_name.grid(row=3, column=1, columnspan=2, sticky="ew", padx=10, pady=6)

        # Precio unitario en USD ($)
        ctk.CTkLabel(item_builder, text="Precio ($):").grid(row=4, column=0, sticky="w", padx=10, pady=6)
        self.ent_prod_price = ctk.CTkEntry(item_builder, placeholder_text="Precio en USD ($)")
        self.ent_prod_price.grid(row=4, column=1, sticky="ew", padx=(10, 5), pady=6)

        # Cantidad a facturar
        ctk.CTkLabel(item_builder, text="Cant:").grid(row=4, column=2, sticky="w", padx=(5, 2), pady=6)
        self.ent_qty = ctk.CTkEntry(item_builder, placeholder_text="Cant.", width=70)
        self.ent_qty.grid(row=4, column=2, sticky="e", padx=(0, 10), pady=6)
        self.ent_qty.insert(0, "1")

        # Indicador de stock disponible en almacén
        self.lbl_prod_stock = ctk.CTkLabel(
            item_builder,
            text="Stock disponible: --",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        self.lbl_prod_stock.grid(row=5, column=0, columnspan=2, sticky="w", padx=10, pady=(0, 8))

        # Botón para añadir el renglón al carrito
        btn_add_item = ctk.CTkButton(
            item_builder,
            text="➕ Agregar a Factura",
            fg_color="#10b981",
            hover_color="#059669",
            height=32,
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self.add_item_to_list
        )
        btn_add_item.grid(row=5, column=2, sticky="e", padx=10, pady=(0, 8))

        # Lista desplazable de renglones facturados
        ctk.CTkLabel(left_frame, text="📋 Detalle de la Factura:", font=ctk.CTkFont(size=12, weight="bold")).grid(row=8, column=0, columnspan=2, sticky="w", padx=15, pady=(10, 5))

        self.items_scroll = ctk.CTkScrollableFrame(left_frame, fg_color=("gray95", "#181825"), corner_radius=8)
        self.items_scroll.grid(row=9, column=0, columnspan=2, sticky="nsew", padx=15, pady=(0, 15))
        left_frame.grid_rowconfigure(9, weight=1)

        # 3. Columna Derecha: Pago, Tasa BCV y Totales
        right_frame = ctk.CTkFrame(self, fg_color=("white", "#1e1e2e"), corner_radius=12)
        right_frame.grid(row=1, column=1, sticky="nsew", padx=(5, 15), pady=(0, 15))
        right_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(right_frame, text="⚙️ Pago y Tasa BCV", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=15, pady=(15, 10))

        # Caja de método de pago y tasa de cambio
        pay_box = ctk.CTkFrame(right_frame, fg_color=("gray92", "#2b2b36"), corner_radius=10)
        pay_box.pack(fill="x", padx=15, pady=(0, 10))
        pay_box.grid_columnconfigure(1, weight=1)

        # Selector de método de pago
        ctk.CTkLabel(pay_box, text="Método de Pago:").grid(row=0, column=0, sticky="w", padx=12, pady=8)
        self.cmb_payment = ctk.CTkOptionMenu(
            pay_box,
            values=["Efectivo", "Transferencia", "Pago Móvil", "Tarjeta de Crédito/Débito"]
        )
        self.cmb_payment.grid(row=0, column=1, sticky="ew", padx=12, pady=8)

        # Entrada de tasa BCV oficial
        ctk.CTkLabel(pay_box, text="Tasa BCV (Bs/$):").grid(row=1, column=0, sticky="w", padx=12, pady=8)
        
        tasa_frame = ctk.CTkFrame(pay_box, fg_color="transparent")
        tasa_frame.grid(row=1, column=1, sticky="ew", padx=12, pady=8)
        tasa_frame.grid_columnconfigure(0, weight=1)

        self.ent_tasa = ctk.CTkEntry(tasa_frame)
        self.ent_tasa.grid(row=0, column=0, sticky="ew")
        self.ent_tasa.insert(0, "36.50")
        self.ent_tasa.bind("<KeyRelease>", lambda e: self.update_totals())

        # Botón para forzar actualización de tasa desde API
        btn_fetch_rate = ctk.CTkButton(
            tasa_frame,
            text="🔄 API",
            width=50,
            fg_color="#3b82f6",
            hover_color="#2563eb",
            command=self.fetch_bcv_rate_async
        )
        btn_fetch_rate.grid(row=0, column=1, sticky="e", padx=(5, 0))

        # Spinner animado para indicar consulta de tasa BCV en curso
        self.spinner_container = ctk.CTkFrame(pay_box, fg_color="transparent")
        self.spinner_container.grid(row=2, column=0, columnspan=2, sticky="w", padx=12, pady=(0, 6))

        self.tasa_spinner = LoadingSpinner(self.spinner_container, text="Consultando Tasa BCV (dolarapi.com)...", font_size=11)
        self.tasa_spinner.pack(anchor="w")

        # Caja de totales de la factura
        ctk.CTkLabel(right_frame, text="🧾 Resumen de Factura", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=15, pady=(10, 5))

        summary_box = ctk.CTkFrame(right_frame, fg_color=("gray92", "#2b2b36"), corner_radius=10)
        summary_box.pack(fill="x", padx=15, pady=5)
        summary_box.grid_columnconfigure(1, weight=1)

        # Subtotal en USD
        ctk.CTkLabel(summary_box, text="Subtotal ($):", font=ctk.CTkFont(size=13)).grid(row=0, column=0, sticky="w", padx=15, pady=8)
        self.lbl_subtotal = ctk.CTkLabel(summary_box, text="$0.00", font=ctk.CTkFont(size=13, weight="bold"))
        self.lbl_subtotal.grid(row=0, column=1, sticky="e", padx=15, pady=8)

        # Casilla de verificación para aplicar o exonerar el IVA (16%)
        self.tax_var = ctk.BooleanVar(value=True)
        self.chk_tax = ctk.CTkCheckBox(summary_box, text="IVA (16%):", variable=self.tax_var, command=self.update_totals)
        self.chk_tax.grid(row=1, column=0, sticky="w", padx=15, pady=8)
        self.lbl_tax = ctk.CTkLabel(summary_box, text="$0.00", font=ctk.CTkFont(size=13, weight="bold"))
        self.lbl_tax.grid(row=1, column=1, sticky="e", padx=15, pady=8)

        ctk.CTkFrame(summary_box, height=2, fg_color="gray").grid(row=2, column=0, columnspan=2, sticky="ew", padx=10, pady=5)

        # Total General en USD ($)
        ctk.CTkLabel(summary_box, text="TOTAL ($):", font=ctk.CTkFont(size=15, weight="bold")).grid(row=3, column=0, sticky="w", padx=15, pady=8)
        self.lbl_total_dolar = ctk.CTkLabel(summary_box, text="$0.00", font=ctk.CTkFont(size=18, weight="bold"), text_color="#10b981")
        self.lbl_total_dolar.grid(row=3, column=1, sticky="e", padx=15, pady=8)

        # Total General en Bolívares (Bs.)
        ctk.CTkLabel(summary_box, text="TOTAL (Bs):", font=ctk.CTkFont(size=15, weight="bold")).grid(row=4, column=0, sticky="w", padx=15, pady=(0, 12))
        self.lbl_total_bs = ctk.CTkLabel(summary_box, text="Bs. 0.00", font=ctk.CTkFont(size=18, weight="bold"), text_color="#3b82f6")
        self.lbl_total_bs.grid(row=4, column=1, sticky="e", padx=15, pady=(0, 12))

        # Botón para guardar y procesar la venta
        self.btn_save = ctk.CTkButton(
            right_frame,
            text="💾 Procesar Factura",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#10b981",
            hover_color="#059669",
            height=45,
            command=self.process_invoice
        )
        self.btn_save.pack(fill="x", padx=15, pady=(20, 5))

        # Botón para limpiar todos los campos del formulario
        btn_clear = ctk.CTkButton(
            right_frame,
            text="🧹 Limpiar Formulario",
            fg_color="gray",
            hover_color="#4b5563",
            height=35,
            command=self.clear_form
        )
        btn_clear.pack(fill="x", padx=15, pady=(0, 15))

    def fetch_bcv_rate_async(self):
        """
        Consulta la tasa oficial del Banco Central de Venezuela en un hilo
        secundario (Thread) para evitar congelar la interfaz gráfica.
        """
        self.tasa_spinner.start()
        def run():
            rate = database.get_bcv_rate()
            try:
                # Comprobar que el widget continúe abierto antes de invocar after
                if self.winfo_exists():
                    self.after(0, lambda: self.update_bcv_rate_ui(rate))
            except Exception:
                pass

        threading.Thread(target=run, daemon=True).start()

    def update_bcv_rate_ui(self, rate):
        """
        Actualiza el valor de la tasa en la caja de texto y recalcula los totales en bolívares.
        
        Parámetros:
        - rate: Tasa numérica en Bs./USD retornada por la API.
        """
        self.tasa_spinner.stop()
        self.tasa_spinner.lbl_spinner.configure(
            text=f"✅ Tasa BCV Compra (dolarapi.com): Bs. {rate:,.2f}",
            text_color="#10b981"
        )
        self.ent_tasa.delete(0, "end")
        self.ent_tasa.insert(0, f"{rate:.2f}")
        self.update_totals()

    def on_cedula_change(self, event=None):
        """
        Evento disparado al escribir en el campo de cédula.
        Busca si el cliente ya existe en la base de datos para autocompletar
        su nombre y teléfono inmediatamente.
        """
        cedula_str = self.ent_cedula.get().strip()
        if not cedula_str:
            self.lbl_client_status.configure(text="")
            return

        client = database.get_client_by_cedula(cedula_str)
        if client:
            self.ent_nombre_cliente.delete(0, "end")
            self.ent_nombre_cliente.insert(0, client['nombre'])
            self.ent_telefono.delete(0, "end")
            self.ent_telefono.insert(0, client['telefono'] or "")
            self.lbl_client_status.configure(
                text="✅ Cliente registrado (Completado automáticamente)",
                text_color="#10b981"
            )
        else:
            self.lbl_client_status.configure(
                text="🆕 Cliente no encontrado: Complete Nombre y Teléfono",
                text_color="#f59e0b"
            )

    def on_product_search_change(self, event=None):
        """
        Evento disparado al escribir en el campo de búsqueda de productos.
        Permite localizar productos por código ID o por coincidencia en el nombre.
        """
        search_str = self.ent_prod_search.get().strip()
        if not search_str:
            self.selected_product_id = None
            self.lbl_prod_status.configure(text="")
            self.lbl_prod_stock.configure(text="Stock disponible: --")
            return

        matched_prod = None
        # Búsqueda directa por ID si es un valor numérico
        if search_str.isdigit():
            matched_prod = database.get_product_by_id(int(search_str))

        # Búsqueda por texto en nombre
        if not matched_prod:
            prods = database.get_all_products(search_str)
            if len(prods) == 1:
                matched_prod = prods[0]
            elif len(prods) > 1:
                self.selected_product_id = None
                self.lbl_prod_status.configure(
                    text=f"🔍 {len(prods)} coincidencias. Seleccione de la lista.",
                    text_color="#3b82f6"
                )
                prod_names = [f"[ID: {p['id']}] {p['nombre']}" for p in prods]
                self.cmb_product.configure(values=prod_names)
                return

        if matched_prod:
            self.selected_product_id = matched_prod['id']
            self.ent_prod_name.delete(0, "end")
            self.ent_prod_name.insert(0, matched_prod['nombre'])
            self.ent_prod_price.delete(0, "end")
            self.ent_prod_price.insert(0, str(matched_prod['precio']))
            self.lbl_prod_stock.configure(text=f"Stock disponible: {matched_prod['cant']} un.")
            self.lbl_prod_status.configure(
                text=f"✅ Producto registrado en inventario (ID: {matched_prod['id']})",
                text_color="#10b981"
            )
        else:
            self.selected_product_id = None
            self.lbl_prod_stock.configure(text="Stock disponible: N/A (Nuevo)")
            self.lbl_prod_status.configure(
                text="🆕 Producto no encontrado: Complete Nombre y Precio para registrarlo",
                text_color="#f59e0b"
            )

    def on_product_dropdown_select(self, choice):
        """
        Maneja la selección de un producto desde el menú desplegable OptionMenu.
        
        Parámetros:
        - choice: Cadena de texto seleccionada con formato '[ID: X] Nombre'.
        """
        if not choice or "[ID: " not in choice:
            return
        try:
            p_id = int(choice.split("]")[0].replace("[ID: ", ""))
            product = database.get_product_by_id(p_id)
            if product:
                self.selected_product_id = product['id']
                self.ent_prod_search.delete(0, "end")
                self.ent_prod_search.insert(0, str(product['id']))
                self.ent_prod_name.delete(0, "end")
                self.ent_prod_name.insert(0, product['nombre'])
                self.ent_prod_price.delete(0, "end")
                self.ent_prod_price.insert(0, str(product['precio']))
                self.lbl_prod_stock.configure(text=f"Stock disponible: {product['cant']} un.")
                self.lbl_prod_status.configure(
                    text=f"✅ Producto seleccionado del catálogo (ID: {product['id']})",
                    text_color="#10b981"
                )
        except Exception:
            pass

    def load_data(self):
        """Carga la lista completa de productos en el selector OptionMenu."""
        self.all_products = database.get_all_products()
        if self.all_products:
            prod_names = [f"[ID: {p['id']}] {p['nombre']}" for p in self.all_products]
            self.cmb_product.configure(values=prod_names)
            self.cmb_product.set(prod_names[0])
        else:
            self.cmb_product.configure(values=["Sin productos registrados"])

    def add_item_to_list(self):
        """
        Valida y agrega un producto a la lista de renglones de la factura actual:
        1. Comprueba que el precio y cantidad sean válidos mayores a cero.
        2. Verifica que las existencias en inventario cubran la cantidad deseada (incluyendo
           cantidades previas ya presentes en el carrito).
        3. Si el producto ya estaba en la lista, incrementa su cantidad.
        4. Si es nuevo, añade el renglón al listado y actualiza los totales.
        """
        nombre_prod = self.ent_prod_name.get().strip()
        price_str = self.ent_prod_price.get().strip()
        qty_str = self.ent_qty.get().strip()

        if not nombre_prod:
            messagebox.showwarning("Atención", "Ingrese o seleccione el nombre del producto.")
            return

        try:
            precio = float(price_str)
            if precio <= 0:
                raise ValueError()
        except ValueError:
            messagebox.showerror("Error", "Ingrese un precio de producto válido mayor a 0.")
            return

        if not qty_str.isdigit() or int(qty_str) <= 0:
            messagebox.showwarning("Atención", "Ingrese una cantidad válida mayor a 0.")
            return

        qty = int(qty_str)

        # Validación de existencias en almacén
        p_id = self.selected_product_id
        if p_id is not None:
            product = database.get_product_by_id(p_id)
            if product:
                already_in_cart = sum(item['cantidad'] for item in self.current_items if item['id_producto'] == p_id)
                if (already_in_cart + qty) > product['cant']:
                    messagebox.showerror("Stock Insuficiente", f"No hay suficiente stock. Disponible: {product['cant']} un. (En carrito: {already_in_cart})")
                    return
        else:
            # Si el producto no existía en la base de datos, registrarlo automáticamente
            try:
                p_id = database.add_product(nombre_prod, cant=qty*2, precio=precio)
                self.selected_product_id = p_id
                self.load_data()
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo registrar el nuevo producto: {str(e)}")
                return

        subtotal = round(qty * precio, 2)

        # Comprobar si ya existe en la lista para fusionar cantidades
        for item in self.current_items:
            if item['id_producto'] == p_id:
                item['cantidad'] += qty
                item['subtotal'] = round(item['cantidad'] * precio, 2)
                self.render_items_list()
                self.update_totals()
                return

        # Agregar como nuevo renglón
        self.current_items.append({
            "id_producto": p_id,
            "nombre": nombre_prod,
            "cantidad": qty,
            "precio": precio,
            "subtotal": subtotal
        })

        self.render_items_list()
        self.update_totals()

    def render_items_list(self):
        """Dibuja en pantalla los renglones de productos agregados al carrito de compra."""
        for widget in self.items_scroll.winfo_children():
            widget.destroy()

        if not self.current_items:
            ctk.CTkLabel(self.items_scroll, text="No hay productos agregados.", text_color="gray").pack(pady=20)
            return

        for index, item in enumerate(self.current_items):
            row = ctk.CTkFrame(self.items_scroll, fg_color=("white", "#2b2b36"), corner_radius=6)
            row.pack(fill="x", pady=3, padx=5)
            row.grid_columnconfigure(0, weight=2)

            # Nombre del producto
            lbl_name = ctk.CTkLabel(row, text=item['nombre'], font=ctk.CTkFont(size=12, weight="bold"), anchor="w")
            lbl_name.grid(row=0, column=0, sticky="w", padx=10, pady=8)

            # Desglose: Cantidad x Precio = Subtotal
            lbl_details = ctk.CTkLabel(
                row,
                text=f"{item['cantidad']} x ${item['precio']:,.2f} = ${item['subtotal']:,.2f}",
                font=ctk.CTkFont(size=12)
            )
            lbl_details.grid(row=0, column=1, sticky="e", padx=10, pady=8)

            # Botón para remover este renglón
            btn_del = ctk.CTkButton(
                row,
                text="❌",
                width=30,
                height=25,
                fg_color="#ef4444",
                hover_color="#dc2626",
                command=lambda i=index: self.remove_item(i)
            )
            btn_del.grid(row=0, column=2, sticky="e", padx=8, pady=8)

    def remove_item(self, index):
        """
        Elimina un renglón del carrito según su índice en la lista.
        
        Parámetros:
        - index: Posición del elemento en la lista `current_items`.
        """
        if 0 <= index < len(self.current_items):
            self.current_items.pop(index)
            self.render_items_list()
            self.update_totals()

    def update_totals(self):
        """
        Calcula y actualiza en tiempo real las cifras del resumen de compra:
        - Suma de subtotales de productos.
        - Monto de IVA (16% si la casilla está marcada).
        - Total en Dólares ($).
        - Total equivalente en Bolívares (Bs.) según la tasa de cambio ingresada.
        """
        subtotal = sum(item['subtotal'] for item in self.current_items)
        tax = subtotal * 0.16 if self.tax_var.get() else 0.0
        total_dolar = subtotal + tax

        try:
            tasa = float(self.ent_tasa.get().strip())
        except ValueError:
            tasa = 0.0

        total_bs = total_dolar * tasa

        self.lbl_subtotal.configure(text=f"${subtotal:,.2f}")
        self.lbl_tax.configure(text=f"${tax:,.2f}")
        self.lbl_total_dolar.configure(text=f"${total_dolar:,.2f}")
        self.lbl_total_bs.configure(text=f"Bs. {total_bs:,.2f}")

    def process_invoice(self):
        """
        Valida todos los datos obligatorios de la venta y ejecuta la transacción
        en la base de datos de manera asíncrona para registrar la factura y descontar el stock.
        """
        cedula_cliente = self.ent_cedula.get().strip()
        nombre_cliente = self.ent_nombre_cliente.get().strip()
        telefono_cliente = self.ent_telefono.get().strip()

        # Validaciones de negocio
        if not cedula_cliente:
            messagebox.showwarning("Atención", "Ingrese la cédula del cliente.")
            return

        if not nombre_cliente:
            messagebox.showwarning("Atención", "El cliente no se encuentra registrado. Por favor ingrese su Nombre y Teléfono para registrarlo.")
            return

        if not self.current_items:
            messagebox.showwarning("Atención", "Agregue al menos un producto a la factura.")
            return

        try:
            tasa = float(self.ent_tasa.get().strip())
            if tasa <= 0:
                raise ValueError()
        except ValueError:
            messagebox.showerror("Error", "Ingrese una tasa de cambio válida mayor a 0.")
            return

        metodo_pago = self.cmb_payment.get()
        subtotal = sum(item['subtotal'] for item in self.current_items)
        iva_monto = subtotal * 0.16 if self.tax_var.get() else 0.0

        # Retroalimentación visual en el botón de procesamiento
        self.btn_save.configure(text="⏳ Procesando Factura...", state="disabled")
        
        def save_task():
            """Tarea en hilo secundario para procesar la transacción de venta."""
            try:
                inv_id = database.save_invoice(
                    cedula_cliente, nombre_cliente, telefono_cliente,
                    metodo_pago, tasa, iva_monto, self.current_items
                )
                self.after(200, lambda: self.on_save_success(inv_id))
            except Exception as e:
                self.after(200, lambda: self.on_save_error(str(e)))

        threading.Thread(target=save_task, daemon=True).start()

    def on_save_success(self, inv_id):
        """Maneja la confirmación exitosa de emisión de factura."""
        self.btn_save.configure(text="💾 Procesar Factura", state="normal")
        messagebox.showinfo("Éxito", f"¡Factura Nº FAC-{inv_id:04d} procesada y registrada exitosamente!")
        self.clear_form()
        self.load_data()

    def on_save_error(self, err_msg):
        """Maneja cualquier error presentado durante el procesamiento de la venta."""
        self.btn_save.configure(text="💾 Procesar Factura", state="normal")
        messagebox.showerror("Error", f"Ocurrió un error al guardar la factura: {err_msg}")

    def clear_form(self):
        """Restaura todos los campos del formulario a sus valores por defecto."""
        self.ent_cedula.delete(0, "end")
        self.ent_nombre_cliente.delete(0, "end")
        self.ent_telefono.delete(0, "end")
        self.lbl_client_status.configure(text="")
        
        self.ent_prod_search.delete(0, "end")
        self.ent_prod_name.delete(0, "end")
        self.ent_prod_price.delete(0, "end")
        self.lbl_prod_status.configure(text="")
        self.lbl_prod_stock.configure(text="Stock disponible: --")
        self.selected_product_id = None

        self.current_items = []
        self.render_items_list()
        self.update_totals()

    def refresh(self):
        """Actualiza la vista con la información fiscal más reciente y consulta la tasa BCV."""
        negocio = database.get_negocio_config()
        if hasattr(self, 'lbl_inv_biz'):
            self.lbl_inv_biz.configure(text=f"🏢 Emisor: {negocio['nombre']}  |  RIF: {negocio['rif']}")
        self.load_data()
        self.clear_form()
        self.fetch_bcv_rate_async()
