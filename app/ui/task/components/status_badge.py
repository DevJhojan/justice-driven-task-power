"""
Componente Status Badge
Muestra el estado de una tarea de forma visual con icono y color
"""

import flet as ft
from typing import Optional
from app.utils.task_helper import (
    format_task_status,
    get_task_status_ft_color,
    get_task_status_icon,
)
from app.utils.helpers.responsives import (
    get_responsive_size,
    get_responsive_icon_size,
)


def create_status_badge(
    status: str,
    page: Optional[ft.Page] = None,
    show_icon: bool = True,
    show_text: bool = True,
    size: Optional[str] = None,
) -> ft.Container:
    """
    Crea un badge visual para mostrar el estado de una tarea
    
    Args:
        status: Estado de la tarea (pendiente, en_progreso, completada, cancelada)
        page: Objeto Page de Flet para cálculos responsive (opcional)
        show_icon: Si se muestra el icono (default: True)
        show_text: Si se muestra el texto (default: True)
        size: Tamaño del badge ('small', 'medium', 'large') (opcional, usa responsive si no se especifica)
    
    Returns:
        Container con el badge de estado estilizado
        
    Ejemplo:
        >>> badge = create_status_badge("pendiente", page=page)
        >>> task_card.controls.append(badge)
    """
    # Obtener propiedades del estado
    status_text = format_task_status(status)
    status_color = get_task_status_ft_color(status)
    status_icon = get_task_status_icon(status)
    
    # Calcular tamaños responsive
    if size == "small":
        icon_size = 14
        text_size = 10
        padding_horizontal = 6
        padding_vertical = 3
        border_radius = 4
    elif size == "large":
        icon_size = 20
        text_size = 14
        padding_horizontal = 12
        padding_vertical = 6
        border_radius = 8
    else:  # medium o responsive
        icon_size = get_responsive_icon_size(page=page, mobile=14, tablet=16, desktop=18)
        text_size = get_responsive_size(page=page, mobile=10, tablet=12, desktop=14)
        padding_horizontal = get_responsive_size(page=page, mobile=8, tablet=10, desktop=12)
        padding_vertical = get_responsive_size(page=page, mobile=4, tablet=5, desktop=6)
        border_radius = get_responsive_size(page=page, mobile=6, tablet=8, desktop=10)
    
    # Crear controles del badge
    badge_controls = []
    
    # Agregar icono si está habilitado
    if show_icon:
        icon = ft.Icon(
            status_icon,
            size=icon_size,
            color=status_color,
        )
        badge_controls.append(icon)
    
    # Agregar texto si está habilitado
    if show_text:
        text = ft.Text(
            status_text,
            size=text_size,
            color=status_color,
            weight=ft.FontWeight.W_500,
        )
        badge_controls.append(text)
    
    # Si no hay controles, retornar un badge vacío
    if not badge_controls:
        return ft.Container()
    
    # Crear el contenido del badge
    badge_content = ft.Row(
        controls=badge_controls,
        spacing=4,
        tight=True,
        alignment=ft.MainAxisAlignment.CENTER,
    )
    
    # Crear el badge con estilo
    badge = ft.Container(
        content=badge_content,
        padding=ft.padding.symmetric(
            horizontal=padding_horizontal,
            vertical=padding_vertical,
        ),
        border_radius=border_radius,
        bgcolor=f"{status_color}20",  # Color con 20% de opacidad
        border=ft.border.all(1, status_color),
    )
    
    return badge


class StatusBadge:
    """
    Clase para crear badges de estado de tareas
    Permite más control y personalización que la función create_status_badge
    """
    
    def __init__(
        self,
        status: str,
        page: Optional[ft.Page] = None,
        show_icon: bool = True,
        show_text: bool = True,
        size: Optional[str] = None,
    ):
        """
        Inicializa el badge de estado
        
        Args:
            status: Estado de la tarea
            page: Objeto Page de Flet para cálculos responsive
            show_icon: Si se muestra el icono
            show_text: Si se muestra el texto
            size: Tamaño del badge ('small', 'medium', 'large')
        """
        self.status = status
        self.page = page
        self.show_icon = show_icon
        self.show_text = show_text
        self.size = size
        self._badge: Optional[ft.Container] = None
    
    def build(self) -> ft.Container:
        """
        Construye y retorna el badge
        
        Returns:
            Container con el badge de estado
        """
        if self._badge is None:
            self._badge = create_status_badge(
                status=self.status,
                page=self.page,
                show_icon=self.show_icon,
                show_text=self.show_text,
                size=self.size,
            )
        return self._badge
    
    def update_status(self, new_status: str):
        """
        Actualiza el estado del badge
        
        Args:
            new_status: Nuevo estado de la tarea
        """
        self.status = new_status
        self._badge = None  # Forzar reconstrucción
    
    def refresh(self):
        """Fuerza la reconstrucción del badge"""
        self._badge = None

