"""
Módulo para la navegación y construcción de formularios.
"""
import flet as ft
from datetime import datetime
from typing import Optional
from app.data.models import Task, SubTask
from app.ui.task_form import TaskForm
from app.services.task_service import TaskService
from .subtask_management import save_subtask


def navigate_to_task_form(
    page: ft.Page,
    editing_task: Optional[Task],
    on_save: callable,
    on_go_back: callable
):
    """
    Navega a la vista del formulario de tarea.
    
    Args:
        page: Página de Flet.
        editing_task: Tarea a editar (None si es nueva).
        on_save: Callback cuando se guarda la tarea.
        on_go_back: Callback para volver.
    """
    title = "Editar Tarea" if editing_task else "Nueva Tarea"
    
    # Crear el formulario
    form = TaskForm(
        on_save=on_save,
        on_cancel=on_go_back,
        task=editing_task
    )
    
    # Detectar el tema actual
    is_dark = page.theme_mode == ft.ThemeMode.DARK
    bgcolor = ft.Colors.BLACK if is_dark else ft.Colors.GREY_50
    
    # Crear la barra de título con botón de volver
    back_button = ft.IconButton(
        icon=ft.Icons.ARROW_BACK,
        on_click=lambda e: on_go_back(),
        icon_color=ft.Colors.RED_400,
        tooltip="Volver"
    )
    
    title_bar = ft.Container(
        content=ft.Row(
            [
                back_button,
                ft.Text(
                    title,
                    size=24,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.RED_400,
                    expand=True
                )
            ],
            alignment=ft.MainAxisAlignment.START,
            vertical_alignment=ft.CrossAxisAlignment.CENTER
        ),
        padding=ft.padding.symmetric(vertical=16, horizontal=20),
        bgcolor=ft.Colors.BLACK87 if is_dark else ft.Colors.RED_50
    )
    
    # Construir la vista del formulario
    form_view = ft.View(
        route="/form",
        controls=[
            title_bar,
            ft.Container(
                content=form.build(),
                expand=True,
                padding=20
            )
        ],
        bgcolor=bgcolor
    )
    
    # Agregar la vista y navegar a ella
    page.views.append(form_view)
    page.go("/form")


