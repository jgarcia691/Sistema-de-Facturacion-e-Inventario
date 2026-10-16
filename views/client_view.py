"""
Módulo de Gestión de Clientes (client_view.py)
==============================================
Proporciona la vista para la administración completa de los clientes:
- Listado y búsqueda en tiempo real por Cédula, Nombre o Teléfono.
- Registro de nuevos clientes mediante ventana emergente.
- Edición de información de contacto de clientes existentes.
- Eliminación de registros con confirmación previa.
- Exportación del directorio completo a hojas de cálculo en Excel.
"""

import customtkinter as ctk
from tkinter import filedialog, messagebox
import database
import excel_exporter

class ClientView(ctk.CTkFrame):
    """
    Vista de Gestión y Directorio de Clientes.
    
    Hereda de `ctk.CTkFrame` para integrarse en el contenedor de vistas de la ventana principal.
    
    Parámetros:
    - parent: Contenedor padre (`main_container`).
    - nav_callback: Callback para navegación entre vistas si se requiere.
    """
    def __init__(self, parent, nav_callback):
        super().__init__(parent, fg_color="transparent")
        self.nav_callback = nav_callback

        # Configuración de pesos de la cuadrícula:
        # Fila 0: Barra de título
        # Fila 1: Barra de búsqueda y acciones
        # Fila 2: Tabla desplazable con lista de clientes
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self.build_ui()
        self.load_clients()

    def build_ui(self):
        """
        Construye los componentes visuales de la vista:
        1. Encabezado con título del módulo.
        2. Barra de acciones: campo de búsqueda, botón de exportar a Excel y botón de nuevo cliente.
        3. Tabla desplazable (`CTkScrollableFrame`) para desplegar la lista de clientes.
        """
        # 1. Barra de Encabezado Superior
        top_frame = ctk.CTkFrame(self, fg_color=("white", "#1e1e2e"), corner_radius=12)
        top_frame.grid(row=0, column=0, sticky="ew", padx=15, pady=(15, 10))
        top_frame.grid_columnconfigure(0, weight=1)

        lbl_title = ctk.CTkLabel(top_frame, text="👥 Gestión de Clientes", font=ctk.CTkFont(size=20, weight="bold"))
        lbl_title.grid(row=0, column=0, sticky="w", padx=20, pady=15)

        # 2. Barra de Búsqueda y Acciones
        action_bar = ctk.CTkFrame(self, fg_color=("white", "#1e1e2e"), corner_radius=12)
        action_bar.grid(row=1, column=0, sticky="ew", padx=15, pady=5)
        action_bar.grid_columnconfigure(0, weight=1)

        # Campo de búsqueda interactiva
        self.ent_search = ctk.CTkEntry(
            action_bar,
            placeholder_text="🔍 Buscar por Cédula, Nombre o Teléfono...",
            height=38
        )
        self.ent_search.grid(row=0, column=0, sticky="ew", padx=15, pady=12)
        # Filtrado en tiempo real al soltar cada tecla
        self.ent_search.bind("<KeyRelease>", lambda e: self.load_clients())

        # Botón para exportar directorio a Excel
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

        # Botón para registrar nuevo cliente
        btn_add = ctk.CTkButton(
            action_bar,
            text="➕ Nuevo Cliente",
            fg_color="#10b981",
            hover_color="#059669",
            height=38,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self.open_add_client_modal
        )
        btn_add.grid(row=0, column=2, sticky="e", padx=15, pady=12)

        # 3. Contenedor Desplazable para la Tabla de Clientes
        self.scroll_table = ctk.CTkScrollableFrame(self, fg_color=("white", "#1e1e2e"), corner_radius=12)
        self.scroll_table.grid(row=2, column=0, sticky="nsew", padx=15, pady=(5, 15))

    def load_clients(self):
        """
        Consulta los clientes en la base de datos aplicando el término de búsqueda actual
        y renderiza dinámicamente cada fila con su Cédula, Nombre, Teléfono y botones de acción.
        """
        # Limpiar filas previas de la tabla
        for widget in self.scroll_table.winfo_children():
            widget.destroy()

        search_term = self.ent_search.get().strip()
        clients = database.get_all_clients(search_term)

        # Si no hay registros que coincidan, mostrar aviso informativo
        if not clients:
            ctk.CTkLabel(self.scroll_table, text="No hay clientes registrados.", text_color="gray", font=ctk.CTkFont(size=14)).pack(pady=40)
            return

        # Cabecera de la tabla de clientes
        header_row = ctk.CTkFrame(self.scroll_table, fg_color=("gray85", "#2b2b36"), corner_radius=6)
        header_row.pack(fill="x", padx=10, pady=(10, 5))

        ctk.CTkLabel(header_row, text="Cédula", font=ctk.CTkFont(size=12, weight="bold"), width=120).pack(side="left", padx=10, pady=8)
        ctk.CTkLabel(header_row, text="Nombre del Cliente", font=ctk.CTkFont(size=12, weight="bold"), anchor="w").pack(side="left", padx=10, pady=8, expand=True, fill="x")
        ctk.CTkLabel(header_row, text="Teléfono", font=ctk.CTkFont(size=12, weight="bold"), width=150).pack(side="left", padx=10, pady=8)
        ctk.CTkLabel(header_row, text="Acciones", font=ctk.CTkFont(size=12, weight="bold"), width=110).pack(side="right", padx=10, pady=8)

        # Renderizar cada cliente como una fila interactiva
        for cli in clients:
            row = ctk.CTkFrame(self.scroll_table, fg_color=("gray95", "#181825"), corner_radius=6)
            row.pack(fill="x", padx=10, pady=3)

            # Cédula del cliente
            ctk.CTkLabel(row, text=cli['cedula'], font=ctk.CTkFont(size=12, weight="bold"), width=120).pack(side="left", padx=10, pady=8)

            # Nombre completo
            ctk.CTkLabel(row, text=cli['nombre'], font=ctk.CTkFont(size=12), anchor="w").pack(side="left", padx=10, pady=8, expand=True, fill="x")

            # Teléfono de contacto
            ctk.CTkLabel(row, text=cli['telefono'] or "N/A", font=ctk.CTkFont(size=12), width=150).pack(side="left", padx=10, pady=8)

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
                command=lambda c=cli: self.open_edit_client_modal(c)
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
                command=lambda c_ced=cli['cedula'], c_nom=cli['nombre']: self.delete_client(c_ced, c_nom)
            )
            btn_del.pack(side="left", padx=2)

    def export_excel(self):
        """
        Permite al usuario seleccionar la ubicación en su equipo para exportar
        el directorio completo de clientes a formato Excel (.xlsx).
        """
        clients = database.get_all_clients()
        if not clients:
            messagebox.showwarning("Atención", "No hay clientes registrados para exportar.")
            return

        # Diálogo para seleccionar la ruta de guardado
        filepath = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Archivos de Excel", "*.xlsx")],
            initialfile="Directorio_Clientes.xlsx"
        )
        if filepath:
            try:
                excel_exporter.export_clients_to_excel(filepath)
                messagebox.showinfo("Éxito", f"Directorio de clientes exportado en:\n{filepath}")
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo exportar a Excel: {str(e)}")

    def open_add_client_modal(self):
        """Abre el diálogo modal en modo 'Creación' para agregar un nuevo cliente."""
        self.show_client_form_modal()

    def open_edit_client_modal(self, client):
        """Abre el diálogo modal en modo 'Edición' con los datos precargados del cliente."""
        self.show_client_form_modal(client)

    def show_client_form_modal(self, client=None):
        """
        Construye y gestiona el formulario emergente para crear o editar un cliente.
        
        Parámetros:
        - client: Diccionario con datos del cliente si es edición, o None si es nuevo.
        """
        is_edit = client is not None
        title = "✏️ Editar Cliente" if is_edit else "➕ Registrar Nuevo Cliente"

        # Configurar ventana emergente secundaria
        dialog = ctk.CTkToplevel(self)
        dialog.title(title)
        dialog.geometry("420x350")
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()

        dialog.grid_columnconfigure(1, weight=1)

        # Título del diálogo
        ctk.CTkLabel(dialog, text=title, font=ctk.CTkFont(size=16, weight="bold")).grid(row=0, column=0, columnspan=2, sticky="w", padx=20, pady=15)

        fields = [
            ("Cédula / ID:", "ent_cedula", client["cedula"] if is_edit else ""),
            ("Nombre del Cliente:", "ent_nombre", client["nombre"] if is_edit else ""),
            ("Teléfono:", "ent_telefono", client["telefono"] if is_edit else ""),
        ]

        entries = {}

        # Generar campos de formulario
        for idx, (label_text, var_name, default_val) in enumerate(fields, start=1):
            ctk.CTkLabel(dialog, text=label_text, font=ctk.CTkFont(size=12)).grid(row=idx, column=0, sticky="w", padx=20, pady=10)
            ent = ctk.CTkEntry(dialog, height=35)
            ent.grid(row=idx, column=1, sticky="ew", padx=20, pady=10)
            ent.insert(0, default_val)
            # La cédula es clave primaria; no se permite modificarla en edición
            if is_edit and var_name == "ent_cedula":
                ent.configure(state="disabled")
            entries[var_name] = ent

        def save_client_data():
            """Valida las entradas y persiste el cliente en la base de datos."""
            cedula = entries["ent_cedula"].get().strip()
            nombre = entries["ent_nombre"].get().strip()
            telefono = entries["ent_telefono"].get().strip()

            if not cedula or not nombre:
                messagebox.showwarning("Atención", "Los campos Cédula y Nombre son obligatorios.", parent=dialog)
                return

            try:
                if is_edit:
                    database.update_client(client['cedula'], nombre, telefono)
                    messagebox.showinfo("Éxito", "Cliente actualizado correctamente.")
                else:
                    # Validar unicidad de cédula antes de insertar
                    if database.get_client_by_cedula(cedula):
                        messagebox.showerror("Error", "Ya existe un cliente con esa cédula.", parent=dialog)
                        return
                    database.add_client(cedula, nombre, telefono)
                    messagebox.showinfo("Éxito", "Cliente registrado correctamente.")

                dialog.destroy()
                self.load_clients()
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo guardar el cliente: {str(e)}", parent=dialog)

        # Botón para procesar guardado
        btn_save = ctk.CTkButton(
            dialog,
            text="💾 Guardar Cliente",
            fg_color="#10b981",
            hover_color="#059669",
            height=40,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=save_client_data
        )
        btn_save.grid(row=4, column=0, columnspan=2, sticky="ew", padx=20, pady=25)

    def delete_client(self, cedula, nombre):
        """
        Solicita confirmación antes de eliminar al cliente de la base de datos.
        
        Parámetros:
        - cedula: Documento de identidad del cliente a eliminar.
        - nombre: Nombre del cliente (utilizado para el mensaje de confirmación).
        """
        confirm = messagebox.askyesno("Confirmar Eliminación", f"¿Está seguro de eliminar al cliente '{nombre}' ({cedula})?")
        if confirm:
            try:
                database.delete_client(cedula)
                messagebox.showinfo("Eliminado", "Cliente eliminado con éxito.")
                self.load_clients()
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo eliminar el cliente: {str(e)}")

    def refresh(self):
        """Recarga el listado de clientes al mostrar la vista."""
        self.load_clients()
