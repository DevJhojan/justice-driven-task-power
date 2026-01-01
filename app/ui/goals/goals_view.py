"""
Vista de Metas (Goals) de la aplicación
"""

import flet as ft


class GoalsView:
    """Clase que representa la vista de metas"""
    
    def __init__(self):
        """Inicializa la vista de metas"""
        pass
    
    def build(self) -> ft.Container:
        """
        Construye y retorna el widget principal de la vista
        
        Returns:
            Container con el contenido de la vista de metas
        """
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Icon(
                        ft.Icons.FLAG,
                        size=80,
                        color=ft.Colors.BLUE_400,
                    ),
                    ft.Text(
                        "Metas",
                        size=32,
                        weight=ft.FontWeight.BOLD,
                        text_align=ft.TextAlign.CENTER,
                        color=ft.Colors.WHITE,
                    ),
                    ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
                    ft.Text(
                        "Estás en la sección de Metas",
                        size=18,
                        text_align=ft.TextAlign.CENTER,
                        color=ft.Colors.WHITE_70,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            padding=20,
            expand=True,
            bgcolor=None,
        )

