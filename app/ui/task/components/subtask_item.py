"""
Componente Subtask Item
Muestra una subtarea individual con checkbox, título y opciones de prioridad
"""

import flet as ft
from typing import Optional, Callable
from app.models.subtask import Subtask
from app.ui.task.components.priority_badge import create_priority_badge
from app.utils.helpers.responsives import (
    get_responsive_size,
    get_responsive_padding,
)


def create_subtask_item(
    subtask: Subtask,
    page: Optional[ft.Page] = None,
    on_toggle_completed: Optional[Callable[[str], None]] = None,
    on_edit: Optional[Callable[[str], None]] = None,
    on_delete: Optional[Callable[[str], None]] = None,
    show_priority: bool = True,
    show_actions: bool = True,
    compact: bool = False,
) -> ft.Container:
    """
    Crea un componente visual para mostrar una subtarea individual
    
    Args:
        subtask: Instancia de Subtask a mostrar
        page: Objeto Page de Flet para cálculos responsive (opcional)
        on_toggle_completed: Callback cuando se marca/desmarca como completada (recibe subtask_id)
        on_edit: Callback cuando se edita la subtarea (recibe subtask_id)
        on_delete: Callback cuando se elimina la subtarea (recibe subtask_id)
        show_priority: Si se muestra el badge de prioridad (default: True)
        show_actions: Si se muestran los botones de acción (editar/eliminar) (default: True)
        compact: Si se usa un diseño compacto (default: False)
    
    Returns:
        Container con el componente de subtarea estilizado
        
    Ejemplo:
        >>> subtask = Subtask(id="sub_1", task_id="task_1", title="Hacer algo")
        >>> item = create_subtask_item(subtask, page=page, on_toggle_completed=handle_toggle)
        >>> subtasks_list.controls.append(item)
    """
    # Calcular tamaños responsive
    if compact:
        padding_value = get_responsive_padding(page=page) // 2
        text_size = get_responsive_size(page=page, mobile=12, tablet=13, desktop=14)
        icon_size = 16
    else:
        padding_value = get_responsive_padding(page=page)
        text_size = get_responsive_size(page=page, mobile=14, tablet=15, desktop=16)
        icon_size = 20
    
    # Checkbox para marcar como completada
    checkbox = ft.Checkbox(
        value=subtask.completed,
        on_change=lambda e: on_toggle_completed(subtask.id) if on_toggle_completed else None,
        scale=0.9 if compact else 1.0,
    )
    
    # Título de la subtarea
    # En Flet, el tachado se puede simular con un Container y un border o simplemente con estilo
    title_text = ft.Text(
        subtask.title,
        size=text_size,
        color=ft.Colors.WHITE if not subtask.completed else ft.Colors.WHITE_54,
        weight=ft.FontWeight.W_500 if not subtask.completed else ft.FontWeight.W_400,
        expand=True,
    )
    
    # Contenedor principal con título
    title_container = ft.Container(
        content=title_text,
        expand=True,
        padding=ft.Padding.symmetric(horizontal=8, vertical=0),
    )
    
    # Controles del item
    item_controls = [checkbox, title_container]
    
    # Agregar badge de prioridad si está habilitado y la subtarea tiene prioridad
    if show_priority and (subtask.urgent or subtask.important):
        priority_badge = create_priority_badge(
            urgent=subtask.urgent,
            important=subtask.important,
            page=page,
            size="small",
            show_quadrant=False,
        )
        item_controls.append(priority_badge)
    
    # Agregar botones de acción si están habilitados
    if show_actions:
        action_buttons = []
        
        if on_edit:
            edit_button = ft.IconButton(
                icon=ft.Icons.EDIT,
                icon_size=icon_size,
                icon_color=ft.Colors.BLUE_400,
                tooltip="Editar subtarea",
                on_click=lambda e: on_edit(subtask.id) if on_edit else None,
            )
            action_buttons.append(edit_button)
        
        if on_delete:
            delete_button = ft.IconButton(
                icon=ft.Icons.DELETE_OUTLINE,
                icon_size=icon_size,
                icon_color=ft.Colors.RED_400,
                tooltip="Eliminar subtarea",
                on_click=lambda e: on_delete(subtask.id) if on_delete else None,
            )
            action_buttons.append(delete_button)
        
        if action_buttons:
            item_controls.extend(action_buttons)
    
    # Row principal con todos los controles
    item_row = ft.Row(
        controls=item_controls,
        spacing=8,
        alignment=ft.MainAxisAlignment.START,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )
    
    # Container principal del item
    item_container = ft.Container(
        content=item_row,
        padding=ft.Padding.symmetric(
            horizontal=padding_value,
            vertical=padding_value // 2,
        ),
        border_radius=get_responsive_size(page=page, mobile=6, tablet=8, desktop=10),
        bgcolor=ft.Colors.GREY_900 if not subtask.completed else None,
        border=ft.Border.all(
            1,
            ft.Colors.GREY_700 if not subtask.completed else ft.Colors.GREY_800
        ) if not compact else None,
    )
    
    return item_container


class SubtaskItem:
    """
    Clase para crear items de subtarea
    Permite más control y personalización que la función create_subtask_item
    """
    
    def __init__(
        self,
        subtask: Subtask,
        page: Optional[ft.Page] = None,
        on_toggle_completed: Optional[Callable[[str], None]] = None,
        on_edit: Optional[Callable[[str], None]] = None,
        on_delete: Optional[Callable[[str], None]] = None,
        show_priority: bool = True,
        show_actions: bool = True,
        compact: bool = False,
    ):
        """
        Inicializa el item de subtarea
        
        Args:
            subtask: Instancia de Subtask a mostrar
            page: Objeto Page de Flet para cálculos responsive
            on_toggle_completed: Callback cuando se marca/desmarca como completada
            on_edit: Callback cuando se edita la subtarea
            on_delete: Callback cuando se elimina la subtarea
            show_priority: Si se muestra el badge de prioridad
            show_actions: Si se muestran los botones de acción
            compact: Si se usa un diseño compacto
        """
        self.subtask = subtask
        self.page = page
        self.on_toggle_completed = on_toggle_completed
        self.on_edit = on_edit
        self.on_delete = on_delete
        self.show_priority = show_priority
        self.show_actions = show_actions
        self.compact = compact
        self._item: Optional[ft.Container] = None
    
    def build(self) -> ft.Container:
        """
        Construye y retorna el item de subtarea
        
        Returns:
            Container con el item de subtarea
        """
        if self._item is None:
            self._item = create_subtask_item(
                subtask=self.subtask,
                page=self.page,
                on_toggle_completed=self.on_toggle_completed,
                on_edit=self.on_edit,
                on_delete=self.on_delete,
                show_priority=self.show_priority,
                show_actions=self.show_actions,
                compact=self.compact,
            )
        return self._item
    
    def update_subtask(self, new_subtask: Subtask):
        """
        Actualiza la subtarea del item
        
        Args:
            new_subtask: Nueva instancia de Subtask
        """
        self.subtask = new_subtask
        self._item = None  # Forzar reconstrucción
    
    def refresh(self):
        """Fuerza la reconstrucción del item"""
        self._item = None

