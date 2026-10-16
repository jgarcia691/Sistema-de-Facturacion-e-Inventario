"""
Módulo de Estadísticas y Análisis Financiero (statistics_view.py)
================================================================
Proporciona la vista analítica con gráficos incrustados y métricas financieras:
- Tarjetas resumen de facturación global en USD ($) y Bolívares (Bs.).
- Conteo de productos activos en catálogo.
- Gráfico de barras horizontales: Top 5 de productos más vendidos por unidades.
- Gráfico de líneas y áreas: Tendencia cronológica de ventas por día en USD.
- Renderizado interactivo nativo con Matplotlib integrado mediante FigureCanvasTkAgg.
"""

import customtkinter as ctk
import matplotlib
# Configurar backend de Matplotlib a TkAgg para integración con Tkinter/CustomTkinter
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import database

class StatisticsView(ctk.CTkFrame):
    """
    Vista de Análisis Financiero y Métricas Estadísticas.
    
    Hereda de `ctk.CTkFrame` para integrarse en la ventana principal.
    
    Parámetros:
    - parent: Contenedor principal (`main_container`).
    - nav_callback: Callback para navegación entre vistas.
    """
    def __init__(self, parent, nav_callback):
        super().__init__(parent, fg_color="transparent")
        self.nav_callback = nav_callback
        
        # Estructura de la cuadrícula:
        # Fila 0: Barra de título
        # Fila 1: Tarjetas métricas financieras
        # Fila 2: Área de gráficos (2 columnas divididas)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        
        self.build_ui()
        
    def build_ui(self):
        """
        Construye la interfaz completa de estadísticas:
        1. Encabezado superior.
        2. Tarjetas KPI de facturación total en USD, Bs y productos.
        3. Sección de dos columnas con los gráficos de Matplotlib incrustados.
        """
        # 1. Barra de Encabezado Superior
        top_frame = ctk.CTkFrame(self, fg_color=("white", "#1e1e2e"), corner_radius=12)
        top_frame.grid(row=0, column=0, sticky="ew", padx=15, pady=(15, 10))
        
        lbl_title = ctk.CTkLabel(top_frame, text="📈 Estadísticas y Reportes de Ventas", font=ctk.CTkFont(size=20, weight="bold"))
        lbl_title.pack(anchor="w", padx=20, pady=15)
        
        # 2. Tarjetas Resumen Financiero (KPIs)
        stats_data = database.get_statistics_data()
        summary_db = database.get_dashboard_summary()
        
        fin_frame = ctk.CTkFrame(self, fg_color="transparent")
        fin_frame.grid(row=1, column=0, sticky="ew", padx=15, pady=5)
        for i in range(3):
            fin_frame.grid_columnconfigure(i, weight=1)
            
        sales_dolar = summary_db["total_sales_dolar"]
        sales_bs = summary_db["total_sales_bs"]
        total_prods = summary_db["total_products"]
        
        # Tarjeta 1: Total Facturado en USD ($)
        self.create_fin_card(fin_frame, 0, "💰 Facturación Total ($)", f"${sales_dolar:,.2f}", "#10b981")
        # Tarjeta 2: Total Facturado en Bolívares (Bs.)
        self.create_fin_card(fin_frame, 1, "🇻🇪 Facturación Total (Bs)", f"Bs. {sales_bs:,.2f}", "#3b82f6")
        # Tarjeta 3: Total de Productos en Catálogo
        self.create_fin_card(fin_frame, 2, "📦 Catálogo de Productos", f"{total_prods} Registrados", "#8b5cf6")
        
        # 3. Área de Gráficos (Dividida en 2 Columnas)
        charts_frame = ctk.CTkFrame(self, fg_color="transparent")
        charts_frame.grid(row=2, column=0, sticky="nsew", padx=15, pady=(10, 15))
        charts_frame.grid_columnconfigure(0, weight=1)
        charts_frame.grid_columnconfigure(1, weight=1)
        charts_frame.grid_rowconfigure(0, weight=1)
        
        # Gráfico 1: Top 5 de Productos Más Vendidos
        chart1_box = ctk.CTkFrame(charts_frame, fg_color=("white", "#1e1e2e"), corner_radius=12)
        chart1_box.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        
        lbl_c1 = ctk.CTkLabel(chart1_box, text="🏆 Top 5 Productos Más Vendidos", font=ctk.CTkFont(size=14, weight="bold"))
        lbl_c1.pack(anchor="w", padx=15, pady=(15, 5))
        
        self.render_top_products_chart(chart1_box, stats_data["top_products"])
        
        # Gráfico 2: Tendencia de Ventas Diarias
        chart2_box = ctk.CTkFrame(charts_frame, fg_color=("white", "#1e1e2e"), corner_radius=12)
        chart2_box.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        
        lbl_c2 = ctk.CTkLabel(chart2_box, text="📅 Tendencia de Ventas por Día ($)", font=ctk.CTkFont(size=14, weight="bold"))
        lbl_c2.pack(anchor="w", padx=15, pady=(15, 5))
        
        self.render_sales_trend_chart(chart2_box, stats_data["sales_by_day"])

    def create_fin_card(self, parent, col, title, value, color):
        """
        Crea una tarjeta KPI estilizada con indicador de color lateral.
        
        Parámetros:
        - parent: Frame contenedor de la tarjeta.
        - col: Índice de columna dentro del grid.
        - title: Etiqueta descriptiva superior.
        - value: Valor numérico o texto a destacar.
        - color: Color hexadecimal para la barra de acento.
        """
        card = ctk.CTkFrame(parent, fg_color=("white", "#1e1e2e"), corner_radius=10)
        card.grid(row=0, column=col, sticky="ew", padx=5)
        
        # Barra vertical de acento
        strip = ctk.CTkFrame(card, fg_color=color, width=6, corner_radius=3)
        strip.pack(side="left", fill="y", padx=(0, 10))
        
        # Contenido de texto
        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(side="left", fill="both", expand=True, padx=10, pady=12)
        
        ctk.CTkLabel(content, text=title, font=ctk.CTkFont(size=11), text_color="gray").pack(anchor="w")
        ctk.CTkLabel(content, text=value, font=ctk.CTkFont(size=18, weight="bold")).pack(anchor="w", pady=(2, 0))

    def render_top_products_chart(self, container, data):
        """
        Dibuja un gráfico de barras horizontales con los 5 productos más vendidos.
        
        Parámetros:
        - container: Widget contenedor de Tkinter donde se incrustará el canvas.
        - data: Lista de filas con `producto_nombre` y `total_qty`.
        """
        fig, ax = plt.subplots(figsize=(5, 3.5), dpi=100)
        
        # Aplicar colores oscuros adaptados a la interfaz
        fig.patch.set_facecolor("#1e1e2e")
        ax.set_facecolor("#1e1e2e")
        
        if data:
            names = [row["producto_nombre"] for row in data]
            quantities = [row["total_qty"] for row in data]
            
            # Truncar nombres excesivamente largos para no desbordar el eje
            names = [n[:15] + "..." if len(n) > 15 else n for n in names]
            
            bars = ax.barh(names, quantities, color="#89b4fa", edgecolor="#313244")
            ax.invert_yaxis()
            
            # Anotación numérica sobre cada barra
            for bar in bars:
                width = bar.get_width()
                ax.text(width + 0.1, bar.get_y() + bar.get_height()/2, f"{int(width)}", 
                        ha='left', va='center', color='white', fontsize=9, fontweight='bold')
        else:
            ax.text(0.5, 0.5, "Sin ventas registradas aún", ha='center', va='center', color='gray')

        # Estilización de ejes y bordes
        ax.tick_params(colors='white', labelsize=9)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_color('#45475a')
        ax.spines['left'].set_color('#45475a')
        ax.xaxis.label.set_color('white')
        ax.yaxis.label.set_color('white')
        
        fig.tight_layout()
        
        # Incrustar el gráfico en CustomTkinter mediante FigureCanvasTkAgg
        canvas = FigureCanvasTkAgg(fig, master=container)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)

    def render_sales_trend_chart(self, container, data):
        """
        Dibuja un gráfico cronológico de línea y área sombreada con la facturación diaria ($).
        
        Parámetros:
        - container: Widget contenedor de Tkinter donde se incrustará el canvas.
        - data: Lista de filas con fecha `day` (YYYY-MM-DD) y total vendido `total`.
        """
        fig, ax = plt.subplots(figsize=(5, 3.5), dpi=100)
        fig.patch.set_facecolor("#1e1e2e")
        ax.set_facecolor("#1e1e2e")
        
        if data:
            days = [row["day"] for row in data]
            totals = [row["total"] for row in data]
            
            # Trazar línea de tendencia y sombreado inferior
            ax.plot(days, totals, marker='o', color='#a6e3a1', linewidth=2, markersize=6)
            ax.fill_between(days, totals, color='#a6e3a1', alpha=0.2)
            
            plt.xticks(rotation=30, ha='right')
        else:
            ax.text(0.5, 0.5, "Sin datos de ventas", ha='center', va='center', color='gray')

        # Estilización de ejes y bordes
        ax.tick_params(colors='white', labelsize=8)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_color('#45475a')
        ax.spines['left'].set_color('#45475a')
        ax.xaxis.label.set_color('white')
        ax.yaxis.label.set_color('white')

        fig.tight_layout()
        
        # Incrustar el gráfico en CustomTkinter mediante FigureCanvasTkAgg
        canvas = FigureCanvasTkAgg(fig, master=container)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)

    def refresh(self):
        """
        Reconstruye la vista para actualizar de inmediato las métricas financieras
        y los gráficos con las ventas más recientes.
        """
        for widget in self.winfo_children():
            widget.destroy()
        self.build_ui()
