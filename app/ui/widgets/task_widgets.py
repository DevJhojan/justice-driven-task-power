"""
Widgets relacionados con tareas.
"""
import flet as ft
from datetime import datetime
from app.data.models import Task, SubTask
from .utils import (
    get_theme_colors,
    is_desktop_platform,
    get_responsive_sizes,
    get_priority_colors,
    get_card_bgcolor
)


def _build_description_with_expand(
    title: str,
    description: str,
    sizes: dict,
    title_style: ft.TextStyle,
    description_color,
    secondary
) -> ft.Column:
    """
    Construye la descripción con efecto de desglose.
    Muestra solo las primeras 3 palabras y un botón "..." para expandir.
    
    Args:
        title: Título de la tarea.
        description: Descripción de la tarea.
        sizes: Tamaños responsive.
        title_style: Estilo del título.
        description_color: Color de la descripción.
        secondary: Color secundario.
    
    Returns:
        Column con el título y descripción con efecto de desglose.
    """
    column_controls = [
        ft.Text(
            title,
            size=sizes['title_size'],
            weight=ft.FontWeight.BOLD,
            style=title_style,
            expand=True,
            max_lines=3,
            overflow=ft.TextOverflow.ELLIPSIS,
            selectable=True
        )
    ]
    
    # Si hay descripción, agregar con efecto de desglose
    if description:
        words = description.split()
        description_expanded = [False]  # Usar lista para poder modificar desde el closure
        
        # Si tiene más de 3 palabras, mostrar solo las primeras 3
        if len(words) > 3:
            preview_text = " ".join(words[:3])
            full_text = description
            
            # Texto de descripción (inicialmente solo preview)
            description_text = ft.Text(
                preview_text,
                size=sizes['description_size'],
                color=description_color,
                style=title_style,
                selectable=True,
                expand=True
            )
            
            # Botón "..."
            expand_button = ft.TextButton(
                text="...",
                on_click=None,  # Se asignará después
                tooltip="Ver más",
                style=ft.ButtonStyle(
                    color=secondary,
                    text_style=ft.TextStyle(size=sizes['description_size'], weight=ft.FontWeight.BOLD),
                    padding=ft.padding.symmetric(horizontal=4, vertical=0)
                )
            )
            
            def toggle_description(e):
                """Alterna entre vista previa y descripción completa."""
                description_expanded[0] = not description_expanded[0]
                if description_expanded[0]:
                    description_text.value = full_text
                    expand_button.text = "Ver menos"
                    expand_button.tooltip = "Ver menos"
                else:
                    description_text.value = preview_text
                    expand_button.text = "..."
                    expand_button.tooltip = "Ver más"
                description_text.update()
                expand_button.update()
            
            expand_button.on_click = toggle_description
            
            # Fila con descripción y botón
            column_controls.append(
                ft.Row(
                    [
                        description_text,
                        expand_button
                    ],
                    spacing=4,
                    wrap=False,
                    vertical_alignment=ft.CrossAxisAlignment.START
                )
            )
        else:
            # Si tiene 3 palabras o menos, mostrar completa sin botón
            column_controls.append(
                ft.Text(
                    description,
                    size=sizes['description_size'],
                    color=description_color,
                    style=title_style,
                    selectable=True
                )
            )
    
    return ft.Column(
        column_controls,
        expand=True,
        spacing=6,
        tight=False
    )


