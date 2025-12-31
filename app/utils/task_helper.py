"""
Funciones auxiliares para tareas
Funciones generales de formateo, validación y cálculo relacionadas con tareas
"""

from datetime import datetime, date
from typing import Optional, Union, Any
import flet as ft


# Estados válidos de tareas
TASK_STATUS_PENDING = "pendiente"
TASK_STATUS_IN_PROGRESS = "en_progreso"
TASK_STATUS_COMPLETED = "completada"
TASK_STATUS_CANCELLED = "cancelada"

VALID_TASK_STATUSES = [
    TASK_STATUS_PENDING,
    TASK_STATUS_IN_PROGRESS,
    TASK_STATUS_COMPLETED,
    TASK_STATUS_CANCELLED,
]


def format_task_status(status: str) -> str:
    """
    Formatea el estado de una tarea a formato legible
    
    Args:
        status: Estado de la tarea
        
    Returns:
        Estado formateado para mostrar en UI
        
    Ejemplo:
        >>> format_task_status("pendiente")
        'Pendiente'
        >>> format_task_status("en_progreso")
        'En Progreso'
    """
    status_map = {
        TASK_STATUS_PENDING: "Pendiente",
        TASK_STATUS_IN_PROGRESS: "En Progreso",
        TASK_STATUS_COMPLETED: "Completada",
        TASK_STATUS_CANCELLED: "Cancelada",
    }
    return status_map.get(status.lower(), status.capitalize())


def get_task_status_color(status: str) -> str:
    """
    Obtiene el color asociado a un estado de tarea
    
    Args:
        status: Estado de la tarea
        
    Returns:
        Color en formato hexadecimal
        
    Ejemplo:
        >>> get_task_status_color("pendiente")
        '#F59E0B'  # Amarillo
        >>> get_task_status_color("completada")
        '#10B981'  # Verde
    """
    colors = {
        TASK_STATUS_PENDING: "#F59E0B",      # Amarillo/Naranja
        TASK_STATUS_IN_PROGRESS: "#3B82F6",  # Azul
        TASK_STATUS_COMPLETED: "#10B981",    # Verde
        TASK_STATUS_CANCELLED: "#6B7280",    # Gris
    }
    return colors.get(status.lower(), "#6B7280")


def get_task_status_ft_color(status: str) -> str:
    """
    Obtiene el color de Flet asociado a un estado de tarea
    
    Args:
        status: Estado de la tarea
        
    Returns:
        Color de Flet (ft.Colors.*)
        
    Ejemplo:
        >>> get_task_status_ft_color("pendiente")
        ft.Colors.ORANGE_500
    """
    colors = {
        TASK_STATUS_PENDING: ft.Colors.ORANGE_500,
        TASK_STATUS_IN_PROGRESS: ft.Colors.BLUE_500,
        TASK_STATUS_COMPLETED: ft.Colors.GREEN_500,
        TASK_STATUS_CANCELLED: ft.Colors.GREY_500,
    }
    return colors.get(status.lower(), ft.Colors.GREY_500)


def get_task_status_icon(status: str) -> str:
    """
    Obtiene el icono asociado a un estado de tarea
    
    Args:
        status: Estado de la tarea
        
    Returns:
        Nombre del icono de Flet
        
    Ejemplo:
        >>> get_task_status_icon("pendiente")
        ft.Icons.PENDING
        >>> get_task_status_icon("completada")
        ft.Icons.CHECK_CIRCLE
    """
    icons = {
        TASK_STATUS_PENDING: ft.Icons.PENDING,
        TASK_STATUS_IN_PROGRESS: ft.Icons.PLAY_CIRCLE,
        TASK_STATUS_COMPLETED: ft.Icons.CHECK_CIRCLE,
        TASK_STATUS_CANCELLED: ft.Icons.CANCEL,
    }
    return icons.get(status.lower(), ft.Icons.CIRCLE)


