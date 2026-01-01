"""
Componente Task Card - Orquestador Final
Orquesta todos los componentes modulares (header, description, info_section, tags, subtasks, actions)
para construir una tarjeta de tarea completa.
"""

import flet as ft
from typing import Optional, Callable
from app.models.task import Task
from app.ui.task.components.cards.header import Header
from app.ui.task.components.cards.description import Description
from app.ui.task.components.cards.info_section import InfoSection
from app.ui.task.components.cards.tags import Tags
from app.ui.task.components.cards.subtasks import SubtasksSection
from app.ui.task.components.cards.actions import Actions
from app.utils.helpers.responsives import (
    get_responsive_padding,
    get_responsive_spacing,
    get_responsive_border_radius,
)


def create_task_card(
    task: Task,
    page: Optional[ft.Page] = None,
    on_click: Optional[Callable[[str], None]] = None,
    on_edit: Optional[Callable[[str], None]] = None,
    on_delete: Optional[Callable[[str], None]] = None,
    on_toggle_status: Optional[Callable[[str], None]] = None,
    on_subtask_toggle: Optional[Callable[[str, str], None]] = None,
    on_subtask_edit: Optional[Callable[[str, str], None]] = None,
    on_subtask_delete: Optional[Callable[[str, str], None]] = None,
    show_subtasks: bool = True,
    show_tags: bool = True,
    show_progress: bool = True,
    compact: bool = False,
    subtasks_expanded: bool = True,
) -> ft.Container:
    """
    Crea un componente visual para mostrar una tarea completa usando componentes modulares.
    
    Args:
        task: Instancia de Task a mostrar
        page: Objeto Page de Flet para cálculos responsive (opcional)
        on_click: Callback cuando se hace clic en la tarjeta (recibe task_id)
        on_edit: Callback cuando se edita la tarea (recibe task_id)
        on_delete: Callback cuando se elimina la tarea (recibe task_id)
        on_toggle_status: Callback cuando se cambia el estado (recibe task_id)
        on_subtask_toggle: Callback cuando se marca/desmarca subtarea (recibe task_id, subtask_id)
        on_subtask_edit: Callback cuando se edita subtarea (recibe task_id, subtask_id)
        on_subtask_delete: Callback cuando se elimina subtarea (recibe task_id, subtask_id)
        show_subtasks: Si se muestran las subtareas (default: True)
        show_tags: Si se muestran las etiquetas (default: True)
        show_progress: Si se muestra la barra de progreso (default: True)
        compact: Si se usa un diseño compacto (default: False)
        subtasks_expanded: Si las subtareas están expandidas por defecto (default: True)
    
    Returns:
        Container con el componente de tarea estilizado
    """
    # Calcular tamaños responsive
    padding_value = get_responsive_padding(page=page)
    if compact:
        padding_value = padding_value // 2
    spacing_value = get_responsive_spacing(page=page, mobile=8, tablet=10, desktop=12)
    
    card_controls: list[ft.Control] = []
    
    # =========================================================================
    # HEADER: Título y badges (estado + prioridad)
    # =========================================================================
    header_comp = Header(task=task, page=page)
    header_row = header_comp.build()
    if header_row:
        card_controls.append(header_row)
    
    # Guardar referencia a badges_row para actualizaciones posteriores
    badges_row = header_comp.badges_row
    
    # =========================================================================
    # DESCRIPTION: Descripción de la tarea
    # =========================================================================
    description_comp = Description(task=task, page=page, compact=compact)
    description_text = description_comp.build()
    if description_text:
        card_controls.append(description_text)
    
    # =========================================================================
    # INFO SECTION: Fecha de vencimiento + barra de progreso
    # =========================================================================
    info_section_comp = InfoSection(
        task=task,
        page=page,
        show_progress=show_progress,
        compact=compact,
    )
    info_row = info_section_comp.build()
    if info_row:
        card_controls.append(info_row)
    
    # Referencias a progress_bar y progress_text para actualizaciones
    progress_bar = info_section_comp.progress_bar
    progress_text = info_section_comp.progress_text
    
    # =========================================================================
    # TAGS: Etiquetas de la tarea
    # =========================================================================
    if show_tags:
        tags_comp = Tags(task=task, page=page, max_tags=5)
        tags_row = tags_comp.build()
        if tags_row:
            card_controls.append(tags_row)
    
    # =========================================================================
    # SUBTASKS: Subtareas con expand/collapse
    # =========================================================================
    if show_subtasks and task.subtasks and len(task.subtasks) > 0:
        subtasks_comp = SubtasksSection(
            task=task,
            page=page,
            on_subtask_toggle=on_subtask_toggle,
            on_subtask_edit=on_subtask_edit,
            on_subtask_delete=on_subtask_delete,
            compact=compact,
            expanded=subtasks_expanded,
            progress_bar=progress_bar,
            progress_text=progress_text,
            badges_row=badges_row,
        )
        
        # Agregar título y lista de subtareas (build retorna tupla)
        subtasks_title, subtasks_list = subtasks_comp.build()
        if subtasks_title:
            card_controls.append(subtasks_title)
        if subtasks_list:
            card_controls.append(subtasks_list)
    
    # =========================================================================
    # ACTIONS: Botones de acción (toggle status, edit, delete)
    # =========================================================================
    if badges_row:
        actions_comp = Actions(
            task=task,
            badges_row=badges_row,
            page=page,
            on_edit=on_edit,
            on_delete=on_delete,
            on_toggle_status=on_toggle_status,
            progress_bar=progress_bar,
            progress_text=progress_text,
            show_progress=show_progress,
        )
        actions_row = actions_comp.build()
        if actions_row:
            card_controls.append(actions_row)
    
    # =========================================================================
    # CONTENEDOR PRINCIPAL
    # =========================================================================
    card_column = ft.Column(
        controls=card_controls,
        spacing=spacing_value,
    )
    
    # Container principal con estilo de tarjeta
    card_container = ft.Container(
        content=card_column,
        padding=ft.Padding.all(padding_value),
        border_radius=get_responsive_border_radius(page=page),
        bgcolor=ft.Colors.GREY_900,
        border=ft.Border.all(1, ft.Colors.GREY_700),
        on_click=lambda e: on_click(task.id) if on_click else None,
        ink=True,
    )
    
    return card_container


