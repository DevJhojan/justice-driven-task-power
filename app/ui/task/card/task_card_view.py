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
        self.expanded_tasks = set()  # Almacenar IDs de tareas expandidas
        self.subtasks_containers = {}  # Almacenar referencias a los containers de subtareas

    def build(self, task: SimpleTask) -> ft.Card:
        """
        Construye y retorna la tarjeta de tarea.

        Args:
            task: Objeto SimpleTask con los datos de la tarea

        Returns:
            Card de Flet con la tarjeta renderizada
        """
        # Control para mostrar/ocultar subtareas
        subtasks_container = self._build_subtasks_container(task)

        # Mostrar checkbox solo si NO hay subtareas
        title_row = self._build_title_row(task)

        return ft.Card(
            content=ft.Container(
                padding=12,
                content=ft.Column(
                    controls=[
                        ft.Row(
                            controls=[
                                title_row,
                                ft.Column(
                                    controls=[
                                        ft.IconButton(
                                            ft.Icons.EDIT,
                                            tooltip="Editar",
                                            on_click=lambda _, t=task: self.on_edit(
                                                t
                                            ),
                                        ),
                                        ft.IconButton(
                                            ft.Icons.DELETE,
                                            tooltip="Eliminar",
                                            icon_color=ft.Colors.RED,
                                            on_click=lambda _, t=task: self.on_delete(
                                                t
                                            ),
                                        ),
                                    ],
                                    spacing=0,
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        ),
                        subtasks_container,
                    ],
                    spacing=4,
                ),
            )
        )

    def _build_title_row(self, task: SimpleTask) -> ft.Control:
        """Construye la fila del título con checkbox si no hay subtareas."""
        if task.subtasks:
            # Si hay subtareas, solo mostrar título sin checkbox
            return ft.Column(
                controls=[
                    ft.Text(
                        task.title,
                        size=16,
                        weight=ft.FontWeight.W_600,
                    ),
                    ft.Text(
                        task.description or "Sin descripción",
                        size=12,
                        color=ft.Colors.GREY_700,
                    ),
                ],
                expand=True,
                spacing=4,
            )
        else:
            # Si NO hay subtareas, mostrar checkbox + título
            return ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Checkbox(
                                value=task.completed,
                            ),
                            ft.Text(
                                task.title,
                                size=16,
                                weight=ft.FontWeight.W_600,
                                color=ft.Colors.GREY_600
                                if task.completed
                                else ft.Colors.WHITE,
                            ),
                        ],
                        spacing=6,
                    ),
                    ft.Text(
                        task.description or "Sin descripción",
                        size=12,
                        color=ft.Colors.GREY_700,
                    ),
                ],
                expand=True,
                spacing=4,
            )

    def _build_subtasks_container(self, task: SimpleTask) -> ft.Container:
        """Construye el contenedor de subtareas visible directamente."""
        if not task.subtasks:
            return ft.Container(height=0)  # Container vacío si no hay subtareas

        is_expanded = task.id in self.expanded_tasks
        
        subtasks_list = ft.Column(spacing=4, visible=is_expanded)
        
        # Guardar referencia para poder actualizarla después
        self.subtasks_containers[task.id] = subtasks_list

        for subtask in task.subtasks:
            subtasks_list.controls.append(
                ft.Container(
                    padding=ft.padding.only(left=12),
                    content=ft.Row(
                        controls=[
                            ft.Checkbox(
                                value=subtask.completed,
                            ),
                            ft.Text(
                                subtask.title,
                                size=12,
                                color=ft.Colors.GREY_600
                                if subtask.completed
                                else ft.Colors.WHITE,
                            ),
                        ],
                        spacing=6,
                    ),
                )
            )

        toggle_btn = ft.TextButton(
            "Subtareas",
            on_click=lambda _: self._toggle_subtasks(task),
            style=ft.ButtonStyle(color=ft.Colors.WHITE)
        )

        return ft.Container(
            content=ft.Column(
                controls=[
                    toggle_btn,
                    subtasks_list,
                ],
                spacing=4,
            )
        )

    def _toggle_subtasks(self, task: SimpleTask):
        """Alterna la visibilidad de las subtareas."""
        if task.id in self.expanded_tasks:
            self.expanded_tasks.remove(task.id)
        else:
            self.expanded_tasks.add(task.id)
        
        # Actualizar la visibilidad del container
        if task.id in self.subtasks_containers:
            self.subtasks_containers[task.id].visible = task.id in self.expanded_tasks