def calculate_completion_percentage(task: Any) -> float:
    """
    Calcula el porcentaje de completitud de una tarea basado en sus subtareas
    
    Args:
        task: Objeto tarea que debe tener subtareas
        
    Returns:
        Porcentaje de completitud (0.0 a 1.0)
        
    Ejemplo:
        >>> task = {"subtasks": [{"completed": True}, {"completed": False}]}
        >>> calculate_completion_percentage(task)
        0.5
    """
    if not hasattr(task, 'subtasks') and not isinstance(task, dict):
        return 0.0
    
    subtasks = getattr(task, 'subtasks', []) if hasattr(task, 'subtasks') else task.get('subtasks', [])
    
    if not subtasks or len(subtasks) == 0:
        # Si no hay subtareas, verificar el estado de la tarea
        status = getattr(task, 'status', None) if hasattr(task, 'status') else task.get('status', None)
        if status == TASK_STATUS_COMPLETED:
            return 1.0
        return 0.0
    
    completed = 0
    for subtask in subtasks:
        is_completed = getattr(subtask, 'completed', False) if hasattr(subtask, 'completed') else subtask.get('completed', False)
        if is_completed:
            completed += 1
    
    return completed / len(subtasks)


def format_completion_percentage(task: Any, decimals: int = 0) -> str:
    """
    Formatea el porcentaje de completitud de una tarea como string
    
    Args:
        task: Objeto tarea
        decimals: Número de decimales (default: 0)
        
    Returns:
        Porcentaje formateado (ej: "75%")
        
    Ejemplo:
        >>> task = {"subtasks": [{"completed": True}, {"completed": False}]}
        >>> format_completion_percentage(task)
        '50%'
    """
    percentage = calculate_completion_percentage(task) * 100
    return f"{percentage:.{decimals}f}%"


def is_task_overdue(task: Any) -> bool:
    """
    Verifica si una tarea está vencida
    
    Args:
        task: Objeto tarea que debe tener due_date
        
    Returns:
        True si la tarea está vencida, False en caso contrario
    """
    if not hasattr(task, 'due_date') and not isinstance(task, dict):
        return False
    
    due_date = getattr(task, 'due_date', None) if hasattr(task, 'due_date') else task.get('due_date', None)
    
    if not due_date:
        return False
    
    # Convertir a date si es datetime
    if isinstance(due_date, datetime):
        due_date = due_date.date()
    elif isinstance(due_date, str):
        try:
            due_date = datetime.fromisoformat(due_date).date()
        except (ValueError, AttributeError):
            return False
    
    if not isinstance(due_date, date):
        return False
    
    return due_date < date.today()


def is_task_due_today(task: Any) -> bool:
    """
    Verifica si una tarea vence hoy
    
    Args:
        task: Objeto tarea que debe tener due_date
        
    Returns:
        True si la tarea vence hoy, False en caso contrario
    """
    if not hasattr(task, 'due_date') and not isinstance(task, dict):
        return False
    
    due_date = getattr(task, 'due_date', None) if hasattr(task, 'due_date') else task.get('due_date', None)
    
    if not due_date:
        return False
    
    # Convertir a date si es datetime
    if isinstance(due_date, datetime):
        due_date = due_date.date()
    elif isinstance(due_date, str):
        try:
            due_date = datetime.fromisoformat(due_date).date()
        except (ValueError, AttributeError):
            return False
    
    if not isinstance(due_date, date):
        return False
    
    return due_date == date.today()


def is_task_due_soon(task: Any, days: int = 3) -> bool:
    """
    Verifica si una tarea vence pronto (en los próximos N días)
    
    Args:
        task: Objeto tarea que debe tener due_date
        days: Número de días para considerar "pronto" (default: 3)
        
    Returns:
        True si la tarea vence pronto, False en caso contrario
    """
    if not hasattr(task, 'due_date') and not isinstance(task, dict):
        return False
    
    due_date = getattr(task, 'due_date', None) if hasattr(task, 'due_date') else task.get('due_date', None)
    
    if not due_date:
        return False
    
    # Convertir a date si es datetime
    if isinstance(due_date, datetime):
        due_date = due_date.date()
    elif isinstance(due_date, str):
        try:
            due_date = datetime.fromisoformat(due_date).date()
        except (ValueError, AttributeError):
            return False
    
    if not isinstance(due_date, date):
        return False
    
    today = date.today()
    days_until_due = (due_date - today).days
    
    return 0 <= days_until_due <= days


