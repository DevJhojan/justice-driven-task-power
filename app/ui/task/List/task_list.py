"""
Lista de tareas unificada.
Combina la versión modular usada por la vista principal con la API ligera
que ejercen los tests (create_task_list/TaskList con operaciones CRUD en memoria).
"""

from __future__ import annotations

from typing import Callable, Iterable, List, Optional, TYPE_CHECKING

import flet as ft
from app.ui.task.card.task_card_view import TaskCardView

if TYPE_CHECKING:
    from app.models.task import Task


def _noop(*_, **__):
    """Default no-op callback to avoid None checks when wiring events."""
    return None


def _build_task_container(task: "Task", task_card_view: TaskCardView) -> ft.Container:
    """Envuelve la tarjeta en un contenedor sencillo para lista plana."""
    return ft.Container(content=task_card_view.build(task), padding=4)


def create_task_list(
    tasks: Optional[Iterable["Task"]] = None,
    page: Optional[ft.Page] = None,
    on_task_click: Optional[Callable[[str], None]] = None,
    on_task_edit: Optional[Callable[[str], None]] = None,
    on_task_delete: Optional[Callable[[str], None]] = None,
    on_task_toggle_status: Optional[Callable[[str], None]] = None,
    on_subtask_toggle: Optional[Callable[[str, str], None]] = None,
    on_task_updated: Optional[Callable[["Task"], None]] = None,
    progress_service=None,
    rewards_view=None,
) -> ft.Column:
    """Crea una columna básica de tareas para los tests unitarios."""

    tasks_list = list(tasks) if tasks else []

    if not tasks_list:
        empty_state = ft.Container(
            content=ft.Text("No hay tareas", color=ft.Colors.GREY_600),
            padding=12,
            border=ft.Border.all(1, ft.Colors.GREY_700),
            border_radius=8,
        )
        return ft.Column(controls=[empty_state], spacing=8)

    task_card_view = TaskCardView(
        on_edit=on_task_edit or _noop,
        on_delete=on_task_delete or _noop,
        on_task_updated=on_task_updated,
        progress_service=progress_service,
        rewards_view=rewards_view,
        page=page,
    )

    # Asignar callback de click solo si se provee
    if on_task_click:
        def with_click(task: "Task"):
            card = task_card_view.build(task)
            card.on_click = lambda _: on_task_click(task.id)
            return ft.Container(content=card, padding=4)
        controls = [with_click(task) for task in tasks_list]
    else:
        controls = [_build_task_container(task, task_card_view) for task in tasks_list]

    return ft.Column(controls=controls, spacing=8)


class TaskList:
    """Componente para renderizar y manipular la lista de tareas."""

    def __init__(
        self,
        on_edit: Optional[Callable] = None,
        on_delete: Optional[Callable] = None,
        on_task_updated: Optional[Callable] = None,
        progress_service=None,
        rewards_view=None,
        page=None,
        tasks: Optional[Iterable["Task"]] = None,
        on_task_click: Optional[Callable[[str], None]] = None,
        on_task_toggle_status: Optional[Callable[[str], None]] = None,
        on_subtask_toggle: Optional[Callable[[str, str], None]] = None,
    ):
        self.on_edit = on_edit or _noop
        self.on_delete = on_delete or _noop
        self.on_task_updated = on_task_updated
        self.progress_service = progress_service
        self.rewards_view = rewards_view
        self.page = page
        self.on_task_click = on_task_click
        self.on_task_toggle_status = on_task_toggle_status
        self.on_subtask_toggle = on_subtask_toggle

        # Datos
        self.tasks: List[Task] = list(tasks) if tasks else []

        # UI
        self.list_column: ft.Column = ft.Column(spacing=8, expand=True)
        self.task_card_view: TaskCardView = TaskCardView(
            self.on_edit,
            self.on_delete,
            self.on_task_updated,
            self.progress_service,
            self.rewards_view,
            self.page,
        )
        self.filter_bar: ft.Row = None
        self.current_filter: str = "pendiente"  # "pendiente", "en_progreso", "completada"
        self.container: ft.Column = None
        self._list_column: Optional[ft.Column] = None

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
        self._list_column = self.container
        self.render(self.tasks)
        return self.container

    def render(self, tasks: List[Task]):
        """
        Renderiza la lista de tareas.

        Args:
            tasks: Lista de tareas a renderizar
        """
        self.tasks = list(tasks)
        filtered_tasks = self._apply_filter(self.tasks)
        
        self.list_column.controls.clear()

        if not filtered_tasks:
            self.list_column.controls.append(
                ft.Text("No hay tareas", color=ft.Colors.GREY_600)
            )
        else:
            for task in filtered_tasks:
                card = self.task_card_view.build(task)
                if self.on_task_click:
                    card.on_click = lambda _, t_id=task.id: self.on_task_click(t_id)
                self.list_column.controls.append(card)

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
            controls=[pendiente_btn, en_progreso_btn, completada_btn],
            spacing=8,
            alignment=ft.MainAxisAlignment.START,
        )
        
        # Guardar referencias a los botones para actualizar estilos
        self.filter_buttons = {
            "pendiente": pendiente_btn,
            "en_progreso": en_progreso_btn,
            "completada": completada_btn,
        }
    
    def _get_button_style(self, filter_type: str) -> ft.ButtonStyle:
        """Retorna el estilo del botón según si está activo o no."""
        is_active = self.current_filter == filter_type
        
        # Colores por estado
        active_colors = {
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
        self.render(self.tasks)
    
    def _apply_filter(self, tasks: List[Task]) -> List[Task]:
        """Aplica el filtro actual a las tareas."""
        return [task for task in tasks if task.status == self.current_filter]

    # ------------------------------------------------------------------
    # API utilizada por tests unitarios
    # ------------------------------------------------------------------
    def add_task(self, task: Task):
        self.tasks.append(task)
        self.refresh()

    def remove_task(self, task_id: str):
        self.tasks = [t for t in self.tasks if t.id != task_id]
        self.refresh()

    def get_task(self, task_id: str) -> Optional[Task]:
        return next((t for t in self.tasks if t.id == task_id), None)

    def update_task(self, task: Task):
        for idx, current in enumerate(self.tasks):
            if current.id == task.id:
                self.tasks[idx] = task
                break
        else:
            self.tasks.append(task)
        self.refresh()

    def filter_tasks(self, predicate: Callable[[Task], bool]) -> List[Task]:
        return [task for task in self.tasks if predicate(task)]

    def sort_tasks(self, key_func: Optional[Callable[[Task], str]] = None):
        key = key_func if key_func else (lambda t: (t.title or "").lower())
        self.tasks.sort(key=key)
        self.refresh()

    def clear(self):
        self.tasks = []
        self.refresh()

    def set_tasks(self, tasks: Iterable[Task]):
        self.tasks = list(tasks)
        self.refresh()

    def refresh(self):
        """Invalida caché y fuerza reconstrucción en próximo build()."""
        self._list_column = None
        # Re-render si ya hay contenedor construido
        if self.container:
            self.render(self.tasks)

    def get_tasks(self) -> List[Task]:
        return list(self.tasks)


__all__ = ["create_task_list", "TaskList"]
