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
    on_edit_subtask: callable
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
    """
    # Cargar todas las tareas sin filtro global
    all_tasks = task_service.get_all_tasks(None)
    
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
        
        # Agregar tareas al contenedor
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
            # Detectar ancho de pantalla para decidir layout
            is_desktop = is_desktop_platform(page)
            screen_width = get_screen_width(page)
            use_grid = is_desktop and isinstance(screen_width, (int, float)) and screen_width > 800 and len(priority_tasks) > 1
            
            if use_grid:
                # En escritorio con suficiente ancho, mostrar en grid de 2 columnas
                tasks_per_row = 2
                for i in range(0, len(priority_tasks), tasks_per_row):
                    row_tasks = priority_tasks[i:i + tasks_per_row]
                    row_cards = []
                    for idx, task in enumerate(row_tasks):
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
                        # Contenedor flexible que se adapta al ancho disponible
                        row_cards.append(
                            ft.Container(
                                content=card,
                                expand=True,
                                margin=ft.margin.only(right=12 if idx < len(row_tasks) - 1 else 0)
                            )
                        )
                    
                    # Crear fila con las tarjetas - adaptable
                    container.controls.append(
                        ft.Row(
                            row_cards,
                            spacing=12,
                            wrap=False,
                            expand=True,
                            scroll=ft.ScrollMode.AUTO if not is_desktop else ft.ScrollMode.HIDDEN
                        )
                    )
            else:
                # En móvil, tablet pequeña o pantallas estrechas, mostrar en columna simple
                for task in priority_tasks:
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
                    # Asegurar que la tarjeta use todo el ancho disponible
                    container.controls.append(
                        ft.Container(
                            content=card,
                            expand=True,
                            width=None
                        )
                    )
    
    page.update()


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

