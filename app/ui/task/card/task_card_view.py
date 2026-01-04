"""
Componente modular para renderizar una tarjeta de tarea con botones de editar y eliminar.
"""

from __future__ import annotations

from typing import Callable, TYPE_CHECKING

import flet as ft

if TYPE_CHECKING:
    from app.models.task import Task


class TaskCardView:
    """Componente para renderizar una tarjeta de tarea individual."""

    def __init__(self, on_edit: Callable, on_delete: Callable, on_task_updated: Callable = None):
        """
        Inicializa el componente de tarjeta de tarea.

        Args:
            on_edit: Callback que se ejecuta al hacer clic en editar
            on_delete: Callback que se ejecuta al hacer clic en eliminar
            on_task_updated: Callback cuando la tarea se actualiza (opcional)
        """
        self.on_edit = on_edit
        self.on_delete = on_delete
        self.on_task_updated = on_task_updated
        self.expanded_tasks = set()  # Almacenar IDs de tareas expandidas
        self.subtasks_containers = {}  # Almacenar referencias a los containers de subtareas

    def build(self, task: Task) -> ft.Card:
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

        # Badge con el estado actual
        status_badge = self._build_status_badge(task)

        # Botones pequeños alineados a la derecha
        action_buttons = ft.Row(
            controls=[
                ft.IconButton(
                    ft.Icons.EDIT,
                    tooltip="Editar",
                    icon_size=18,
                    on_click=lambda _, t=task: self.on_edit(t),
                ),
                ft.IconButton(
                    ft.Icons.DELETE,
                    tooltip="Eliminar",
                    icon_size=18,
                    icon_color=ft.Colors.RED,
                    on_click=lambda _, t=task: self.on_delete(t),
                ),
            ],
            spacing=0,
        )

        return ft.Card(
            content=ft.Container(
                padding=12,
                content=ft.Column(
                    controls=[
                        ft.Row(
                            controls=[
                                title_row,
                                status_badge,
                                action_buttons,
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            vertical_alignment=ft.CrossAxisAlignment.START,
                        ),
                        subtasks_container,
                    ],
                    spacing=4,
                ),
            )
        )

    def _build_title_row(self, task: Task) -> ft.Control:
        """Construye la fila del título con checkbox si no hay subtareas."""
        if task.subtasks:
            # Si hay subtareas, mostrar título y estado basado en progreso
            status_text = self._get_status_text(task)
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
                    ft.Text(
                        status_text,
                        size=11,
                        color=ft.Colors.BLUE_ACCENT,
                        weight=ft.FontWeight.W_500,
                    ),
                ],
                expand=True,
                spacing=4,
            )
        else:
            # Si NO hay subtareas, mostrar checkbox + título (manual)
            return ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Checkbox(
                                value=task.status == "completada",
                                on_change=lambda e: self._on_task_checkbox_changed(task, e),
                            ),
                            ft.Text(
                                task.title,
                                size=16,
                                weight=ft.FontWeight.W_600,
                                color=ft.Colors.GREY_600
                                if task.status == "completada"
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

    def _build_subtasks_container(self, task: Task) -> ft.Container:
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
                                on_change=lambda e, st=subtask, t=task: self._on_subtask_checkbox_changed(st, t, e),
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

    def _toggle_subtasks(self, task: Task):
        """Alterna la visibilidad de las subtareas."""
        if task.id in self.expanded_tasks:
            self.expanded_tasks.remove(task.id)
        else:
            self.expanded_tasks.add(task.id)
        
        # Actualizar la visibilidad del container
        if task.id in self.subtasks_containers:
            self.subtasks_containers[task.id].visible = task.id in self.expanded_tasks
    
    def _get_status_text(self, task: Task) -> str:
        """Retorna el texto del estado de la tarea basado en subtareas."""
        if not task.subtasks:
            return ""
        
        completed_count = sum(1 for st in task.subtasks if st.completed)
        total_count = len(task.subtasks)
        
        return f"{completed_count}/{total_count} completadas - {task.status}"
    
    def _on_task_checkbox_changed(self, task: Task, e):
        """Maneja el cambio del checkbox de la tarea (sin subtareas)."""
        from app.utils.task_helper import TASK_STATUS_COMPLETED, TASK_STATUS_PENDING
        
        if e.control.value:
            task.status = TASK_STATUS_COMPLETED
        else:
            task.status = TASK_STATUS_PENDING
        
        if self.on_task_updated:
            self.on_task_updated(task)
    
    def _build_status_badge(self, task: Task) -> ft.Container:
        """Construye un badge con el estado de la tarea con color según el estado."""
        status_color = self._get_status_color(task.status)
        status_label = self._get_status_label(task.status)
        
        return ft.Container(
            content=ft.Text(
                status_label,
                size=12,
                weight=ft.FontWeight.W_600,
                color=ft.Colors.BLACK,
            ),
            bgcolor=status_color,
            padding=ft.padding.symmetric(horizontal=12, vertical=6),
            border_radius=12,
        )
    
    def _get_status_color(self, status: str) -> str:
        """Retorna el color según el estado de la tarea."""
        if status == "pendiente":
            return ft.Colors.AMBER
        elif status == "en_progreso":
            return ft.Colors.LIGHT_BLUE
        elif status == "completada":
            return ft.Colors.LIGHT_GREEN
        else:
            return ft.Colors.GREY_400
    
    def _get_status_label(self, status: str) -> str:
        """Retorna el label a mostrar según el estado."""
        if status == "pendiente":
            return "Pendiente"
        elif status == "en_progreso":
            return "En progreso"
        elif status == "completada":
            return "Completada"
        else:
            return status
    
    def _on_subtask_checkbox_changed(self, subtask, task: Task, e):
        """Maneja el cambio del checkbox de una subtarea."""
        subtask.toggle_completed()
        # Actualizar el estado de la tarea basado en sus subtareas
        task.update_status_from_subtasks()
        
        if self.on_task_updated:
            self.on_task_updated(task)
