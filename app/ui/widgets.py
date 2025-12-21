"""
Widgets reutilizables para la interfaz de usuario.
"""
import flet as ft
from datetime import date
from app.data.models import Task, SubTask


def create_task_card(task: Task, on_toggle, on_edit, on_delete, on_toggle_subtask=None, on_add_subtask=None, on_delete_subtask=None, on_edit_subtask=None, page: ft.Page = None) -> ft.Card:
    """
    Crea una tarjeta de tarea responsive.
    
    Args:
        task: Tarea a mostrar.
        on_toggle: Callback cuando se cambia el estado de completado.
        on_edit: Callback cuando se edita la tarea.
        on_delete: Callback cuando se elimina la tarea.
        page: Página de Flet para detectar el tema.
        
    Returns:
        Widget Card con la información de la tarea.
    """
    # Detectar el tema actual y plataforma
    is_dark = page.theme_mode == ft.ThemeMode.DARK if page else False
    is_desktop = page and (page.platform == ft.PagePlatform.WINDOWS or page.platform == ft.PagePlatform.LINUX or page.platform == ft.PagePlatform.MACOS)
    is_tablet = False  # Se puede detectar por tamaño de pantalla si es necesario
    
    scheme = page.theme.color_scheme if page and page.theme else None
    primary = scheme.primary if scheme and scheme.primary else ft.Colors.RED_600
    secondary = scheme.secondary if scheme and scheme.secondary else ft.Colors.RED_400
    
    # Tamaños responsive
    title_size = 18 if is_desktop else 16
    description_size = 14 if is_desktop else 12
    icon_size = 24 if is_desktop else 20
    button_icon_size = 22 if is_desktop else 20
    card_padding = 20 if is_desktop else 16
    card_margin = ft.margin.only(bottom=16 if is_desktop else 12)
    
    # Colores adaptativos según el tema y matiz
    title_color = ft.Colors.GREY_400 if task.completed else (
        ft.Colors.WHITE if is_dark else primary
    )
    description_color = ft.Colors.GREY_500 if is_dark else ft.Colors.GREY_600
    
    # Color según prioridad de Matriz de Eisenhower
    priority_colors = {
        'urgent_important': ft.Colors.RED_600,  # Rojo para Urgente e Importante
        'not_urgent_important': ft.Colors.GREEN_600,  # Verde para No Urgente e Importante
        'urgent_not_important': ft.Colors.ORANGE_600,  # Naranja para Urgente y No Importante
        'not_urgent_not_important': ft.Colors.GREY_500  # Gris para No Urgente y No Importante
    }
    
    priority_labels = {
        'urgent_important': 'Urgente e Importante',
        'not_urgent_important': 'No Urgente e Importante',
        'urgent_not_important': 'Urgente y No Importante',
        'not_urgent_not_important': 'No Urgente y No Importante'
    }
    
    priority_color = priority_colors.get(task.priority, ft.Colors.GREY_300)
    priority_label = priority_labels.get(task.priority, 'No Urgente e Importante')
    
    # Icono de estado
    status_icon = ft.Icons.CHECK_CIRCLE if task.completed else ft.Icons.RADIO_BUTTON_UNCHECKED
    status_color = secondary if task.completed else ft.Colors.GREY_600
    
    # Estilo del texto según estado
    title_style = ft.TextStyle(
        decoration=ft.TextDecoration.LINE_THROUGH if task.completed else None,
        color=title_color
    )
    
    # Color de fondo de la tarjeta según el tema
    card_bgcolor = ft.Colors.BLACK87 if is_dark else None
    
    # Construir lista de controles de la tarjeta - responsive
    card_controls = [
        ft.Row(
            [
                ft.IconButton(
                    icon=status_icon,
                    icon_color=status_color,
                    icon_size=icon_size,
                    on_click=lambda e, task_obj=task: on_toggle(task_obj.id),
                    tooltip="Marcar como completada" if not task.completed else "Marcar como pendiente",
                    width=icon_size + 8,
                    height=icon_size + 8
                ),
                ft.Column(
                    [
                        ft.Text(
                            task.title,
                            size=title_size,
                            weight=ft.FontWeight.BOLD,
                            style=title_style,
                            expand=True,
                            max_lines=2 if not is_desktop else None,
                            overflow=ft.TextOverflow.ELLIPSIS
                        ),
                        ft.Text(
                            task.description if task.description else "Sin descripción",
                            size=description_size,
                            color=description_color,
                            style=title_style if task.completed else None,
                            max_lines=3 if not is_desktop else None,
                            overflow=ft.TextOverflow.ELLIPSIS
                        ),
                    ],
                    expand=True,
                    spacing=6 if is_desktop else 4,
                    tight=False
                ),
            ],
            spacing=12 if is_desktop else 8,
            expand=True,
            wrap=False
        )
    ]
    
    # Agregar subtareas si existen
    if task.subtasks and len(task.subtasks) > 0:
        subtasks_list = []
        for subtask in task.subtasks:
            from datetime import datetime
            
            subtask_icon = ft.Icons.CHECK_CIRCLE if subtask.completed else ft.Icons.RADIO_BUTTON_UNCHECKED
            subtask_color = secondary if subtask.completed else ft.Colors.GREY_600
            subtask_text_color = ft.Colors.GREY_400 if subtask.completed else (ft.Colors.WHITE if is_dark else ft.Colors.BLACK87)
            subtask_desc_color = ft.Colors.GREY_500 if is_dark else ft.Colors.GREY_600
            
            # Formatear fecha límite si existe
            deadline_text = ""
            if subtask.deadline:
                try:
                    deadline_text = subtask.deadline.strftime("%d/%m/%Y %H:%M")
                    # Verificar si está vencida
                    if subtask.deadline < datetime.now() and not subtask.completed:
                        deadline_text = f"⚠️ {deadline_text} (Vencida)"
                except:
                    deadline_text = "Fecha inválida"
            
            # Construir controles de la subtarea
            subtask_text_controls = [
                ft.Text(
                    subtask.title,
                    size=12,
                    weight=ft.FontWeight.BOLD,
                    color=subtask_text_color,
                    expand=True,
                    style=ft.TextStyle(
                        decoration=ft.TextDecoration.LINE_THROUGH if subtask.completed else None
                    )
                )
            ]
            
            # Agregar descripción si existe
            if subtask.description:
                subtask_text_controls.append(
                    ft.Text(
                        subtask.description,
                        size=10,
                        color=subtask_desc_color,
                        style=ft.TextStyle(
                            decoration=ft.TextDecoration.LINE_THROUGH if subtask.completed else None
                        )
                    )
                )
            
            # Agregar fecha límite si existe
            if deadline_text:
                subtask_text_controls.append(
                    ft.Text(
                        deadline_text,
                        size=9,
                        color=secondary if "Vencida" in deadline_text else ft.Colors.GREY_500,
                        weight=ft.FontWeight.BOLD if "Vencida" in deadline_text else None
                    )
                )
            
            # Construir controles de la fila
            subtask_row_controls = [
                ft.IconButton(
                    icon=subtask_icon,
                    icon_color=subtask_color,
                    icon_size=16,
                    on_click=lambda e, st=subtask: on_toggle_subtask(st.id) if on_toggle_subtask else None,
                    tooltip="Marcar subtarea",
                    width=32,
                    height=32
                ),
                ft.Column(
                    subtask_text_controls,
                    spacing=2,
                    expand=True,
                    tight=True
                )
            ]
            
            # Agregar botones de acción si existen
            if on_edit_subtask or on_delete_subtask:
                action_buttons = []
                
                if on_edit_subtask:
                    action_buttons.append(
                        ft.IconButton(
                            icon=ft.Icons.EDIT,
                            icon_color=secondary,
                            icon_size=16,
                            on_click=lambda e, st=subtask: on_edit_subtask(st),
                            tooltip="Editar subtarea",
                            width=32,
                            height=32
                        )
                    )
                
                if on_delete_subtask:
                    action_buttons.append(
                        ft.IconButton(
                            icon=ft.Icons.DELETE,
                            icon_color=secondary,
                            icon_size=16,
                            on_click=lambda e, st_id=subtask.id: on_delete_subtask(st_id),
                            tooltip="Eliminar subtarea",
                            width=32,
                            height=32
                        )
                    )
                
                subtask_row_controls.append(
                    ft.Row(action_buttons, spacing=0)
                )
            
            # Contenedor principal de la subtarea
            subtask_content = ft.Column(
                [
                    ft.Row(
                        subtask_row_controls,
                        spacing=4,
                        expand=True
                    )
                ],
                spacing=2,
                tight=True
            )
            
            subtask_row = ft.Container(
                content=subtask_content,
                padding=ft.padding.symmetric(vertical=4, horizontal=8),
                border=ft.border.all(1, ft.Colors.GREY_800 if is_dark else ft.Colors.GREY_300),
                border_radius=4,
                margin=ft.margin.only(bottom=4)
            )
            subtasks_list.append(subtask_row)
        
        if subtasks_list:
            card_controls.append(
                ft.Container(
                    content=ft.Column(
                        subtasks_list,
                        spacing=4,
                        tight=True
                    ),
                    padding=ft.padding.only(left=40, top=4, bottom=4),
                )
            )
    
    # Botón para agregar subtarea
    if on_add_subtask:
        def make_add_handler(task_id):
            def handler(e):
                on_add_subtask(task_id)
            return handler
        
        card_controls.append(
            ft.Container(
                content=ft.TextButton(
                    icon=ft.Icons.ADD,
                    text="Agregar subtarea",
                    icon_color=secondary,
                    on_click=make_add_handler(task.id),
                    tooltip="Agregar subtarea"
                ),
                padding=ft.padding.only(left=40, top=4, bottom=4),
            )
        )
    
    # Fila de acciones
    card_controls.append(
        ft.Row(
            [
                    ft.Container(
                        content=ft.Text(
                            priority_label,
                            size=11 if is_desktop else 10,
                            color=ft.Colors.WHITE,
                            weight=ft.FontWeight.BOLD
                        ),
                        bgcolor=priority_color,
                        padding=ft.padding.symmetric(
                            horizontal=10 if is_desktop else 8,
                            vertical=6 if is_desktop else 4
                        ),
                        border_radius=12,
                    ),
                ft.Row(
                    [
                ft.IconButton(
                    icon=ft.Icons.EDIT,
                    icon_color=secondary,
                    icon_size=button_icon_size,
                    on_click=lambda e, t=task: on_edit(t),
                    tooltip="Editar",
                    width=button_icon_size + 12 if is_desktop else button_icon_size + 8,
                    height=button_icon_size + 12 if is_desktop else button_icon_size + 8
                ),
                ft.IconButton(
                    icon=ft.Icons.DELETE,
                    icon_color=primary,
                    icon_size=button_icon_size,
                    on_click=lambda e, task_id=task.id: on_delete(task_id),
                    tooltip="Eliminar",
                    width=button_icon_size + 12 if is_desktop else button_icon_size + 8,
                    height=button_icon_size + 12 if is_desktop else button_icon_size + 8
                ),
                    ],
                    spacing=0
                )
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
        )
    )
    
    return ft.Card(
        content=ft.Container(
            content=ft.Column(
                card_controls,
                spacing=10 if is_desktop else 8,
                tight=False
            ),
            padding=card_padding,
            border_radius=10 if is_desktop else 8,
            bgcolor=card_bgcolor,
        ),
        elevation=3 if is_desktop else 2,
        margin=card_margin
    )


def create_empty_state(page: ft.Page = None) -> ft.Container:
    """
    Crea un widget para mostrar cuando no hay tareas.
    
    Args:
        page: Página de Flet para detectar el tema.
    
    Returns:
        Container con mensaje de estado vacío.
    """
    # Detectar el tema actual
    is_dark = page.theme_mode == ft.ThemeMode.DARK if page else False
    scheme = page.theme.color_scheme if page and page.theme else None
    primary = scheme.primary if scheme and scheme.primary else ft.Colors.RED_600
    secondary = scheme.secondary if scheme and scheme.secondary else ft.Colors.RED_400
    
    # Colores adaptativos con matiz
    icon_color = primary
    text_color = secondary if is_dark else primary
    subtitle_color = primary
    
    return ft.Container(
        content=ft.Column(
            [
                ft.Icon(
                    ft.Icons.TASK_ALT,
                    size=64,
                    color=icon_color
                ),
                ft.Text(
                    "No hay tareas",
                    size=18,
                    weight=ft.FontWeight.BOLD,
                    color=text_color
                ),
                ft.Text(
                    "¡Crea tu primera tarea!",
                    size=14,
                    color=subtitle_color
                )
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=8
        ),
        padding=40,
        alignment=ft.alignment.center
    )


def create_statistics_card(stats: dict, page: ft.Page = None) -> ft.Card:
    """
    Crea una tarjeta con estadísticas de tareas.
    
    Args:
        stats: Diccionario con estadísticas.
        page: Página de Flet para detectar el tema.
        
    Returns:
        Widget Card con estadísticas.
    """
    # Detectar el tema actual
    is_dark = page.theme_mode == ft.ThemeMode.DARK if page else False
    scheme = page.theme.color_scheme if page and page.theme else None
    primary = scheme.primary if scheme and scheme.primary else ft.Colors.RED_600
    secondary = scheme.secondary if scheme and scheme.secondary else ft.Colors.RED_400
    
    # Color adaptativo para las etiquetas
    label_color = ft.Colors.GREY_400 if is_dark else ft.Colors.GREY_600
    
    # Color de fondo de la tarjeta de estadísticas
    stats_card_bgcolor = ft.Colors.BLACK87 if is_dark else None
    
    return ft.Card(
        content=ft.Container(
            content=ft.Row(
                [
                    ft.Column(
                        [
                            ft.Text(
                                str(stats.get('total', 0)),
                                size=24,
                                weight=ft.FontWeight.BOLD,
                                color=primary
                            ),
                            ft.Text("Total", size=12, color=label_color)
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        expand=True
                    ),
                    ft.VerticalDivider(),
                    ft.Column(
                        [
                            ft.Text(
                                str(stats.get('completed', 0)),
                                size=24,
                                weight=ft.FontWeight.BOLD,
                                color=secondary
                            ),
                            ft.Text("Completadas", size=12, color=label_color)
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        expand=True
                    ),
                    ft.VerticalDivider(),
                    ft.Column(
                        [
                            ft.Text(
                                str(stats.get('pending', 0)),
                                size=24,
                                weight=ft.FontWeight.BOLD,
                                color=primary
                            ),
                            ft.Text("Pendientes", size=12, color=label_color)
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        expand=True
                    )
                ],
                alignment=ft.MainAxisAlignment.SPACE_EVENLY
            ),
            padding=16,
            bgcolor=stats_card_bgcolor,
        ),
        elevation=1,
        margin=ft.margin.only(bottom=8)
    )


def create_habit_card(habit, metrics: dict, on_toggle_completion, on_edit, on_delete, on_view_details, page: ft.Page = None) -> ft.Card:
    """
    Crea una tarjeta de hábito.
    
    Args:
        habit: Hábito a mostrar.
        metrics: Diccionario con métricas del hábito.
        on_toggle_completion: Callback cuando se marca/desmarca cumplimiento.
        on_edit: Callback cuando se edita el hábito.
        on_delete: Callback cuando se elimina el hábito.
        on_view_details: Callback cuando se ve el detalle del hábito.
        page: Página de Flet para detectar el tema.
        
    Returns:
        Widget Card con la información del hábito.
    """
    # Detectar el tema actual
    is_dark = page.theme_mode == ft.ThemeMode.DARK if page else False
    scheme = page.theme.color_scheme if page and page.theme else None
    primary = scheme.primary if scheme and scheme.primary else ft.Colors.RED_600
    secondary = scheme.secondary if scheme and scheme.secondary else ft.Colors.RED_400
    
    # Colores adaptativos según el tema
    title_color = ft.Colors.WHITE if is_dark else primary
    description_color = ft.Colors.GREY_500 if is_dark else ft.Colors.GREY_600
    
    # Color de fondo de la tarjeta según el tema
    card_bgcolor = ft.Colors.BLACK87 if is_dark else None
    
    # Color según el estado activo
    status_color = secondary if habit.active else ft.Colors.GREY_500
    status_text = "Activo" if habit.active else "Inactivo"
    
    # Información de métricas
    streak = metrics.get('streak', 0)
    completion_percentage = metrics.get('completion_percentage', 0.0)
    total_completions = metrics.get('total_completions', 0)
    
    # Color del streak según su valor
    streak_color = secondary if streak > 0 else ft.Colors.GREY_500
    
    # Construir controles de la tarjeta
    card_controls = [
        ft.Row(
            [
                ft.Column(
                    [
                        ft.Text(
                            habit.title,
                            size=18,
                            weight=ft.FontWeight.BOLD,
                            color=title_color,
                            expand=True
                        ),
                        ft.Text(
                            habit.description if habit.description else "Sin descripción",
                            size=12,
                            color=description_color,
                            max_lines=2,
                            overflow=ft.TextOverflow.ELLIPSIS
                        ),
                    ],
                    expand=True,
                    spacing=4
                ),
                # Botón para marcar/desmarcar cumplimiento de hoy
                ft.IconButton(
                    icon=ft.Icons.CHECK_CIRCLE if metrics.get('last_completion_date') == date.today() else ft.Icons.RADIO_BUTTON_UNCHECKED,
                    icon_color=secondary if metrics.get('last_completion_date') == date.today() else ft.Colors.GREY_600,
                    on_click=lambda e, h=habit: on_toggle_completion(h.id),
                    tooltip="Marcar cumplimiento de hoy"
                )
            ],
            spacing=8,
            expand=True
        ),
        ft.Divider(height=1),
        # Métricas
        ft.Row(
            [
                # Streak
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Text(
                                str(streak),
                                size=20,
                                weight=ft.FontWeight.BOLD,
                                color=streak_color
                            ),
                            ft.Text(
                                "Días seguidos",
                                size=10,
                                color=description_color
                            )
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=2,
                        tight=True
                    ),
                    expand=True
                ),
                ft.VerticalDivider(),
                # Porcentaje
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Text(
                                f"{completion_percentage:.0f}%",
                                size=20,
                                weight=ft.FontWeight.BOLD,
                                color=secondary
                            ),
                            ft.Text(
                                "Cumplimiento",
                                size=10,
                                color=description_color
                            )
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=2,
                        tight=True
                    ),
                    expand=True
                ),
                ft.VerticalDivider(),
                # Total
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Text(
                                str(total_completions),
                                size=20,
                                weight=ft.FontWeight.BOLD,
                                color=primary
                            ),
                            ft.Text(
                                "Total",
                                size=10,
                                color=description_color
                            )
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=2,
                        tight=True
                    ),
                    expand=True
                )
            ],
            alignment=ft.MainAxisAlignment.SPACE_EVENLY
        ),
        ft.Divider(height=1),
        # Fila de acciones
        ft.Row(
            [
                # Estado y frecuencia
                ft.Container(
                    content=ft.Row(
                        [
                            ft.Container(
                                content=ft.Text(
                                    status_text,
                                    size=10,
                                    color=ft.Colors.WHITE,
                                    weight=ft.FontWeight.BOLD
                                ),
                                bgcolor=status_color,
                                padding=ft.padding.symmetric(horizontal=8, vertical=4),
                                border_radius=12,
                            ),
                            ft.Text(
                                f"• {habit.frequency.capitalize()}",
                                size=10,
                                color=description_color
                            )
                        ],
                        spacing=4
                    ),
                    expand=True
                ),
                # Botones de acción
                ft.Row(
                    [
                        ft.IconButton(
                            icon=ft.Icons.INFO_OUTLINE,
                            icon_color=secondary,
                            icon_size=20,
                            on_click=lambda e, h=habit: on_view_details(h),
                            tooltip="Ver detalles"
                        ),
                        ft.IconButton(
                            icon=ft.Icons.EDIT,
                            icon_color=secondary,
                            icon_size=20,
                            on_click=lambda e, h=habit: on_edit(h),
                            tooltip="Editar"
                        ),
                        ft.IconButton(
                            icon=ft.Icons.DELETE,
                            icon_color=primary,
                            icon_size=20,
                            on_click=lambda e, h_id=habit.id: on_delete(h_id),
                            tooltip="Eliminar"
                        ),
                    ],
                    spacing=0
                )
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
        )
    ]
    
    return ft.Card(
        content=ft.Container(
            content=ft.Column(
                card_controls,
                spacing=8,
                tight=True
            ),
            padding=12,
            border_radius=8,
            bgcolor=card_bgcolor,
        ),
        elevation=2,
        margin=ft.margin.symmetric(vertical=4)
    )


