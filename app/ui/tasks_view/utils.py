"""
Utilidades y funciones auxiliares para TasksView.
"""
import flet as ft


def get_priority_colors(priority: str, is_dark: bool) -> dict:
    """
    Obtiene los colores para una prioridad específica.
    
    Args:
        priority: Prioridad de la tarea.
        is_dark: Si el tema es oscuro.
    
    Returns:
        Diccionario con los colores de la prioridad.
    """
    colors = {
        'urgent_important': {
            'primary': ft.Colors.RED_600,
            'light': ft.Colors.RED_50 if not is_dark else ft.Colors.RED_900,
            'bg': ft.Colors.RED_100 if not is_dark else ft.Colors.RED_900,
            'text': '🔴 Urgente e Importante'
        },
        'not_urgent_important': {
            'primary': ft.Colors.GREEN_600,
            'light': ft.Colors.GREEN_50 if not is_dark else ft.Colors.GREEN_900,
            'bg': ft.Colors.GREEN_100 if not is_dark else ft.Colors.GREEN_900,
            'text': '🟢 No Urgente e Importante'
        },
        'urgent_not_important': {
            'primary': ft.Colors.ORANGE_600,
            'light': ft.Colors.ORANGE_50 if not is_dark else ft.Colors.ORANGE_900,
            'bg': ft.Colors.ORANGE_100 if not is_dark else ft.Colors.ORANGE_900,
            'text': '🟡 Urgente y No Importante'
        },
        'not_urgent_not_important': {
            'primary': ft.Colors.GREY_500,
            'light': ft.Colors.GREY_50 if not is_dark else ft.Colors.GREY_800,
            'bg': ft.Colors.GREY_100 if not is_dark else ft.Colors.GREY_800,
            'text': '⚪ No Urgente y No Importante'
        }
    }
    return colors.get(priority, colors['not_urgent_important'])


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


# Constantes de prioridades
PRIORITIES = [
    'urgent_important',
    'not_urgent_important',
    'urgent_not_important',
    'not_urgent_not_important'
]

PRIORITY_ORDER = {
    'urgent_important': 0,
    'not_urgent_important': 1,
    'urgent_not_important': 2,
    'not_urgent_not_important': 3
}

PRIORITY_DISPLAY = [
    ('urgent_important', '🔴', 'Urgente e\nImportante'),
    ('not_urgent_important', '🟢', 'No Urgente e\nImportante'),
    ('urgent_not_important', '🟡', 'Urgente y No\nImportante'),
    ('not_urgent_not_important', '⚪', 'No Urgente y No\nImportante')
]

