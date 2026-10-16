"""
Módulo de Gestión de Inventario y Productos (inventory_view.py)
==============================================================
Proporciona la vista para la administración completa del catálogo de productos:
- Visualización interactiva del stock de productos con IDs, nombres, existencias y precios.
- Badges dinámicos de advertencia visual para productos con stock bajo (≤ 5 unidades).
- Búsqueda en tiempo real por ID o nombre del producto.
- Registro de nuevos productos con validación numérica de existencias y precios en USD.
- Modificación y eliminación de productos existentes.
- Exportación del catálogo completo a hojas de cálculo formateadas en Excel.
"""

import customtkinter as ctk
from tkinter import filedialog, messagebox
import database
import excel_exporter
from animations import LoadingSpinner

class InventoryView(ctk.CTkFrame):
    """
    Vista de Catálogo de Productos y Control de Inventario.
    
    Hereda de `ctk.CTkFrame` para integrarse en el contenedor de vistas de la aplicación.
    
    Parámetros:
    - parent: Contenedor padre (`main_container`).
    - nav_callback: Callback para navegación entre vistas.
    """
    def __init__(self, parent, nav_callback):
        super().__init__(parent, fg_color="transparent")
        self.nav_callback = nav_callback
        
        # Estructura de la cuadrícula:
        # Fila 0: Barra de título
        # Fila 1: Barra de acciones (búsqueda, exportación y nuevo producto)
        # Fila 2: Tabla desplazable de productos
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        
        self.build_ui()
        self.load_inventory()

    def build_ui(self):
        """
        Construye la interfaz visual del módulo de inventario:
        1. Encabezado de la vista.
        2. Barra de acciones con buscador, exportador a Excel, acceso a carpeta y botón de agregar.
        3. Tabla desplazable (`CTkScrollableFrame`) para desplegar la lista de productos.
        """
        # 1. Barra de Encabezado Superior
        top_frame = ctk.CTkFrame(self, fg_color=("white", "#1e1e2e"), corner_radius=12)
        top_frame.grid(row=0, column=0, sticky="ew", padx=15, pady=(15, 10))
        top_frame.grid_columnconfigure(0, weight=1)
        
        lbl_title = ctk.CTkLabel(top_frame, text="📦 Gestión de Productos e Inventario", font=ctk.CTkFont(size=20, weight="bold"))
        lbl_title.grid(row=0, column=0, sticky="w", padx=20, pady=15)
        
        # 2. Barra de Herramientas y Filtros
        action_bar = ctk.CTkFrame(self, fg_color=("white", "#1e1e2e"), corner_radius=12)
        action_bar.grid(row=1, column=0, sticky="ew", padx=15, pady=5)
        action_bar.grid_columnconfigure(0, weight=1)
        
        # Campo de búsqueda interactiva
        self.ent_search = ctk.CTkEntry(
            action_bar, 
            placeholder_text="🔍 Buscar por ID o nombre del producto...",
            height=38
        )
        self.ent_search.grid(row=0, column=0, sticky="ew", padx=15, pady=12)
        self.ent_search.bind("<KeyRelease>", lambda e: self.load_inventory())

        # Botón para exportar a Excel
        btn_excel = ctk.CTkButton(
            action_bar,
            text="📊 Exportar a Excel",
            fg_color="#3b82f6",
            hover_color="#2563eb",
            height=38,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self.export_excel
        )
        btn_excel.grid(row=0, column=1, sticky="e", padx=(0, 5), pady=12)

        # Botón para abrir la carpeta de reportes
        btn_folder = ctk.CTkButton(
            action_bar,
            text="📁 Carpeta Reportes",
            fg_color=("#475569", "#334155"),
            hover_color=("#334155", "#1e293b"),
            height=38,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=excel_exporter.open_reports_folder
        )
        btn_folder.grid(row=0, column=2, sticky="e", padx=(0, 5), pady=12)
        
        # Botón para registrar nuevo producto
        btn_add = ctk.CTkButton(
            action_bar, 
            text="➕ Nuevo Producto", 
            fg_color="#10b981", 
            hover_color="#059669",
            height=38,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self.open_add_product_modal
        )
        btn_add.grid(row=0, column=3, sticky="e", padx=15, pady=12)

        # 3. Contenedor Desplazable de Productos
        self.scroll_table = ctk.CTkScrollableFrame(self, fg_color=("white", "#1e1e2e"), corner_radius=12)
        self.scroll_table.grid(row=2, column=0, sticky="nsew", padx=15, pady=(5, 15))

    def load_inventory(self):
        """
        Consulta los productos en la base de datos aplicando el filtro de búsqueda
        y renderiza dinámicamente cada producto en la tabla con sus badges de stock y acciones.
        """
        # Limpiar registros previos en pantalla
        for widget in self.scroll_table.winfo_children():
            widget.destroy()
            
        search_term = self.ent_search.get().strip()
        products = database.get_all_products(search_term)
        
        # Si no hay productos registrados o coincidentes
        if not products:
            ctk.CTkLabel(self.scroll_table, text="No hay productos registrados.", text_color="gray", font=ctk.CTkFont(size=14)).pack(pady=40)
            return

        # Cabecera de la tabla de inventario
        header_row = ctk.CTkFrame(self.scroll_table, fg_color=("gray85", "#2b2b36"), corner_radius=6)
        header_row.pack(fill="x", padx=10, pady=(10, 5))
        
        ctk.CTkLabel(header_row, text="ID", font=ctk.CTkFont(size=12, weight="bold"), width=60).pack(side="left", padx=10, pady=8)
        ctk.CTkLabel(header_row, text="Nombre del Producto", font=ctk.CTkFont(size=12, weight="bold"), anchor="w").pack(side="left", padx=10, pady=8, expand=True, fill="x")
        ctk.CTkLabel(header_row, text="Cantidad (Stock)", font=ctk.CTkFont(size=12, weight="bold"), width=120).pack(side="left", padx=10, pady=8)
        ctk.CTkLabel(header_row, text="Precio ($)", font=ctk.CTkFont(size=12, weight="bold"), width=110).pack(side="left", padx=10, pady=8)
        ctk.CTkLabel(header_row, text="Acciones", font=ctk.CTkFont(size=12, weight="bold"), width=110).pack(side="right", padx=10, pady=8)

        # Renderizar cada producto encontrado
        for prod in products:
            row = ctk.CTkFrame(self.scroll_table, fg_color=("gray95", "#181825"), corner_radius=6)
            row.pack(fill="x", padx=10, pady=3)
            
            # ID del producto
            ctk.CTkLabel(row, text=str(prod['id']), font=ctk.CTkFont(size=12, weight="bold"), width=60).pack(side="left", padx=10, pady=8)
            
            # Nombre del producto
            ctk.CTkLabel(row, text=prod['nombre'], font=ctk.CTkFont(size=12), anchor="w").pack(side="left", padx=10, pady=8, expand=True, fill="x")
            
            # Cantidad y Badge de Alerta de Stock Bajo (≤ 5 unidades)
            is_low = prod['cant'] <= 5
            stock_bg = "#ef4444" if is_low else "#10b981"
            stock_txt = f"{prod['cant']} un." + (" ⚠️ Alerta" if is_low else "")
            
            badge_stock = ctk.CTkLabel(
                row, 
                text=stock_txt, 
                fg_color=stock_bg, 
                text_color="white", 
                corner_radius=4, 
                width=110, 
                font=ctk.CTkFont(size=11, weight="bold")
            )
            badge_stock.pack(side="left", padx=10, pady=8)
            
            # Precio unitario en USD ($)
            ctk.CTkLabel(row, text=f"${prod['precio']:,.2f}", font=ctk.CTkFont(size=12, weight="bold"), text_color="#10b981", width=110).pack(side="left", padx=10, pady=8)
            
            # Contenedor de botones de acción rápida (Editar / Eliminar)
            btn_box = ctk.CTkFrame(row, fg_color="transparent")
            btn_box.pack(side="right", padx=10, pady=8)
            
            # Botón Editar
            btn_edit = ctk.CTkButton(
                btn_box, 
                text="✏️", 
                width=35, 
                height=28, 
                fg_color="#3b82f6", 
                hover_color="#2563eb",
                command=lambda p=prod: self.open_edit_product_modal(p)
            )
            btn_edit.pack(side="left", padx=2)
            
            # Botón Eliminar
            btn_del = ctk.CTkButton(
                btn_box, 
                text="🗑️", 
                width=35, 
                height=28, 
                fg_color="#ef4444", 
                hover_color="#dc2626",
                command=lambda p_id=prod['id'], p_name=prod['nombre']: self.delete_product(p_id, p_name)
            )
            btn_del.pack(side="left", padx=2)

    def export_excel(self):
        """
        Exporta el catálogo completo a un archivo Excel en la carpeta 'reportes/'
        con métricas de stock y valorización total del inventario.
        """
        products = database.get_all_products()
        if not products:
            messagebox.showwarning("Atención", "No hay productos registrados para exportar.")
            return

        try:
            filepath = excel_exporter.export_products_to_excel()
            import os
            msg = (
                f"✅ Inventario de productos exportado exitosamente a la carpeta 'reportes':\n\n"
                f"• Archivo: {os.path.basename(filepath)}\n"
                f"• Ubicación: {filepath}\n"
                f"• Total de productos: {len(products)}\n\n"
                f"¿Desea abrir la carpeta 'reportes' ahora?"
            )
            if messagebox.askyesno("Éxito - Inventario Exportado", msg):
                excel_exporter.open_reports_folder()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo exportar a Excel: {str(e)}")

    def open_add_product_modal(self):
        """Abre el diálogo modal en modo 'Creación' para agregar un nuevo producto."""
        self.show_product_form_modal()

    def open_edit_product_modal(self, product):
        """Abre el diálogo modal en modo 'Edición' con los datos precargados del producto."""
        self.show_product_form_modal(product)

    def show_product_form_modal(self, product=None):
        """
        Construye y gestiona el formulario emergente para registrar o editar un producto.
        
        Parámetros:
        - product: Diccionario con datos del producto si es edición, o None si es nuevo.
        """
        is_edit = product is not None
        title = "✏️ Editar Producto" if is_edit else "➕ Registrar Nuevo Producto"
        
        # Configuración de ventana emergente secundaria
        dialog = ctk.CTkToplevel(self)
        dialog.title(title)
        dialog.geometry("420x350")
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()
        
        dialog.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(dialog, text=title, font=ctk.CTkFont(size=16, weight="bold")).grid(row=0, column=0, columnspan=2, sticky="w", padx=20, pady=15)
        
        fields = [
            ("Nombre del Producto:", "ent_nombre", product["nombre"] if is_edit else ""),
            ("Cantidad (Stock):", "ent_cant", str(product["cant"]) if is_edit else "10"),
            ("Precio ($):", "ent_precio", str(product["precio"]) if is_edit else "0.00"),
        ]
        
        entries = {}
        
        # Generar campos de entrada
        for idx, (label_text, var_name, default_val) in enumerate(fields, start=1):
            ctk.CTkLabel(dialog, text=label_text, font=ctk.CTkFont(size=12)).grid(row=idx, column=0, sticky="w", padx=20, pady=10)
            ent = ctk.CTkEntry(dialog, height=35)
            ent.grid(row=idx, column=1, sticky="ew", padx=20, pady=10)
            ent.insert(0, default_val)
            entries[var_name] = ent

        def save_product_data():
            """Valida los campos numéricos y persiste el producto en la base de datos."""
            nombre = entries["ent_nombre"].get().strip()
            
            if not nombre:
                messagebox.showwarning("Atención", "Ingrese el nombre del producto.", parent=dialog)
                return
                
            try:
                cant = int(entries["ent_cant"].get().strip())
                precio = float(entries["ent_precio"].get().strip())
                if cant < 0 or precio < 0:
                    raise ValueError()
            except ValueError:
                messagebox.showerror("Error", "La cantidad debe ser un número entero >= 0 y el precio un número válido >= 0.", parent=dialog)
                return
                
            try:
                if is_edit:
                    database.update_product(product['id'], nombre, cant, precio)
                    messagebox.showinfo("Éxito", "Producto actualizado correctamente.")
                else:
                    database.add_product(nombre, cant, precio)
                    messagebox.showinfo("Éxito", "Producto registrado correctamente.")
                    
                dialog.destroy()
                self.load_inventory()
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo guardar el producto: {str(e)}", parent=dialog)

        # Botón de guardado
        btn_save = ctk.CTkButton(
            dialog, 
            text="💾 Guardar Producto", 
            fg_color="#10b981", 
            hover_color="#059669",
            height=40,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=save_product_data
        )
        btn_save.grid(row=4, column=0, columnspan=2, sticky="ew", padx=20, pady=25)

    def delete_product(self, product_id, product_name):
        """
        Solicita confirmación antes de eliminar el producto de la base de datos.
        
        Parámetros:
        - product_id: ID numérico del producto.
        - product_name: Nombre del producto (para el diálogo de confirmación).
        """
        confirm = messagebox.askyesno("Confirmar Eliminación", f"¿Está seguro de eliminar el producto '{product_name}' (ID: {product_id})?")
        if confirm:
            try:
                database.delete_product(product_id)
                messagebox.showinfo("Eliminado", "Producto eliminado con éxito.")
                self.load_inventory()
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo eliminar el producto: {str(e)}")

    def refresh(self):
        """Recarga el inventario al mostrar la vista."""
        self.load_inventory()