def create_task_card(
    task: Task,
    on_toggle,
    on_edit,
    on_delete,
    on_toggle_subtask=None,
    on_add_subtask=None,
    on_delete_subtask=None,
    on_edit_subtask=None,
    page: ft.Page = None
) -> ft.Card:
    """
    Crea una tarjeta de tarea responsive.
    
    Args:
        task: Tarea a mostrar.
        on_toggle: Callback cuando se cambia el estado de completado.
        on_edit: Callback cuando se edita la tarea.
        on_delete: Callback cuando se elimina la tarea.
        on_toggle_subtask: Callback para alternar subtarea.
        on_add_subtask: Callback para agregar subtarea.
        on_delete_subtask: Callback para eliminar subtarea.
        on_edit_subtask: Callback para editar subtarea.
        page: Página de Flet para detectar el tema.
        
    Returns:
        Widget Card con la información de la tarea.
    """
    # Obtener colores y tamaños
    is_dark, primary, secondary, scheme = get_theme_colors(page)
    is_desktop = is_desktop_platform(page)
    sizes = get_responsive_sizes(is_desktop)
    priority_colors, priority_labels = get_priority_colors()
    
    # Colores adaptativos según el tema y matiz
    title_color = ft.Colors.GREY_400 if task.completed else (
        ft.Colors.WHITE if is_dark else primary
    )
    description_color = ft.Colors.GREY_500 if is_dark else ft.Colors.GREY_600
    
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
    
    # Construir lista de controles de la tarjeta
    card_controls = [
        ft.Row(
            [
                ft.IconButton(
                    icon=status_icon,
                    icon_color=status_color,
                    icon_size=sizes['icon_size'],
                    on_click=lambda e, task_obj=task: on_toggle(task_obj.id),
                    tooltip="Marcar como completada" if not task.completed else "Marcar como pendiente",
                    width=sizes['icon_size'] + 8,
                    height=sizes['icon_size'] + 8
                ),
                ft.Container(
                    content=_build_description_with_expand(
                        task.title,
                        task.description if task.description and task.description.strip() else "",
                        sizes,
                        title_style,
                        description_color,
                        secondary
                    ),
                    expand=True,
                    padding=0
                ),
            ],
            spacing=12 if is_desktop else 8,
            expand=True,
            wrap=False,
            vertical_alignment=ft.CrossAxisAlignment.START
        )
    ]
    
    # Agregar subtareas si existen con funcionalidad de desglose (expandir/colapsar)
    # Filtrar subtareas vacías (sin título o con título vacío)
    valid_subtasks = [st for st in task.subtasks if st.title and st.title.strip()] if task.subtasks else []
    if valid_subtasks and len(valid_subtasks) > 0:
        # Contenedor para las subtareas (inicialmente colapsado)
        subtasks_container = ft.Container(
            content=ft.Column(
                [],
                spacing=4,
                tight=True
            ),
            padding=ft.padding.only(left=40, top=4, bottom=4),
            visible=False  # Inicialmente oculto
        )
        
        # Estado de expansión
        expand_icon = ft.Icons.EXPAND_MORE
        collapse_icon = ft.Icons.EXPAND_LESS
        subtasks_expanded = [False]  # Usar lista para poder modificar desde el closure
        
        # Crear el botón primero
        expand_button = ft.IconButton(
            icon=expand_icon,
            icon_color=secondary,
            icon_size=18,
            tooltip="Mostrar subtareas",
            width=32,
            height=32
        )
        
        def toggle_subtasks_display(e):
            """Alterna la visualización de las subtareas."""
            subtasks_expanded[0] = not subtasks_expanded[0]
            subtasks_container.visible = subtasks_expanded[0]
            
            # Actualizar el icono del botón
            if subtasks_expanded[0]:
                expand_button.icon = collapse_icon
                expand_button.tooltip = "Ocultar subtareas"
            else:
                expand_button.icon = expand_icon
                expand_button.tooltip = "Mostrar subtareas"
            
            # Si se expande, construir las subtareas
            if subtasks_expanded[0] and len(subtasks_container.content.controls) == 0:
                subtasks_list = _build_subtasks_list(
                    valid_subtasks,
                    is_dark,
                    secondary,
                    on_toggle_subtask,
                    on_edit_subtask,
                    on_delete_subtask
                )
                subtasks_container.content.controls = subtasks_list
            
            subtasks_container.update()
            expand_button.update()
        
        # Asignar el handler después de definir la función
        expand_button.on_click = toggle_subtasks_display
        
        # Contador de subtareas (solo contar subtareas válidas)
        completed_count = sum(1 for st in valid_subtasks if st.completed)
        total_count = len(valid_subtasks)
        subtasks_text = f"{completed_count}/{total_count} subtareas"
        
        # Fila con botón de expandir y contador
        card_controls.append(
            ft.Row(
                [
                    expand_button,
                    ft.Text(
                        subtasks_text,
                        size=11 if is_desktop else 10,
                        color=secondary if completed_count == total_count else (ft.Colors.GREY_600 if is_dark else ft.Colors.GREY_500),
                        weight=ft.FontWeight.BOLD if completed_count == total_count else None
                    )
                ],
                spacing=4,
                alignment=ft.MainAxisAlignment.START
            )
        )
        
        # Contenedor de subtareas (inicialmente oculto)
        card_controls.append(subtasks_container)
        
        # Botón para agregar subtarea (solo visible cuando hay subtareas)
        if on_add_subtask:
            add_subtask_button = ft.Container(
                content=ft.TextButton(
                    icon=ft.Icons.ADD,
                    text="Agregar subtarea",
                    icon_color=secondary,
                    on_click=lambda e: on_add_subtask(task.id),
                    tooltip="Agregar subtarea"
                ),
                padding=ft.padding.only(left=40, top=4, bottom=4),
                visible=False  # Inicialmente oculto
            )
            
            # Actualizar la función toggle para mostrar/ocultar el botón de agregar
            original_toggle = toggle_subtasks_display
            def toggle_with_add_button(e):
                original_toggle(e)
                add_subtask_button.visible = subtasks_expanded[0]
                add_subtask_button.update()
            
            expand_button.on_click = toggle_with_add_button
            card_controls.append(add_subtask_button)
    else:
        # Si no hay subtareas, mostrar el botón de agregar directamente
        if on_add_subtask:
            card_controls.append(
                ft.Container(
                    content=ft.TextButton(
                        icon=ft.Icons.ADD,
                        text="Agregar subtarea",
                        icon_color=secondary,
                        on_click=lambda e: on_add_subtask(task.id),
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
                            icon_size=sizes['button_icon_size'],
                            on_click=lambda e, t=task: on_edit(t),
                            tooltip="Editar",
                            width=sizes['button_icon_size'] + 12 if is_desktop else sizes['button_icon_size'] + 8,
                            height=sizes['button_icon_size'] + 12 if is_desktop else sizes['button_icon_size'] + 8
                        ),
                        ft.IconButton(
                            icon=ft.Icons.DELETE,
                            icon_color=primary,
                            icon_size=sizes['button_icon_size'],
                            on_click=lambda e, task_id=task.id: on_delete(task_id),
                            tooltip="Eliminar",
                            width=sizes['button_icon_size'] + 12 if is_desktop else sizes['button_icon_size'] + 8,
                            height=sizes['button_icon_size'] + 12 if is_desktop else sizes['button_icon_size'] + 8
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
            padding=sizes['card_padding'],
            border_radius=sizes['card_border_radius'],
            bgcolor=get_card_bgcolor(is_dark),
        ),
        elevation=sizes['card_elevation'],
        margin=sizes['card_margin']
    )


def _build_subtasks_list(
    subtasks,
    is_dark: bool,
    secondary,
    on_toggle_subtask=None,
    on_edit_subtask=None,
    on_delete_subtask=None
):
    """
    Construye la lista de widgets de subtareas.
    
    Args:
        subtasks: Lista de subtareas.
        is_dark: Si el tema es oscuro.
        secondary: Color secundario.
        on_toggle_subtask: Callback para alternar subtarea.
        on_edit_subtask: Callback para editar subtarea.
        on_delete_subtask: Callback para eliminar subtarea.
    
    Returns:
        Lista de widgets de subtareas.
    """
    subtasks_list = []
    
    # Filtrar subtareas vacías (sin título o con título vacío)
    valid_subtasks = [st for st in subtasks if st.title and st.title.strip()]
    
    for subtask in valid_subtasks:
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
    
    return subtasks_list


def create_empty_state(page: ft.Page = None) -> ft.Container:
    """
    Crea un widget para mostrar cuando no hay tareas.
    
    Args:
        page: Página de Flet para detectar el tema.
    
    Returns:
        Container con mensaje de estado vacío.
    """
    is_dark, primary, secondary, scheme = get_theme_colors(page)
    
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
    is_dark, primary, secondary, scheme = get_theme_colors(page)
    
    # Color adaptativo para las etiquetas
    label_color = ft.Colors.GREY_400 if is_dark else ft.Colors.GREY_600
    
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
            bgcolor=get_card_bgcolor(is_dark),
        ),
        elevation=1,
        margin=ft.margin.only(bottom=8)
    )

