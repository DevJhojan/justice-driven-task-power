"""
Componente de navegación inferior (Bottom Navigation)
Permite navegar entre diferentes pantallas usando una barra inferior
"""

import flet as ft
from typing import Callable, Dict, List


class BottomNav:
    """Clase que maneja la navegación inferior entre pantallas"""
    
    def __init__(self, screens: Dict[int, ft.Control], on_navigate: Callable = None):
        """
        Inicializa el componente de navegación inferior
        
        Args:
            screens: Diccionario con las pantallas {índice: control}
            on_navigate: Callback opcional que se ejecuta al cambiar de pantalla
        """
        self.screens = screens
        self.on_navigate = on_navigate
        self.current_index = 0
        
        # Crear la barra de navegación
        self.nav_bar = ft.NavigationBar(
            selected_index=0,
            on_change=self._handle_navigation,
            destinations=[
                ft.NavigationBarDestination(
                    icon=ft.Icons.HOME,
                    label="Inicio",
                ),
                ft.NavigationBarDestination(
                    icon=ft.Icons.TASK,
                    label="Tareas",
                ),
                ft.NavigationBarDestination(
                    icon=ft.Icons.SETTINGS,
                    label="Configuración",
                ),
            ],
        )
    
    def _handle_navigation(self, e):
        """
        Maneja el evento de cambio de navegación
        
        Args:
            e: Evento de cambio de navegación
        """
        self.current_index = e.control.selected_index
        
        # Ejecutar callback si existe
        if self.on_navigate:
            self.on_navigate(self.current_index)
    
    def build(self, page: ft.Page) -> ft.Container:
        """
        Construye el layout completo con la pantalla actual y la barra de navegación
        
        Args:
            page: Objeto Page de Flet
            
        Returns:
            Container con el layout completo
        """
        # Obtener la pantalla actual
        current_screen = self.screens.get(self.current_index, self.screens[0])
        
        return ft.Container(
            content=ft.Column(
                controls=[
                    # Contenedor para la pantalla actual - ocupa todo el espacio disponible
                    ft.Container(
                        content=current_screen,
                        expand=True,
                    ),
                    # Barra de navegación inferior - solo ocupa su espacio natural
                    self.nav_bar,
                ],
                spacing=0,
                expand=True,
            ),
            expand=True,
        )
    
    def navigate_to(self, index: int, page: ft.Page):
        """
        Navega a una pantalla específica
        
        Args:
            index: Índice de la pantalla a la que navegar
            page: Objeto Page de Flet
        """
        if index in self.screens:
            self.current_index = index
            self.nav_bar.selected_index = index
            page.update()


# ============================================================================
# PANTALLAS DE EJEMPLO
# ============================================================================

class Screen1:
    """Primera pantalla de ejemplo - Inicio"""
    
    def build(self) -> ft.Container:
        """Construye la primera pantalla"""
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Icon(
                        ft.Icons.HOME,
                        size=80,
                        color=ft.Colors.BLUE_700,
                    ),
                    ft.Text(
                        "Pantalla de Inicio",
                        size=32,
                        weight=ft.FontWeight.BOLD,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
                    ft.Text(
                        "Esta es la primera pantalla de la aplicación.",
                        size=18,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Text(
                        "Usa la barra inferior para navegar.",
                        size=16,
                        color=ft.Colors.GREY_600,
                        text_align=ft.TextAlign.CENTER,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            padding=20,
            expand=True,
            bgcolor=ft.Colors.WHITE,
        )


class Screen2:
    """Segunda pantalla de ejemplo - Tareas"""
    
    def build(self) -> ft.Container:
        """Construye la segunda pantalla"""
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Icon(
                        ft.Icons.TASK,
                        size=80,
                        color=ft.Colors.GREEN_700,
                    ),
                    ft.Text(
                        "Pantalla de Tareas",
                        size=32,
                        weight=ft.FontWeight.BOLD,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
                    ft.Text(
                        "Esta es la segunda pantalla.",
                        size=18,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Text(
                        "Aquí puedes gestionar tus tareas.",
                        size=16,
                        color=ft.Colors.GREY_600,
                        text_align=ft.TextAlign.CENTER,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            padding=20,
            expand=True,
            bgcolor=ft.Colors.WHITE,
        )


class Screen3:
    """Tercera pantalla de ejemplo - Configuración"""
    
    def build(self) -> ft.Container:
        """Construye la tercera pantalla"""
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Icon(
                        ft.Icons.SETTINGS,
                        size=80,
                        color=ft.Colors.ORANGE_700,
                    ),
                    ft.Text(
                        "Pantalla de Configuración",
                        size=32,
                        weight=ft.FontWeight.BOLD,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
                    ft.Text(
                        "Esta es la tercera pantalla.",
                        size=18,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Text(
                        "Aquí puedes ajustar la configuración.",
                        size=16,
                        color=ft.Colors.GREY_600,
                        text_align=ft.TextAlign.CENTER,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            padding=20,
            expand=True,
            bgcolor=ft.Colors.WHITE,
        )


# ============================================================================
# DEMO EJECUTABLE
# ============================================================================

def main(page: ft.Page):
    """
    Función principal del demo para probar el BottomNav
    
    Args:
        page: Objeto Page de Flet
    """
    # Configuración de la ventana
    page.title = "Demo - Bottom Navigation"
    page.window.width = 600
    page.window.height = 700
    
    # Configuración de la página
    page.padding = 0
    page.spacing = 0
    page.bgcolor = ft.Colors.WHITE
    
    # Crear las pantallas
    screen1 = Screen1()
    screen2 = Screen2()
    screen3 = Screen3()
    
    # Contenedor para la pantalla actual (se actualizará dinámicamente)
    current_screen_container = ft.Container(
        content=screen1.build(),
        expand=True,
    )
    
    # Función para manejar la navegación
    def handle_navigation(index: int):
        """Actualiza la pantalla cuando se cambia de tab"""
        screens = [screen1, screen2, screen3]
        if 0 <= index < len(screens):
            current_screen_container.content = screens[index].build()
            page.update()
    
    # Crear el BottomNav
    bottom_nav = BottomNav(
        screens={
            0: screen1.build(),
            1: screen2.build(),
            2: screen3.build(),
        },
        on_navigate=handle_navigation,
    )
    
    # Crear el layout completo usando el BottomNav
    layout = ft.Column(
        controls=[
            # Pantalla actual - ocupa todo el espacio disponible
            current_screen_container,
            # Barra de navegación - solo ocupa su espacio natural en la parte inferior
            bottom_nav.nav_bar,
        ],
        spacing=0,
        expand=True,
    )
    
    # Agregar a la página
    page.add(layout)
    page.update()


if __name__ == "__main__":
    # Ejecutar el demo
    ft.run(main)

