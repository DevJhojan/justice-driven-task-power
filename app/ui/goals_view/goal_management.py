"""
Módulo para la gestión de objetivos (CRUD).
"""
import flet as ft
from typing import Optional
from app.data.models import Goal
from app.services.goal_service import GoalService
from app.ui.widgets.task_widgets import get_theme_colors, get_card_bgcolor


def create_goal_card(
    goal: Goal,
    on_toggle: callable,
    on_edit: callable,
    on_delete: callable,
    page: ft.Page = None
) -> ft.Card:
    """
    Crea una tarjeta de objetivo.
    
    Args:
        goal: Objetivo a mostrar.
        on_toggle: Callback cuando se cambia el estado de completado.
        on_edit: Callback cuando se edita el objetivo.
        on_delete: Callback cuando se elimina el objetivo.
        page: Página de Flet para detectar el tema.
        
    Returns:
        Widget Card con la información del objetivo.
    """
    is_dark, primary, secondary, scheme = get_theme_colors(page)
    bgcolor = get_card_bgcolor(is_dark)
    
    # Colores adaptativos según el tema
    title_color = ft.Colors.GREY_400 if goal.completed else (
        ft.Colors.WHITE if is_dark else primary
    )
    description_color = ft.Colors.GREY_500 if is_dark else ft.Colors.GREY_600
    
    # Etiquetas de frecuencia
    frequency_labels = {
        'daily': 'Diario',
        'weekly': 'Semanal',
        'monthly': 'Mensual',
        'quarterly': 'Trimestral',
        'semiannual': 'Semestral',
        'annual': 'Anual'
    }
    frequency_label = frequency_labels.get(goal.frequency, goal.frequency)
    
    # Icono de estado
    status_icon = ft.Icons.CHECK_CIRCLE if goal.completed else ft.Icons.RADIO_BUTTON_UNCHECKED
    status_color = secondary if goal.completed else ft.Colors.GREY_600
    
    # Estilo del texto según estado
    title_style = ft.TextStyle(
        decoration=ft.TextDecoration.LINE_THROUGH if goal.completed else None,
        color=title_color
    )
    
    # Información de fecha objetivo
    target_date_text = ""
    if goal.target_date:
        target_date_text = goal.target_date.strftime("%d/%m/%Y")
    
    # Construir controles de la tarjeta
    card_controls = [
        ft.Row(
            [
                ft.IconButton(
                    icon=status_icon,
                    icon_color=status_color,
                    icon_size=24,
                    on_click=lambda e, goal_obj=goal: on_toggle(goal_obj.id),
                    tooltip="Marcar como completado" if not goal.completed else "Marcar como pendiente"
                ),
                ft.Column(
                    [
                        ft.Text(
                            goal.title,
                            size=18,
                            weight=ft.FontWeight.BOLD,
                            style=title_style,
                            expand=True
                        ),
                        ft.Text(
                            goal.description if goal.description else "Sin descripción",
                            size=14,
                            color=description_color,
                            style=title_style if goal.completed else None,
                            max_lines=3,
                            overflow=ft.TextOverflow.ELLIPSIS
                        ),
                    ],
                    expand=True,
                    spacing=4
                ),
                ft.PopupMenuButton(
                    icon=ft.Icons.MORE_VERT,
                    items=[
                        ft.PopupMenuItem(
                            text="Editar",
                            icon=ft.Icons.EDIT,
                            on_click=lambda e, goal_obj=goal: on_edit(goal_obj)
                        ),
                        ft.PopupMenuItem(
                            text="Eliminar",
                            icon=ft.Icons.DELETE,
                            on_click=lambda e, goal_obj=goal: on_delete(goal_obj.id)
                        )
                    ]
                )
            ],
            spacing=8,
            expand=True,
            vertical_alignment=ft.CrossAxisAlignment.START
        ),
        ft.Divider(height=1),
        ft.Row(
            [
                ft.Container(
                    content=ft.Row(
                        [
                            ft.Icon(ft.Icons.CALENDAR_TODAY, size=16, color=secondary),
                            ft.Text(
                                frequency_label,
                                size=12,
                                color=secondary,
                                weight=ft.FontWeight.BOLD
                            )
                        ],
                        spacing=4
                    ),
                    padding=8,
                    bgcolor=ft.Colors.BLUE_50 if not is_dark else ft.Colors.BLUE_900,
                    border_radius=8
                ),
                target_date_text and ft.Container(
                    content=ft.Row(
                        [
                            ft.Icon(ft.Icons.TARGET, size=16, color=primary),
                            ft.Text(
                                target_date_text,
                                size=12,
                                color=primary
                            )
                        ],
                        spacing=4
                    ),
                    padding=8,
                    bgcolor=ft.Colors.ORANGE_50 if not is_dark else ft.Colors.ORANGE_900,
                    border_radius=8
                ) or ft.Container()
            ],
            spacing=8
        )
    ]
    
    return ft.Card(
        content=ft.Container(
            content=ft.Column(card_controls, spacing=12),
            padding=16,
            bgcolor=bgcolor
        ),
        elevation=2
    )


