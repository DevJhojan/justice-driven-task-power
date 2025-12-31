"""
Funciones auxiliares para diseño responsive
Calcula valores adaptativos basados en el tamaño de la ventana
"""

from typing import Optional, Union
import flet as ft


# Breakpoints comunes
MOBILE_BREAKPOINT = 600
TABLET_BREAKPOINT = 900
DESKTOP_BREAKPOINT = 1200


def get_responsive_padding(window_width: Optional[int] = None, page: Optional[ft.Page] = None) -> int:
    """
    Obtiene padding responsive según el ancho de la ventana
    
    Args:
        window_width: Ancho de la ventana (opcional)
        page: Objeto Page de Flet (opcional, se usa si window_width no se proporciona)
        
    Returns:
        Padding en píxeles (10px móvil, 20px desktop)
        
    Ejemplo:
        >>> padding = get_responsive_padding(page=page)
        >>> container.padding = padding
    """
    width = _get_window_width(window_width, page)
    
    if width < MOBILE_BREAKPOINT:
        return 10  # Móvil
    else:
        return 20  # Desktop


def get_responsive_size(
    window_width: Optional[int] = None,
    page: Optional[ft.Page] = None,
    mobile: int = 14,
    tablet: int = 16,
    desktop: int = 18
) -> int:
    """
    Obtiene tamaño de fuente responsive según el ancho de la ventana
    
    Args:
        window_width: Ancho de la ventana (opcional)
        page: Objeto Page de Flet (opcional)
        mobile: Tamaño para móvil (default: 14)
        tablet: Tamaño para tablet (default: 16)
        desktop: Tamaño para desktop (default: 18)
        
    Returns:
        Tamaño de fuente en píxeles
        
    Ejemplo:
        >>> font_size = get_responsive_size(page=page, mobile=12, desktop=16)
        >>> text.size = font_size
    """
    width = _get_window_width(window_width, page)
    
    if width < MOBILE_BREAKPOINT:
        return mobile
    elif width < TABLET_BREAKPOINT:
        return tablet
    else:
        return desktop


def get_responsive_icon_size(
    window_width: Optional[int] = None,
    page: Optional[ft.Page] = None,
    mobile: int = 24,
    tablet: int = 32,
    desktop: int = 40
) -> int:
    """
    Obtiene tamaño de icono responsive
    
    Args:
        window_width: Ancho de la ventana (opcional)
        page: Objeto Page de Flet (opcional)
        mobile: Tamaño para móvil (default: 24)
        tablet: Tamaño para tablet (default: 32)
        desktop: Tamaño para desktop (default: 40)
        
    Returns:
        Tamaño de icono en píxeles
    """
    width = _get_window_width(window_width, page)
    
    if width < MOBILE_BREAKPOINT:
        return mobile
    elif width < TABLET_BREAKPOINT:
        return tablet
    else:
        return desktop


def get_responsive_width(
    window_width: Optional[int] = None,
    page: Optional[ft.Page] = None,
    max_width: Optional[int] = None,
    padding: Optional[int] = None
) -> int:
    """
    Obtiene ancho responsive con padding incluido
    
    Args:
        window_width: Ancho de la ventana (opcional)
        page: Objeto Page de Flet (opcional)
        max_width: Ancho máximo permitido (opcional)
        padding: Padding a restar (opcional, usa responsive si no se proporciona)
        
    Returns:
        Ancho en píxeles
        
    Ejemplo:
        >>> width = get_responsive_width(page=page, max_width=800)
        >>> container.width = width
    """
    width = _get_window_width(window_width, page)
    
    if padding is None:
        padding = get_responsive_padding(window_width=width, page=page)
    
    calculated_width = width - (padding * 2)
    
    if max_width is not None and calculated_width > max_width:
        return max_width
    
    return max(calculated_width, 200)  # Mínimo 200px


