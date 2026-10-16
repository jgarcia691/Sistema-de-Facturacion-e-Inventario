"""
Punto de Entrada Principal (main.py)
====================================
Inicializa y coordina la aplicación nativa de escritorio:
- Configura la ventana principal (`ctk.CTk`), resolución base (1280x720) y modo maximizado.
- Inicializa la base de datos local SQLite y carga la configuración de la empresa.
- Construye la barra lateral de navegación con la tuerca de opciones (⚙️), el membrete comercial,
  los botones de acceso a los módulos y el selector de temas visuales.
- Administra el contenedor principal y las transiciones fluidas entre vistas.
- Maneja el cierre limpio del proceso sin bloqueos en consola.
"""

import os
import sys
import customtkinter as ctk
from tkinter import messagebox
import database
from animations import animate_slide_fade_in

# Importación de los componentes de vista del sistema
from views.dashboard_view import DashboardView
from views.invoice_view import InvoiceView
from views.history_view import HistoryView
from views.inventory_view import InventoryView
from views.client_view import ClientView
from views.statistics_view import StatisticsView
from views.settings_modal import SettingsModal

# Configuración global de apariencia inicial de CustomTkinter
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class InventoryApp(ctk.CTk):
    """
    Clase principal de la aplicación GUI.
    
    Hereda de `ctk.CTk` para representar la ventana raíz de Windows.
    Coordina la inicialización de la base de datos, el armado de la barra lateral,
    el contenedor de vistas intercambiables y el ciclo de vida del programa.
    """
    def __init__(self):
        """
        Constructor de la aplicación principal:
        - Inicializa las tablas de SQLite y recupera el nombre del negocio.
        - Establece el título de la ventana y los límites de dimensiones.
        - Registra el protocolo de intercepción de cierre de ventana (`WM_DELETE_WINDOW`).
        - Ensambla la barra lateral y el contenedor de módulos.
        - Muestra el Dashboard inicial y programa el maximizado automático.
        """
        super().__init__()
        
        # 1. Inicializar la Base de Datos SQLite y obtener datos de la empresa
        database.init_db()
        negocio = database.get_negocio_config()

        # 2. Configurar propiedades de la ventana de Windows
        self.title(f"Sistema de Inventario y Facturación - {negocio['nombre']}")
        self.geometry("1280x720")
        self.minsize(1024, 600)
        
        # Interceptar el evento de cierre de ventana para terminar procesos en consola
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # 3. Configuración del diseño Grid (2 columnas: Sidebar fija + Contenido dinámico)
        self.grid_columnconfigure(0, weight=0)  # Columna 0: Barra lateral fija
        self.grid_columnconfigure(1, weight=1)  # Columna 1: Contenedor principal expandible
        self.grid_rowconfigure(0, weight=1)
        
        self.active_nav_key = "dashboard"
        
        # 4. Construir interfaz base
        self.build_sidebar()
        self.build_content_area()
        
        # 5. Cargar vista inicial
        self.show_view("dashboard")

        # 6. Maximizar la ventana automáticamente tras inicializar
        self.after(50, self.maximize_window)

    def maximize_window(self):
        """
        Inicia la ventana en modo maximizado de manera compatible en Windows
        utilizando el estado 'zoomed' de Tkinter.
        """
        try:
            self.state("zoomed")
        except Exception:
            try:
                self.attributes("-zoomed", True)
            except Exception:
                pass

    def build_sidebar(self):
        """
        Construye la barra lateral izquierda (Sidebar):
        - Logotipo y título del sistema.
        - Botón con tuerca de opciones (⚙️) para configurar el negocio.
        - Tarjeta resumen con el nombre comercial y RIF actualizados.
        - Botones de navegación para cada módulo.
        - Pie de página con selector de tema (Oscuro/Claro/Sistema) y botón de salida.
        """
        # Contenedor de la barra lateral
        self.sidebar_frame = ctk.CTkFrame(self, width=230, corner_radius=0, fg_color=("gray90", "#181825"))
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(9, weight=1)  # Expansor elástico antes del footer
        
        # 1. Cabecera con Logotipo, Título y Tuerca de Opciones
        brand_frame = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        brand_frame.grid(row=0, column=0, padx=15, pady=(20, 10), sticky="ew")
        brand_frame.grid_columnconfigure(1, weight=1)
        
        lbl_logo = ctk.CTkLabel(brand_frame, text="📦", font=ctk.CTkFont(size=28))
        lbl_logo.grid(row=0, column=0, padx=(0, 8), sticky="w")
        
        brand_title = ctk.CTkLabel(
            brand_frame, 
            text="INVENTARIO\n& FACTURACIÓN", 
            font=ctk.CTkFont(size=13, weight="bold"),
            justify="left"
        )
        brand_title.grid(row=0, column=1, sticky="w")

        # Botón Tuerca de Opciones (⚙️)
        self.btn_gear = ctk.CTkButton(
            brand_frame,
            text="⚙️",
            width=34,
            height=34,
            fg_color=("gray80", "#262636"),
            hover_color=("#3b82f6", "#2563eb"),
            text_color=("gray10", "white"),
            font=ctk.CTkFont(size=16),
            corner_radius=8,
            command=self.open_settings_modal
        )
        self.btn_gear.grid(row=0, column=2, padx=(6, 0), sticky="e")

        # 2. Tarjeta con Datos Comerciales del Negocio
        negocio = database.get_negocio_config()
        self.biz_card = ctk.CTkFrame(self.sidebar_frame, fg_color=("white", "#20202e"), corner_radius=8)
        self.biz_card.grid(row=1, column=0, padx=15, pady=(0, 12), sticky="ew")
        
        self.lbl_biz_name = ctk.CTkLabel(
            self.biz_card,
            text=f"🏢 {negocio['nombre']}",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=("#2563eb", "#60a5fa"),
            anchor="w"
        )
        self.lbl_biz_name.pack(anchor="w", padx=10, pady=(6, 1))

        self.lbl_biz_rif = ctk.CTkLabel(
            self.biz_card,
            text=f"RIF: {negocio['rif']}",
            font=ctk.CTkFont(size=10),
            text_color="gray",
            anchor="w"
        )
        self.lbl_biz_rif.pack(anchor="w", padx=10, pady=(0, 6))

        # 3. Lista de Botones de Navegación
        self.nav_buttons = {}
        
        nav_items = [
            ("dashboard", "📊 Dashboard", "dashboard"),
            ("invoice", "📄 Nueva Factura", "invoice"),
            ("history", "📜 Historial", "history"),
            ("inventory", "📦 Productos", "inventory"),
            ("client", "👥 Clientes", "client"),
            ("stats", "📈 Estadísticas", "stats"),
        ]
        
        for idx, (key, label, view_name) in enumerate(nav_items, start=2):
            btn = ctk.CTkButton(
                self.sidebar_frame,
                text=label,
                anchor="w",
                font=ctk.CTkFont(size=14, weight="bold"),
                height=42,
                corner_radius=8,
                fg_color="transparent",
                text_color=("gray10", "gray90"),
                hover_color=("gray80", "#2b2b36"),
                command=lambda k=key: self.show_view(k)
            )
            btn.grid(row=idx, column=0, padx=15, pady=3, sticky="ew")
            self.nav_buttons[key] = btn

        # 4. Pie de la Barra Lateral (Footer)
        footer_frame = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        footer_frame.grid(row=10, column=0, padx=15, pady=15, sticky="ew")

        # Botón Configuración del Negocio en el pie de página
        btn_business_config = ctk.CTkButton(
            footer_frame,
            text="⚙️ Datos del Negocio",
            fg_color=("#3b82f6", "#2563eb"),
            hover_color=("#2563eb", "#1d4ed8"),
            height=32,
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self.open_settings_modal
        )
        btn_business_config.pack(fill="x", pady=(0, 8))
        
        # Selector de Apariencia (Modo Oscuro / Claro / Sistema)
        lbl_theme = ctk.CTkLabel(footer_frame, text="Modo de Apariencia:", font=ctk.CTkFont(size=11), text_color="gray")
        lbl_theme.pack(anchor="w", pady=(0, 5))
        
        self.theme_option = ctk.CTkOptionMenu(
            footer_frame,
            values=["Oscuro", "Claro", "Sistema"],
            command=self.change_appearance_mode,
            height=30
        )
        self.theme_option.pack(fill="x")
        
        # Botón para cerrar la aplicación limpiamente
        btn_exit = ctk.CTkButton(
            footer_frame,
            text="🚪 Cerrar Programa",
            fg_color=("gray75", "#272738"),
            hover_color=("gray65", "#37374d"),
            text_color=("gray10", "gray90"),
            height=32,
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self.on_closing
        )
        btn_exit.pack(fill="x", pady=(8, 0))

        # Indicador de versión del sistema
        ctk.CTkLabel(footer_frame, text="v1.0.0 Native Python", font=ctk.CTkFont(size=10), text_color="gray50").pack(pady=(8, 0))

    def open_settings_modal(self):
        """
        Abre el diálogo modal `SettingsModal` para editar la información fiscal y comercial.
        Pasa `self.on_business_updated` como callback para sincronizar los cambios al guardar.
        """
        SettingsModal(self, on_save_callback=self.on_business_updated)

    def on_business_updated(self):
        """
        Callback ejecutado automáticamente tras guardar cambios en los datos del negocio:
        - Actualiza el título de la ventana de Windows con el nuevo nombre.
        - Actualiza la tarjeta de la barra lateral con el nombre y RIF.
        - Refresca la vista actualmente visible en pantalla.
        """
        negocio = database.get_negocio_config()
        self.title(f"Sistema de Inventario y Facturación - {negocio['nombre']}")
        if hasattr(self, 'lbl_biz_name'):
            self.lbl_biz_name.configure(text=f"🏢 {negocio['nombre']}")
        if hasattr(self, 'lbl_biz_rif'):
            self.lbl_biz_rif.configure(text=f"RIF: {negocio['rif']}")

        # Actualizar la vista activa para reflejar los datos de inmediato
        if hasattr(self, 'views') and self.active_nav_key in self.views:
            active_view = self.views[self.active_nav_key]
            if hasattr(active_view, 'refresh'):
                active_view.refresh()

    def build_content_area(self):
        """
        Construye el contenedor principal (`main_container`) e instancia
        cada una de las 6 vistas del sistema dentro de él.
        """
        self.main_container = ctk.CTkFrame(self, fg_color=("gray95", "#11111b"), corner_radius=0)
        self.main_container.grid(row=0, column=1, sticky="nsew")
        self.main_container.grid_columnconfigure(0, weight=1)
        self.main_container.grid_rowconfigure(0, weight=1)
        
        # Diccionario con las instancias de cada vista del sistema
        self.views = {
            "dashboard": DashboardView(self.main_container, nav_callback=self.show_view),
            "invoice": InvoiceView(self.main_container, nav_callback=self.show_view),
            "history": HistoryView(self.main_container, nav_callback=self.show_view),
            "inventory": InventoryView(self.main_container, nav_callback=self.show_view),
            "client": ClientView(self.main_container, nav_callback=self.show_view),
            "stats": StatisticsView(self.main_container, nav_callback=self.show_view)
        }

    def show_view(self, key):
        """
        Cambia la vista mostrada en el contenedor principal:
        1. Actualiza el estilo del botón activo en la barra lateral.
        2. Ejecuta el método `refresh()` de la vista seleccionada.
        3. Realiza una animación suave de entrada mediante `animate_slide_fade_in`.
        
        Parámetros:
        - key: Identificador de la vista ('dashboard', 'invoice', 'history', etc.).
        """
        if key not in self.views:
            return
            
        self.active_nav_key = key
        
        # Actualizar resaltado de los botones del menú lateral
        for b_key, btn in self.nav_buttons.items():
            if b_key == key:
                btn.configure(fg_color=("#3b82f6", "#3b82f6"), text_color="white")
            else:
                btn.configure(fg_color="transparent", text_color=("gray10", "gray90"))

        # Refrescar datos de la vista antes de desplegar
        target_view = self.views[key]
        if hasattr(target_view, 'refresh'):
            target_view.refresh()
            
        # Ejecutar transición fluida de deslizamiento
        animate_slide_fade_in(target_view)

    def change_appearance_mode(self, mode_str):
        """
        Modifica el tema visual de la aplicación según la selección del usuario.
        
        Parámetros:
        - mode_str: 'Oscuro', 'Claro' o 'Sistema'.
        """
        mapping = {
            "Oscuro": "Dark",
            "Claro": "Light",
            "Sistema": "System"
        }
        ctk.set_appearance_mode(mapping.get(mode_str, "Dark"))

    def on_closing(self):
        """
        Cierra limpiamente la aplicación:
        - Cancela todos los temporizadores o eventos pendientes programados con `after`.
        - Oculta, destruye la ventana gráfica de Tkinter.
        - Finaliza el proceso de Python de inmediato liberando la terminal.
        """
        try:
            # Cancelar eventos pendientes de CustomTkinter/Tk para evitar errores en consola
            for after_id in self.tk.call("after", "info"):
                try:
                    self.after_cancel(after_id)
                except Exception:
                    pass
        except Exception:
            pass

        try:
            self.withdraw()
        except Exception:
            pass

        try:
            self.quit()
        except Exception:
            pass

        try:
            self.destroy()
        except Exception:
            pass

        # Finalizar el proceso del sistema operativo
        os._exit(0)

if __name__ == "__main__":
    # Inicialización del bucle principal de la interfaz
    app = InventoryApp()
    try:
        app.mainloop()
    except (KeyboardInterrupt, SystemExit):
        pass
    except Exception as e:
        print(f"Error inesperado: {e}")
    finally:
        os._exit(0)
