"""
Aplicación principal - App Movil Real Live
Punto de entrada de la aplicación
"""

import flet as ft
from app.ui.home_view import HomeView


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
    page.window.center()
    
    # Configuración del tema
    page.theme_mode = ft.ThemeMode.LIGHT
    
    # Configuración de la página
    page.padding = 0
    page.spacing = 0
    
    # Cargar la vista principal (Home)
    home_view = HomeView()
    page.add(home_view.build())
    
    # Actualizar la página
    page.update()


if __name__ == "__main__":
    # Ejecutar la aplicación
    ft.run(main)