def get_responsive_columns(
    window_width: Optional[int] = None,
    page: Optional[ft.Page] = None
) -> int:
    """
    Obtiene número de columnas responsive para grid
    
    Args:
        window_width: Ancho de la ventana (opcional)
        page: Objeto Page de Flet (opcional)
        
    Returns:
        Número de columnas (1 móvil, 2 tablet, 3 desktop)
        
    Ejemplo:
        >>> columns = get_responsive_columns(page=page)
        >>> grid.columns = columns
    """
    width = _get_window_width(window_width, page)
    
    if width < MOBILE_BREAKPOINT:
        return 1  # Móvil: 1 columna
    elif width < TABLET_BREAKPOINT:
        return 2  # Tablet: 2 columnas
    else:
        return 3  # Desktop: 3 columnas


def get_responsive_spacing(
    window_width: Optional[int] = None,
    page: Optional[ft.Page] = None,
    mobile: int = 8,
    tablet: int = 12,
    desktop: int = 16
) -> int:
    """
    Obtiene espaciado responsive
    
    Args:
        window_width: Ancho de la ventana (opcional)
        page: Objeto Page de Flet (opcional)
        mobile: Espaciado para móvil (default: 8)
        tablet: Espaciado para tablet (default: 12)
        desktop: Espaciado para desktop (default: 16)
        
    Returns:
        Espaciado en píxeles
    """
    width = _get_window_width(window_width, page)
    
    if width < MOBILE_BREAKPOINT:
        return mobile
    elif width < TABLET_BREAKPOINT:
        return tablet
    else:
        return desktop


def is_mobile(window_width: Optional[int] = None, page: Optional[ft.Page] = None) -> bool:
    """
    Verifica si el dispositivo es móvil
    
    Args:
        window_width: Ancho de la ventana (opcional)
        page: Objeto Page de Flet (opcional)
        
    Returns:
        True si es móvil, False en caso contrario
    """
    width = _get_window_width(window_width, page)
    return width < MOBILE_BREAKPOINT


def is_tablet(window_width: Optional[int] = None, page: Optional[ft.Page] = None) -> bool:
    """
    Verifica si el dispositivo es tablet
    
    Args:
        window_width: Ancho de la ventana (opcional)
        page: Objeto Page de Flet (opcional)
        
    Returns:
        True si es tablet, False en caso contrario
    """
    width = _get_window_width(window_width, page)
    return MOBILE_BREAKPOINT <= width < TABLET_BREAKPOINT


def is_desktop(window_width: Optional[int] = None, page: Optional[ft.Page] = None) -> bool:
    """
    Verifica si el dispositivo es desktop
    
    Args:
        window_width: Ancho de la ventana (opcional)
        page: Objeto Page de Flet (opcional)
        
    Returns:
        True si es desktop, False en caso contrario
    """
    width = _get_window_width(window_width, page)
    return width >= TABLET_BREAKPOINT


def get_device_type(window_width: Optional[int] = None, page: Optional[ft.Page] = None) -> str:
    """
    Obtiene el tipo de dispositivo
    
    Args:
        window_width: Ancho de la ventana (opcional)
        page: Objeto Page de Flet (opcional)
        
    Returns:
        "mobile", "tablet" o "desktop"
        
    Ejemplo:
        >>> device = get_device_type(page=page)
        >>> if device == "mobile":
        ...     # Configuración móvil
    """
    width = _get_window_width(window_width, page)
    
    if width < MOBILE_BREAKPOINT:
        return "mobile"
    elif width < TABLET_BREAKPOINT:
        return "tablet"
    else:
        return "desktop"


