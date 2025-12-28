"""
Formulario para crear y editar tareas.
"""
import flet as ft
from typing import Optional

from app.data.models import Task
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
        
        self._show_dialog()
    
    def _show_dialog(self):
        """Muestra el diálogo del formulario."""
        is_editing = self.task is not None
        
        self.page.dialog = ft.AlertDialog(
            title=ft.Text("Editar tarea" if is_editing else "Nueva tarea"),
            content=ft.Container(
                content=ft.Column(
                    [
                        self.title_field,
                        self.description_field,
                        self.due_date_field
                    ],
                    spacing=16,
                    tight=True
                ),
                width=400,
                padding=16
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=self._cancel),
                ft.TextButton("Guardar", on_click=self._save)
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
            else:
                # Crear nueva tarea
                self.task_service.create_task(title, description, due_date_str)
            
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

