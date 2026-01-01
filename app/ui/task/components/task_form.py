"""
Componente Task Form
Formulario para crear y editar tareas con todos sus atributos
"""

import flet as ft
from typing import Optional, Callable, List
from datetime import date, timedelta, datetime
from app.models.task import Task
from app.models.subtask import Subtask
from app.utils.task_helper import (
    TASK_STATUS_PENDING,
    TASK_STATUS_IN_PROGRESS,
    TASK_STATUS_COMPLETED,
    TASK_STATUS_CANCELLED,
    VALID_TASK_STATUSES,
)
from app.utils.helpers.responsives import get_responsive_padding, get_responsive_spacing


class TaskForm:
    """
    Formulario para crear y editar tareas.
    Maneja validación, campos dinámicos y subtareas.
    """
    
    def __init__(
        self,
        page: ft.Page,
        task: Optional[Task] = None,
        on_save: Optional[Callable[[Task], None]] = None,
        on_cancel: Optional[Callable] = None,
    ):
        """
        Inicializa el formulario de tareas.
        
        Args:
            page: Página de Flet
            task: Tarea a editar (None para crear nueva)
            on_save: Callback al guardar (recibe la tarea)
            on_cancel: Callback al cancelar
        """
        self.page = page
        self.task = task
        self.on_save = on_save
        self.on_cancel = on_cancel
        self.is_edit_mode = task is not None
        
        # Controles del formulario
        self.title_field: Optional[ft.TextField] = None
        self.description_field: Optional[ft.TextField] = None
        self.status_dropdown: Optional[ft.Dropdown] = None
        self.urgent_checkbox: Optional[ft.Checkbox] = None
        self.important_checkbox: Optional[ft.Checkbox] = None
        self.due_date_picker: Optional[ft.DatePicker] = None
        self.due_date_text: Optional[ft.Text] = None
        self.tags_field: Optional[ft.TextField] = None
        self.notes_field: Optional[ft.TextField] = None
        self.subtasks_column: Optional[ft.Column] = None
        self.error_text: Optional[ft.Text] = None
        
        # Estado de subtareas
        self.subtasks: List[Subtask] = []
        if self.task and self.task.subtasks:
            self.subtasks = list(self.task.subtasks)
        
        # Fecha seleccionada
        self.selected_date: Optional[date] = None
        if self.task and self.task.due_date:
            self.selected_date = self.task.due_date
    
    def build(self) -> ft.Container:
        """Construye el formulario completo."""
        # Campo de título
        self.title_field = ft.TextField(
            label="Título *",
            hint_text="Ingrese el título de la tarea",
            value=self.task.title if self.task else "",
            max_length=100,
            border_color=ft.Colors.RED_700,
            focused_border_color=ft.Colors.RED_400,
            cursor_color=ft.Colors.RED_400,
            expand=True,
        )
        
        # Campo de descripción
        self.description_field = ft.TextField(
            label="Descripción",
            hint_text="Descripción detallada de la tarea",
            value=self.task.description if self.task else "",
            multiline=True,
            min_lines=3,
            max_lines=5,
            max_length=500,
            border_color=ft.Colors.RED_700,
            focused_border_color=ft.Colors.RED_400,
            cursor_color=ft.Colors.RED_400,
            expand=True,
        )
        
        # Dropdown de estado
        self.status_dropdown = ft.Dropdown(
            label="Estado",
            value=self.task.status if self.task else TASK_STATUS_PENDING,
            options=[
                ft.dropdown.Option(TASK_STATUS_PENDING, "Pendiente"),
                ft.dropdown.Option(TASK_STATUS_IN_PROGRESS, "En Progreso"),
                ft.dropdown.Option(TASK_STATUS_COMPLETED, "Completada"),
                ft.dropdown.Option(TASK_STATUS_CANCELLED, "Cancelada"),
            ],
            border_color=ft.Colors.RED_700,
            focused_border_color=ft.Colors.RED_400,
            width=200,
        )
        
        # Checkboxes de prioridad (Matriz de Eisenhower)
        self.urgent_checkbox = ft.Checkbox(
            label="Urgente",
            value=self.task.urgent if self.task else False,
            fill_color=ft.Colors.RED_700,
        )
        
        self.important_checkbox = ft.Checkbox(
            label="Importante",
            value=self.task.important if self.task else False,
            fill_color=ft.Colors.RED_700,
        )
        
        # DatePicker para fecha de vencimiento
        def handle_date_change(e):
            if e.control.value:
                self.selected_date = e.control.value
                self.due_date_text.value = f"📅 {self.selected_date.strftime('%d/%m/%Y')}"
            else:
                self.selected_date = None
                self.due_date_text.value = "📅 Sin fecha"
            self.page.update()
        
        self.due_date_picker = ft.DatePicker(
            first_date=date.today(),
            last_date=date.today() + timedelta(days=365 * 2),
            on_change=handle_date_change,
        )
        
        self.page.overlay.append(self.due_date_picker)
        
        date_str = "Sin fecha"
        if self.selected_date:
            date_str = self.selected_date.strftime('%d/%m/%Y')
        
        self.due_date_text = ft.Text(
            f"📅 {date_str}",
            size=14,
            color=ft.Colors.GREY_400,
        )
        
        def open_date_picker(e):
            self.due_date_picker.open = True
            self.page.update()
        
        def clear_date(e):
            self.selected_date = None
            self.due_date_text.value = "📅 Sin fecha"
            self.page.update()
        
        # Campo de tags
        tags_value = ""
        if self.task and self.task.tags:
            tags_value = ", ".join(self.task.tags)
        
        self.tags_field = ft.TextField(
            label="Etiquetas",
            hint_text="Separadas por comas (ej: python, backend, api)",
            value=tags_value,
            border_color=ft.Colors.RED_700,
            focused_border_color=ft.Colors.RED_400,
            cursor_color=ft.Colors.RED_400,
        )
        
        # Campo de notas
        self.notes_field = ft.TextField(
            label="Notas adicionales",
            hint_text="Notas, comentarios o recordatorios",
            value=self.task.notes if self.task else "",
            multiline=True,
            min_lines=2,
            max_lines=4,
            max_length=300,
            border_color=ft.Colors.RED_700,
            focused_border_color=ft.Colors.RED_400,
            cursor_color=ft.Colors.RED_400,
        )
        
        # Sección de subtareas
        self.subtasks_column = ft.Column(spacing=8)
        self._render_subtasks()
        
        def add_subtask(e):
            self._add_subtask_field()
            self.page.update()
        
        # Texto de error
        self.error_text = ft.Text(
            "",
            color=ft.Colors.RED_400,
            size=12,
            visible=False,
        )
        
        # Botones de acción
        def handle_save(e):
            if self._validate_and_save():
                if self.on_save:
                    self.on_save(self._build_task())
        
        def handle_cancel(e):
            if self.on_cancel:
                self.on_cancel()
        
        save_button = ft.FilledButton(
            "Guardar" if self.is_edit_mode else "Crear Tarea",
            icon=ft.Icons.SAVE,
            on_click=handle_save,
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.RED_700,
                color=ft.Colors.WHITE,
            ),
        )
        
        cancel_button = ft.OutlinedButton(
            "Cancelar",
            icon=ft.Icons.CANCEL,
            on_click=handle_cancel,
            style=ft.ButtonStyle(
                side=ft.BorderSide(2, ft.Colors.RED_700),
                color=ft.Colors.RED_700,
            ),
        )
        
        # Layout del formulario
        form_content = ft.Column(
            controls=[
                ft.Text(
                    "Editar Tarea" if self.is_edit_mode else "Nueva Tarea",
                    size=24,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.RED_400,
                ),
                ft.Divider(height=1, color=ft.Colors.RED_900),
                
                # Campos principales
                self.title_field,
                self.description_field,
                
                # Fila de estado y prioridad
                ft.Row(
                    controls=[
                        self.status_dropdown,
                        ft.Column(
                            controls=[
                                ft.Text("Prioridad:", size=12, weight=ft.FontWeight.BOLD),
                                self.urgent_checkbox,
                                self.important_checkbox,
                            ],
                            spacing=4,
                        ),
                    ],
                    spacing=20,
                    wrap=True,
                ),
                
                # Fecha de vencimiento
                ft.Column(
                    controls=[
                        ft.Text("Fecha de vencimiento:", size=12, weight=ft.FontWeight.BOLD),
                        self.due_date_text,
                        ft.Row(
                            controls=[
                                ft.FilledButton(
                                    "Elegir fecha",
                                    icon=ft.Icons.CALENDAR_MONTH,
                                    on_click=open_date_picker,
                                    style=ft.ButtonStyle(
                                        bgcolor=ft.Colors.RED_900,
                                        color=ft.Colors.WHITE,
                                    ),
                                ),
                                ft.TextButton(
                                    "Limpiar",
                                    on_click=clear_date,
                                    style=ft.ButtonStyle(
                                        color=ft.Colors.RED_700,
                                    ),
                                ),
                            ],
                            spacing=8,
                        ),
                    ],
                    spacing=8,
                ),
                
                # Tags y notas
                self.tags_field,
                self.notes_field,
                
                # Subtareas
                ft.Column(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Text("Subtareas:", size=14, weight=ft.FontWeight.BOLD),
                                ft.IconButton(
                                    icon=ft.Icons.ADD_CIRCLE,
                                    icon_color=ft.Colors.RED_700,
                                    tooltip="Agregar subtarea",
                                    on_click=add_subtask,
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        ),
                        self.subtasks_column,
                    ],
                    spacing=8,
                ),
                
                # Error
                self.error_text,
                
                ft.Divider(height=1, color=ft.Colors.RED_900),
                
                # Botones
                ft.Row(
                    controls=[save_button, cancel_button],
                    alignment=ft.MainAxisAlignment.END,
                    spacing=12,
                ),
            ],
            spacing=16,
            scroll=ft.ScrollMode.AUTO,
        )
        
        return ft.Container(
            content=ft.Column(
                controls=[form_content],
                scroll=ft.ScrollMode.AUTO,
                expand=True,
            ),
            padding=get_responsive_padding(page=self.page),
            bgcolor=ft.Colors.GREY_900,
            border_radius=12,
            border=ft.Border.all(1, ft.Colors.RED_900),
            height=600,
        )
    
    def _render_subtasks(self):
        """Renderiza la lista de subtareas."""
        self.subtasks_column.controls.clear()
        
        if not self.subtasks:
            self.subtasks_column.controls.append(
                ft.Text(
                    "No hay subtareas. Haz clic en + para agregar.",
                    size=12,
                    color=ft.Colors.GREY_600,
                    italic=True,
                )
            )
            return
        
        for idx, subtask in enumerate(self.subtasks):
            def make_delete_handler(index):
                return lambda e: self._delete_subtask(index)
            
            def make_toggle_handler(index):
                return lambda e: self._toggle_subtask(index, e.control.value)
            
            subtask_row = ft.Row(
                controls=[
                    ft.Checkbox(
                        value=subtask.completed,
                        on_change=make_toggle_handler(idx),
                        fill_color=ft.Colors.RED_700,
                    ),
                    ft.Text(
                        subtask.title,
                        size=13,
                        expand=True,
                        color=ft.Colors.GREY_400 if subtask.completed else ft.Colors.WHITE,
                        italic=subtask.completed,
                    ),
                    ft.IconButton(
                        icon=ft.Icons.DELETE_OUTLINE,
                        icon_color=ft.Colors.RED_400,
                        icon_size=20,
                        tooltip="Eliminar",
                        on_click=make_delete_handler(idx),
                    ),
                ],
                spacing=8,
            )
            self.subtasks_column.controls.append(subtask_row)
    
    def _add_subtask_field(self):
        """Muestra un campo para agregar una nueva subtarea."""
        subtask_input = ft.TextField(
            hint_text="Título de la subtarea",
            border_color=ft.Colors.RED_700,
            focused_border_color=ft.Colors.RED_400,
            cursor_color=ft.Colors.RED_400,
            autofocus=True,
        )
        
        def save_subtask(e):
            title = subtask_input.value.strip()
            if title:
                new_subtask = Subtask(
                    id=f"subtask_{len(self.subtasks)}_{datetime.now().timestamp()}",
                    task_id=self.task.id if self.task else "",
                    title=title,
                    completed=False,
                )
                self.subtasks.append(new_subtask)
                self._render_subtasks()
                self.page.update()
        
        def cancel_subtask(e):
            self._render_subtasks()
            self.page.update()
        
        subtask_row = ft.Row(
            controls=[
                subtask_input,
                ft.IconButton(
                    icon=ft.Icons.CHECK,
                    icon_color=ft.Colors.GREEN_400,
                    tooltip="Guardar",
                    on_click=save_subtask,
                ),
                ft.IconButton(
                    icon=ft.Icons.CLOSE,
                    icon_color=ft.Colors.RED_400,
                    tooltip="Cancelar",
                    on_click=cancel_subtask,
                ),
            ],
            spacing=8,
        )
        
        self.subtasks_column.controls.clear()
        self.subtasks_column.controls.append(subtask_row)
    
    def _delete_subtask(self, index: int):
        """Elimina una subtarea por índice."""
        if 0 <= index < len(self.subtasks):
            self.subtasks.pop(index)
            self._render_subtasks()
            self.page.update()
    
    def _toggle_subtask(self, index: int, completed: bool):
        """Marca/desmarca una subtarea como completada."""
        if 0 <= index < len(self.subtasks):
            self.subtasks[index].completed = completed
            self._render_subtasks()
            self.page.update()
    
    def _validate_and_save(self) -> bool:
        """Valida los campos del formulario."""
        # Verificar que los controles estén inicializados
        if not self.title_field or not self.description_field or not self.tags_field or not self.error_text:
            return False
        
        errors = []
        
        # Validar título
        title = self.title_field.value
        if not title or not title.strip():
            errors.append("El título es obligatorio")
        elif len(title) > 100:
            errors.append("El título no puede exceder 100 caracteres")
        
        # Validar descripción
        description = self.description_field.value
        if description and len(description) > 500:
            errors.append("La descripción no puede exceder 500 caracteres")
        
        # Validar tags
        if self.tags_field.value:
            tags = [t.strip() for t in self.tags_field.value.split(",") if t.strip()]
            if len(tags) > 10:
                errors.append("Máximo 10 etiquetas permitidas")
        
        # Mostrar errores
        if errors:
            self.error_text.value = " • " + "\n • ".join(errors)
            self.error_text.visible = True
            self.page.update()
            return False
        
        self.error_text.visible = False
        return True
    
    def _build_task(self) -> Task:
        """Construye el objeto Task con los datos del formulario."""
        # Verificar que los controles estén inicializados
        if not self.title_field or not self.description_field or not self.status_dropdown or \
           not self.urgent_checkbox or not self.important_checkbox or not self.notes_field or \
           not self.tags_field:
            raise ValueError("Los controles del formulario no están inicializados")
        
        # Procesar tags
        tags = []
        if self.tags_field.value:
            tags = [t.strip() for t in self.tags_field.value.split(",") if t.strip()]
        
        # Crear o actualizar tarea
        if self.is_edit_mode and self.task:
            self.task.title = self.title_field.value.strip() if self.title_field.value else ""
            self.task.description = self.description_field.value.strip() if self.description_field.value else ""
            self.task.status = self.status_dropdown.value or TASK_STATUS_PENDING
            self.task.urgent = self.urgent_checkbox.value or False
            self.task.important = self.important_checkbox.value or False
            self.task.due_date = self.selected_date
            self.task.tags = tags
            self.task.notes = self.notes_field.value.strip() if self.notes_field.value else ""
            self.task.subtasks = self.subtasks
            self.task.updated_at = datetime.now()
            return self.task
        else:
            from uuid import uuid4
            return Task(
                id=str(uuid4()),
                title=self.title_field.value.strip() if self.title_field.value else "",
                description=self.description_field.value.strip() if self.description_field.value else "",
                status=self.status_dropdown.value or TASK_STATUS_PENDING,
                urgent=self.urgent_checkbox.value or False,
                important=self.important_checkbox.value or False,
                due_date=self.selected_date,
                tags=tags,
                notes=self.notes_field.value.strip() if self.notes_field.value else "",
                subtasks=self.subtasks,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
