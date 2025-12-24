"""
Funciones auxiliares comunes para widgets.
"""
import flet as ft


def get_theme_colors(page: ft.Page = None):
    """
    Obtiene los colores del tema actual.
    
    Args:
        page: Página de Flet para detectar el tema.
    
    Returns:
        Tupla con (is_dark, primary, secondary, scheme)
    """
    is_dark = page.theme_mode == ft.ThemeMode.DARK if page else False
    scheme = page.theme.color_scheme if page and page.theme else None
    primary = scheme.primary if scheme and scheme.primary else ft.Colors.RED_600
    secondary = scheme.secondary if scheme and scheme.secondary else ft.Colors.RED_400
    
    return is_dark, primary, secondary, scheme


def is_desktop_platform(page: ft.Page = None) -> bool:
    """
    Verifica si la plataforma actual es de escritorio.
    
    Args:
        page: Página de Flet.
    
    Returns:
        True si es escritorio, False en caso contrario.
    """
    if not page:
        return False
    return page.platform in [
        ft.PagePlatform.WINDOWS,
        ft.PagePlatform.LINUX,
        ft.PagePlatform.MACOS
    ]


def get_responsive_sizes(is_desktop: bool):
    """
    Obtiene los tamaños responsive según la plataforma.
    
    Args:
        is_desktop: Si es escritorio.
    
    Returns:
        Diccionario con los tamaños.
    """
    return {
        'title_size': 18 if is_desktop else 16,
        'description_size': 14 if is_desktop else 12,
        'icon_size': 24 if is_desktop else 20,
        'button_icon_size': 22 if is_desktop else 20,
        'card_padding': 20 if is_desktop else 16,
        'card_margin': ft.margin.only(bottom=16 if is_desktop else 12),
        'card_border_radius': 10 if is_desktop else 8,
        'card_elevation': 3 if is_desktop else 2
    }


def get_priority_colors():
    """
    Obtiene los colores y etiquetas de prioridad de la Matriz de Eisenhower.
    
    Returns:
        Tupla con (priority_colors, priority_labels)
    """
    priority_colors = {
        'urgent_important': ft.Colors.RED_600,
        'not_urgent_important': ft.Colors.GREEN_600,
        'urgent_not_important': ft.Colors.ORANGE_600,
        'not_urgent_not_important': ft.Colors.GREY_500
    }
    
    priority_labels = {
        'urgent_important': 'Urgente e Importante',
        'not_urgent_important': 'No Urgente e Importante',
        'urgent_not_important': 'Urgente y No Importante',
        'not_urgent_not_important': 'No Urgente y No Importante'
    }
    
    return priority_colors, priority_labels


def get_card_bgcolor(is_dark: bool):
    """
    Obtiene el color de fondo de la tarjeta según el tema.
    
    Args:
        is_dark: Si el tema es oscuro.
    
    Returns:
        Color de fondo.
    """
    return ft.Colors.BLACK87 if is_dark else None

