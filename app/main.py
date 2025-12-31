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
    
    # Configuración del tema
    page.theme_mode = ft.ThemeMode.LIGHT
    
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
        home_view = HomeView()
        page.add(home_view.build(page))
        
        # Actualizar la página
        page.update()
    
    # Mostrar la pantalla de carga primero
    loading_screen = LoadingScreen(on_complete=show_home_view)
    page.add(loading_screen.build())
    page.update()
    
    # Iniciar la animación de carga (dura 5 segundos por defecto)
    loading_screen.start_loading(page, duration=5.0)