class TaskCard:
    """
    Clase orquestadora para crear tarjetas de tareas usando componentes modulares.
    Proporciona control sobre construcción, caching y refresh de todos los componentes.
    """
    
    def __init__(
        self,
        task: Task,
        page: Optional[ft.Page] = None,
        on_click: Optional[Callable[[str], None]] = None,
        on_edit: Optional[Callable[[str], None]] = None,
        on_delete: Optional[Callable[[str], None]] = None,
        on_toggle_status: Optional[Callable[[str], None]] = None,
        on_subtask_toggle: Optional[Callable[[str, str], None]] = None,
        on_subtask_edit: Optional[Callable[[str, str], None]] = None,
        on_subtask_delete: Optional[Callable[[str, str], None]] = None,
        show_subtasks: bool = True,
        show_tags: bool = True,
        show_progress: bool = True,
        compact: bool = False,
        subtasks_expanded: bool = True,
    ):
        """
        Inicializa la tarjeta de tarea orquestadora.
        
        Args:
            task: Instancia de Task a mostrar
            page: Objeto Page de Flet para cálculos responsive
            on_click: Callback cuando se hace clic en la tarjeta
            on_edit: Callback cuando se edita la tarea
            on_delete: Callback cuando se elimina la tarea
            on_toggle_status: Callback cuando se cambia el estado
            on_subtask_toggle: Callback cuando se marca/desmarca subtarea
            on_subtask_edit: Callback cuando se edita subtarea
            on_subtask_delete: Callback cuando se elimina subtarea
            show_subtasks: Si se muestran las subtareas
            show_tags: Si se muestran las etiquetas
            show_progress: Si se muestra la barra de progreso
            compact: Si se usa un diseño compacto
            subtasks_expanded: Si las subtareas están expandidas por defecto
        """
        self.task = task
        self.page = page
        self.on_click = on_click
        self.on_edit = on_edit
        self.on_delete = on_delete
        self.on_toggle_status = on_toggle_status
        self.on_subtask_toggle = on_subtask_toggle
        self.on_subtask_edit = on_subtask_edit
        self.on_subtask_delete = on_subtask_delete
        self.show_subtasks = show_subtasks
        self.show_tags = show_tags
        self.show_progress = show_progress
        self.compact = compact
        self.subtasks_expanded = subtasks_expanded
        
        self._card: Optional[ft.Container] = None
        
        # Componentes individuales (para acceso directo si es necesario)
        self.header: Optional[Header] = None
        self.description: Optional[Description] = None
        self.info_section: Optional[InfoSection] = None
        self.tags: Optional[Tags] = None
        self.subtasks: Optional[SubtasksSection] = None
        self.actions: Optional[Actions] = None
    
    def build(self) -> ft.Container:
        """
        Construye y retorna la tarjeta de tarea usando todos los componentes modulares.
        
        Returns:
            Container con la tarjeta de tarea
        """
        if self._card is None:
            self._card = create_task_card(
                task=self.task,
                page=self.page,
                on_click=self.on_click,
                on_edit=self.on_edit,
                on_delete=self.on_delete,
                on_toggle_status=self.on_toggle_status,
                on_subtask_toggle=self.on_subtask_toggle,
                on_subtask_edit=self.on_subtask_edit,
                on_subtask_delete=self.on_subtask_delete,
                show_subtasks=self.show_subtasks,
                show_tags=self.show_tags,
                show_progress=self.show_progress,
                compact=self.compact,
                subtasks_expanded=self.subtasks_expanded,
            )
        return self._card
    
    def update_task(self, new_task: Task):
        """
        Actualiza la tarea de la tarjeta y fuerza reconstrucción.
        
        Args:
            new_task: Nueva instancia de Task
        """
        self.task = new_task
        self.refresh()
    
    def refresh(self):
        """Invalida el caché y fuerza la reconstrucción de la tarjeta."""
        self._card = None
        self.header = None
        self.description = None
        self.info_section = None
        self.tags = None
        self.subtasks = None
        self.actions = None
