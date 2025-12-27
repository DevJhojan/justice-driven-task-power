"""
Módulo para la gestión de tareas (CRUD).
"""
import flet as ft
from typing import Optional
from app.data.models import Task
from app.services.task_service import TaskService
from app.ui.widgets import create_task_card
from .utils import is_desktop_platform, get_screen_width, PRIORITIES


def load_tasks_into_containers(
    page: ft.Page,
    task_service: TaskService,
    priority_containers: dict,
    priority_filters: dict,
    on_toggle: callable,
    on_edit: callable,
    on_delete: callable,
    on_toggle_subtask: callable,
    on_add_subtask: callable,
    on_delete_subtask: callable,
    on_edit_subtask: callable,
    view_mode: str = "lista_normal"
):
    """
    Carga las tareas desde la base de datos y las distribuye por prioridad.
    
    Args:
        page: Página de Flet.
        task_service: Servicio para gestionar tareas.
        priority_containers: Diccionario con contenedores por prioridad.
        priority_filters: Diccionario con filtros por prioridad.
        on_toggle: Callback para toggle de tarea.
        on_edit: Callback para editar tarea.
        on_delete: Callback para eliminar tarea.
        on_toggle_subtask: Callback para toggle de subtarea.
        on_add_subtask: Callback para agregar subtarea.
        on_delete_subtask: Callback para eliminar subtarea.
        on_edit_subtask: Callback para editar subtarea.
        view_mode: Modo de vista ('lista_normal', 'lista_4do', 'kanban').
    """
    # Cargar todas las tareas sin filtro global
    all_tasks = task_service.get_all_tasks(None)
    
    # Si está en modo lista_normal, cargar todas las tareas juntas en un solo contenedor
    if view_mode == "lista_normal":
        # Limpiar todos los contenedores de prioridad
        for priority in priority_containers:
            priority_containers[priority].controls.clear()
        
        # Usar el contenedor de urgent_important como contenedor único para todas las tareas
        all_tasks_container = priority_containers['urgent_important']
        
        # Renderizar todas las tareas juntas sin separación por prioridad
        if all_tasks:
            _render_lista_normal(
                all_tasks_container, all_tasks, page,
                on_toggle, on_edit, on_delete,
                on_toggle_subtask, on_add_subtask, on_delete_subtask, on_edit_subtask
            )
        else:
            # Mostrar mensaje de estado vacío
            all_tasks_container.controls.append(
                ft.Container(
                    content=ft.Text(
                        "No hay tareas",
                        size=14,
                        color=ft.Colors.GREY_500,
                        text_align=ft.TextAlign.CENTER
                    ),
                    padding=20,
                    alignment=ft.alignment.center
                )
            )
    else:
        # Modo Matriz de Eisenhower o Kanban: distribuir tareas por prioridad
        # Limpiar todos los contenedores de prioridad
        for priority in priority_containers:
            priority_containers[priority].controls.clear()
        
        # Distribuir tareas por prioridad y aplicar filtro de cada sección
        for priority in PRIORITIES:
            container = priority_containers[priority]
            filter_value = priority_filters[priority]
            
            # Filtrar tareas de esta prioridad
            priority_tasks = [t for t in all_tasks if t.priority == priority]
            
            # Aplicar filtro de completado si existe
            if filter_value is not None:
                priority_tasks = [t for t in priority_tasks if t.completed == filter_value]
            
            # Agregar tareas al contenedor según el modo de vista
            if not priority_tasks:
                # Mostrar estado vacío solo si hay filtro activo
                if filter_value is not None:
                    empty_text = "Completadas" if filter_value else "Pendientes"
                    container.controls.append(
                        ft.Container(
                            content=ft.Text(
                                f"No hay tareas {empty_text.lower()} en esta prioridad",
                                size=14,
                                color=ft.Colors.GREY_500,
                                text_align=ft.TextAlign.CENTER
                            ),
                            padding=20,
                            alignment=ft.alignment.center
                        )
                    )
            else:
                # Renderizar según el modo de vista seleccionado
                if view_mode == "lista_4do":
                    _render_lista_4do(
                        container, priority_tasks, page,
                        on_toggle, on_edit, on_delete,
                        on_toggle_subtask, on_add_subtask, on_delete_subtask, on_edit_subtask
                    )
                elif view_mode == "kanban":
                    _render_kanban(
                        container, priority_tasks, page,
                        on_toggle, on_edit, on_delete,
                        on_toggle_subtask, on_add_subtask, on_delete_subtask, on_edit_subtask
                    )
                else:
                    # Fallback a lista normal
                    _render_lista_normal(
                        container, priority_tasks, page,
                        on_toggle, on_edit, on_delete,
                        on_toggle_subtask, on_add_subtask, on_delete_subtask, on_edit_subtask
                    )
    
    page.update()