def load_goals_into_container(
    page: ft.Page,
    goal_service: GoalService,
    goals_container: ft.Column,
    current_filter: Optional[str],
    on_toggle: callable,
    on_edit: callable,
    on_delete: callable
):
    """
    Carga los objetivos desde la base de datos y los agrega al contenedor.
    
    Args:
        page: Página de Flet.
        goal_service: Servicio para gestionar objetivos.
        goals_container: Contenedor donde se agregarán los objetivos.
        current_filter: Filtro de frecuencia actual (None para todos).
        on_toggle: Callback para toggle de objetivo.
        on_edit: Callback para editar objetivo.
        on_delete: Callback para eliminar objetivo.
    """
    # Cargar objetivos según el filtro
    goals = goal_service.get_all_goals(filter_frequency=current_filter)
    
    # Limpiar contenedor
    goals_container.controls.clear()
    
    if not goals:
        frequency_labels = {
            None: "objetivos",
            'daily': 'objetivos diarios',
            'weekly': 'objetivos semanales',
            'monthly': 'objetivos mensuales',
            'quarterly': 'objetivos trimestrales',
            'semiannual': 'objetivos semestrales',
            'annual': 'objetivos anuales'
        }
        label = frequency_labels.get(current_filter, "objetivos")
        goals_container.controls.append(
            ft.Container(
                content=ft.Text(
                    f"No hay {label}",
                    size=16,
                    color=ft.Colors.GREY_500,
                    text_align=ft.TextAlign.CENTER
                ),
                padding=40,
                alignment=ft.alignment.center
            )
        )
    else:
        for goal in goals:
            card = create_goal_card(
                goal,
                on_toggle=on_toggle,
                on_edit=on_edit,
                on_delete=on_delete,
                page=page
            )
            goals_container.controls.append(
                ft.Container(
                    content=card,
                    margin=ft.margin.only(bottom=12)
                )
            )
    
    page.update()


def toggle_goal(goal_service: GoalService, goal_id: int):
    """Cambia el estado de completado de un objetivo."""
    goal_service.toggle_goal_complete(goal_id)


def delete_goal(page: ft.Page, goal_service: GoalService, goal_id: int) -> bool:
    """
    Elimina un objetivo.
    
    Args:
        page: Página de Flet.
        goal_service: Servicio para gestionar objetivos.
        goal_id: ID del objetivo a eliminar.
    
    Returns:
        True si se eliminó correctamente, False en caso contrario.
    """
    if goal_id is None:
        return False
    
    try:
        deleted = goal_service.delete_goal(int(goal_id))
        if deleted:
            page.snack_bar = ft.SnackBar(
                content=ft.Text("Objetivo eliminado correctamente"),
                bgcolor=ft.Colors.RED_700
            )
            page.snack_bar.open = True
        else:
            page.snack_bar = ft.SnackBar(
                content=ft.Text("No se pudo eliminar el objetivo"),
                bgcolor=ft.Colors.RED
            )
            page.snack_bar.open = True
        page.update()
        return deleted
    except Exception as ex:
        page.snack_bar = ft.SnackBar(
            content=ft.Text(f"Error: {str(ex)}"),
            bgcolor=ft.Colors.RED
        )
        page.snack_bar.open = True
        page.update()
        return False


def save_goal(goal_service: GoalService, *args):
    """
    Guarda un objetivo (crear o actualizar).
    
    Args:
        goal_service: Servicio para gestionar objetivos.
        *args: Si el primer argumento es un Goal, es actualización. 
               Si no, son (title, description, frequency, target_date) para crear.
    """
    # Si el primer argumento es un objeto Goal, es una actualización
    if args and isinstance(args[0], Goal):
        goal = args[0]
        goal_service.update_goal(goal)
    else:
        title, description, frequency, target_date = args
        goal_service.create_goal(title, description, frequency, target_date)

