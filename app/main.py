"""
Aplicación principal - App Movil Real Live
Punto de entrada de la aplicación
"""

import flet as ft
from app.ui.home_view import HomeView
from app.utils.screem_load import LoadingScreen


def main(page: ft.Page):
    """
    Función principal que configura la ventana y la interfaz de la aplicación.
    
    Args:
        page: Objeto Page de Flet que representa la página principal
    """
    # Configuración de la ventana
    page.title = "Justice Driven Task Power"
    page.window.width = 800
    page.window.height = 600
    page.window.min_width = 400
    page.window.min_height = 500
    # page.window.center() eliminado - no necesario en Flet 0.80.0
    
    # Configuración del tema - Oscuro con matices rojos
    page.theme_mode = ft.ThemeMode.DARK
    page.theme = ft.Theme(
        color_scheme_seed=ft.Colors.RED_900,
        use_material3=True,
    )
    page.bgcolor = ft.Colors.GREY_900
    page.dark_theme = ft.Theme(
        color_scheme=ft.ColorScheme(
            primary=ft.Colors.RED_700,
            on_primary=ft.Colors.WHITE,
            secondary=ft.Colors.RED_900,
            on_secondary=ft.Colors.WHITE,
            surface=ft.Colors.GREY_800,
            on_surface=ft.Colors.WHITE,
            error=ft.Colors.RED_400,
            on_error=ft.Colors.WHITE,
        ),
        use_material3=True,
    )
    
    # Configuración de la página
    page.padding = 0
    page.spacing = 0
    
    def show_home_view():
        """
        Función callback que se ejecuta cuando termina la pantalla de carga.
        Cambia la vista a la pantalla principal (Home).
        """
        # Limpiar la página
        page.clean()
        
        # Cargar la vista principal (Home) con BottomNav
        page.add(HomeView().build(page))
        
        # Actualizar la página
        page.update()
    
    # Mostrar la pantalla de carga primero
    loading_screen = LoadingScreen(on_complete=show_home_view)
    page.add(loading_screen.build(page))  # Pasar page para cálculos responsive
    page.update()
    
    # Iniciar la animación de carga (dura 5 segundos por defecto)
    loading_screen.start_loading(page, duration=5.0)
