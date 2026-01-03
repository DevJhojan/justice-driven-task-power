"""
Formulario reutilizable para crear/editar tareas simples con subtareas.
"""

from __future__ import annotations

from typing import Callable, Optional

import flet as ft
from app.ui.task.form.subtask_manager import SubtaskManager


class TaskForm:
    def __init__(self, on_save: Callable, on_cancel: Callable):
        self.on_save = on_save
        self.on_cancel = on_cancel

        self.title_field: Optional[ft.TextField] = None
        self.desc_field: Optional[ft.TextField] = None
        self.subtask_manager: Optional[SubtaskManager] = None
        self.card: Optional[ft.Card] = None

    def build(self) -> ft.Card:
        self.title_field = ft.TextField(label="Título", autofocus=True, expand=True)
        self.desc_field = ft.TextField(
            label="Descripción",
            multiline=True,
            min_lines=2,
            max_lines=4,
            expand=True,
        )
        self.subtask_manager = SubtaskManager()

        save_btn = ft.ElevatedButton(
            "Guardar", icon=ft.Icons.SAVE, on_click=self.on_save
        )
        cancel_btn = ft.TextButton("Cancelar", icon=ft.Icons.CLOSE, on_click=self.on_cancel)

        self.card = ft.Card(
            content=ft.Container(
                padding=16,
                content=ft.Column(
                    controls=[
                        ft.Text("Tarea", size=18, weight=ft.FontWeight.BOLD),
                        self.title_field,
                        self.desc_field,
                        ft.Divider(height=8, color=ft.Colors.TRANSPARENT),
                        self.subtask_manager.build(),
                        ft.Row(
                            [save_btn, cancel_btn],
                            alignment=ft.MainAxisAlignment.END,
                        ),
                    ],
                    spacing=12,
                ),
            )
        )
        return self.card

    def reset(self):
        if self.title_field:
            self.title_field.value = ""
        if self.desc_field:
            self.desc_field.value = ""
        if self.subtask_manager:
            self.subtask_manager.reset()

    def set_values(self, title: str, description: str, subtasks: list = None):
        if self.title_field:
            self.title_field.value = title
        if self.desc_field:
            self.desc_field.value = description
        if self.subtask_manager and subtasks:
            self.subtask_manager.set_subtasks(subtasks)

