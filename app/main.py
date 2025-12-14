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
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 0
    page.spacing = 0
    
    # Personalizar tema claro con matices rojos
    page.theme = ft.Theme(
        color_scheme_seed=ft.Colors.RED_700,
        use_material3=True,
        color_scheme=ft.ColorScheme(
            primary=ft.Colors.RED_700,
            on_primary=ft.Colors.WHITE,
            secondary=ft.Colors.RED_600,
            on_secondary=ft.Colors.WHITE,
            surface=ft.Colors.WHITE,
            on_surface=ft.Colors.BLACK87,
            background=ft.Colors.GREY_50,
            on_background=ft.Colors.BLACK87,
            error=ft.Colors.RED_600,
            on_error=ft.Colors.WHITE,
        )
    )
    
    # Personalizar tema oscuro con tonos negros y matices rojos
    page.dark_theme = ft.Theme(
        color_scheme_seed=ft.Colors.RED_900,
        use_material3=True,
        color_scheme=ft.ColorScheme(
            primary=ft.Colors.RED_700,
            on_primary=ft.Colors.WHITE,
            secondary=ft.Colors.RED_800,
            on_secondary=ft.Colors.WHITE,
            surface=ft.Colors.BLACK87,
            on_surface=ft.Colors.WHITE,
            background=ft.Colors.BLACK,
            on_background=ft.Colors.WHITE,
            error=ft.Colors.RED_400,
            on_error=ft.Colors.WHITE,
        )
    )
    
    # Establecer el color de fondo de la página según el tema inicial
    page.bgcolor = ft.Colors.BLACK if page.theme_mode == ft.ThemeMode.DARK else ft.Colors.GREY_50
    
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

