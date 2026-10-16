"""
Módulo de Configuración del Negocio (settings_modal.py)
=======================================================
Proporciona la ventana modal emergente para ver y actualizar la información
fiscal y comercial de la empresa:
- Razón Social / Nombre Comercial
- Documento de Identificación Fiscal (RIF / NIT / Cédula jurídica)
- Dirección Fiscal y Comercial
- Teléfono de contacto

Estos datos se sincronizan con la base de datos SQLite y se reflejan en las facturas,
el panel principal y las exportaciones a Excel.
"""

import customtkinter as ctk
from tkinter import messagebox
import database

class SettingsModal(ctk.CTkToplevel):
    """
    Ventana modal emergente (CTkToplevel) para la edición de los datos del negocio.
    
    Características:
    - Modalidad modal (`grab_set` y `transient`), impidiendo interacción con la ventana
      principal hasta cerrar o guardar.
    - Centrado automático con respecto a la ventana padre.
    - Validación de campos requeridos antes de persistir.
    - Notificación mediante callback (`on_save_callback`) para refrescar vistas activas.
    """
    def __init__(self, parent, on_save_callback=None):
        """
        Constructor del diálogo modal de configuración.
        
        Parámetros:
        - parent: Ventana principal de la aplicación (`InventoryApp`).
        - on_save_callback: Función a ejecutar tras guardar exitosamente los cambios.
        """
        super().__init__(parent)
        self.parent = parent
        self.on_save_callback = on_save_callback

        # Configuración básica de la ventana emergente
        self.title("⚙️ Configuración del Negocio")
        self.geometry("540x550")
        self.resizable(False, False)

        # Establecer comportamiento modal dependiente de la ventana padre
        self.transient(parent)
        self.grab_set()

        # Centrar en la pantalla sobre la ventana principal
        self.center_window(parent)

        # Configuración del grid principal (1 columna responsiva)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Construir interfaz gráfica y precargar valores almacenados
        self.build_ui()
        self.load_data()

        # Forzar foco sobre la ventana modal tras desplegar
        self.after(100, self.focus_force)

    def center_window(self, parent):
        """
        Calcula las coordenadas X e Y para centrar el modal exactamente
        sobre la ventana padre.
        """
        try:
            parent.update_idletasks()
            p_x = parent.winfo_rootx()
            p_y = parent.winfo_rooty()
            p_w = parent.winfo_width()
            p_h = parent.winfo_height()

            w = 540
            h = 550
            x = p_x + (p_w - w) // 2
            y = p_y + (p_h - h) // 2
            self.geometry(f"{w}x{h}+{max(x, 0)}+{max(y, 0)}")
        except Exception:
            pass

    def build_ui(self):
        """
        Construye todos los elementos visuales del modal:
        1. Encabezado con ícono y descripción.
        2. Formulario con campos de texto para Nombre, RIF, Dirección y Teléfono.
        3. Botones de acción 'Guardar Cambios' y 'Cancelar'.
        """
        # 1. Encabezado / Banner Superior
        header_frame = ctk.CTkFrame(self, fg_color=("white", "#1e1e2e"), corner_radius=10)
        header_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))
        header_frame.grid_columnconfigure(1, weight=1)

        lbl_icon = ctk.CTkLabel(header_frame, text="⚙️", font=ctk.CTkFont(size=30))
        lbl_icon.grid(row=0, column=0, rowspan=2, padx=(15, 12), pady=15)

        lbl_title = ctk.CTkLabel(
            header_frame, 
            text="Datos de la Empresa / Negocio", 
            font=ctk.CTkFont(size=16, weight="bold")
        )
        lbl_title.grid(row=0, column=1, sticky="w", pady=(12, 2))

        lbl_sub = ctk.CTkLabel(
            header_frame, 
            text="Configure la información que aparecerá en sus facturas y reportes.", 
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        lbl_sub.grid(row=1, column=1, sticky="w", pady=(0, 12))

        # 2. Formulario de Datos
        form_frame = ctk.CTkFrame(self, fg_color=("white", "#1e1e2e"), corner_radius=10)
        form_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)
        form_frame.grid_columnconfigure(0, weight=1)

        # Campo: Nombre del Negocio / Razón Social
        ctk.CTkLabel(
            form_frame, 
            text="🏢 Nombre del Negocio / Razón Social:", 
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(anchor="w", padx=20, pady=(15, 4))

        self.ent_nombre = ctk.CTkEntry(
            form_frame, 
            placeholder_text="Ej: Comercializadora El Éxito C.A.",
            height=36
        )
        self.ent_nombre.pack(fill="x", padx=20, pady=(0, 10))

        # Campo: RIF (Registro de Información Fiscal)
        ctk.CTkLabel(
            form_frame, 
            text="📄 RIF / Documento Fiscal:", 
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(anchor="w", padx=20, pady=(5, 4))

        self.ent_rif = ctk.CTkEntry(
            form_frame, 
            placeholder_text="Ej: J-12345678-9 / V-12345678",
            height=36
        )
        self.ent_rif.pack(fill="x", padx=20, pady=(0, 10))

        # Campo: Dirección Fiscal / Comercial
        ctk.CTkLabel(
            form_frame, 
            text="📍 Dirección Fiscal / Comercial:", 
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(anchor="w", padx=20, pady=(5, 4))

        self.ent_direccion = ctk.CTkEntry(
            form_frame, 
            placeholder_text="Ej: Av. Bolívar, Centro Comercial Plaza, Local 12",
            height=36
        )
        self.ent_direccion.pack(fill="x", padx=20, pady=(0, 10))

        # Campo: Teléfono de Contacto (Opcional)
        ctk.CTkLabel(
            form_frame, 
            text="📞 Teléfono de Contacto (Opcional):", 
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(anchor="w", padx=20, pady=(5, 4))

        self.ent_telefono = ctk.CTkEntry(
            form_frame, 
            placeholder_text="Ej: 0414-1234567 / 0212-9876543",
            height=36
        )
        self.ent_telefono.pack(fill="x", padx=20, pady=(0, 15))

        # 3. Botones de Acción Inferiores
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=(5, 20))
        btn_frame.grid_columnconfigure(0, weight=1)
        btn_frame.grid_columnconfigure(1, weight=1)

        # Botón Cancelar (Cierra la ventana sin alterar la base de datos)
        btn_cancel = ctk.CTkButton(
            btn_frame,
            text="✖ Cancelar",
            fg_color=("gray75", "#333344"),
            hover_color=("gray65", "#444455"),
            text_color=("gray10", "gray90"),
            height=40,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self.destroy
        )
        btn_cancel.grid(row=0, column=0, padx=(0, 8), sticky="ew")

        # Botón Guardar Cambios
        btn_save = ctk.CTkButton(
            btn_frame,
            text="💾 Guardar Cambios",
            fg_color=("#10b981", "#059669"),
            hover_color=("#059669", "#047857"),
            height=40,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self.save_settings
        )
        btn_save.grid(row=0, column=1, padx=(8, 0), sticky="ew")

    def load_data(self):
        """
        Carga los datos actuales del negocio desde la base de datos
        y los coloca en los campos de entrada correspondientes.
        """
        config = database.get_negocio_config()
        self.ent_nombre.delete(0, "end")
        self.ent_nombre.insert(0, config.get("nombre", ""))

        self.ent_rif.delete(0, "end")
        self.ent_rif.insert(0, config.get("rif", ""))

        self.ent_direccion.delete(0, "end")
        self.ent_direccion.insert(0, config.get("direccion", ""))

        self.ent_telefono.delete(0, "end")
        self.ent_telefono.insert(0, config.get("telefono", ""))

    def save_settings(self):
        """
        Valida que los campos obligatorios no estén vacíos y actualiza
        los datos en la base de datos a través de `database.update_negocio_config`.
        Invoca el callback `on_save_callback` y cierra la ventana modal.
        """
        nombre = self.ent_nombre.get().strip()
        rif = self.ent_rif.get().strip()
        direccion = self.ent_direccion.get().strip()
        telefono = self.ent_telefono.get().strip()

        # Validación de campos obligatorios
        if not nombre:
            messagebox.showwarning("Atención", "Por favor ingrese el nombre del negocio.")
            self.ent_nombre.focus_set()
            return

        if not rif:
            messagebox.showwarning("Atención", "Por favor ingrese el RIF del negocio.")
            self.ent_rif.focus_set()
            return

        if not direccion:
            messagebox.showwarning("Atención", "Por favor ingrese la dirección del negocio.")
            self.ent_direccion.focus_set()
            return

        try:
            # Persistir los datos en la base de datos
            database.update_negocio_config(nombre, rif, direccion, telefono)
            messagebox.showinfo(
                "Éxito", 
                "✅ ¡Datos del negocio actualizados exitosamente!\n\nLos cambios se reflejarán en las facturas y reportes del sistema."
            )
            # Notificar al componente invocador si existe callback
            if self.on_save_callback:
                self.on_save_callback()
            # Cerrar el diálogo modal
            self.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron guardar los datos: {str(e)}")