def _render_lista_normal(
    container: ft.Column,
    tasks: list,
    page: ft.Page,
    on_toggle: callable,
    on_edit: callable,
    on_delete: callable,
    on_toggle_subtask: callable,
    on_add_subtask: callable,
    on_delete_subtask: callable,
    on_edit_subtask: callable
):
    """Renderiza las tareas en vista de lista normal (columna simple)."""
    is_desktop = is_desktop_platform(page)
    
    for task in tasks:
        card = create_task_card(
            task,
            on_toggle=on_toggle,
            on_edit=on_edit,
            on_delete=on_delete,
            on_toggle_subtask=on_toggle_subtask,
            on_add_subtask=on_add_subtask,
            on_delete_subtask=on_delete_subtask,
            on_edit_subtask=on_edit_subtask,
            page=page
        )
        container.controls.append(
            ft.Container(
                content=card,
                expand=True,
                width=None,
                margin=ft.margin.only(bottom=12)
            )
        )


def _render_lista_4do(
    container: ft.Column,
    tasks: list,
    page: ft.Page,
    on_toggle: callable,
    on_edit: callable,
    on_delete: callable,
    on_toggle_subtask: callable,
    on_add_subtask: callable,
    on_delete_subtask: callable,
    on_edit_subtask: callable
):
    """Renderiza las tareas en vista de lista 4 do (grid de 4 columnas)."""
    is_desktop = is_desktop_platform(page)
    screen_width = get_screen_width(page)
    
    # Determinar número de columnas según el ancho de pantalla
    if is_desktop and isinstance(screen_width, (int, float)) and screen_width > 1200:
        columns_per_row = 4
    elif is_desktop and isinstance(screen_width, (int, float)) and screen_width > 800:
        columns_per_row = 3
    elif isinstance(screen_width, (int, float)) and screen_width > 600:
        columns_per_row = 2
    else:
        columns_per_row = 1  # Móvil: una columna
    
    # Agrupar tareas en filas
    for i in range(0, len(tasks), columns_per_row):
        row_tasks = tasks[i:i + columns_per_row]
        row_cards = []
        
        for task in row_tasks:
            card = create_task_card(
                task,
                on_toggle=on_toggle,
                on_edit=on_edit,
                on_delete=on_delete,
                on_toggle_subtask=on_toggle_subtask,
                on_add_subtask=on_add_subtask,
                on_delete_subtask=on_delete_subtask,
                on_edit_subtask=on_edit_subtask,
                page=page
            )
            row_cards.append(
                ft.Container(
                    content=card,
                    expand=True,
                    margin=ft.margin.only(right=8)
                )
            )
        
        # Agregar fila al contenedor
        container.controls.append(
            ft.Row(
                row_cards,
                spacing=8,
                wrap=False,
                expand=True,
                scroll=ft.ScrollMode.AUTO if columns_per_row > 1 and not is_desktop else ft.ScrollMode.HIDDEN
            )
        )


