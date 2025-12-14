"""
Widgets reutilizables para la interfaz de usuario.
"""
import flet as ft
from app.data.models import Task


def create_task_card(task: Task, on_toggle, on_edit, on_delete, page: ft.Page = None) -> ft.Card:
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
    
    # Color según prioridad
    priority_colors = {
        'high': ft.Colors.RED_300,
        'medium': ft.Colors.ORANGE_300,
        'low': ft.Colors.GREEN_300
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
    status_color = ft.Colors.GREEN if task.completed else ft.Colors.GREY
    
    # Estilo del texto según estado
    title_style = ft.TextStyle(
        decoration=ft.TextDecoration.LINE_THROUGH if task.completed else None,
        color=title_color
    )
    
    return ft.Card(
        content=ft.Container(
            content=ft.Column(
                [
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
                    ),
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
                                        icon_color=ft.Colors.BLUE,
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
                ],
                spacing=8,
                tight=True
            ),
            padding=12,
            border_radius=8,
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
    
    # Colores adaptativos
    icon_color = ft.Colors.GREY_500 if is_dark else ft.Colors.GREY_400
    text_color = ft.Colors.GREY_400 if is_dark else ft.Colors.GREY_600
    subtitle_color = ft.Colors.GREY_500 if is_dark else ft.Colors.GREY_500
    
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
                                color=ft.Colors.BLUE
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
                                color=ft.Colors.GREEN
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
                                color=ft.Colors.ORANGE
                            ),
                            ft.Text("Pendientes", size=12, color=label_color)
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        expand=True
                    )
                ],
                alignment=ft.MainAxisAlignment.SPACE_EVENLY
            ),
            padding=16
        ),
        elevation=1,
        margin=ft.margin.only(bottom=8)
    )

