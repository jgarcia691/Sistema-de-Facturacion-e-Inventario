"""
Módulo de Compilación Automatizada (build_exe.py)
=================================================
Este script automatiza el empaquetado del Sistema de Inventario y Facturación
en un archivo ejecutable nativo para Windows (.exe) utilizando PyInstaller.

Configuración incluida:
- Modo archivo único (--onefile).
- Modo ventana gráfica sin consola negra (--windowed).
- Recolección completa de assets de customtkinter, matplotlib y openpyxl.
- Inclusión del paquete de vistas ('views').
"""

import os
import sys
import subprocess

def build():
    """
    Ejecuta el proceso de compilación utilizando PyInstaller.
    
    Procedimiento:
    1. Determina las rutas absolutas del script principal ('main.py') y la carpeta raíz.
    2. Construye los argumentos de línea de comandos para PyInstaller garantizando la
       inclusión de todas las dependencias gráficas y módulos.
    3. Lanza el subproceso de compilación.
    4. Verifica que el binario 'SistemaInventario.exe' haya sido creado exitosamente
       en la carpeta 'dist/' y reporta su tamaño en disco.
    """
    print("=" * 60)
    print("Iniciando compilacion del Sistema de Inventario y Facturacion")
    print("=" * 60)
    
    # Obtener la ruta base del proyecto
    base_dir = os.path.dirname(os.path.abspath(__file__))
    main_script = os.path.join(base_dir, "main.py")
    
    # Definición de parámetros para PyInstaller:
    # - --noconfirm: Sobrescribe la salida anterior sin preguntar.
    # - --clean: Limpia cachés temporales antes de compilar.
    # - --onefile: Empaqueta todo en un único binario ejecutable (.exe).
    # - --windowed: Oculta la consola de comandos de Windows (modo GUI puro).
    # - --name: Nombre del archivo de salida.
    # - --collect-all: Empaqueta recursos, temas y fuentes de las librerías indicadas.
    # - --add-data: Copia la carpeta 'views' dentro del bundle.
    cmd = [
        sys.executable,
        "-m", "PyInstaller",
        "--noconfirm",
        "--clean",
        "--onefile",
        "--windowed",
        "--name", "SistemaInventario",
        "--collect-all", "customtkinter",
        "--collect-all", "matplotlib",
        "--collect-all", "openpyxl",
        "--add-data", f"{os.path.join(base_dir, 'views')};views",
        main_script
    ]
    
    print("Comando de compilacion:")
    print(" ".join(cmd))
    print("-" * 60)
    
    # Ejecutar PyInstaller en un subproceso
    result = subprocess.run(cmd, cwd=base_dir)
    
    # Evaluar resultado de la compilación
    if result.returncode == 0:
        exe_path = os.path.join(base_dir, "dist", "SistemaInventario.exe")
        if os.path.exists(exe_path):
            size_mb = os.path.getsize(exe_path) / (1024 * 1024)
            print("=" * 60)
            print("Compilacion EXITOSA!")
            print(f"Ejecutable generado en: {exe_path}")
            print(f"Tamano: {size_mb:.2f} MB")
            print("=" * 60)
        else:
            print("Compilacion finalizo pero no se encontro el ejecutable en dist/")
    else:
        print(f"Error durante la compilacion. Codigo de salida: {result.returncode}")

if __name__ == "__main__":
    # Inicia la compilación si se invoca directamente desde consola
    build()
