"""
Punto de entrada principal de la aplicación de tareas.
"""
import sys
from pathlib import Path

# Agregar el directorio raíz al PYTHONPATH para que las importaciones funcionen
# tanto ejecutando como módulo como directamente
root_dir = Path(__file__).parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

import flet as ft
from app.ui.home_view import HomeView


def main(page: ft.Page):
    """
    Función principal de la aplicación.
    
    Args:
        page: Página de Flet.
    """
    # Configuración de la página
    page.title = "Aplicación de Tareas"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 0
    page.spacing = 0
    
    # Configuración para móvil
    page.horizontal_alignment = ft.CrossAxisAlignment.STRETCH
    page.vertical_alignment = ft.MainAxisAlignment.START
    
    # Inicializar la vista principal
    HomeView(page)


if __name__ == "__main__":
    # Ejecutar la aplicación
    # Para móvil: usar ft.app(target=main, view=ft.AppView.FLET_APP)
    # Para web: usar ft.app(target=main, view=ft.AppView.WEB_BROWSER)
    # Para desktop: usar ft.app(target=main)
    
    # Modo aplicación móvil
    ft.app(
        target=main,
        view=ft.AppView.WEB_BROWSER,  # Modo aplicación móvil
        assets_dir="assets"  # Directorio de assets
    )

