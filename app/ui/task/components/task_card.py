"""
Componente Task Card
Muestra una tarea completa con todos sus detalles, badges, subtareas y acciones
"""

import flet as ft
from typing import Optional, Callable
from app.models.task import Task
from app.ui.task.components.status_badge import create_status_badge
from app.ui.task.components.priority_badge import create_priority_badge
from app.ui.task.components.subtask_item import create_subtask_item
from app.utils.task_helper import (
    calculate_completion_percentage,
    format_completion_percentage,
    is_task_overdue,
    is_task_due_today,
    is_task_due_soon,
)
from app.utils.helpers.formats import format_date
from app.utils.helpers.responsives import (
    get_responsive_size,
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
) -> ft.Container:
    """
    Crea un componente visual para mostrar una tarea completa
    
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
    
    Returns:
        Container con el componente de tarea estilizado
        
    Ejemplo:
        >>> task = Task(id="task_1", title="Mi Tarea", user_id="user_1")
        >>> card = create_task_card(task, page=page, on_click=handle_click)
        >>> tasks_list.controls.append(card)
    """
    # Calcular tamaños responsive
    if compact:
        padding_value = get_responsive_padding(page=page) // 2
        title_size = get_responsive_size(page=page, mobile=16, tablet=18, desktop=20)
        description_size = get_responsive_size(page=page, mobile=12, tablet=13, desktop=14)
        spacing_value = get_responsive_spacing(page=page, mobile=6, tablet=8, desktop=10)
    else:
        padding_value = get_responsive_padding(page=page)
        title_size = get_responsive_size(page=page, mobile=18, tablet=20, desktop=22)
        description_size = get_responsive_size(page=page, mobile=13, tablet=14, desktop=15)
        spacing_value = get_responsive_spacing(page=page, mobile=8, tablet=10, desktop=12)
    
    # Contenedor principal de la tarjeta
    card_controls = []
    
    # Header: Título y badges
    header_controls = []
    
    # Título de la tarea
    title_text = ft.Text(
        task.title,
        size=title_size,
        weight=ft.FontWeight.BOLD,
        color=ft.Colors.WHITE,
        expand=True,
    )
    header_controls.append(title_text)
    
    # Badges de estado y prioridad
    badges_row = ft.Row(
        controls=[
            create_status_badge(task.status, page=page, size="small"),
            create_priority_badge(
                urgent=task.urgent,
                important=task.important,
                page=page,
                size="small",
                show_quadrant=False,
            ),
        ],
        spacing=6,
        tight=True,
    )
    header_controls.append(badges_row)
    
    header_row = ft.Row(
        controls=header_controls,
        spacing=10,
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )
    card_controls.append(header_row)
    
    # Descripción (si existe)
    if task.description:
        description_text = ft.Text(
            task.description,
            size=description_size,
            color=ft.Colors.WHITE_70,
            max_lines=3 if compact else 5,
            overflow=ft.TextOverflow.ELLIPSIS,
        )
        card_controls.append(description_text)
    
    # Información adicional: Fecha de vencimiento y progreso
    info_controls = []
    
    # Fecha de vencimiento
    if task.due_date:
        due_date_color = ft.Colors.RED_400 if is_task_overdue(task) else (
            ft.Colors.ORANGE_400 if is_task_due_today(task) else (
                ft.Colors.YELLOW_400 if is_task_due_soon(task) else ft.Colors.WHITE_70
            )
        )
        
        due_date_icon = ft.Icons.CALENDAR_TODAY
        if is_task_overdue(task):
            due_date_icon = ft.Icons.WARNING
        elif is_task_due_today(task):
            due_date_icon = ft.Icons.TODAY
        
        due_date_row = ft.Row(
            controls=[
                ft.Icon(due_date_icon, size=16, color=due_date_color),
                ft.Text(
                    format_date(task.due_date),
                    size=description_size,
                    color=due_date_color,
                ),
            ],
            spacing=6,
            tight=True,
        )
        info_controls.append(due_date_row)
    
    # Barra de progreso (si hay subtareas o si está completada)
    if show_progress:
        completion_percentage = calculate_completion_percentage(task)
        
        progress_row = ft.Row(
            controls=[
                ft.Icon(ft.Icons.CHECK_CIRCLE_OUTLINE, size=16, color=ft.Colors.BLUE_400),
                ft.Text(
                    format_completion_percentage(task),
                    size=description_size,
                    color=ft.Colors.WHITE_70,
                ),
                ft.ProgressBar(
                    value=completion_percentage,
                    width=100 if compact else 150,
                    height=6,
                    color=ft.Colors.BLUE_400,
                    bgcolor=ft.Colors.GREY_800,
                ),
            ],
            spacing=8,
            alignment=ft.MainAxisAlignment.START,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )
        info_controls.append(progress_row)
    
    if info_controls:
        info_row = ft.Row(
            controls=info_controls,
            spacing=15,
            wrap=True,
        )
        card_controls.append(info_row)
    
    # Tags (si existen)
    if show_tags and task.tags:
        tags_row = ft.Row(
            controls=[
                ft.Container(
                    content=ft.Text(
                        tag,
                        size=10,
                        color=ft.Colors.BLUE_300,
                    ),
                    padding=ft.Padding.symmetric(horizontal=6, vertical=2),
                    border_radius=4,
                    bgcolor=ft.Colors.BLUE_900,
                )
                for tag in task.tags[:5]  # Máximo 5 tags
            ],
            spacing=6,
            wrap=True,
        )
        card_controls.append(tags_row)
    
    # Subtareas (si existen y están habilitadas)
    if show_subtasks and task.subtasks:
        subtasks_title = ft.Text(
            f"Subtareas ({len(task.subtasks)})",
            size=description_size,
            weight=ft.FontWeight.W_500,
            color=ft.Colors.WHITE_70,
        )
        card_controls.append(subtasks_title)
        
        # Lista de subtareas
        subtasks_list = ft.Column(
            controls=[
                create_subtask_item(
                    subtask=subtask,
                    page=page,
                    on_toggle_completed=lambda sid=subtask.id: on_subtask_toggle(task.id, sid) if on_subtask_toggle else None,
                    on_edit=lambda sid=subtask.id: on_subtask_edit(task.id, sid) if on_subtask_edit else None,
                    on_delete=lambda sid=subtask.id: on_subtask_delete(task.id, sid) if on_subtask_delete else None,
                    show_priority=True,
                    show_actions=not compact,
                    compact=compact,
                )
                for subtask in task.subtasks
            ],
            spacing=6,
        )
        card_controls.append(subtasks_list)
    
    # Botones de acción
    action_buttons = []
    
    if on_toggle_status:
        status_icon = ft.Icons.CHECK_CIRCLE if task.status != "completada" else ft.Icons.UNDO
        toggle_button = ft.IconButton(
            icon=status_icon,
            icon_size=20,
            icon_color=ft.Colors.GREEN_400,
            tooltip="Cambiar estado",
            on_click=lambda e: on_toggle_status(task.id) if on_toggle_status else None,
        )
        action_buttons.append(toggle_button)
    
    if on_edit:
        edit_button = ft.IconButton(
            icon=ft.Icons.EDIT,
            icon_size=20,
            icon_color=ft.Colors.BLUE_400,
            tooltip="Editar tarea",
            on_click=lambda e: on_edit(task.id) if on_edit else None,
        )
        action_buttons.append(edit_button)
    
    if on_delete:
        delete_button = ft.IconButton(
            icon=ft.Icons.DELETE_OUTLINE,
            icon_size=20,
            icon_color=ft.Colors.RED_400,
            tooltip="Eliminar tarea",
            on_click=lambda e: on_delete(task.id) if on_delete else None,
        )
        action_buttons.append(delete_button)
    
    if action_buttons:
        actions_row = ft.Row(
            controls=action_buttons,
            spacing=5,
            alignment=ft.MainAxisAlignment.END,
        )
        card_controls.append(actions_row)
    
    # Contenedor principal de la tarjeta
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
    Clase para crear tarjetas de tareas
    Permite más control y personalización que la función create_task_card
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
    ):
        """
        Inicializa la tarjeta de tarea
        
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
        self._card: Optional[ft.Container] = None
    
    def build(self) -> ft.Container:
        """
        Construye y retorna la tarjeta de tarea
        
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
            )
        return self._card
    
    def update_task(self, new_task: Task):
        """
        Actualiza la tarea de la tarjeta
        
        Args:
            new_task: Nueva instancia de Task
        """
        self.task = new_task
        self._card = None  # Forzar reconstrucción
    
    def refresh(self):
        """Fuerza la reconstrucción de la tarjeta"""
        self._card = None

