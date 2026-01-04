"""
Handlers para Task Card
Funciones que manejan los eventos de interacción con la tarjeta de tarea
"""

import flet as ft
from typing import Optional, Callable
from app.models.task import Task
from app.ui.task.status_badge import create_status_badge
from app.utils.task_helper import (
    calculate_completion_percentage,
    format_completion_percentage,
    TASK_STATUS_PENDING,
    TASK_STATUS_IN_PROGRESS,
    TASK_STATUS_COMPLETED,
)


def create_subtask_toggle_handler(
    task: Task,
    page: Optional[ft.Page],
    progress_bar: Optional[ft.ProgressBar],
    progress_text: Optional[ft.Text],
    badges_row: ft.Row,
    show_progress: bool,
    on_subtask_toggle: Optional[Callable[[str, str], None]] = None,
) -> Callable[[str], None]:
    """
    Crea un handler que actualiza el progreso y estado automáticamente
    cuando se marca/desmarca una subtarea
    
    Args:
        task: Instancia de Task
        page: Objeto Page de Flet para actualizar la UI
        progress_bar: Barra de progreso a actualizar
        progress_text: Texto del porcentaje a actualizar
        badges_row: Fila de badges que contiene el badge de estado
        show_progress: Si se muestra el progreso
        on_subtask_toggle: Callback original a llamar después de actualizar
    
    Returns:
        Función handler que recibe el subtask_id
    """
    def handler(received_subtask_id: str):
        """Handler que se ejecuta cuando se marca/desmarca una subtarea"""
        # Buscar la subtarea en la tarea
        subtask = next((st for st in task.subtasks if st.id == received_subtask_id), None)
        if subtask:
            # Alternar el estado de completitud de la subtarea
            subtask.toggle_completed()
            
            # Calcular nuevo porcentaje de completitud
            new_percentage = calculate_completion_percentage(task)
            
            # Actualizar estado de la tarea según el progreso
            _update_task_status_by_progress(
                task=task,
                new_percentage=new_percentage,
                badges_row=badges_row,
                page=page,
            )
            
            # Actualizar progreso si está habilitado
            if show_progress and progress_bar is not None and progress_text is not None:
                progress_bar.value = new_percentage
                progress_text.value = format_completion_percentage(task)
            
            # Actualizar la página si está disponible
            if page:
                page.update()
            
            # Llamar al callback original si existe
            if on_subtask_toggle:
                on_subtask_toggle(task.id, received_subtask_id)
    
    return handler


def create_toggle_status_handler(
    task: Task,
    page: Optional[ft.Page],
    progress_bar: Optional[ft.ProgressBar],
    progress_text: Optional[ft.Text],
    badges_row: ft.Row,
    toggle_button: ft.IconButton,
    show_progress: bool,
    on_toggle_status: Optional[Callable[[str], None]] = None,
) -> Callable:
    """
    Crea un handler que alterna el estado de una tarea sin subtareas
    
    Args:
        task: Instancia de Task (debe estar sin subtareas)
        page: Objeto Page de Flet para actualizar la UI
        progress_bar: Barra de progreso a actualizar
        progress_text: Texto del porcentaje a actualizar
        badges_row: Fila de badges que contiene el badge de estado
        toggle_button: Botón de toggle para actualizar su ícono
        show_progress: Si se muestra el progreso
        on_toggle_status: Callback original a llamar después de actualizar
    
    Returns:
        Función handler que se ejecuta al hacer clic
    """
    def handler(e):
        """Handler que se ejecuta cuando se hace clic en el botón de toggle"""
        # Si la tarea no está completada, marcarla como completada
        if task.status != TASK_STATUS_COMPLETED:
            # Actualizar estado a completada
            task.update_status(TASK_STATUS_COMPLETED)
            
            # Actualizar progreso a 100% (sin subtareas, completar = 100%)
            if show_progress and progress_bar is not None and progress_text is not None:
                progress_bar.value = 1.0
                progress_text.value = format_completion_percentage(task)
        else:
            # Si está completada, marcarla como pendiente
            task.update_status(TASK_STATUS_PENDING)
            
            # Actualizar progreso a 0% (sin subtareas, descompletar = 0%)
            if show_progress and progress_bar is not None and progress_text is not None:
                progress_bar.value = 0.0
                progress_text.value = format_completion_percentage(task)
        
        # Reconstruir el badge de estado
        new_status_badge = create_status_badge(task.status, page=page, size="small")
        badges_row.controls[0] = new_status_badge
        
        # Actualizar el ícono del botón
        toggle_button.icon = ft.Icons.CHECK_CIRCLE if task.status != TASK_STATUS_COMPLETED else ft.Icons.UNDO
        
        # Actualizar la página
        if page:
            page.update()
        
        # Llamar al callback original si existe
        if on_toggle_status:
            on_toggle_status(task.id)
    
    return handler


def _update_task_status_by_progress(
    task: Task,
    new_percentage: float,
    badges_row: ft.Row,
    page: Optional[ft.Page],
):
    """
    Actualiza el estado de la tarea según el porcentaje de completitud
    
    Args:
        task: Instancia de Task a actualizar
        new_percentage: Nuevo porcentaje de completitud (0.0 a 1.0)
        badges_row: Fila de badges que contiene el badge de estado
        page: Objeto Page de Flet para actualizar la UI
    """
    # Si está al 100%, cambiar a "Completada"
    if new_percentage >= 1.0:
        if task.status != TASK_STATUS_COMPLETED:
            task.update_status(TASK_STATUS_COMPLETED)
            # Reconstruir el badge de estado
            new_status_badge = create_status_badge(task.status, page=page, size="small")
            badges_row.controls[0] = new_status_badge
    # Si está al 0% (no hay subtareas completadas), cambiar a "Pendiente"
    elif new_percentage == 0.0:
        if task.status != TASK_STATUS_PENDING:
            task.update_status(TASK_STATUS_PENDING)
            # Reconstruir el badge de estado
            new_status_badge = create_status_badge(task.status, page=page, size="small")
            badges_row.controls[0] = new_status_badge
    # Si está entre 0% y 100%, cambiar a "En progreso" si no lo está
    else:
        if task.status == TASK_STATUS_PENDING or task.status == TASK_STATUS_COMPLETED:
            task.update_status(TASK_STATUS_IN_PROGRESS)
            # Reconstruir el badge de estado
            new_status_badge = create_status_badge(task.status, page=page, size="small")
            badges_row.controls[0] = new_status_badge

