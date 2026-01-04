"""
Formulario reutilizable para crear/editar tareas simples con subtareas.
"""

from __future__ import annotations

from typing import Callable, Optional

import flet as ft
from app.ui.task.form.subtask_manager import SubtaskManager


class TaskForm:
    def __init__(self, on_save: Callable, on_cancel: Callable, on_subtask_changed: Callable = None):
        self.on_save = on_save
        self.on_cancel = on_cancel
        self.on_subtask_changed = on_subtask_changed

        self.title_field: Optional[ft.TextField] = None
        self.desc_field: Optional[ft.TextField] = None
        self.subtask_manager: Optional[SubtaskManager] = None
        self.card: Optional[ft.Card] = None
        self.error_container: Optional[ft.Container] = None
        self.error_text: Optional[ft.Text] = None
        self.page: Optional[ft.Page] = None

    def build(self) -> ft.Card:
        self.title_field = ft.TextField(label="Título", autofocus=True, expand=True)
        self.desc_field = ft.TextField(
            label="Descripción",
            multiline=True,
            min_lines=2,
            max_lines=4,
            expand=True,
        )
        self.subtask_manager = SubtaskManager(on_subtask_changed=self.on_subtask_changed)

        # Contenedor de errores
        self.error_text = ft.Text(
            "",
            size=12,
            color=ft.Colors.RED_400,
            selectable=True,
        )
        
        copy_error_btn = ft.IconButton(
            icon=ft.Icons.CONTENT_COPY,
            icon_size=16,
            tooltip="Copiar error",
            on_click=self._copy_error,
        )
        
        self.error_container = ft.Container(
            content=ft.Row(
                controls=[
                    self.error_text,
                    copy_error_btn,
                ],
                spacing=8,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=12,
            bgcolor=ft.Colors.RED_900,
            border_radius=8,
            visible=False,
        )

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
                        self.error_container,
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
    
    def set_page(self, page: ft.Page):
        """Establece la página para copiar errores."""
        self.page = page
    
    def show_error(self, error_message: str):
        """Muestra un error en el contenedor."""
        if self.error_text and self.error_container:
            self.error_text.value = error_message
            self.error_container.visible = True
            if self.page:
                self.page.update()
    
    def clear_error(self):
        """Limpia el error."""
        if self.error_text and self.error_container:
            self.error_text.value = ""
            self.error_container.visible = False
            if self.page:
                self.page.update()
    
    def _copy_error(self, _):
        """Copia el mensaje de error al portapapeles."""
        if self.error_text and self.page:
            error_msg = self.error_text.value
            self.page.set_clipboard(error_msg)
            self.page.snack_bar = ft.SnackBar(content=ft.Text("Error copiado"))
            self.page.snack_bar.open = True
            self.page.update()

