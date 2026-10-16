"""
Módulo del Historial de Facturas (history_view.py)
==================================================
Proporciona la vista para consultar y auditar todas las facturas emitidas:
- Listado cronológico de ventas con ID formateado (FAC-XXXX), fecha, cliente y totales.
- Búsqueda en tiempo real por número de factura, cédula o nombre del cliente.
- Modal de detalle de factura con membrete del negocio y desglose de renglones.
- Exportación estructurada a libros de Excel (.xlsx) agrupados por Año-Mes y hojas diarias.
- Acceso directo a la carpeta local de reportes en el explorador de Windows.
"""

import customtkinter as ctk
from tkinter import filedialog, messagebox
import database
import excel_exporter

class HistoryView(ctk.CTkFrame):
    """
    Vista de Historial y Auditoría de Facturación.
    
    Hereda de `ctk.CTkFrame` para integrarse en la ventana principal.
    
    Parámetros:
    - parent: Contenedor padre (`main_container`).
    - nav_callback: Callback para navegación entre vistas.
    """
    def __init__(self, parent, nav_callback):
        super().__init__(parent, fg_color="transparent")
        self.nav_callback = nav_callback
        
        # Estructura de filas de la cuadrícula:
        # Fila 0: Barra de título
        # Fila 1: Barra de búsqueda y botones de exportación
        # Fila 2: Tabla desplazable con las facturas emitidas
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        
        self.build_ui()
        self.load_history()

    def build_ui(self):
        """
        Construye los componentes de la interfaz de usuario:
        1. Encabezado superior.
        2. Barra de filtros interactivos y accesos a exportación Excel / carpeta reportes.
        3. Tabla desplazable (`CTkScrollableFrame`) para listar las facturas.
        """
        # 1. Barra de Encabezado Superior
        top_frame = ctk.CTkFrame(self, fg_color=("white", "#1e1e2e"), corner_radius=12)
        top_frame.grid(row=0, column=0, sticky="ew", padx=15, pady=(15, 10))
        top_frame.grid_columnconfigure(0, weight=1)
        
        lbl_title = ctk.CTkLabel(top_frame, text="📜 Historial de Facturas Emitidas", font=ctk.CTkFont(size=20, weight="bold"))
        lbl_title.grid(row=0, column=0, sticky="w", padx=20, pady=15)
        
        # 2. Barra de Búsqueda y Botones de Acción
        filter_frame = ctk.CTkFrame(self, fg_color=("white", "#1e1e2e"), corner_radius=12)
        filter_frame.grid(row=1, column=0, sticky="ew", padx=15, pady=5)
        filter_frame.grid_columnconfigure(0, weight=1)
        
        # Entrada de búsqueda en tiempo real
        self.ent_search = ctk.CTkEntry(
            filter_frame, 
            placeholder_text="🔍 Buscar por Nº de Factura, Cédula o Nombre del Cliente...",
            height=38
        )
        self.ent_search.grid(row=0, column=0, sticky="ew", padx=15, pady=12)
        self.ent_search.bind("<KeyRelease>", lambda e: self.load_history())

        # Botón para exportar a Excel por Año-Mes y Días
        btn_excel = ctk.CTkButton(
            filter_frame,
            text="📊 Exportar a Excel",
            fg_color="#10b981",
            hover_color="#059669",
            height=38,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self.export_excel
        )
        btn_excel.grid(row=0, column=1, sticky="e", padx=(0, 10), pady=12)

        # Botón para abrir la carpeta 'reportes' en Windows Explorer
        btn_folder = ctk.CTkButton(
            filter_frame,
            text="📁 Carpeta Reportes",
            fg_color=("#3b82f6", "#2563eb"),
            hover_color=("#2563eb", "#1d4ed8"),
            height=38,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=excel_exporter.open_reports_folder
        )
        btn_folder.grid(row=0, column=2, sticky="e", padx=(0, 15), pady=12)

        # 3. Contenedor Desplazable para la Lista de Facturas
        self.scroll_table = ctk.CTkScrollableFrame(self, fg_color=("white", "#1e1e2e"), corner_radius=12)
        self.scroll_table.grid(row=2, column=0, sticky="nsew", padx=15, pady=(5, 15))

    def load_history(self):
        """
        Consulta las facturas en la base de datos aplicando el filtro de búsqueda
        y renderiza dinámicamente cada registro en la tabla con sus totales y botón de detalle.
        """
        # Limpiar registros previos en pantalla
        for widget in self.scroll_table.winfo_children():
            widget.destroy()
            
        search_term = self.ent_search.get().strip()
        invoices = database.get_all_invoices(search_term)
        
        # Si no hay facturas registradas o coincidentes
        if not invoices:
            ctk.CTkLabel(self.scroll_table, text="No se encontraron facturas.", text_color="gray", font=ctk.CTkFont(size=14)).pack(pady=40)
            return

        # Cabecera de la tabla de facturas
        header_row = ctk.CTkFrame(self.scroll_table, fg_color=("gray85", "#2b2b36"), corner_radius=6)
        header_row.pack(fill="x", padx=10, pady=(10, 5))
        
        ctk.CTkLabel(header_row, text="Nº Factura", font=ctk.CTkFont(size=12, weight="bold"), width=90).pack(side="left", padx=10, pady=8)
        ctk.CTkLabel(header_row, text="Fecha", font=ctk.CTkFont(size=12, weight="bold"), width=130).pack(side="left", padx=5, pady=8)
        ctk.CTkLabel(header_row, text="Cédula", font=ctk.CTkFont(size=12, weight="bold"), width=100).pack(side="left", padx=5, pady=8)
        ctk.CTkLabel(header_row, text="Cliente", font=ctk.CTkFont(size=12, weight="bold"), anchor="w").pack(side="left", padx=10, pady=8, expand=True, fill="x")
        ctk.CTkLabel(header_row, text="Total ($)", font=ctk.CTkFont(size=12, weight="bold"), width=90).pack(side="left", padx=5, pady=8)
        ctk.CTkLabel(header_row, text="Total (Bs)", font=ctk.CTkFont(size=12, weight="bold"), width=110).pack(side="left", padx=5, pady=8)
        ctk.CTkLabel(header_row, text="Acción", font=ctk.CTkFont(size=12, weight="bold"), width=90).pack(side="right", padx=10, pady=8)

        # Renderizar cada factura encontrada
        for inv in invoices:
            row = ctk.CTkFrame(self.scroll_table, fg_color=("gray95", "#181825"), corner_radius=6)
            row.pack(fill="x", padx=10, pady=3)
            
            # Número de factura formateado
            ctk.CTkLabel(row, text=f"FAC-{inv['id']:04d}", font=ctk.CTkFont(size=12, weight="bold"), width=90).pack(side="left", padx=10, pady=8)
            
            # Fecha y hora de emisión (truncando microsegundos)
            date_fmt = inv['fecha'].split(".")[0]
            ctk.CTkLabel(row, text=date_fmt, font=ctk.CTkFont(size=11), text_color="gray", width=130).pack(side="left", padx=5, pady=8)
            
            # Cédula del cliente
            ctk.CTkLabel(row, text=inv['cedula_cliente'], font=ctk.CTkFont(size=11), width=100).pack(side="left", padx=5, pady=8)
            
            # Nombre del cliente
            ctk.CTkLabel(row, text=inv['cliente_nombre'] or "N/A", font=ctk.CTkFont(size=12), anchor="w").pack(side="left", padx=10, pady=8, expand=True, fill="x")
            
            # Total en dólares ($)
            ctk.CTkLabel(row, text=f"${inv['total_dolar']:,.2f}", font=ctk.CTkFont(size=12, weight="bold"), text_color="#10b981", width=90).pack(side="left", padx=5, pady=8)
            # Total en bolívares (Bs.)
            ctk.CTkLabel(row, text=f"Bs. {inv['total_bs']:,.2f}", font=ctk.CTkFont(size=12, weight="bold"), text_color="#3b82f6", width=110).pack(side="left", padx=5, pady=8)
            
            # Botón para visualizar el desglose detallado de la factura
            btn_view = ctk.CTkButton(
                row, 
                text="👁️ Detalle", 
                width=80, 
                height=28, 
                font=ctk.CTkFont(size=11),
                command=lambda i_id=inv['id']: self.show_invoice_detail_modal(i_id)
            )
            btn_view.pack(side="right", padx=10, pady=8)

    def export_excel(self):
        """
        Ejecuta la exportación de todas las facturas a la carpeta 'reportes/'
        organizadas en archivos por Año-Mes y hojas por Día.
        Pregunta al usuario si desea abrir la carpeta de reportes al finalizar.
        """
        invoices = database.get_all_invoices()
        if not invoices:
            messagebox.showwarning("Atención", "No hay facturas en el historial para exportar.")
            return

        try:
            saved_files = excel_exporter.export_invoices_by_day_and_month(invoices)
            if not saved_files:
                messagebox.showwarning("Atención", "No se encontraron facturas para exportar.")
                return

            import os
            files_list = "\n".join([f"• {os.path.basename(f)}" for f in saved_files])
            msg = (
                f"✅ Facturas exportadas exitosamente a la carpeta 'reportes':\n\n"
                f"{files_list}\n\n"
                f"Cada archivo está dividido en hojas según el día (ej. 'Día 07').\n"
                f"Si ya existía un reporte previo para ese día, fue actualizado con los datos más recientes.\n\n"
                f"¿Desea abrir la carpeta 'reportes' ahora?"
            )
            if messagebox.askyesno("Éxito - Reportes Generados", msg):
                excel_exporter.open_reports_folder()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo exportar a Excel: {str(e)}")

    def show_invoice_detail_modal(self, invoice_id):
        """
        Despliega un diálogo emergente modal con el recibo completo de la factura:
        - Membrete comercial de la empresa emisora (Nombre, RIF, Dirección, Teléfono).
        - Identificador de factura, fecha, método de pago y tasa de cambio aplicada.
        - Datos del cliente.
        - Tabla con todos los renglones de productos, cantidades, precios unitarios y subtotales.
        - Pie de página con el monto total a pagar en USD y Bolívares.
        
        Parámetros:
        - invoice_id: Identificador numérico de la factura en la base de datos.
        """
        inv, items = database.get_invoice_details(invoice_id)
        if not inv:
            return

        # Configuración de la ventana modal
        dialog = ctk.CTkToplevel(self)
        dialog.title(f"Detalle de Factura FAC-{inv['id']:04d}")
        dialog.geometry("620x560")
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()
        
        dialog.grid_columnconfigure(0, weight=1)
        dialog.grid_rowconfigure(2, weight=1)

        # 1. Membrete de la Empresa y Datos de Factura
        header = ctk.CTkFrame(dialog, fg_color=("white", "#1e1e2e"), corner_radius=10)
        header.grid(row=0, column=0, sticky="ew", padx=15, pady=15)
        
        negocio = database.get_negocio_config()
        ctk.CTkLabel(header, text=f"🏢 {negocio['nombre']}", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=15, pady=(10, 1))
        
        biz_info = f"RIF: {negocio['rif']}  |  {negocio['direccion']}"
        if negocio.get('telefono'):
            biz_info += f"  |  Tel: {negocio['telefono']}"
        ctk.CTkLabel(header, text=biz_info, font=ctk.CTkFont(size=11), text_color="gray").pack(anchor="w", padx=15, pady=(0, 6))

        ctk.CTkLabel(header, text=f"FACTURA Nº FAC-{inv['id']:04d}", font=ctk.CTkFont(size=15, weight="bold"), text_color=("#2563eb", "#60a5fa")).pack(anchor="w", padx=15, pady=(2, 2))
        
        info_str = f"Fecha: {inv['fecha']} | Pago: {inv['metodo_pago']} | Tasa: Bs. {inv['tasa']:,.2f}/$"
        ctk.CTkLabel(header, text=info_str, font=ctk.CTkFont(size=11), text_color="gray").pack(anchor="w", padx=15, pady=(0, 10))

        # 2. Tarjeta con Datos del Cliente
        client_box = ctk.CTkFrame(dialog, fg_color=("gray92", "#2b2b36"), corner_radius=8)
        client_box.grid(row=1, column=0, sticky="ew", padx=15, pady=(0, 10))
        
        ctk.CTkLabel(client_box, text=f"Cliente: {inv['cliente_nombre']} ({inv['cedula_cliente']})", font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=15, pady=(8, 2))
        if inv['cliente_telefono']:
            ctk.CTkLabel(client_box, text=f"Teléfono: {inv['cliente_telefono']}", font=ctk.CTkFont(size=11), text_color="gray").pack(anchor="w", padx=15, pady=(0, 8))

        # 3. Tabla Desplazable de Renglones / Productos Facturados
        items_scroll = ctk.CTkScrollableFrame(dialog, fg_color=("gray95", "#181825"), corner_radius=8)
        items_scroll.grid(row=2, column=0, sticky="nsew", padx=15, pady=(0, 10))
        
        hdr = ctk.CTkFrame(items_scroll, fg_color="transparent")
        hdr.pack(fill="x", padx=5, pady=5)
        ctk.CTkLabel(hdr, text="Producto", font=ctk.CTkFont(size=12, weight="bold"), anchor="w").pack(side="left", padx=5, expand=True, fill="x")
        ctk.CTkLabel(hdr, text="Cant.", font=ctk.CTkFont(size=12, weight="bold"), width=50).pack(side="left", padx=5)
        ctk.CTkLabel(hdr, text="Precio U. ($)", font=ctk.CTkFont(size=12, weight="bold"), width=90).pack(side="left", padx=5)
        ctk.CTkLabel(hdr, text="Subtotal ($)", font=ctk.CTkFont(size=12, weight="bold"), width=90).pack(side="right", padx=5)

        for item in items:
            row = ctk.CTkFrame(items_scroll, fg_color=("white", "#2b2b36"), corner_radius=6)
            row.pack(fill="x", padx=5, pady=2)
            
            subtotal = item['cantidad'] * item['producto_precio']
            ctk.CTkLabel(row, text=item['producto_nombre'], font=ctk.CTkFont(size=12), anchor="w").pack(side="left", padx=10, pady=6, expand=True, fill="x")
            ctk.CTkLabel(row, text=str(item['cantidad']), font=ctk.CTkFont(size=12), width=50).pack(side="left", padx=5, pady=6)
            ctk.CTkLabel(row, text=f"${item['producto_precio']:,.2f}", font=ctk.CTkFont(size=12), width=90).pack(side="left", padx=5, pady=6)
            ctk.CTkLabel(row, text=f"${subtotal:,.2f}", font=ctk.CTkFont(size=12, weight="bold"), width=90).pack(side="right", padx=10, pady=6)

        # 4. Pie de Factura con Totales
        footer = ctk.CTkFrame(dialog, fg_color=("white", "#1e1e2e"), corner_radius=10)
        footer.grid(row=3, column=0, sticky="ew", padx=15, pady=(0, 15))
        
        tot_text = f"TOTAL: ${inv['total_dolar']:,.2f}  |  Bs. {inv['total_bs']:,.2f}"
        ctk.CTkLabel(footer, text="MONTO TOTAL:", font=ctk.CTkFont(size=14, weight="bold")).pack(side="left", padx=15, pady=12)
        ctk.CTkLabel(footer, text=tot_text, font=ctk.CTkFont(size=15, weight="bold"), text_color="#10b981").pack(side="right", padx=15, pady=12)

    def refresh(self):
        """Recarga el listado de facturas al regresar a esta vista."""
        self.load_history()
