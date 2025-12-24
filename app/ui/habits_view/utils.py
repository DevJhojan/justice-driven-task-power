"""
Utilidades y funciones auxiliares para HabitsView.
"""
import flet as ft
from datetime import date
from typing import Set


def get_screen_width(page: ft.Page) -> int:
    """
    Obtiene el ancho de la pantalla de forma segura.
    
    Args:
        page: Página de Flet.
    
    Returns:
        Ancho de la pantalla o 1024 por defecto.
    """
    try:
        screen_width = page.width if (hasattr(page, 'width') and page.width is not None and isinstance(page.width, (int, float))) else 1024
    except (AttributeError, TypeError):
        screen_width = 1024
    return screen_width


def is_desktop_platform(page: ft.Page) -> bool:
    """
    Verifica si la plataforma es de escritorio.
    
    Args:
        page: Página de Flet.
    
    Returns:
        True si es escritorio, False en caso contrario.
    """
    return page.platform == ft.PagePlatform.WINDOWS or page.platform == ft.PagePlatform.LINUX or page.platform == ft.PagePlatform.MACOS


def load_completion_dates(habit_service, habit_id: int) -> Set[date]:
    """
    Carga las fechas de cumplimiento de un hábito desde la base de datos.
    
    Args:
        habit_service: Servicio de hábitos
        habit_id: ID del hábito
    
    Returns:
        Conjunto de fechas de cumplimiento
    """
    completions = habit_service.repository.get_completions(habit_id)
    return {c.completion_date.date() for c in completions}

