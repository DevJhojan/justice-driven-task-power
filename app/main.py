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
    
    # Inicializar la vista principal
    HomeView(page)


if __name__ == "__main__":
    # Ejecutar la aplicación
    # Para desarrollo: ventana nativa Flet
    # Para producción Android: se construye con build_android.sh
    ft.app(target=main, view=ft.AppView.FLET_APP, assets_dir="assets")

