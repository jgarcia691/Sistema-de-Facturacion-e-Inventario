"""
Módulo del Panel Principal / Dashboard (dashboard_view.py)
==========================================================
Proporciona la pantalla de inicio del sistema:
- Presenta un diseño limpio y minimalista de bienvenida al usuario.
- Muestra el membrete comercial y fiscal del negocio en tiempo real
  (Nombre, RIF, Dirección y Teléfono).
- Informa el estado operativo del sistema y la fecha/hora actual.
- Ofrece un acceso rápido a la configuración del negocio.
"""

import customtkinter as ctk
from datetime import datetime
import database

class DashboardView(ctk.CTkFrame):
    """
    Vista del Panel de Control Principal de la aplicación.
    
    Hereda de `ctk.CTkFrame` y se incrusta en el contenedor principal de `InventoryApp`.
    
    Parámetros:
    - parent: Contenedor padre (`main_container` de la ventana principal).
    - nav_callback: Función de devolución de llamada para navegar entre vistas.
    """
    def __init__(self, parent, nav_callback):
        super().__init__(parent, fg_color="transparent")
        self.nav_callback = nav_callback
        
        # Configurar celda principal para centrar el contenido
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Construir la estructura visual
        self.build_ui()

    def build_ui(self):
        """
        Construye la interfaz gráfica de bienvenida:
        1. Consulta la información comercial vigente en la base de datos.
        2. Crea una tarjeta central estilizada con bordes redondeados y adaptada a 720p/1080p.
        3. Muestra el saludo, nombre de la empresa, datos fiscales e instrucciones de uso.
        4. Integra el botón para abrir el modal de configuración de la empresa.
        5. Renderiza el indicador inferior de estado en línea y fecha/hora.
        """
        # Obtener datos de la empresa desde la base de datos
        negocio = database.get_negocio_config()
        
        # Tarjeta de Bienvenida Principal (Centrada, limpia y responsiva)
        welcome_card = ctk.CTkFrame(
            self, 
            fg_color=("white", "#1e1e2e"), 
            corner_radius=16,
            border_width=1,
            border_color=("gray85", "#2b2b3a")
        )
        welcome_card.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.88, relheight=0.78)
        
        # Emblema / Icono Principal de Bienvenida
        lbl_icon = ctk.CTkLabel(
            welcome_card, 
            text="👋", 
            font=ctk.CTkFont(size=48)
        )
        lbl_icon.pack(pady=(24, 6))
        
        # Saludo de Bienvenida Principal
        lbl_title = ctk.CTkLabel(
            welcome_card, 
            text="¡Bienvenido al Sistema!", 
            font=ctk.CTkFont(size=28, weight="bold")
        )
        lbl_title.pack(pady=(0, 6))

        # Nombre de la Empresa o Negocio (Destacado en color de acento)
        lbl_biz_name = ctk.CTkLabel(
            welcome_card,
            text=negocio['nombre'],
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=("#2563eb", "#60a5fa")
        )
        lbl_biz_name.pack(pady=(0, 6))

        # Información Fiscal (RIF, Dirección y Teléfono concatenados de forma estética)
        biz_details = []
        if negocio.get('rif'):
            biz_details.append(f"RIF: {negocio['rif']}")
        if negocio.get('direccion'):
            biz_details.append(negocio['direccion'])
        if negocio.get('telefono'):
            biz_details.append(f"Tel: {negocio['telefono']}")

        details_str = "   •   ".join(biz_details)
        if details_str:
            lbl_fiscal = ctk.CTkLabel(
                welcome_card,
                text=details_str,
                font=ctk.CTkFont(size=13),
                text_color="gray"
            )
            lbl_fiscal.pack(pady=(0, 15))

        # Línea divisoria suave
        divider = ctk.CTkFrame(welcome_card, height=1, fg_color=("gray85", "#2e2e40"))
        divider.pack(fill="x", padx=60, pady=10)

        # Mensaje de Orientación / Guía de Uso
        lbl_message = ctk.CTkLabel(
            welcome_card, 
            text="Panel de control preparado y listo para operar.\nUtilice el menú lateral de la izquierda para acceder a los diferentes módulos\nde Facturación, Historial, Inventario, Clientes y Estadísticas.",
            font=ctk.CTkFont(size=14),
            text_color=("gray30", "gray70"),
            justify="center"
        )
        lbl_message.pack(pady=(10, 20))

        # Botón para Abrir Configuración del Negocio
        btn_config = ctk.CTkButton(
            welcome_card,
            text="⚙️ Configurar Datos del Negocio",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=("#3b82f6", "#2563eb"),
            hover_color=("#2563eb", "#1d4ed8"),
            height=38,
            corner_radius=8,
            command=self.open_settings
        )
        btn_config.pack(pady=(5, 20))

        # Estado del sistema y timestamp al pie de la tarjeta
        now_str = datetime.now().strftime("%d/%m/%Y %H:%M")
        lbl_status = ctk.CTkLabel(
            welcome_card,
            text=f"🟢 Sistema en línea  |  {now_str}",
            font=ctk.CTkFont(size=11),
            text_color="gray50"
        )
        lbl_status.pack(side="bottom", pady=15)

    def open_settings(self):
        """
        Instancia y muestra el modal `SettingsModal` para modificar los datos
        de la empresa. Al guardar, actualiza los encabezados de la aplicación.
        """
        from views.settings_modal import SettingsModal
        top = self.winfo_toplevel()
        cb = top.on_business_updated if hasattr(top, 'on_business_updated') else self.refresh
        SettingsModal(top, on_save_callback=cb)

    def refresh(self):
        """
        Reconstruye por completo la interfaz visual del dashboard para
        reflejar de inmediato cualquier cambio realizado en los datos del negocio.
        """
        for widget in self.winfo_children():
            widget.destroy()
        self.build_ui()
