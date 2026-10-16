"""
Módulo de Animaciones y Efectos Visuales (animations.py)
========================================================
Proporciona utilidades y componentes visuales para mejorar la experiencia de usuario (UX):
1. LoadingSpinner: Indicador animado de espera / consulta asíncrona.
2. animate_slide_fade_in: Transición vertical suave al cambiar de vista.
3. apply_hover_lift: Micro-animación de cambio de color al pasar el cursor (hover).
"""

import customtkinter as ctk

class LoadingSpinner(ctk.CTkFrame):
    """
    Componente visual de carga animada (Spinner / Loader).
    
    Muestra una secuencia cíclica de caracteres braille rotativos junto a un
    mensaje descriptivo (por ejemplo: 'Consultando Tasa BCV...').
    
    Parámetros:
    - parent: Contenedor padre donde se alojará el spinner.
    - text: Texto explicativo de la operación en curso.
    - font_size: Tamaño de la tipografía para el texto y spinner.
    - **kwargs: Argumentos adicionales heredados de CTkFrame.
    """
    def __init__(self, parent, text="Cargando datos...", font_size=13, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.text = text
        # Secuencia de fotogramas para simular la rotación del loader
        self.spinner_frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        self.frame_idx = 0
        self.is_running = False

        # Etiqueta que renderiza el fotograma actual y el texto informativo
        self.lbl_spinner = ctk.CTkLabel(
            self,
            text=f"{self.spinner_frames[0]}  {self.text}",
            font=ctk.CTkFont(size=font_size, weight="bold"),
            text_color="#3b82f6"
        )
        self.lbl_spinner.pack(padx=10, pady=10)

    def start(self):
        """Inicia el ciclo de animación del spinner en bucle."""
        if not self.is_running:
            self.is_running = True
            self._animate()

    def stop(self):
        """Detiene la animación del spinner."""
        self.is_running = False

    def _animate(self):
        """
        Procedimiento interno recursivo que avanza al siguiente fotograma
        y programa la siguiente actualización utilizando `after`.
        """
        if not self.is_running:
            return
        
        # Avanzar al siguiente símbolo de la lista circular
        self.frame_idx = (self.frame_idx + 1) % len(self.spinner_frames)
        icon = self.spinner_frames[self.frame_idx]
        
        try:
            if self.lbl_spinner.winfo_exists():
                self.lbl_spinner.configure(text=f"{icon}  {self.text}")
                # Programar el siguiente fotograma cada 80 milisegundos
                self.after(80, self._animate)
        except Exception:
            self.is_running = False

def animate_slide_fade_in(view_widget, duration_ms=150, steps=8):
    """
    Realiza una transición suave de entrada (desplazamiento vertical fluido)
    para las vistas del contenedor principal al seleccionarlas en el menú.
    
    Parámetros:
    - view_widget: Widget de la vista que se desea mostrar.
    - duration_ms: Duración total aproximada de la animación en milisegundos.
    - steps: Cantidad de pasos o fotogramas de interpolación del desplazamiento.
    """
    try:
        # Traer la vista al frente del contenedor
        view_widget.tkraise()
        
        offset_step = 12 // steps
        current_y = 12

        def step_anim(current_step):
            """Paso recursivo de interpolación de la posición vertical."""
            nonlocal current_y
            # Si se alcanzaron los pasos finales o el widget dejó de existir, fijar en posición final
            if current_step >= steps or not view_widget.winfo_exists():
                view_widget.place(relx=0, rely=0, relwidth=1, relheight=1)
                return

            current_y = max(0, current_y - offset_step)
            # Reubicar ligeramente hacia arriba simulando entrada fluida
            view_widget.place(relx=0, rely=0, relwidth=1, relheight=1, y=current_y)
            view_widget.after(duration_ms // steps, lambda: step_anim(current_step + 1))

        step_anim(0)
    except Exception:
        # En caso de error inesperado, colocar directamente sin animación
        view_widget.place(relx=0, rely=0, relwidth=1, relheight=1)

def apply_hover_lift(widget, normal_fg, hover_fg, lift_pixels=3):
    """
    Aplica un efecto interactivo de cambio de color al pasar el cursor sobre un componente.
    
    Parámetros:
    - widget: Componente al que se enlazarán los eventos del mouse (<Enter> y <Leave>).
    - normal_fg: Color del componente en estado de reposo.
    - hover_fg: Color del componente cuando el puntero del mouse está sobre él.
    - lift_pixels: Desplazamiento opcional de elevación visual.
    """
    def on_enter(e):
        """Evento al entrar el cursor en el widget."""
        try:
            widget.configure(fg_color=hover_fg)
        except Exception:
            pass

    def on_leave(e):
        """Evento al salir el cursor del widget."""
        try:
            widget.configure(fg_color=normal_fg)
        except Exception:
            pass

    widget.bind("<Enter>", on_enter)
    widget.bind("<Leave>", on_leave)
