"""
Punto de entrada principal de la aplicación.
Este archivo permite ejecutar la aplicación desde el directorio raíz.
"""
import sys
from pathlib import Path

# Agregar el directorio raíz al path para que los imports funcionen
sys.path.insert(0, str(Path(__file__).parent))

# Importar y ejecutar la función main desde app.main
from app.main import main
import flet as ft

if __name__ == "__main__":
    # Ejecutar la aplicación
    # Para desarrollo: ventana nativa Flet
    # Para producción Android: se construye con build_android.sh
    ft.app(
        target=main, 
        view=ft.AppView.FLET_APP, 
        assets_dir="assets"
    )