def get_task_urgency_indicator(task: Any) -> str:
    """
    Obtiene un indicador de urgencia basado en la fecha de vencimiento
    
    Args:
        task: Objeto tarea
        
    Returns:
        Indicador de urgencia: "overdue", "due_today", "due_soon", "normal"
    """
    if is_task_overdue(task):
        return "overdue"
    elif is_task_due_today(task):
        return "due_today"
    elif is_task_due_soon(task):
        return "due_soon"
    else:
        return "normal"


def count_subtasks(task: Any) -> int:
    """
    Cuenta el número de subtareas de una tarea
    
    Args:
        task: Objeto tarea
        
    Returns:
        Número de subtareas
    """
    if not hasattr(task, 'subtasks') and not isinstance(task, dict):
        return 0
    
    subtasks = getattr(task, 'subtasks', []) if hasattr(task, 'subtasks') else task.get('subtasks', [])
    return len(subtasks) if subtasks else 0


def count_completed_subtasks(task: Any) -> int:
    """
    Cuenta el número de subtareas completadas
    
    Args:
        task: Objeto tarea
        
    Returns:
        Número de subtareas completadas
    """
    if not hasattr(task, 'subtasks') and not isinstance(task, dict):
        return 0
    
    subtasks = getattr(task, 'subtasks', []) if hasattr(task, 'subtasks') else task.get('subtasks', [])
    
    if not subtasks:
        return 0
    
    completed = 0
    for subtask in subtasks:
        is_completed = getattr(subtask, 'completed', False) if hasattr(subtask, 'completed') else subtask.get('completed', False)
        if is_completed:
            completed += 1
    
    return completed


def has_subtasks(task: Any) -> bool:
    """
    Verifica si una tarea tiene subtareas
    
    Args:
        task: Objeto tarea
        
    Returns:
        True si tiene subtareas, False en caso contrario
    """
    return count_subtasks(task) > 0


def is_task_completed(task: Any) -> bool:
    """
    Verifica si una tarea está completada
    
    Args:
        task: Objeto tarea
        
    Returns:
        True si está completada, False en caso contrario
    """
    status = getattr(task, 'status', None) if hasattr(task, 'status') else task.get('status', None)
    return status == TASK_STATUS_COMPLETED


def is_task_pending(task: Any) -> bool:
    """
    Verifica si una tarea está pendiente
    
    Args:
        task: Objeto tarea
        
    Returns:
        True si está pendiente, False en caso contrario
    """
    status = getattr(task, 'status', None) if hasattr(task, 'status') else task.get('status', None)
    return status == TASK_STATUS_PENDING


def is_task_in_progress(task: Any) -> bool:
    """
    Verifica si una tarea está en progreso
    
    Args:
        task: Objeto tarea
        
    Returns:
        True si está en progreso, False en caso contrario
    """
    status = getattr(task, 'status', None) if hasattr(task, 'status') else task.get('status', None)
    return status == TASK_STATUS_IN_PROGRESS


def filter_tasks_by_status(tasks: list, status: str) -> list:
    """
    Filtra tareas por estado
    
    Args:
        tasks: Lista de tareas
        status: Estado a filtrar
        
    Returns:
        Lista de tareas filtradas
    """
    if not status or status.lower() == "normal" or status.lower() == "todas":
        return tasks
    
    filtered = []
    for task in tasks:
        task_status = getattr(task, 'status', None) if hasattr(task, 'status') else task.get('status', None)
        if task_status and task_status.lower() == status.lower():
            filtered.append(task)
    
    return filtered


def get_task_summary(task: Any) -> dict:
    """
    Obtiene un resumen completo de una tarea
    
    Args:
        task: Objeto tarea
        
    Returns:
        Diccionario con resumen de la tarea
    """
    subtasks_count = count_subtasks(task)
    completed_subtasks = count_completed_subtasks(task)
    completion_percentage = calculate_completion_percentage(task)
    
    return {
        "subtasks_total": subtasks_count,
        "subtasks_completed": completed_subtasks,
        "completion_percentage": completion_percentage,
        "is_overdue": is_task_overdue(task),
        "is_due_today": is_task_due_today(task),
        "is_due_soon": is_task_due_soon(task),
        "urgency_indicator": get_task_urgency_indicator(task),
        "is_completed": is_task_completed(task),
    }

