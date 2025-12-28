"""
Formulario para crear y editar tareas.
"""
import flet as ft
from typing import Optional, List

from app.data.models import Task, Subtask
from app.services.task_service import TaskService


class TaskForm:
    """Formulario de tarea."""
    
    def __init__(self, page: ft.Page, task_service: TaskService, 
                 task: Optional[Task] = None, on_save: Optional[callable] = None):
        """
        Inicializa el formulario.
        
        Args:
            page: Página de Flet.
            task_service: Servicio de tareas.
            task: Tarea a editar (None para crear nueva).
            on_save: Callback a ejecutar después de guardar.
        """
        self.page = page
        self.task_service = task_service
        self.task = task
        self.on_save = on_save
        self.subtasks: List[Subtask] = []
        self.subtasks_to_delete: List[int] = []
        
        # Cargar subtareas si estamos editando
        if task and task.id:
            self.subtasks = self.task_service.get_subtasks(task.id)
        
        # Campos del formulario
        self.title_field = ft.TextField(
            label="Título",
            hint_text="Ingresa el título de la tarea",
            autofocus=True,
            value=task.title if task else ""
        )
        
        self.description_field = ft.TextField(
            label="Descripción",
            hint_text="Descripción de la tarea (opcional)",
            multiline=True,
            min_lines=3,
            max_lines=5,
            value=task.description if task else ""
        )
        
        self.due_date_field = ft.TextField(
            label="Fecha de vencimiento",
            hint_text="YYYY-MM-DD (opcional)",
            value=task.due_date.isoformat() if task and task.due_date else ""
        )
        
        # Campo para nueva subtarea
        self.new_subtask_field = ft.TextField(
            label="Nueva subtarea",
            hint_text="Ingresa el título de la subtarea",
            on_submit=self._add_subtask
        )
        
        self.subtasks_container = None
    
    def build_view(self) -> ft.View:
        """Construye una vista completa para el formulario."""
        is_editing = self.task is not None
        is_dark = self.page.theme_mode == ft.ThemeMode.DARK
        title_color = ft.Colors.RED_700 if not is_dark else ft.Colors.RED_500
        bg_color = ft.Colors.WHITE if not is_dark else ft.Colors.BLACK
        
        # Construir lista de subtareas
        self.subtasks_container = ft.Container(
            content=self._build_subtasks_list()
        )
        
        btn_color = ft.Colors.RED_700 if not is_dark else ft.Colors.RED_500
        
        add_subtask_button = ft.ElevatedButton(
            "Agregar subtarea",
            icon=ft.Icons.ADD,
            on_click=self._add_subtask,
            bgcolor=btn_color,
            color=ft.Colors.WHITE
        )
        
        # Barra superior con título y botones
        header = ft.Container(
            content=ft.Row(
                [
                    ft.IconButton(
                        icon=ft.Icons.ARROW_BACK,
                        icon_color=title_color,
                        on_click=self._cancel,
                        tooltip="Volver"
                    ),
                    ft.Text(
                        "Editar tarea" if is_editing else "Nueva tarea",
                        size=20,
                        weight=ft.FontWeight.BOLD,
                        color=title_color,
                        expand=True
                    ),
                    ft.ElevatedButton(
                        "Guardar",
                        icon=ft.Icons.SAVE,
                        on_click=self._save,
                        bgcolor=btn_color,
                        color=ft.Colors.WHITE
                    )
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN
            ),
            padding=16,
            bgcolor=ft.Colors.SURFACE if is_dark else ft.Colors.WHITE,
            border=ft.border.only(bottom=ft.border.BorderSide(1, ft.Colors.OUTLINE))
        )
        
        # Contenido principal con scroll
        content = ft.Container(
            content=ft.Column(
                [
                    self.title_field,
                    self.description_field,
                    self.due_date_field,
                    ft.Divider(),
                    ft.Text(
                        "Subtareas",
                        size=16,
                        weight=ft.FontWeight.BOLD,
                        color=title_color
                    ),
                    self.subtasks_container,
                    ft.Row(
                        [self.new_subtask_field, add_subtask_button],
                        spacing=8
                    )
                ],
                spacing=16,
                scroll=ft.ScrollMode.AUTO,
                expand=True
            ),
            padding=16,
            expand=True
        )
        
        # Crear la vista
        route = f"/task-form?id={self.task.id}" if self.task and self.task.id else "/task-form"
        return ft.View(
            route=route,
            controls=[
                ft.Column(
                    [header, content],
                    spacing=0,
                    expand=True
                )
            ],
            bgcolor=bg_color
        )
    
    def _build_subtasks_list(self) -> ft.Column:
        """Construye la lista de subtareas."""
        subtasks_items = []
        
        for subtask in self.subtasks:
            if subtask.id and subtask.id in self.subtasks_to_delete:
                continue
            
            subtask_field = ft.TextField(
                value=subtask.title,
                on_change=lambda e, s=subtask: setattr(s, 'title', e.control.value),
                expand=True
            )
            
            delete_btn = ft.IconButton(
                icon=ft.Icons.DELETE,
                icon_color=ft.Colors.RED,
                on_click=lambda e, s=subtask: self._remove_subtask(s),
                tooltip="Eliminar"
            )
            
            subtasks_items.append(
                ft.Row(
                    [subtask_field, delete_btn],
                    spacing=8
                )
            )
        
        return ft.Column(subtasks_items, spacing=8)
    
    def _add_subtask(self, e):
        """Agrega una nueva subtarea a la lista."""
        title = self.new_subtask_field.value.strip()
        if not title:
            return
        
        new_subtask = Subtask(
            id=None,  # Nueva subtarea
            task_id=self.task.id if self.task else 0,
            title=title,
            completed=False
        )
        
        self.subtasks.append(new_subtask)
        self.new_subtask_field.value = ""
        self._refresh_subtasks_list()
    
    def _remove_subtask(self, subtask: Subtask):
        """Elimina una subtarea de la lista."""
        if subtask.id:
            self.subtasks_to_delete.append(subtask.id)
        self.subtasks.remove(subtask)
        self._refresh_subtasks_list()
    
    def _refresh_subtasks_list(self):
        """Actualiza la lista de subtareas en el diálogo."""
        if self.subtasks_container:
            self.subtasks_container.content = self._build_subtasks_list()
            self.page.update()
    
    def _show_dialog(self):
        """Muestra el diálogo del formulario."""
        is_editing = self.task is not None
        is_dark = self.page.theme_mode == ft.ThemeMode.DARK
        title_color = ft.Colors.RED_700 if not is_dark else ft.Colors.RED_500
        
        # Construir lista de subtareas
        self.subtasks_container = ft.Container(
            content=self._build_subtasks_list()
        )
        
        btn_color = ft.Colors.RED_700 if not is_dark else ft.Colors.RED_500
        
        add_subtask_button = ft.ElevatedButton(
            "Agregar subtarea",
            icon=ft.Icons.ADD,
            on_click=self._add_subtask,
            bgcolor=btn_color,
            color=ft.Colors.WHITE
        )
        
        self.page.dialog = ft.AlertDialog(
            title=ft.Text(
                "Editar tarea" if is_editing else "Nueva tarea",
                color=title_color,
                weight=ft.FontWeight.BOLD
            ),
            content=ft.Container(
                content=ft.Column(
                    [
                        self.title_field,
                        self.description_field,
                        self.due_date_field,
                        ft.Divider(),
                        ft.Text(
                            "Subtareas",
                            size=14,
                            weight=ft.FontWeight.BOLD,
                            color=title_color
                        ),
                        self.subtasks_container,
                        ft.Row(
                            [self.new_subtask_field, add_subtask_button],
                            spacing=8
                        )
                    ],
                    spacing=12,
                    tight=True,
                    scroll=ft.ScrollMode.AUTO
                ),
                width=500,
                height=500,
                padding=16
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=self._cancel),
                ft.TextButton(
                    "Guardar",
                    on_click=self._save,
                    style=ft.ButtonStyle(
                        color=btn_color
                    )
                )
            ],
            modal=True
        )
        self.page.dialog.open = True
        self.page.update()
    
    def _save(self, e):
        """Guarda la tarea."""
        title = self.title_field.value.strip()
        if not title:
            self._show_error("El título es requerido")
            return
        
        description = self.description_field.value.strip() or None
        due_date_str = self.due_date_field.value.strip() or None
        
        # Validar formato de fecha
        if due_date_str:
            try:
                from datetime import date
                date.fromisoformat(due_date_str)
            except ValueError:
                self._show_error("Formato de fecha inválido. Use YYYY-MM-DD")
                return
        
        try:
            task_id = None
            if self.task:
                # Actualizar tarea existente
                self.task.title = title
                self.task.description = description
                if due_date_str:
                    from datetime import date
                    self.task.due_date = date.fromisoformat(due_date_str)
                else:
                    self.task.due_date = None
                self.task_service.update_task(self.task)
                task_id = self.task.id
            else:
                # Crear nueva tarea
                new_task = self.task_service.create_task(title, description, due_date_str)
                task_id = new_task.id
            
            # Gestionar subtareas
            if task_id:
                # Eliminar subtareas marcadas para eliminar
                for subtask_id in self.subtasks_to_delete:
                    self.task_service.delete_subtask(subtask_id)
                
                # Crear o actualizar subtareas
                for subtask in self.subtasks:
                    if subtask.id is None:
                        # Nueva subtarea
                        subtask.task_id = task_id
                        self.task_service.create_subtask(task_id, subtask.title)
                    else:
                        # Actualizar subtarea existente
                        self.task_service.update_subtask(subtask)
            
            self.page.close_dialog()
            if self.on_save:
                self.on_save()
        except Exception as ex:
            self._show_error(f"Error al guardar: {str(ex)}")
    
    def _cancel(self, e):
        """Cancela el formulario."""
        self.page.close_dialog()
    
    def _show_error(self, message: str):
        """Muestra un mensaje de error."""
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(message),
            bgcolor=ft.Colors.RED
        )
        self.page.snack_bar.open = True
        self.page.update()

