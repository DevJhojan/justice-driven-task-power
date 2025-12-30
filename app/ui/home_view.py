"""
Vista principal (Home) de la aplicación
"""

import flet as ft


class HomeView:
    """Clase que representa la vista principal de la aplicación"""
    
    def __init__(self):
        """Inicializa la vista principal"""
        pass
    
    def build(self) -> ft.Container:
        """
        Construye y retorna el widget principal de la vista
        
        Returns:
            Container con el contenido de la vista principal
        """
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(
                        "Welcome to theJustice Driven Task Power",
                        size=24,
                        weight=ft.FontWeight.BOLD,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
                    ft.Text(
                        "Tu aplicación está lista para comenzar",
                        size=16,
                        text_align=ft.TextAlign.CENTER,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            padding=20,
            expand=True,
        )

