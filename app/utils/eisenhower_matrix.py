"""
Funciones auxiliares para la Matriz de Eisenhower
Gestiona la clasificación de tareas según urgencia e importancia

La Matriz de Eisenhower tiene 4 cuadrantes:
- Q1: Urgente e Importante (Hacer primero)
- Q2: Importante pero no Urgente (Programar)
- Q3: Urgente pero no Importante (Delegar)
- Q4: Ni Urgente ni Importante (Eliminar)
"""

from typing import Literal, Optional
import flet as ft


# Tipos de cuadrantes
Quadrant = Literal["Q1", "Q2", "Q3", "Q4"]


def get_eisenhower_quadrant(urgent: bool, important: bool) -> Quadrant:
    """
    Calcula el cuadrante de Eisenhower basado en urgencia e importancia
    
    Args:
        urgent: Si la tarea es urgente
        important: Si la tarea es importante
        
    Returns:
        Cuadrante de Eisenhower (Q1, Q2, Q3, Q4)
        
    Ejemplo:
        >>> get_eisenhower_quadrant(True, True)
        'Q1'
        >>> get_eisenhower_quadrant(False, True)
        'Q2'
    """
    if urgent and important:
        return "Q1"
    elif not urgent and important:
        return "Q2"
    elif urgent and not important:
        return "Q3"
    else:
        return "Q4"


def get_quadrant_name(quadrant: Quadrant) -> str:
    """
    Obtiene el nombre descriptivo de un cuadrante
    
    Args:
        quadrant: Cuadrante de Eisenhower (Q1, Q2, Q3, Q4)
        
    Returns:
        Nombre descriptivo del cuadrante
        
    Ejemplo:
        >>> get_quadrant_name("Q1")
        'Hacer primero'
        >>> get_quadrant_name("Q2")
        'Programar'
    """
    names = {
        "Q1": "Hacer primero",
        "Q2": "Programar",
        "Q3": "Delegar",
        "Q4": "Eliminar",
    }
    return names.get(quadrant, "Desconocido")


def get_quadrant_description(quadrant: Quadrant) -> str:
    """
    Obtiene la descripción detallada de un cuadrante
    
    Args:
        quadrant: Cuadrante de Eisenhower
        
    Returns:
        Descripción del cuadrante
        
    Ejemplo:
        >>> get_quadrant_description("Q1")
        'Urgente e Importante - Hacer primero'
    """
    descriptions = {
        "Q1": "Urgente e Importante - Hacer primero",
        "Q2": "Importante pero no Urgente - Programar",
        "Q3": "Urgente pero no Importante - Delegar",
        "Q4": "Ni Urgente ni Importante - Eliminar",
    }
    return descriptions.get(quadrant, "Desconocido")


def get_quadrant_color(quadrant: Quadrant) -> str:
    """
    Obtiene el color asociado a un cuadrante para la UI
    
    Args:
        quadrant: Cuadrante de Eisenhower
        
    Returns:
        Color en formato hexadecimal
        
    Ejemplo:
        >>> get_quadrant_color("Q1")
        '#EF4444'  # Rojo
    """
    colors = {
        "Q1": "#EF4444",  # Rojo - Urgente e Importante
        "Q2": "#3B82F6",  # Azul - Importante pero no Urgente
        "Q3": "#F59E0B",  # Amarillo/Naranja - Urgente pero no Importante
        "Q4": "#6B7280",  # Gris - Ni Urgente ni Importante
    }
    return colors.get(quadrant, "#6B7280")


def get_quadrant_ft_color(quadrant: Quadrant) -> str:
    """
    Obtiene el color de Flet asociado a un cuadrante
    
    Args:
        quadrant: Cuadrante de Eisenhower
        
    Returns:
        Color de Flet (ft.Colors.*)
        
    Ejemplo:
        >>> get_quadrant_ft_color("Q1")
        ft.Colors.RED_500
    """
    colors = {
        "Q1": ft.Colors.RED_500,
        "Q2": ft.Colors.BLUE_500,
        "Q3": ft.Colors.ORANGE_500,
        "Q4": ft.Colors.GREY_500,
    }
    return colors.get(quadrant, ft.Colors.GREY_500)


