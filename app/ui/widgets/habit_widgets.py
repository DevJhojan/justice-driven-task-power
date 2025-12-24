"""
Widgets relacionados con hábitos.
"""
import flet as ft
from datetime import date
from .utils import get_theme_colors, get_card_bgcolor


def create_habit_card(
    habit,
    metrics: dict,
    on_toggle_completion,
    on_edit,
    on_delete,
    on_view_details,
    page: ft.Page = None
) -> ft.Card:
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
    is_dark, primary, secondary, scheme = get_theme_colors(page)
    
    # Colores adaptativos según el tema
    title_color = ft.Colors.WHITE if is_dark else primary
    description_color = ft.Colors.GREY_500 if is_dark else ft.Colors.GREY_600
    
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
                            icon=ft.Icons.ANALYTICS,
                            icon_color=secondary,
                            icon_size=20,
                            on_click=lambda e, h=habit: on_view_details(h),
                            tooltip="Ver métricas"
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
            bgcolor=get_card_bgcolor(is_dark),
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
    is_dark, primary, secondary, scheme = get_theme_colors(page)
    
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
            bgcolor=get_card_bgcolor(is_dark),
        ),
        elevation=1,
        margin=ft.margin.only(bottom=8)
    )

