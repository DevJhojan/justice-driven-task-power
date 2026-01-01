"""
Componente Task List
Muestra una lista de tarjetas de tareas usando el componente TaskCard modularizado.
Proporciona funcionalidades para filtrado, ordenamiento y gestión de tareas.
"""

import flet as ft
from typing import Optional, Callable, List
from app.models.task import Task
from app.ui.task.components.cards import TaskCard
from app.utils.helpers.responsives import (
    get_responsive_padding,
    get_responsive_spacing,
)


def create_task_list(
    tasks: List[Task],
    page: Optional[ft.Page] = None,
    on_task_click: Optional[Callable[[str], None]] = None,
    on_task_edit: Optional[Callable[[str], None]] = None,
    on_task_delete: Optional[Callable[[str], None]] = None,
    on_task_toggle_status: Optional[Callable[[str], None]] = None,
    on_subtask_toggle: Optional[Callable[[str, str], None]] = None,
    on_subtask_edit: Optional[Callable[[str, str], None]] = None,
    on_subtask_delete: Optional[Callable[[str, str], None]] = None,
    show_subtasks: bool = True,
    show_tags: bool = True,
    show_progress: bool = True,
    compact: bool = False,
    spacing: Optional[int] = None,
) -> ft.Column:
    """
    Crea un componente visual para mostrar una lista de tareas.
    Cada tarea se renderiza como una tarjeta usando TaskCard.
    
    Args:
        tasks: Lista de instancias de Task a mostrar
        page: Objeto Page de Flet para cálculos responsive (opcional)
        on_task_click: Callback cuando se hace clic en una tarjeta (recibe task_id)
        on_task_edit: Callback cuando se edita una tarea (recibe task_id)
        on_task_delete: Callback cuando se elimina una tarea (recibe task_id)
        on_task_toggle_status: Callback cuando se cambia el estado (recibe task_id)
        on_subtask_toggle: Callback cuando se marca/desmarca subtarea (recibe task_id, subtask_id)
        on_subtask_edit: Callback cuando se edita subtarea (recibe task_id, subtask_id)
        on_subtask_delete: Callback cuando se elimina subtarea (recibe task_id, subtask_id)
        show_subtasks: Si se muestran las subtareas (default: True)
        show_tags: Si se muestran las etiquetas (default: True)
        show_progress: Si se muestra la barra de progreso (default: True)
        compact: Si se usa un diseño compacto (default: False)
        spacing: Espaciado entre tarjetas (auto si no se especifica)
    
    Returns:
        Column con todas las tarjetas de tareas
        
    Ejemplo:
        >>> tasks = [task1, task2, task3]
        >>> task_list = create_task_list(tasks, page=page, on_task_edit=handle_edit)
        >>> tasks_view.controls.append(task_list)
    """
    # Calcular espaciado responsive
    if spacing is None:
        spacing = get_responsive_spacing(page=page, mobile=8, tablet=10, desktop=12)
    
    # Crear tarjetas para cada tarea
    task_cards: list[ft.Control] = []
    
    for task in tasks:
        task_card = TaskCard(
            task=task,
            page=page,
            on_click=on_task_click,
            on_edit=on_task_edit,
            on_delete=on_task_delete,
            on_toggle_status=on_task_toggle_status,
            on_subtask_toggle=on_subtask_toggle,
            on_subtask_edit=on_subtask_edit,
            on_subtask_delete=on_subtask_delete,
            show_subtasks=show_subtasks,
            show_tags=show_tags,
            show_progress=show_progress,
            compact=compact,
        )
        
        # Agregar la tarjeta construida
        card = task_card.build()
        if card:
            task_cards.append(card)
    
    # Si no hay tareas, mostrar mensaje vacío
    if not task_cards:
        task_cards = [
            ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Icon(
                            icon=ft.Icons.TASK,
                            size=64,
                            color=ft.Colors.GREY_600,
                        ),
                        ft.Text(
                            "No hay tareas",
                            size=18,
                            color=ft.Colors.WHITE_70,
                        ),
                        ft.Text(
                            "Crea una nueva tarea para comenzar",
                            size=14,
                            color=ft.Colors.WHITE_54,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=16,
                ),
                alignment=ft.Alignment(0, 0),
                padding=get_responsive_padding(page=page),
                expand=True,
            )
        ]
    
    # Crear columna con todas las tarjetas
    task_list_column = ft.Column(
        controls=task_cards,
        spacing=spacing,
        scroll=ft.ScrollMode.AUTO,
    )
    
    return task_list_column


