"""
Componente modular para renderizar una tarjeta de tarea con botones de editar y eliminar.
"""

from __future__ import annotations

from typing import Callable, TYPE_CHECKING

import flet as ft

if TYPE_CHECKING:
    from app.ui.task.task_view import SimpleTask


class TaskCardView:
    """Componente para renderizar una tarjeta de tarea individual."""

    def __init__(self, on_edit: Callable, on_delete: Callable):
        """
        Inicializa el componente de tarjeta de tarea.

        Args:
            on_edit: Callback que se ejecuta al hacer clic en editar
            on_delete: Callback que se ejecuta al hacer clic en eliminar
        """
        self.on_edit = on_edit
        self.on_delete = on_delete

    def build(self, task: SimpleTask) -> ft.Card:
        """
        Construye y retorna la tarjeta de tarea.

        Args:
            task: Objeto SimpleTask con los datos de la tarea

        Returns:
            Card de Flet con la tarjeta renderizada
        """
        return ft.Card(
            content=ft.Container(
                padding=12,
                content=ft.Row(
                    controls=[
                        ft.Column(
                            controls=[
                                ft.Text(task.title, size=16, weight=ft.FontWeight.W_600),
                                ft.Text(
                                    task.description or "Sin descripción",
                                    size=12,
                                    color=ft.Colors.GREY_700,
                                ),
                            ],
                            expand=True,
                            spacing=4,
                        ),
                        ft.IconButton(
                            ft.Icons.EDIT,
                            tooltip="Editar",
                            on_click=lambda _, t=task: self.on_edit(t),
                        ),
                        ft.IconButton(
                            ft.Icons.DELETE,
                            tooltip="Eliminar",
                            icon_color=ft.Colors.RED,
                            on_click=lambda _, t=task: self.on_delete(t),
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
            )
        )
