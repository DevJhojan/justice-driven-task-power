"""
Componente para gestionar subtareas dentro del formulario de tareas.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional
import uuid

import flet as ft
from app.models.subtask import Subtask

if TYPE_CHECKING:
    pass


class SubtaskManager:
    """Gestor de subtareas para agregar/editar dentro del formulario principal."""

    def __init__(self):
        self.subtasks: list[Subtask] = []
        self.subtask_input: Optional[ft.TextField] = None
        self.subtasks_column: Optional[ft.Column] = None

    def build(self) -> ft.Container:
        """Construye la interfaz de gestión de subtareas."""
        self.subtask_input = ft.TextField(
            label="Agregar subtarea",
            expand=True,
        )
        add_subtask_btn = ft.IconButton(
            icon=ft.Icons.ADD,
            tooltip="Agregar subtarea",
            on_click=self._add_subtask,
        )

        self.subtasks_column = ft.Column(spacing=4)

        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text("Subtareas", size=14, weight=ft.FontWeight.W_600),
                    ft.Row(
                        controls=[self.subtask_input, add_subtask_btn],
                        spacing=8,
                    ),
                    self.subtasks_column,
                ],
                spacing=8,
            ),
        )

    def _add_subtask(self, _):
        """Agrega una nueva subtarea a la lista."""
        if not self.subtask_input:
            return

        title = (self.subtask_input.value or "").strip()
        if not title:
            return

        # Crear subtarea con modelo real
        subtask = Subtask(
            id=str(uuid.uuid4()),
            task_id="",  # Se asignará cuando se guarde la tarea
            title=title,
            completed=False,
        )
        self.subtasks.append(subtask)
        self.subtask_input.value = ""

        self._refresh_subtasks()

    def _delete_subtask(self, subtask: Subtask):
        """Elimina una subtarea de la lista."""
        self.subtasks = [s for s in self.subtasks if s.id != subtask.id]
        self._refresh_subtasks()

    def _refresh_subtasks(self):
        """Refresca la lista visual de subtareas."""
        if not self.subtasks_column:
            return

        self.subtasks_column.controls.clear()

        for subtask in self.subtasks:
            self.subtasks_column.controls.append(
                ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Checkbox(
                                value=subtask.completed,
                                on_change=lambda _, st=subtask: self._toggle_subtask(st),
                            ),
                            ft.Text(
                                subtask.title,
                                size=12,
                                color=ft.Colors.GREY_600
                                if subtask.completed
                                else ft.Colors.WHITE,
                            ),
                            ft.IconButton(
                                ft.Icons.DELETE,
                                icon_size=16,
                                icon_color=ft.Colors.RED,
                                on_click=lambda _, st=subtask: self._delete_subtask(st),
                            ),
                        ],
                        spacing=8,
                    ),
                )
            )

    def _toggle_subtask(self, subtask: Subtask):
        """Marca/desmarca una subtarea como completada."""
        subtask.toggle_completed()
        self._refresh_subtasks()

    def set_subtasks(self, subtasks: list):
        """Establece las subtareas (para edición)."""
        self.subtasks = subtasks if subtasks else []
        self._refresh_subtasks()

    def get_subtasks(self) -> list:
        """Obtiene la lista actual de subtareas."""
        return self.subtasks

    def reset(self):
        """Reinicia el gestor de subtareas."""
        self.subtasks = []
        if self.subtask_input:
            self.subtask_input.value = ""
        if self.subtasks_column:
            self.subtasks_column.controls.clear()
