"""
Widgets reutilizables para la interfaz de usuario.
"""
import flet as ft
from app.data.models import Task, SubTask


def create_task_card(task: Task, on_toggle, on_edit, on_delete, on_toggle_subtask=None, on_add_subtask=None, on_delete_subtask=None, on_edit_subtask=None, page: ft.Page = None) -> ft.Card:
    """
    Crea una tarjeta de tarea.
    
    Args:
        task: Tarea a mostrar.
        on_toggle: Callback cuando se cambia el estado de completado.
        on_edit: Callback cuando se edita la tarea.
        on_delete: Callback cuando se elimina la tarea.
        page: Página de Flet para detectar el tema.
        
    Returns:
        Widget Card con la información de la tarea.
    """
    # Detectar el tema actual
    is_dark = page.theme_mode == ft.ThemeMode.DARK if page else False
    
    # Colores adaptativos según el tema
    title_color = ft.Colors.GREY_400 if task.completed else (ft.Colors.WHITE if is_dark else ft.Colors.BLACK87)
    description_color = ft.Colors.GREY_500 if is_dark else ft.Colors.GREY_600
    
    # Color según prioridad (esquema rojo/negro)
    priority_colors = {
        'high': ft.Colors.RED_600,
        'medium': ft.Colors.RED_800,
        'low': ft.Colors.RED_900
    }
    
    priority_labels = {
        'high': 'Alta',
        'medium': 'Media',
        'low': 'Baja'
    }
    
    priority_color = priority_colors.get(task.priority, ft.Colors.GREY_300)
    priority_label = priority_labels.get(task.priority, 'Media')
    
    # Icono de estado
    status_icon = ft.Icons.CHECK_CIRCLE if task.completed else ft.Icons.RADIO_BUTTON_UNCHECKED
    status_color = ft.Colors.RED_400 if task.completed else ft.Colors.GREY_600
    
    # Estilo del texto según estado
    title_style = ft.TextStyle(
        decoration=ft.TextDecoration.LINE_THROUGH if task.completed else None,
        color=title_color
    )
    
    # Color de fondo de la tarjeta según el tema
    card_bgcolor = ft.Colors.BLACK87 if is_dark else None
    
    # Construir lista de controles de la tarjeta
    card_controls = [
        ft.Row(
            [
                ft.IconButton(
                    icon=status_icon,
                    icon_color=status_color,
                    on_click=lambda e, task_obj=task: on_toggle(task_obj.id),
                    tooltip="Marcar como completada" if not task.completed else "Marcar como pendiente"
                ),
                ft.Column(
                    [
                        ft.Text(
                            task.title,
                            size=16,
                            weight=ft.FontWeight.BOLD,
                            style=title_style,
                            expand=True
                        ),
                        ft.Text(
                            task.description if task.description else "Sin descripción",
                            size=12,
                            color=description_color,
                            style=title_style if task.completed else None
                        ),
                    ],
                    expand=True,
                    spacing=4
                ),
            ],
            spacing=8,
            expand=True
        )
    ]
    
    # Agregar subtareas si existen
    if task.subtasks and len(task.subtasks) > 0:
        subtasks_list = []
        for subtask in task.subtasks:
            from datetime import datetime
            
            subtask_icon = ft.Icons.CHECK_CIRCLE if subtask.completed else ft.Icons.RADIO_BUTTON_UNCHECKED
            subtask_color = ft.Colors.RED_400 if subtask.completed else ft.Colors.GREY_600
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
                        color=ft.Colors.RED_400 if "Vencida" in deadline_text else ft.Colors.GREY_500,
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
                            icon_color=ft.Colors.RED_400,
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
                            icon_color=ft.Colors.RED_400,
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
                    icon_color=ft.Colors.RED_400,
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
                        size=10,
                        color=ft.Colors.WHITE,
                        weight=ft.FontWeight.BOLD
                    ),
                    bgcolor=priority_color,
                    padding=ft.padding.symmetric(horizontal=8, vertical=4),
                    border_radius=12,
                ),
                ft.Row(
                    [
                        ft.IconButton(
                            icon=ft.Icons.EDIT,
                            icon_color=ft.Colors.RED_400,
                            icon_size=20,
                            on_click=lambda e, t=task: on_edit(t),
                            tooltip="Editar"
                        ),
                        ft.IconButton(
                            icon=ft.Icons.DELETE,
                            icon_color=ft.Colors.RED,
                            icon_size=20,
                            on_click=lambda e, task_id=task.id: on_delete(task_id),
                            tooltip="Eliminar"
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
    
    # Colores adaptativos con matices rojos
    icon_color = ft.Colors.RED_600 if is_dark else ft.Colors.RED_500
    text_color = ft.Colors.RED_400 if is_dark else ft.Colors.RED_700
    subtitle_color = ft.Colors.RED_700 if is_dark else ft.Colors.RED_600
    
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
                                color=ft.Colors.RED_400
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
                                color=ft.Colors.RED_500
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
                                color=ft.Colors.RED_600
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

