"""
Vista principal de tareas.
"""
import flet as ft
from typing import Optional

from app.data.models import Task
from app.services.task_service import TaskService
from app.ui.tasks.form import TaskForm


class TasksView:
    """Vista para gestión de tareas."""
    
    def __init__(self, page: ft.Page, task_service: TaskService, points_service=None):
        """
        Inicializa la vista de tareas.
        
        Args:
            page: Página de Flet.
            task_service: Servicio de tareas.
            points_service: Servicio de puntos (opcional).
        """
        self.page = page
        self.task_service = task_service
        self.points_service = points_service
        self.tasks_container = None
    
    def build_ui(self) -> ft.Container:
        """
        Construye la interfaz de usuario de tareas.
        
        Returns:
            Container con la vista de tareas.
        """
        # Contenedor para las tareas
        self.tasks_container = ft.Column(
            [],
            spacing=8,
            scroll=ft.ScrollMode.AUTO,
            expand=True
        )
        
        # Barra de título
        is_dark = self.page.theme_mode == ft.ThemeMode.DARK
        title_color = ft.Colors.RED_700 if not is_dark else ft.Colors.RED_500
        btn_color = ft.Colors.RED_700 if not is_dark else ft.Colors.RED_600
        
        title_bar = ft.Container(
            content=ft.Row(
                [
                    ft.Text(
                        "📋 Mis Tareas",
                        size=24,
                        weight=ft.FontWeight.BOLD,
                        color=title_color
                    ),
                    ft.IconButton(
                        icon=ft.Icons.ADD,
                        on_click=self._open_task_form,
                        tooltip="Agregar tarea",
                        icon_color=btn_color
                    )
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN
            ),
            padding=16,
            bgcolor=ft.Colors.SURFACE
        )
        
        # Cargar tareas
        self._load_tasks()
        
        # Vista principal
        return ft.Container(
            content=ft.Column(
                [
                    title_bar,
                    ft.Container(
                        content=self.tasks_container,
                        padding=16,
                        expand=True
                    )
                ],
                spacing=0,
                expand=True
            ),
            expand=True
        )
    
    def _load_tasks(self):
        """Carga las tareas desde el servicio."""
        if self.tasks_container is None:
            return
        
        tasks = self.task_service.get_all_tasks()
        self.tasks_container.controls.clear()
        
        if not tasks:
            self.tasks_container.controls.append(
                ft.Container(
                    content=ft.Text(
                        "No hay tareas. ¡Crea una nueva!",
                        size=16,
                        text_align=ft.TextAlign.CENTER
                    ),
                    alignment=ft.alignment.center,
                    padding=32
                )
            )
        else:
            for task in tasks:
                self.tasks_container.controls.append(
                    self._build_task_card(task)
                )
        
        if self.page:
            self.page.update()
    
    def _build_task_card(self, task: Task) -> ft.Container:
        """
        Construye una tarjeta para una tarea.
        
        Args:
            task: Tarea a mostrar.
        
        Returns:
            Container con la tarjeta de la tarea.
        """
        # Color según el estado
        bg_color = ft.Colors.GREEN_100 if task.status == "completada" else ft.Colors.WHITE
        if self.page.theme_mode == ft.ThemeMode.DARK:
            bg_color = ft.Colors.GREEN_900 if task.status == "completada" else ft.Colors.SURFACE
        
        # Checkbox para marcar como completada
        checkbox = ft.Checkbox(
            value=task.status == "completada",
            on_change=lambda e, t=task: self._toggle_task_status(t)
        )
        
        # Botones de acción
        is_dark = self.page.theme_mode == ft.ThemeMode.DARK
        btn_color = ft.Colors.RED_700 if not is_dark else ft.Colors.RED_500
        
        edit_button = ft.IconButton(
            icon=ft.Icons.EDIT,
            on_click=lambda e, t=task: self._open_task_form(e, t),
            tooltip="Editar",
            icon_color=btn_color
        )
        
        delete_button = ft.IconButton(
            icon=ft.Icons.DELETE,
            on_click=lambda e, t=task: self._delete_task(t),
            tooltip="Eliminar",
            icon_color=ft.Colors.RED
        )
        
        # Fecha de vencimiento si existe
        due_date_text = ""
        if task.due_date:
            due_date_text = f"📅 {task.due_date.strftime('%d/%m/%Y')}"
        
        # Obtener subtareas
        subtasks = self.task_service.get_subtasks(task.id) if task.id else []
        
        # Construir lista de subtareas
        subtasks_content = []
        if subtasks:
            for subtask in subtasks:
                subtask_checkbox = ft.Checkbox(
                    value=subtask.completed,
                    on_change=lambda e, s=subtask: self._toggle_subtask(s),
                    label=subtask.title,
                    data=subtask
                )
                subtasks_content.append(subtask_checkbox)
        
        # Contenido de la tarjeta
        content_items = [
            ft.Row(
                [
                    checkbox,
                    ft.Column(
                        [
                            ft.Text(
                                task.title,
                                size=16,
                                weight=ft.FontWeight.BOLD,
                                expand=True,
                                color=ft.Colors.RED_800 if self.page.theme_mode == ft.ThemeMode.LIGHT else ft.Colors.RED_400
                            ),
                            ft.Text(
                                task.description or "",
                                size=12,
                                color=ft.Colors.GREY,
                                visible=bool(task.description)
                            ),
                            ft.Text(
                                due_date_text,
                                size=11,
                                color=ft.Colors.GREY_700,
                                visible=bool(task.due_date)
                            )
                        ],
                        spacing=4,
                        expand=True
                    ),
                    edit_button,
                    delete_button
                ],
                spacing=8,
                vertical_alignment=ft.CrossAxisAlignment.START
            )
        ]
        
        # Agregar subtareas si existen
        if subtasks_content:
            content_items.append(
                ft.Container(
                    content=ft.Column(
                        subtasks_content,
                        spacing=4
                    ),
                    padding=ft.padding.only(left=32, top=8),
                    border=ft.border.only(left=ft.border.BorderSide(2, ft.Colors.GREY_400))
                )
            )
        
        content = ft.Column(content_items, spacing=4)
        
        return ft.Container(
            content=content,
            padding=16,
            bgcolor=bg_color,
            border_radius=8,
            border=ft.border.all(1, ft.Colors.OUTLINE)
        )
    
    def _toggle_subtask(self, subtask):
        """Alterna el estado de una subtarea."""
        self.task_service.toggle_subtask(subtask.id)
        self._load_tasks()
    
    def _toggle_task_status(self, task: Task):
        """Alterna el estado de una tarea."""
        if task.status == "completada":
            self.task_service.mark_as_pending(task.id, self.points_service)
        else:
            self.task_service.mark_as_completed(task.id, self.points_service)
        self._load_tasks()
    
    def _delete_task(self, task: Task):
        """Elimina una tarea."""
        def confirm_delete(e):
            self.task_service.delete_task(task.id)
            self._load_tasks()
            self.page.close_dialog()
        
        self.page.dialog = ft.AlertDialog(
            title=ft.Text("Confirmar eliminación"),
            content=ft.Text(f"¿Estás seguro de que quieres eliminar la tarea '{task.title}'?"),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: self.page.close_dialog()),
                ft.TextButton("Eliminar", on_click=confirm_delete, style=ft.ButtonStyle(color=ft.Colors.RED))
            ]
        )
        self.page.dialog.open = True
        self.page.update()
    
    def _open_task_form(self, e, task: Optional[Task] = None):
        """Abre el formulario de tarea en una nueva vista."""
        route = f"/task-form?id={task.id}" if task and task.id else "/task-form"
        self.page.go(route)