def get_responsive_card_width(
    window_width: Optional[int] = None,
    page: Optional[ft.Page] = None,
    columns: Optional[int] = None
) -> Union[int, float]:
    """
    Obtiene ancho responsive para tarjetas en grid
    
    Args:
        window_width: Ancho de la ventana (opcional)
        page: Objeto Page de Flet (opcional)
        columns: Número de columnas (opcional, se calcula si no se proporciona)
        
    Returns:
        Ancho de tarjeta (puede ser expand para flex)
        
    Ejemplo:
        >>> card_width = get_responsive_card_width(page=page)
        >>> card.width = card_width
    """
    if columns is None:
        columns = get_responsive_columns(window_width, page)
    
    # Si es una sola columna, usar expand
    if columns == 1:
        return -1  # -1 indica expand en Flet
    
    # Para múltiples columnas, calcular ancho
    width = _get_window_width(window_width, page)
    padding = get_responsive_padding(window_width=width, page=page)
    spacing = get_responsive_spacing(window_width=width, page=page)
    
    available_width = width - (padding * 2)
    card_width = (available_width - (spacing * (columns - 1))) / columns
    
    return max(card_width, 150)  # Mínimo 150px


def get_responsive_border_radius(
    window_width: Optional[int] = None,
    page: Optional[ft.Page] = None,
    mobile: int = 8,
    tablet: int = 10,
    desktop: int = 12
) -> int:
    """
    Obtiene radio de borde responsive
    
    Args:
        window_width: Ancho de la ventana (opcional)
        page: Objeto Page de Flet (opcional)
        mobile: Radio para móvil (default: 8)
        tablet: Radio para tablet (default: 10)
        desktop: Radio para desktop (default: 12)
        
    Returns:
        Radio de borde en píxeles
    """
    width = _get_window_width(window_width, page)
    
    if width < MOBILE_BREAKPOINT:
        return mobile
    elif width < TABLET_BREAKPOINT:
        return tablet
    else:
        return desktop


def get_responsive_elevation(
    window_width: Optional[int] = None,
    page: Optional[ft.Page] = None,
    mobile: int = 1,
    tablet: int = 2,
    desktop: int = 3
) -> int:
    """
    Obtiene elevación (sombra) responsive para tarjetas
    
    Args:
        window_width: Ancho de la ventana (opcional)
        page: Objeto Page de Flet (opcional)
        mobile: Elevación para móvil (default: 1)
        tablet: Elevación para tablet (default: 2)
        desktop: Elevación para desktop (default: 3)
        
    Returns:
        Nivel de elevación
    """
    width = _get_window_width(window_width, page)
    
    if width < MOBILE_BREAKPOINT:
        return mobile
    elif width < TABLET_BREAKPOINT:
        return tablet
    else:
        return desktop


def _get_window_width(window_width: Optional[int] = None, page: Optional[ft.Page] = None) -> int:
    """
    Función auxiliar para obtener el ancho de la ventana
    
    Args:
        window_width: Ancho proporcionado directamente
        page: Objeto Page de Flet
        
    Returns:
        Ancho de la ventana en píxeles (default: 800 si no se puede obtener)
    """
    if window_width is not None and window_width > 0:
        return window_width
    
    if page is not None and hasattr(page, 'window') and page.window.width > 0:
        return page.window.width
    
    # Valor por defecto
    return 800


def get_responsive_max_width(
    window_width: Optional[int] = None,
    page: Optional[ft.Page] = None,
    mobile: Optional[int] = None,
    tablet: Optional[int] = None,
    desktop: Optional[int] = None
) -> Optional[int]:
    """
    Obtiene ancho máximo responsive para contenedores
    
    Args:
        window_width: Ancho de la ventana (opcional)
        page: Objeto Page de Flet (opcional)
        mobile: Ancho máximo móvil (opcional)
        tablet: Ancho máximo tablet (opcional)
        desktop: Ancho máximo desktop (opcional)
        
    Returns:
        Ancho máximo en píxeles o None
    """
    width = _get_window_width(window_width, page)
    
    if width < MOBILE_BREAKPOINT:
        return mobile
    elif width < TABLET_BREAKPOINT:
        return tablet
    else:
        return desktop

