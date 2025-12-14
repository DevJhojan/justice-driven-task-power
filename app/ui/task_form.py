"""
Formulario para crear y editar tareas.
"""
import flet as ft
from app.data.models import Task
from typing import Optional, Callable


class TaskForm:
    """Formulario para crear/editar tareas."""
    
    def __init__(self, on_save: Callable, on_cancel: Callable, task: Optional[Task] = None):
        """
        Inicializa el formulario.
        
        Args:
            on_save: Callback cuando se guarda la tarea.
            on_cancel: Callback cuando se cancela.
            task: Tarea a editar (None para crear nueva).
        """
        self.on_save = on_save
        self.on_cancel = on_cancel
        self.task = task
        
        # Campos del formulario
        self.title_field = ft.TextField(
            label="Título",
            hint_text="Ingresa el título de la tarea",
            autofocus=True,
            expand=True,
            value=task.title if task else ""
        )
        
        self.description_field = ft.TextField(
            label="Descripción",
            hint_text="Ingresa una descripción (opcional)",
            multiline=True,
            min_lines=3,
            max_lines=5,
            expand=True,
            value=task.description if task else ""
        )
        
        self.priority_dropdown = ft.Dropdown(
            label="Prioridad",
            options=[
                ft.dropdown.Option("low", "Baja"),
                ft.dropdown.Option("medium", "Media"),
                ft.dropdown.Option("high", "Alta"),
            ],
            value=task.priority if task else "medium",
            expand=True
        )
        
        # Botones
        self.save_button = ft.ElevatedButton(
            text="Guardar",
            icon=ft.Icons.SAVE,
            on_click=self._handle_save,
            color=ft.Colors.WHITE,
            bgcolor=ft.Colors.BLUE
        )
        
        self.cancel_button = ft.OutlinedButton(
            text="Cancelar",
            icon=ft.Icons.CANCEL,
            on_click=lambda e: on_cancel()
        )
    
    def build(self) -> ft.Container:
        """
        Construye el widget del formulario.
        
        Returns:
            Container con el formulario completo.
        """
        title = "Editar Tarea" if self.task else "Nueva Tarea"
        
        return ft.Container(
            content=ft.Column(
                [
                    ft.Text(
                        title,
                        size=24,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.BLUE
                    ),
                    ft.Divider(),
                    self.title_field,
                    self.description_field,
                    self.priority_dropdown,
                    ft.Row(
                        [
                            self.save_button,
                            self.cancel_button
                        ],
                        alignment=ft.MainAxisAlignment.END,
                        spacing=8
                    )
                ],
                spacing=16,
                scroll=ft.ScrollMode.AUTO
            ),
            padding=20,
            expand=True
        )
    
    def _handle_save(self, e):
        """Maneja el evento de guardar."""
        title = self.title_field.value
        description = self.description_field.value or ""
        priority = self.priority_dropdown.value or "medium"
        
        if not title or not title.strip():
            # Mostrar error
            self.title_field.error_text = "El título es obligatorio"
            self.title_field.update()
            return
        
        self.title_field.error_text = None
        self.title_field.update()
        
        # Crear o actualizar tarea
        if self.task:
            # Actualizar tarea existente
            self.task.title = title.strip()
            self.task.description = description.strip()
            self.task.priority = priority
            self.on_save(self.task)
        else:
            # Crear nueva tarea
            self.on_save(title.strip(), description.strip(), priority)
    
    def get_task_data(self) -> dict:
        """
        Obtiene los datos del formulario.
        
        Returns:
            Diccionario con los datos de la tarea.
        """
        return {
            'title': self.title_field.value or "",
            'description': self.description_field.value or "",
            'priority': self.priority_dropdown.value or "medium"
        }

