"""
Componente Priority Badge
Muestra la prioridad de una tarea según la Matriz de Eisenhower de forma visual con icono y color
"""

import flet as ft
from typing import Optional
from app.utils.eisenhower_matrix import (
    get_eisenhower_quadrant,
    get_quadrant_name,
    get_quadrant_ft_color,
    get_quadrant_icon,
    get_priority_label,
    get_priority_badge_text,
    Quadrant,
)
from app.utils.helpers.responsives import (
    get_responsive_size,
    get_responsive_icon_size,
)


def create_priority_badge(
    urgent: bool,
    important: bool,
    page: Optional[ft.Page] = None,
    show_icon: bool = True,
    show_text: bool = True,
    size: Optional[str] = None,
    show_quadrant: bool = False,
) -> ft.Container:
    """
    Crea un badge visual para mostrar la prioridad de una tarea según la Matriz de Eisenhower
    
    Args:
        urgent: Si la tarea es urgente
        important: Si la tarea es importante
        page: Objeto Page de Flet para cálculos responsive (opcional)
        show_icon: Si se muestra el icono (default: True)
        show_text: Si se muestra el texto (default: True)
        size: Tamaño del badge ('small', 'medium', 'large') (opcional, usa responsive si no se especifica)
        show_quadrant: Si se muestra el cuadrante (Q1, Q2, Q3, Q4) en lugar del nombre (default: False)
    
    Returns:
        Container con el badge de prioridad estilizado
        
    Ejemplo:
        >>> badge = create_priority_badge(urgent=True, important=True, page=page)
        >>> task_card.controls.append(badge)
    """
    # Calcular el cuadrante de Eisenhower
    quadrant = get_eisenhower_quadrant(urgent, important)
    
    # Obtener propiedades del cuadrante
    if show_quadrant:
        priority_text = get_priority_badge_text(urgent, important)  # "Q1", "Q2", etc.
    else:
        priority_text = get_priority_label(urgent, important)  # "Urgente e Importante", etc.
    
    priority_color = get_quadrant_ft_color(quadrant)
    priority_icon = get_quadrant_icon(quadrant)
    
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
            priority_icon,
            size=icon_size,
            color=priority_color,
        )
        badge_controls.append(icon)
    
    # Agregar texto si está habilitado
    if show_text:
        text = ft.Text(
            priority_text,
            size=text_size,
            color=priority_color,
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
        padding=ft.Padding.symmetric(
            horizontal=padding_horizontal,
            vertical=padding_vertical,
        ),
        border_radius=border_radius,
        bgcolor=f"{priority_color}20",  # Color con 20% de opacidad
        border=ft.Border.all(1, priority_color),
    )
    
    return badge


def create_priority_badge_from_quadrant(
    quadrant: Quadrant,
    page: Optional[ft.Page] = None,
    show_icon: bool = True,
    show_text: bool = True,
    size: Optional[str] = None,
    show_quadrant: bool = False,
) -> ft.Container:
    """
    Crea un badge visual para mostrar la prioridad desde un cuadrante de Eisenhower
    
    Args:
        quadrant: Cuadrante de Eisenhower (Q1, Q2, Q3, Q4)
        page: Objeto Page de Flet para cálculos responsive (opcional)
        show_icon: Si se muestra el icono (default: True)
        show_text: Si se muestra el texto (default: True)
        size: Tamaño del badge ('small', 'medium', 'large') (opcional, usa responsive si no se especifica)
        show_quadrant: Si se muestra el cuadrante (Q1, Q2, Q3, Q4) en lugar del nombre (default: False)
    
    Returns:
        Container con el badge de prioridad estilizado
        
    Ejemplo:
        >>> badge = create_priority_badge_from_quadrant("Q1", page=page)
        >>> task_card.controls.append(badge)
    """
    # Obtener propiedades del cuadrante
    if show_quadrant:
        priority_text = quadrant  # "Q1", "Q2", etc.
    else:
        priority_text = get_quadrant_name(quadrant)  # "Hacer primero", "Programar", etc.
    
    priority_color = get_quadrant_ft_color(quadrant)
    priority_icon = get_quadrant_icon(quadrant)
    
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
            priority_icon,
            size=icon_size,
            color=priority_color,
        )
        badge_controls.append(icon)
    
    # Agregar texto si está habilitado
    if show_text:
        text = ft.Text(
            priority_text,
            size=text_size,
            color=priority_color,
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
        padding=ft.Padding.symmetric(
            horizontal=padding_horizontal,
            vertical=padding_vertical,
        ),
        border_radius=border_radius,
        bgcolor=f"{priority_color}20",  # Color con 20% de opacidad
        border=ft.Border.all(1, priority_color),
    )
    
    return badge