def create_habit_empty_state(page: ft.Page = None) -> ft.Container:
    """
    Crea un widget para mostrar cuando no hay hábitos.
    
    Args:
        page: Página de Flet para detectar el tema.
    
    Returns:
        Container con mensaje de estado vacío.
    """
    # Detectar el tema actual
    is_dark = page.theme_mode == ft.ThemeMode.DARK if page else False
    scheme = page.theme.color_scheme if page and page.theme else None
    primary = scheme.primary if scheme and scheme.primary else ft.Colors.RED_600
    secondary = scheme.secondary if scheme and scheme.secondary else ft.Colors.RED_400
    
    # Colores adaptativos con matiz
    icon_color = primary
    text_color = secondary if is_dark else primary
    subtitle_color = primary
    
    return ft.Container(
        content=ft.Column(
            [
                ft.Icon(
                    ft.Icons.CALENDAR_VIEW_WEEK,
                    size=64,
                    color=icon_color
                ),
                ft.Text(
                    "No hay hábitos",
                    size=18,
                    weight=ft.FontWeight.BOLD,
                    color=text_color
                ),
                ft.Text(
                    "¡Crea tu primer hábito!",
                    size=14,
                    color=subtitle_color
                )
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=8
        ),
        padding=40,
        alignment=ft.alignment.center
    )


def create_habit_statistics_card(stats: dict, page: ft.Page = None) -> ft.Card:
    """
    Crea una tarjeta con estadísticas de hábitos.
    
    Args:
        stats: Diccionario con estadísticas.
        page: Página de Flet para detectar el tema.
        
    Returns:
        Widget Card con estadísticas.
    """
    # Detectar el tema actual
    is_dark = page.theme_mode == ft.ThemeMode.DARK if page else False
    scheme = page.theme.color_scheme if page and page.theme else None
    primary = scheme.primary if scheme and scheme.primary else ft.Colors.RED_600
    secondary = scheme.secondary if scheme and scheme.secondary else ft.Colors.RED_400
    
    # Color adaptativo para las etiquetas
    label_color = ft.Colors.GREY_400 if is_dark else ft.Colors.GREY_600
    
    # Color de fondo de la tarjeta de estadísticas
    stats_card_bgcolor = ft.Colors.BLACK87 if is_dark else None
    
    return ft.Card(
        content=ft.Container(
            content=ft.Row(
                [
                    ft.Column(
                        [
                            ft.Text(
                                str(stats.get('total', 0)),
                                size=24,
                                weight=ft.FontWeight.BOLD,
                                color=primary
                            ),
                            ft.Text("Total", size=12, color=label_color)
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        expand=True
                    ),
                    ft.VerticalDivider(),
                    ft.Column(
                        [
                            ft.Text(
                                str(stats.get('active', 0)),
                                size=24,
                                weight=ft.FontWeight.BOLD,
                                color=secondary
                            ),
                            ft.Text("Activos", size=12, color=label_color)
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        expand=True
                    ),
                    ft.VerticalDivider(),
                    ft.Column(
                        [
                            ft.Text(
                                str(stats.get('habits_with_streak', 0)),
                                size=24,
                                weight=ft.FontWeight.BOLD,
                                color=primary
                            ),
                            ft.Text("Con racha", size=12, color=label_color)
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        expand=True
                    )
                ],
                alignment=ft.MainAxisAlignment.SPACE_EVENLY
            ),
            padding=16,
            bgcolor=stats_card_bgcolor,
        ),
        elevation=1,
        margin=ft.margin.only(bottom=8)
    )

