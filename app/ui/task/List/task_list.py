"""
Componente modular para renderizar la lista de tareas.
"""

from __future__ import annotations

from typing import List, Callable, TYPE_CHECKING

import flet as ft
from app.ui.task.card.task_card_view import TaskCardView

if TYPE_CHECKING:
    from app.models.task import Task


class TaskList:
    """Componente para renderizar la lista de tareas."""

    def __init__(self, on_edit: Callable, on_delete: Callable, on_task_updated: Callable = None):
        """
        Inicializa el componente de lista de tareas.

        Args:
            on_edit: Callback cuando se hace clic en editar
            on_delete: Callback cuando se hace clic en eliminar
            on_task_updated: Callback cuando se actualiza una tarea (opcional)
        """
        self.on_edit = on_edit
        self.on_delete = on_delete
        self.on_task_updated = on_task_updated
        self.list_column: ft.Column = ft.Column(spacing=8, expand=True)
        self.task_card_view: TaskCardView = TaskCardView(
            on_edit, on_delete, on_task_updated
        )
        self.filter_bar: ft.Row = None
        self.current_filter: str = "todos"  # "todos", "pendiente", "en_progreso", "completada"
        self.all_tasks: List[Task] = []
        self.container: ft.Column = None

    def build(self) -> ft.Column:
        """Retorna el contenedor con la barra de filtros y la lista de tareas."""
        self._build_filter_bar()
        
        self.container = ft.Column(
            controls=[
                self.filter_bar,
                self.list_column,
            ],
            spacing=12,
            expand=True,
        )
        
        return self.container

    def render(self, tasks: List[Task]):
        """
        Renderiza la lista de tareas.

        Args:
            tasks: Lista de tareas a renderizar
        """
        self.all_tasks = tasks
        filtered_tasks = self._apply_filter(tasks)
        
        self.list_column.controls.clear()

        if not filtered_tasks:
            self.list_column.controls.append(
                ft.Text("No hay tareas", color=ft.Colors.GREY_600)
            )
        else:
            for task in filtered_tasks:
                self.list_column.controls.append(self.task_card_view.build(task))

    def show(self):
        """Muestra la lista de tareas."""
        if self.container:
            self.container.visible = True

    def hide(self):
        """Oculta la lista de tareas."""
        if self.container:
            self.container.visible = False
    
    def _build_filter_bar(self):
        """Construye la barra de filtros con los estados."""
        todos_btn = ft.ElevatedButton(
            "Todos",
            on_click=lambda _: self._set_filter("todos"),
            style=self._get_button_style("todos"),
        )
        
        pendiente_btn = ft.ElevatedButton(
            "Pendiente",
            on_click=lambda _: self._set_filter("pendiente"),
            style=self._get_button_style("pendiente"),
        )
        
        en_progreso_btn = ft.ElevatedButton(
            "En progreso",
            on_click=lambda _: self._set_filter("en_progreso"),
            style=self._get_button_style("en_progreso"),
        )
        
        completada_btn = ft.ElevatedButton(
            "Completada",
            on_click=lambda _: self._set_filter("completada"),
            style=self._get_button_style("completada"),
        )
        
        self.filter_bar = ft.Row(
            controls=[todos_btn, pendiente_btn, en_progreso_btn, completada_btn],
            spacing=8,
            alignment=ft.MainAxisAlignment.START,
        )
        
        # Guardar referencias a los botones para actualizar estilos
        self.filter_buttons = {
            "todos": todos_btn,
            "pendiente": pendiente_btn,
            "en_progreso": en_progreso_btn,
            "completada": completada_btn,
        }
    
    def _get_button_style(self, filter_type: str) -> ft.ButtonStyle:
        """Retorna el estilo del botón según si está activo o no."""
        is_active = self.current_filter == filter_type
        
        # Colores por estado
        active_colors = {
            "todos": (ft.Colors.GREY_700, ft.Colors.WHITE),
            "pendiente": (ft.Colors.AMBER, ft.Colors.BLACK),
            "en_progreso": (ft.Colors.BLUE_600, ft.Colors.WHITE),
            "completada": (ft.Colors.GREEN_500, ft.Colors.WHITE),
        }

        if is_active:
            bgcolor, color = active_colors.get(
                filter_type, (ft.Colors.GREY_700, ft.Colors.WHITE)
            )
        else:
            bgcolor = ft.Colors.GREY_800
            color = ft.Colors.WHITE70
        
        return ft.ButtonStyle(
            bgcolor=bgcolor,
            color=color,
        )
    
    def _set_filter(self, filter_type: str):
        """Establece el filtro actual y actualiza la lista."""
        self.current_filter = filter_type
        
        # Actualizar estilos de los botones
        for key, btn in self.filter_buttons.items():
            btn.style = self._get_button_style(key)
        
        # Re-renderizar con el nuevo filtro
        self.render(self.all_tasks)
    
    def _apply_filter(self, tasks: List[Task]) -> List[Task]:
        """Aplica el filtro actual a las tareas."""
        if self.current_filter == "todos":
            return tasks
        else:
            return [task for task in tasks if task.status == self.current_filter]