def get_quadrant_icon(quadrant: Quadrant) -> str:
    """
    Obtiene el icono asociado a un cuadrante
    
    Args:
        quadrant: Cuadrante de Eisenhower
        
    Returns:
        Nombre del icono de Flet
        
    Ejemplo:
        >>> get_quadrant_icon("Q1")
        ft.Icons.PRIORITY_HIGH
    """
    icons = {
        "Q1": ft.Icons.PRIORITY_HIGH,      # Urgente e Importante
        "Q2": ft.Icons.SCHEDULE,           # Programar
        "Q3": ft.Icons.FORWARD,            # Delegar
        "Q4": ft.Icons.DELETE_OUTLINE,     # Eliminar
    }
    return icons.get(quadrant, ft.Icons.CIRCLE)


def get_priority_label(urgent: bool, important: bool) -> str:
    """
    Obtiene una etiqueta de prioridad legible basada en urgencia e importancia
    
    Args:
        urgent: Si la tarea es urgente
        important: Si la tarea es importante
        
    Returns:
        Etiqueta de prioridad
        
    Ejemplo:
        >>> get_priority_label(True, True)
        'Urgente e Importante'
        >>> get_priority_label(False, True)
        'Importante'
    """
    if urgent and important:
        return "Urgente e Importante"
    elif not urgent and important:
        return "Importante"
    elif urgent and not important:
        return "Urgente"
    else:
        return "Baja Prioridad"


def get_priority_badge_text(urgent: bool, important: bool) -> str:
    """
    Obtiene un texto corto para badge de prioridad
    
    Args:
        urgent: Si la tarea es urgente
        important: Si la tarea es importante
        
    Returns:
        Texto corto para badge
        
    Ejemplo:
        >>> get_priority_badge_text(True, True)
        'Q1'
        >>> get_priority_badge_text(False, True)
        'Q2'
    """
    quadrant = get_eisenhower_quadrant(urgent, important)
    return quadrant


def sort_tasks_by_quadrant(tasks: list) -> dict[str, list]:
    """
    Organiza tareas en un diccionario por cuadrante
    
    Args:
        tasks: Lista de tareas (deben tener atributos urgent e important)
        
    Returns:
        Diccionario con tareas organizadas por cuadrante
        
    Ejemplo:
        >>> tasks = [
        ...     {"urgent": True, "important": True, "title": "Tarea 1"},
        ...     {"urgent": False, "important": True, "title": "Tarea 2"},
        ... ]
        >>> sort_tasks_by_quadrant(tasks)
        {'Q1': [{'urgent': True, 'important': True, 'title': 'Tarea 1'}], 
         'Q2': [{'urgent': False, 'important': True, 'title': 'Tarea 2'}]}
    """
    organized = {
        "Q1": [],
        "Q2": [],
        "Q3": [],
        "Q4": [],
    }
    
    for task in tasks:
        urgent = getattr(task, 'urgent', False) if hasattr(task, 'urgent') else task.get('urgent', False)
        important = getattr(task, 'important', False) if hasattr(task, 'important') else task.get('important', False)
        
        quadrant = get_eisenhower_quadrant(urgent, important)
        organized[quadrant].append(task)
    
    return organized


def get_quadrant_priority_order() -> list[Quadrant]:
    """
    Obtiene el orden de prioridad de los cuadrantes
    
    Returns:
        Lista de cuadrantes ordenados por prioridad (Q1, Q2, Q3, Q4)
        
    Ejemplo:
        >>> get_quadrant_priority_order()
        ['Q1', 'Q2', 'Q3', 'Q4']
    """
    return ["Q1", "Q2", "Q3", "Q4"]


def is_high_priority(urgent: bool, important: bool) -> bool:
    """
    Verifica si una tarea es de alta prioridad (Q1)
    
    Args:
        urgent: Si la tarea es urgente
        important: Si la tarea es importante
        
    Returns:
        True si es Q1 (alta prioridad), False en caso contrario
    """
    return urgent and important


def is_medium_priority(urgent: bool, important: bool) -> bool:
    """
    Verifica si una tarea es de prioridad media (Q2)
    
    Args:
        urgent: Si la tarea es urgente
        important: Si la tarea es importante
        
    Returns:
        True si es Q2 (prioridad media), False en caso contrario
    """
    return not urgent and important


def is_low_priority(urgent: bool, important: bool) -> bool:
    """
    Verifica si una tarea es de baja prioridad (Q3 o Q4)
    
    Args:
        urgent: Si la tarea es urgente
        important: Si la tarea es importante
        
    Returns:
        True si es Q3 o Q4 (baja prioridad), False en caso contrario
    """
    return not important

