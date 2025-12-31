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
    subtasks_expanded: bool = True,
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
        subtasks_expanded: Si las subtareas están expandidas por defecto (default: True)
    
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
    # Guardar referencia al badge de estado para poder actualizarlo
    status_badge = create_status_badge(task.status, page=page, size="small")
    priority_badge = create_priority_badge(
        urgent=task.urgent,
        important=task.important,
        page=page,
        size="small",
        show_quadrant=False,
    )
    
    badges_row = ft.Row(
        controls=[
            status_badge,
            priority_badge,
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
    progress_bar = None
    progress_text = None
    
    if show_progress:
        completion_percentage = calculate_completion_percentage(task)
        
        # Crear controles de progreso con referencias para actualización dinámica
        progress_text = ft.Text(
            format_completion_percentage(task),
            size=description_size,
            color=ft.Colors.WHITE_70,
        )
        
        progress_bar = ft.ProgressBar(
            value=completion_percentage,
            width=100 if compact else 150,
            height=6,
            color=ft.Colors.BLUE_400,
            bgcolor=ft.Colors.GREY_800,
        )
        
        progress_row = ft.Row(
            controls=[
                ft.Icon(ft.Icons.CHECK_CIRCLE_OUTLINE, size=16, color=ft.Colors.BLUE_400),
                progress_text,
                progress_bar,
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
        # Estado inicial de expansión (usar el parámetro recibido)
        # Usamos una lista para poder modificar el valor desde el closure
        subtasks_expanded_state = [subtasks_expanded]
        
        # Función wrapper para actualizar progreso automáticamente
        def create_subtask_toggle_handler(subtask_id: str):
            """Crea un handler que actualiza el progreso automáticamente"""
            def handler(received_subtask_id: str):
                # Usar el ID recibido (que viene del callback de subtask_item)
                # Actualizar el objeto Task localmente
                subtask = next((st for st in task.subtasks if st.id == received_subtask_id), None)
                if subtask:
                    subtask.toggle_completed()
                    
                    # Calcular nuevo porcentaje de completitud
                    new_percentage = calculate_completion_percentage(task)
                    
                    # Actualizar estado de la tarea según el progreso
                    from app.utils.task_helper import (
                        TASK_STATUS_PENDING,
                        TASK_STATUS_IN_PROGRESS,
                        TASK_STATUS_COMPLETED,
                    )
                    
                    # Actualizar estado de la tarea según el progreso
                    # Si está al 100%, cambiar a "Completada"
                    if new_percentage >= 1.0:
                        if task.status != TASK_STATUS_COMPLETED:
                            task.update_status(TASK_STATUS_COMPLETED)
                            # Reconstruir el badge de estado
                            new_status_badge = create_status_badge(task.status, page=page, size="small")
                            badges_row.controls[0] = new_status_badge
                    # Si está al 0% (no hay subtareas completadas), cambiar a "Pendiente"
                    elif new_percentage == 0.0:
                        if task.status != TASK_STATUS_PENDING:
                            task.update_status(TASK_STATUS_PENDING)
                            # Reconstruir el badge de estado
                            new_status_badge = create_status_badge(task.status, page=page, size="small")
                            badges_row.controls[0] = new_status_badge
                    # Si está entre 0% y 100%, cambiar a "En progreso" si no lo está
                    else:
                        if task.status == TASK_STATUS_PENDING or task.status == TASK_STATUS_COMPLETED:
                            task.update_status(TASK_STATUS_IN_PROGRESS)
                            # Reconstruir el badge de estado
                            new_status_badge = create_status_badge(task.status, page=page, size="small")
                            badges_row.controls[0] = new_status_badge
                    
                    # Actualizar progreso si está habilitado
                    if show_progress and progress_bar is not None and progress_text is not None:
                        progress_bar.value = new_percentage
                        progress_text.value = format_completion_percentage(task)
                    
                    # Actualizar la página si está disponible
                    if page:
                        page.update()
                    
                    # Llamar al callback original si existe
                    if on_subtask_toggle:
                        on_subtask_toggle(task.id, received_subtask_id)
            return handler
        
        # Lista de subtareas
        subtasks_list = ft.Column(
            controls=[
                create_subtask_item(
                    subtask=subtask,
                    page=page,
                    on_toggle_completed=create_subtask_toggle_handler(subtask.id),
                    on_edit=lambda sid=subtask.id: on_subtask_edit(task.id, sid) if on_subtask_edit else None,
                    on_delete=lambda sid=subtask.id: on_subtask_delete(task.id, sid) if on_subtask_delete else None,
                    show_priority=True,
                    show_actions=not compact,
                    compact=compact,
                )
                for subtask in task.subtasks
            ],
            spacing=6,
            visible=subtasks_expanded_state[0],
        )
        
        # Botón para expandir/contraer
        expand_button = ft.IconButton(
            icon=ft.Icons.EXPAND_MORE if subtasks_expanded_state[0] else ft.Icons.CHEVRON_RIGHT,
            icon_size=20,
            icon_color=ft.Colors.WHITE_70,
            tooltip="Expandir/Contraer subtareas",
        )
        
        # Función para toggle de expandir/contraer
        def toggle_subtasks(e):
            subtasks_expanded_state[0] = not subtasks_expanded_state[0]
            subtasks_list.visible = subtasks_expanded_state[0]
            expand_button.icon = ft.Icons.EXPAND_MORE if subtasks_expanded_state[0] else ft.Icons.CHEVRON_RIGHT
            if page:
                page.update()
        
        expand_button.on_click = toggle_subtasks
        
        # Título con botón de expandir/contraer
        subtasks_title_row = ft.Row(
            controls=[
                expand_button,
                ft.Text(
                    f"Subtareas ({len(task.subtasks)})",
                    size=description_size,
                    weight=ft.FontWeight.W_500,
                    color=ft.Colors.WHITE_70,
                ),
            ],
            spacing=8,
            tight=True,
            alignment=ft.MainAxisAlignment.START,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )
        card_controls.append(subtasks_title_row)
        card_controls.append(subtasks_list)
    
    # Botones de acción
    action_buttons = []
    
    # El botón de completar solo se muestra si no hay subtareas
    # Si hay subtareas, el progreso se controla a través de las subtareas individuales
    if on_toggle_status and (not task.subtasks or len(task.subtasks) == 0):
        status_icon = ft.Icons.CHECK_CIRCLE if task.status != "completada" else ft.Icons.UNDO
        
        # Crear el botón primero
        toggle_button = ft.IconButton(
            icon=status_icon,
            icon_size=20,
            icon_color=ft.Colors.GREEN_400,
            tooltip="Cambiar estado",
        )
        
        # Handler para el botón de toggle de estado
        # Solo se usa cuando NO hay subtareas
        def handle_toggle_status(e):
            from app.utils.task_helper import (
                TASK_STATUS_PENDING,
                TASK_STATUS_COMPLETED,
            )
            
            # Si la tarea no está completada, marcarla como completada
            if task.status != TASK_STATUS_COMPLETED:
                # Actualizar estado a completada
                task.update_status(TASK_STATUS_COMPLETED)
                
                # Actualizar progreso a 100% (sin subtareas, completar = 100%)
                if show_progress and progress_bar is not None and progress_text is not None:
                    progress_bar.value = 1.0
                    progress_text.value = format_completion_percentage(task)
            else:
                # Si está completada, marcarla como pendiente
                task.update_status(TASK_STATUS_PENDING)
                
                # Actualizar progreso a 0% (sin subtareas, descompletar = 0%)
                if show_progress and progress_bar is not None and progress_text is not None:
                    progress_bar.value = 0.0
                    progress_text.value = format_completion_percentage(task)
            
            # Reconstruir el badge de estado
            new_status_badge = create_status_badge(task.status, page=page, size="small")
            badges_row.controls[0] = new_status_badge
            
            # Actualizar el ícono del botón
            toggle_button.icon = ft.Icons.CHECK_CIRCLE if task.status != TASK_STATUS_COMPLETED else ft.Icons.UNDO
            
            # Actualizar la página
            if page:
                page.update()
            
            # Llamar al callback original si existe
            if on_toggle_status:
                on_toggle_status(task.id)
        
        # Asignar el handler al botón
        toggle_button.on_click = handle_toggle_status
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
        subtasks_expanded: bool = True,
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
                subtasks_expanded=self.subtasks_expanded,
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

