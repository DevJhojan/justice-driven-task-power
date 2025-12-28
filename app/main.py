"""
Punto de entrada principal de la aplicación.
"""
import flet as ft
from app.ui.home_view import HomeView


def main(page: ft.Page):
    """
    Función principal de la aplicación.
    
    Args:
        page: Página de Flet.
    """
    # Configuración de la página
    page.title = "Productividad Personal"
    page.padding = 0
    page.spacing = 0
    
    # Configuración para móvil y escritorio
    page.horizontal_alignment = ft.CrossAxisAlignment.STRETCH
    page.vertical_alignment = ft.MainAxisAlignment.START
    
    # Configurar tema con matices rojos - Tema claro
    page.theme = ft.Theme(
        color_scheme_seed=ft.Colors.RED_700,  # Rojo principal
        primary_swatch=ft.Colors.RED,
    )
    
    # Configurar tema oscuro con matices rojos
    page.dark_theme = ft.Theme(
        color_scheme_seed=ft.Colors.RED_900,  # Rojo oscuro principal
        primary_swatch=ft.Colors.RED,
    )
    
    # Personalizar colores del tema
    # Tema claro
    page.theme.color_scheme.primary = ft.Colors.RED_700
    page.theme.color_scheme.secondary = ft.Colors.RED_600
    page.theme.color_scheme.on_primary = ft.Colors.WHITE
    page.theme.color_scheme.on_secondary = ft.Colors.WHITE
    
    # Tema oscuro
    page.dark_theme.color_scheme.primary = ft.Colors.RED_600
    page.dark_theme.color_scheme.secondary = ft.Colors.RED_500
    page.dark_theme.color_scheme.on_primary = ft.Colors.WHITE
    page.dark_theme.color_scheme.on_secondary = ft.Colors.WHITE
    
    # Inicializar la vista principal
    HomeView(page)


if __name__ == "__main__":
    # Ejecutar la aplicación
    # Para desarrollo: ventana nativa Flet
    # Para producción Android: se construye con build_android.sh
    ft.app(target=main, view=ft.AppView.FLET_APP, assets_dir="assets")