class PriorityBadge:
    """
    Clase para crear badges de prioridad de tareas según la Matriz de Eisenhower
    Permite más control y personalización que las funciones create_priority_badge
    """
    
    def __init__(
        self,
        urgent: Optional[bool] = None,
        important: Optional[bool] = None,
        quadrant: Optional[Quadrant] = None,
        page: Optional[ft.Page] = None,
        show_icon: bool = True,
        show_text: bool = True,
        size: Optional[str] = None,
        show_quadrant: bool = False,
    ):
        """
        Inicializa el badge de prioridad
        
        Args:
            urgent: Si la tarea es urgente (opcional si se proporciona quadrant)
            important: Si la tarea es importante (opcional si se proporciona quadrant)
            quadrant: Cuadrante de Eisenhower directamente (opcional si se proporcionan urgent/important)
            page: Objeto Page de Flet para cálculos responsive
            show_icon: Si se muestra el icono
            show_text: Si se muestra el texto
            size: Tamaño del badge ('small', 'medium', 'large')
            show_quadrant: Si se muestra el cuadrante (Q1, Q2, etc.) en lugar del nombre
        """
        if quadrant is not None:
            self.quadrant = quadrant
            self.urgent = None
            self.important = None
        elif urgent is not None and important is not None:
            self.urgent = urgent
            self.important = important
            self.quadrant = get_eisenhower_quadrant(urgent, important)
        else:
            raise ValueError("Debe proporcionar 'quadrant' o ambos 'urgent' e 'important'")
        
        self.page = page
        self.show_icon = show_icon
        self.show_text = show_text
        self.size = size
        self.show_quadrant = show_quadrant
        self._badge: Optional[ft.Container] = None
    
    def build(self) -> ft.Container:
        """
        Construye y retorna el badge
        
        Returns:
            Container con el badge de prioridad
        """
        if self._badge is None:
            if self.quadrant is not None and (self.urgent is None or self.important is None):
                # Usar cuadrante directamente
                self._badge = create_priority_badge_from_quadrant(
                    quadrant=self.quadrant,
                    page=self.page,
                    show_icon=self.show_icon,
                    show_text=self.show_text,
                    size=self.size,
                    show_quadrant=self.show_quadrant,
                )
            else:
                # Usar urgent e important
                self._badge = create_priority_badge(
                    urgent=self.urgent,
                    important=self.important,
                    page=self.page,
                    show_icon=self.show_icon,
                    show_text=self.show_text,
                    size=self.size,
                    show_quadrant=self.show_quadrant,
                )
        return self._badge
    
    def update_priority(self, urgent: Optional[bool] = None, important: Optional[bool] = None, quadrant: Optional[Quadrant] = None):
        """
        Actualiza la prioridad del badge
        
        Args:
            urgent: Si la tarea es urgente (opcional)
            important: Si la tarea es importante (opcional)
            quadrant: Cuadrante de Eisenhower directamente (opcional)
        """
        if quadrant is not None:
            self.quadrant = quadrant
            self.urgent = None
            self.important = None
        elif urgent is not None and important is not None:
            self.urgent = urgent
            self.important = important
            self.quadrant = get_eisenhower_quadrant(urgent, important)
        else:
            raise ValueError("Debe proporcionar 'quadrant' o ambos 'urgent' e 'important'")
        
        self._badge = None  # Forzar reconstrucción
    
    def refresh(self):
        """Fuerza la reconstrucción del badge"""
        self._badge = None

