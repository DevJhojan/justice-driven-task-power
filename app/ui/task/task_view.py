"""
Vista de Tareas (Tasks) de la aplicación
"""

import flet as ft


class TaskView:
    """Clase que representa la vista de tareas"""
    
    def __init__(self):
        """Inicializa la vista de tareas"""
        pass
    
    def build(self) -> ft.Container:
        """
        Construye y retorna el widget principal de la vista
        
        Returns:
            Container con el contenido de la vista de tareas
        """
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Icon(
                        ft.Icons.TASK,
                        size=80,
                        color=ft.Colors.ORANGE_700,
                    ),
                    ft.Text(
                        "Tareas",
                        size=32,
                        weight=ft.FontWeight.BOLD,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
                    ft.Text(
                        "Estás en la sección de Tareas",
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