def _render_kanban(
    container: ft.Column,
    tasks: list,
    page: ft.Page,
    on_toggle: callable,
    on_edit: callable,
    on_delete: callable,
    on_toggle_subtask: callable,
    on_add_subtask: callable,
    on_delete_subtask: callable,
    on_edit_subtask: callable
):
    """Renderiza las tareas en vista Kanban (columnas por estado)."""
    is_dark = page.theme_mode == ft.ThemeMode.DARK
    is_desktop = is_desktop_platform(page)
    screen_width = get_screen_width(page)
    
    # Separar tareas por estado
    pending_tasks = [t for t in tasks if not t.completed]
    completed_tasks = [t for t in tasks if t.completed]
    
    # Colores para las columnas
    bg_color = ft.Colors.BLACK87 if is_dark else ft.Colors.GREY_100
    border_color = ft.Colors.GREY_700 if is_dark else ft.Colors.GREY_300
    
    # Crear columnas Kanban
    kanban_columns = []
    
    # Columna de Pendientes
    pending_controls = [
        ft.Container(
            content=ft.Text(
                "Pendientes",
                size=16,
                weight=ft.FontWeight.BOLD,
                color=ft.Colors.BLUE if not is_dark else ft.Colors.BLUE_300
            ),
            padding=12,
            bgcolor=ft.Colors.BLUE_50 if not is_dark else ft.Colors.BLUE_900,
            border=ft.border.only(bottom=ft.BorderSide(2, ft.Colors.BLUE))
        )
    ]
    
    if pending_tasks:
        pending_controls.extend([
            ft.Container(
                content=create_task_card(
                    task,
                    on_toggle=on_toggle,
                    on_edit=on_edit,
                    on_delete=on_delete,
                    on_toggle_subtask=on_toggle_subtask,
                    on_add_subtask=on_add_subtask,
                    on_delete_subtask=on_delete_subtask,
                    on_edit_subtask=on_edit_subtask,
                    page=page
                ),
                margin=ft.margin.only(bottom=8)
            )
            for task in pending_tasks
        ])
    else:
        pending_controls.append(
            ft.Container(
                content=ft.Text(
                    "No hay tareas pendientes",
                    size=14,
                    color=ft.Colors.GREY_500,
                    text_align=ft.TextAlign.CENTER
                ),
                padding=20,
                alignment=ft.alignment.center
            )
        )
    
    pending_column = ft.Column(
        pending_controls,
        spacing=0,
        scroll=ft.ScrollMode.AUTO,
        expand=True
    )
    
    # Columna de Completadas
    completed_controls = [
        ft.Container(
            content=ft.Text(
                "Completadas",
                size=16,
                weight=ft.FontWeight.BOLD,
                color=ft.Colors.GREEN if not is_dark else ft.Colors.GREEN_300
            ),
            padding=12,
            bgcolor=ft.Colors.GREEN_50 if not is_dark else ft.Colors.GREEN_900,
            border=ft.border.only(bottom=ft.BorderSide(2, ft.Colors.GREEN))
        )
    ]
    
    if completed_tasks:
        completed_controls.extend([
            ft.Container(
                content=create_task_card(
                    task,
                    on_toggle=on_toggle,
                    on_edit=on_edit,
                    on_delete=on_delete,
                    on_toggle_subtask=on_toggle_subtask,
                    on_add_subtask=on_add_subtask,
                    on_delete_subtask=on_delete_subtask,
                    on_edit_subtask=on_edit_subtask,
                    page=page
                ),
                margin=ft.margin.only(bottom=8)
            )
            for task in completed_tasks
        ])
    else:
        completed_controls.append(
            ft.Container(
                content=ft.Text(
                    "No hay tareas completadas",
                    size=14,
                    color=ft.Colors.GREY_500,
                    text_align=ft.TextAlign.CENTER
                ),
                padding=20,
                alignment=ft.alignment.center
            )
        )
    
    completed_column = ft.Column(
        completed_controls,
        spacing=0,
        scroll=ft.ScrollMode.AUTO,
        expand=True
    )
    
    # Agregar columnas al contenedor Kanban
    kanban_row = ft.Row(
        [
            ft.Container(
                content=pending_column,
                expand=True,
                bgcolor=bg_color,
                border=ft.border.all(1, border_color),
                border_radius=8,
                padding=8,
                margin=ft.margin.only(right=8)
            ),
            ft.Container(
                content=completed_column,
                expand=True,
                bgcolor=bg_color,
                border=ft.border.all(1, border_color),
                border_radius=8,
                padding=8
            )
        ],
        spacing=8,
        scroll=ft.ScrollMode.AUTO if not is_desktop else ft.ScrollMode.HIDDEN,
        expand=True
    )
    
    container.controls.append(kanban_row)


def toggle_task(task_service: TaskService, task_id: int):
    """Cambia el estado de completado de una tarea."""
    task_service.toggle_task_complete(task_id)


def delete_task(page: ft.Page, task_service: TaskService, task_id: int) -> bool:
    """
    Elimina una tarea.
    
    Args:
        page: Página de Flet.
        task_service: Servicio para gestionar tareas.
        task_id: ID de la tarea a eliminar.
    
    Returns:
        True si se eliminó correctamente, False en caso contrario.
    """
    if task_id is None:
        return False
    
    try:
        deleted = task_service.delete_task(int(task_id))
        if deleted:
            page.snack_bar = ft.SnackBar(
                content=ft.Text("Tarea eliminada correctamente"),
                bgcolor=ft.Colors.RED_700
            )
            page.snack_bar.open = True
        else:
            page.snack_bar = ft.SnackBar(
                content=ft.Text("No se pudo eliminar la tarea"),
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


def save_task(task_service: TaskService, *args):
    """
    Guarda una tarea (crear o actualizar).
    
    Args:
        task_service: Servicio para gestionar tareas.
        *args: Si el primer argumento es un Task, es actualización. 
               Si no, son (title, description, priority) para crear.
    """
    # Si el primer argumento es un objeto Task, es una actualización
    if args and isinstance(args[0], Task):
        # Actualizar tarea existente
        task = args[0]
        task_service.update_task(task)
    else:
        # Crear nueva tarea
        title, description, priority = args
        task_service.create_task(title, description, priority)