def navigate_to_subtask_form(
    page: ft.Page,
    task_service: TaskService,
    editing_subtask: Optional[SubTask],
    editing_subtask_task_id: Optional[int],
    on_go_back: callable,
    on_save_complete: callable
):
    """
    Navega a la vista del formulario de subtarea.
    
    Args:
        page: Página de Flet.
        task_service: Servicio para gestionar tareas.
        editing_subtask: Subtarea a editar (None si es nueva).
        editing_subtask_task_id: ID de la tarea padre.
        on_go_back: Callback para volver.
        on_save_complete: Callback cuando se guarda exitosamente.
    """
    # Determinar si es edición o creación
    is_editing = editing_subtask is not None
    
    # Crear campos del formulario con valores iniciales si es edición
    subtask_title_field = ft.TextField(
        label="Título de la subtarea",
        hint_text="Ingresa el título de la subtarea",
        autofocus=True,
        expand=True,
        value=editing_subtask.title if is_editing else ""
    )
    
    subtask_description_field = ft.TextField(
        label="Descripción",
        hint_text="Ingresa una descripción (opcional)",
        multiline=True,
        min_lines=3,
        max_lines=5,
        expand=True,
        value=editing_subtask.description if is_editing and editing_subtask.description else ""
    )
    
    # Formatear fecha límite si existe
    deadline_value = ""
    if is_editing and editing_subtask.deadline:
        try:
            deadline_value = editing_subtask.deadline.strftime("%Y-%m-%d %H:%M")
        except:
            deadline_value = ""
    
    subtask_deadline_field = ft.TextField(
        label="Fecha límite",
        hint_text="YYYY-MM-DD HH:MM (opcional)",
        expand=True,
        helper_text="Formato: 2024-12-31 23:59",
        value=deadline_value
    )
    
    # Detectar el tema actual
    is_dark = page.theme_mode == ft.ThemeMode.DARK
    bgcolor = ft.Colors.BLACK if is_dark else ft.Colors.GREY_50
    title_bar_bgcolor = ft.Colors.BLACK87 if is_dark else ft.Colors.RED_50
    
    def save_subtask_handler(e):
        title = subtask_title_field.value
        description = subtask_description_field.value or ""
        deadline_str = subtask_deadline_field.value or ""
        
        if not title or not title.strip():
            subtask_title_field.error_text = "El título es obligatorio"
            subtask_title_field.update()
            return
        
        # Validar y parsear fecha límite
        deadline = None
        if deadline_str.strip():
            try:
                # Intentar parsear diferentes formatos
                formats = [
                    "%Y-%m-%d %H:%M",
                    "%Y-%m-%d",
                    "%d/%m/%Y %H:%M",
                    "%d/%m/%Y"
                ]
                parsed = False
                for fmt in formats:
                    try:
                        deadline = datetime.strptime(deadline_str.strip(), fmt)
                        parsed = True
                        break
                    except ValueError:
                        continue
                
                if not parsed:
                    subtask_deadline_field.error_text = "Formato inválido. Use YYYY-MM-DD HH:MM"
                    subtask_deadline_field.update()
                    return
            except Exception as ex:
                subtask_deadline_field.error_text = f"Error al parsear fecha: {str(ex)}"
                subtask_deadline_field.update()
                return
        
        # Guardar usando el módulo de subtareas
        success = save_subtask(
            page,
            task_service,
            is_editing,
            editing_subtask,
            editing_subtask_task_id,
            title,
            description,
            deadline_str
        )
        
        if success:
            on_go_back()
            on_save_complete()
    
    # Crear la barra de título con botón de volver
    back_button = ft.IconButton(
        icon=ft.Icons.ARROW_BACK,
        on_click=lambda e: on_go_back(),
        icon_color=ft.Colors.RED_400,
        tooltip="Volver"
    )
    
    title_bar = ft.Container(
        content=ft.Row(
            [
                back_button,
                ft.Text(
                    "Editar Subtarea" if is_editing else "Nueva Subtarea",
                    size=24,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.RED_400,
                    expand=True
                )
            ],
            alignment=ft.MainAxisAlignment.START,
            vertical_alignment=ft.CrossAxisAlignment.CENTER
        ),
        padding=ft.padding.symmetric(vertical=16, horizontal=20),
        bgcolor=title_bar_bgcolor
    )
    
    # Botones de acción
    save_button = ft.ElevatedButton(
        text="Guardar",
        icon=ft.Icons.SAVE,
        on_click=save_subtask_handler,
        color=ft.Colors.WHITE,
        bgcolor=ft.Colors.RED_700,
        expand=True
    )
    
    cancel_button = ft.OutlinedButton(
        text="Cancelar",
        icon=ft.Icons.CANCEL,
        on_click=lambda e: on_go_back(),
        expand=True
    )
    
    # Construir la vista del formulario
    form_view = ft.View(
        route="/subtask-form",
        controls=[
            title_bar,
            ft.Container(
                content=ft.Column(
                    [
                        subtask_title_field,
                        subtask_description_field,
                        subtask_deadline_field,
                        ft.Row(
                            [
                                save_button,
                                cancel_button
                            ],
                            spacing=8,
                            alignment=ft.MainAxisAlignment.END
                        )
                    ],
                    spacing=16,
                    expand=True,
                    scroll=ft.ScrollMode.AUTO
                ),
                expand=True,
                padding=20
            )
        ],
        bgcolor=bgcolor
    )
    
    # Agregar la vista y navegar a ella
    page.views.append(form_view)
    page.go("/subtask-form")

