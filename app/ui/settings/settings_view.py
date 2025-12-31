"""
Vista de Configuración (Settings) de la aplicación
"""

import flet as ft


class SettingsView:
    """Clase que representa la vista de configuración"""
    
    def __init__(self):
        """Inicializa la vista de configuración"""
        pass
    
    def build(self) -> ft.Container:
        """
        Construye y retorna el widget principal de la vista
        
        Returns:
            Container con el contenido de la vista de configuración
        """
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Icon(
                        ft.Icons.SETTINGS,
                        size=80,
                        color=ft.Colors.GREY_700,
                    ),
                    ft.Text(
                        "Configuración",
                        size=32,
                        weight=ft.FontWeight.BOLD,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
                    ft.Text(
                        "Estás en la sección de Configuración",
                        size=18,
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