class TaskList:
    """
    Clase para gestionar una lista de tareas con caching y actualizaciones dinámicas.
    Proporciona métodos para agregar, eliminar, actualizar y filtrar tareas.
    """
    
    def __init__(
        self,
        tasks: Optional[List[Task]] = None,
        page: Optional[ft.Page] = None,
        on_task_click: Optional[Callable[[str], None]] = None,
        on_task_edit: Optional[Callable[[str], None]] = None,
        on_task_delete: Optional[Callable[[str], None]] = None,
        on_task_toggle_status: Optional[Callable[[str], None]] = None,
        on_subtask_toggle: Optional[Callable[[str, str], None]] = None,
        on_subtask_edit: Optional[Callable[[str, str], None]] = None,
        on_subtask_delete: Optional[Callable[[str, str], None]] = None,
        show_subtasks: bool = True,
        show_tags: bool = True,
        show_progress: bool = True,
        compact: bool = False,
    ):
        """
        Inicializa la lista de tareas.
        
        Args:
            tasks: Lista de tareas a mostrar (default: lista vacía)
            page: Objeto Page de Flet para cálculos responsive
            on_task_click: Callback cuando se hace clic en una tarjeta
            on_task_edit: Callback cuando se edita una tarea
            on_task_delete: Callback cuando se elimina una tarea
            on_task_toggle_status: Callback cuando se cambia el estado
            on_subtask_toggle: Callback cuando se marca/desmarca subtarea
            on_subtask_edit: Callback cuando se edita subtarea
            on_subtask_delete: Callback cuando se elimina subtarea
            show_subtasks: Si se muestran las subtareas
            show_tags: Si se muestran las etiquetas
            show_progress: Si se muestra la barra de progreso
            compact: Si se usa un diseño compacto
        """
        self.tasks = tasks if tasks is not None else []
        self.page = page
        self.on_task_click = on_task_click
        self.on_task_edit = on_task_edit
        self.on_task_delete = on_task_delete
        self.on_task_toggle_status = on_task_toggle_status
        self.on_subtask_toggle = on_subtask_toggle
        self.on_subtask_edit = on_subtask_edit
        self.on_subtask_delete = on_subtask_delete
        self.show_subtasks = show_subtasks
        self.show_tags = show_tags
        self.show_progress = show_progress
        self.compact = compact
        
        self._list_column: Optional[ft.Column] = None
    
    def build(self) -> ft.Column:
        """
        Construye y retorna la lista de tareas.
        
        Returns:
            Column con todas las tarjetas de tareas
        """
        if self._list_column is None:
            self._list_column = create_task_list(
                tasks=self.tasks,
                page=self.page,
                on_task_click=self.on_task_click,
                on_task_edit=self.on_task_edit,
                on_task_delete=self.on_task_delete,
                on_task_toggle_status=self.on_task_toggle_status,
                on_subtask_toggle=self.on_subtask_toggle,
                on_subtask_edit=self.on_subtask_edit,
                on_subtask_delete=self.on_subtask_delete,
                show_subtasks=self.show_subtasks,
                show_tags=self.show_tags,
                show_progress=self.show_progress,
                compact=self.compact,
            )
        return self._list_column
    
    def add_task(self, task: Task):
        """
        Agrega una tarea a la lista.
        
        Args:
            task: Tarea a agregar
        """
        self.tasks.append(task)
        self.refresh()
    
    def remove_task(self, task_id: str):
        """
        Elimina una tarea de la lista por ID.
        
        Args:
            task_id: ID de la tarea a eliminar
        """
        self.tasks = [t for t in self.tasks if t.id != task_id]
        self.refresh()
    
    def update_task(self, task: Task):
        """
        Actualiza una tarea existente.
        
        Args:
            task: Tarea con datos actualizados
        """
        for i, t in enumerate(self.tasks):
            if t.id == task.id:
                self.tasks[i] = task
                break
        self.refresh()
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """
        Obtiene una tarea por ID.
        
        Args:
            task_id: ID de la tarea a obtener
            
        Returns:
            Task si existe, None en caso contrario
        """
        for task in self.tasks:
            if task.id == task_id:
                return task
        return None
    
    def filter_tasks(self, predicate) -> List[Task]:
        """
        Filtra tareas basado en un predicado.
        
        Args:
            predicate: Función que retorna True si la tarea debe incluirse
            
        Returns:
            Lista de tareas que cumplen el predicado
        """
        return [t for t in self.tasks if predicate(t)]
    
    def sort_tasks(self, key_func=None):
        """
        Ordena las tareas basado en una función clave.
        
        Args:
            key_func: Función que extrae la clave de ordenamiento
                     (default: ordenar por título)
        """
        if key_func is None:
            key_func = lambda t: t.title
        
        self.tasks.sort(key=key_func)
        self.refresh()
    
    def refresh(self):
        """Invalida el caché y fuerza la reconstrucción de la lista."""
        self._list_column = None
    
    def clear(self):
        """Elimina todas las tareas de la lista."""
        self.tasks = []
        self.refresh()
    
    def set_tasks(self, tasks: List[Task]):
        """
        Reemplaza la lista de tareas.
        
        Args:
            tasks: Nueva lista de tareas
        """
        self.tasks = tasks
        self.refresh()
    
    def get_tasks(self) -> List[Task]:
        """
        Retorna la lista actual de tareas.
        
        Returns:
            Lista de tareas
        """
        return self.tasks.copy()
