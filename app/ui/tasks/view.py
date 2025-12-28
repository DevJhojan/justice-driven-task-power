"""
Vista principal de tareas.
"""
import flet as ft
from datetime import datetime
from typing import Optional

from app.data.models import Task
from app.services.task_service import TaskService


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
        self._editing_task_id = None  # ID de la tarea que se está editando (None si no hay ninguna)
        self._expanded_subtasks = set()  # Set de IDs de tareas con subtareas expandidas
        self._sort_order = "recent"  # "recent" para más reciente primero, "oldest" para más antiguo primero
    
    def build_ui(self) -> ft.Container:
        """
        Construye la interfaz de usuario de tareas.
        
        Returns:
            Container con la vista de tareas.
        """
        # Contenedor para las tareas
        self.tasks_container = ft.Column(
            [],
            spacing=8
        )
        
        # Contenedor del formulario (oculto por defecto)
        self.form_container = self._build_form_container()
        
        # Barra de título
        is_dark = self.page.theme_mode == ft.ThemeMode.DARK
        title_color = ft.Colors.RED_700 if not is_dark else ft.Colors.RED_500
        btn_color = ft.Colors.RED_700 if not is_dark else ft.Colors.RED_600
        
        # Botón de filtro de ordenamiento
        sort_icon = ft.Icons.ARROW_DOWNWARD if self._sort_order == "recent" else ft.Icons.ARROW_UPWARD
        sort_tooltip = "Más reciente primero" if self._sort_order == "recent" else "Más antiguo primero"
        sort_button = ft.IconButton(
            icon=sort_icon,
            on_click=self._toggle_sort_order,
            tooltip=sort_tooltip,
            icon_color=btn_color
        )
        
        title_bar = ft.Container(
            content=ft.Row(
                [
                    ft.Text(
                        "📋 Mis Tareas",
                        size=24,
                        weight=ft.FontWeight.BOLD,
                        color=title_color
                    ),
                    ft.Row(
                        [
                            sort_button,
                            ft.IconButton(
                                icon=ft.Icons.ADD,
                                on_click=self._toggle_form,
                                tooltip="Agregar tarea",
                                icon_color=btn_color
                            )
                        ],
                        spacing=4
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
                    self.form_container,  # Formulario (aparece primero cuando está visible)
                    ft.Container(
                        content=self.tasks_container,
                        padding=16
                    )
                ],
                spacing=0,
                scroll=ft.ScrollMode.AUTO,
                expand=True
            ),
            expand=True
        )
    
    def _load_tasks(self):
        """Carga las tareas desde el servicio."""
        if self.tasks_container is None:
            return
        
        tasks = list(self.task_service.get_all_tasks())
        
        # Ordenar según el filtro seleccionado
        if self._sort_order == "recent":
            # Más reciente primero (created_at más reciente)
            tasks.sort(key=lambda t: t.created_at if t.created_at else datetime.min, reverse=True)
        else:
            # Más antiguo primero (created_at más antiguo)
            tasks.sort(key=lambda t: t.created_at if t.created_at else datetime.max)
        
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
                # Si esta tarea se está editando, mostrar formulario inline en lugar de la tarjeta
                if self._editing_task_id == task.id:
                    self.tasks_container.controls.append(
                        self._build_inline_form(task)
                    )
                else:
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
            on_click=lambda e, t=task: self._toggle_form(e, t),
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
        
        # Verificar si las subtareas están expandidas
        is_subtasks_expanded = task.id in self._expanded_subtasks if task.id else False
        
        # Botón para expandir/contraer subtareas (solo si hay subtareas)
        subtasks_button = None
        if subtasks:
            subtasks_button = ft.IconButton(
                icon=ft.Icons.EXPAND_MORE if not is_subtasks_expanded else ft.Icons.EXPAND_LESS,
                on_click=lambda e, t=task: self._toggle_subtasks_expansion(t),
                tooltip=f"{len(subtasks)} subtarea(s)" if len(subtasks) == 1 else f"{len(subtasks)} subtareas",
                icon_color=btn_color,
                icon_size=20
            )
        
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
                    subtasks_button if subtasks_button else ft.Container(width=0, height=0),  # Espacio reservado si no hay subtareas
                    edit_button,
                    delete_button
                ],
                spacing=8,
                vertical_alignment=ft.CrossAxisAlignment.START
            )
        ]
        
        # Agregar subtareas si existen y están expandidas
        if subtasks_content and is_subtasks_expanded:
            content_items.append(
                ft.Container(
                    content=ft.Column(
                        subtasks_content,
                        spacing=4
                    ),
                    padding=ft.padding.only(left=32, top=8),
                    border=ft.border.only(left=ft.border.BorderSide(2, ft.Colors.GREY_400)),
                    visible=is_subtasks_expanded
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
    
    def _toggle_subtasks_expansion(self, task: Task):
        """Expande o contrae las subtareas de una tarea."""
        if task.id:
            if task.id in self._expanded_subtasks:
                self._expanded_subtasks.remove(task.id)
            else:
                self._expanded_subtasks.add(task.id)
            self._load_tasks()
            self.page.update()
    
    def _toggle_sort_order(self, e):
        """Alterna entre ordenamiento más reciente primero y más antiguo primero."""
        self._sort_order = "oldest" if self._sort_order == "recent" else "recent"
        self._load_tasks()
        # Reconstruir la UI para actualizar el icono del botón
        self.build_ui()
        if self.page:
            self.page.update()
    
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
    
    def _toggle_form(self, e, task: Optional[Task] = None):
        """Muestra u oculta el formulario de tarea."""
        if task and task.id:
            # Editar tarea específica - modo inline
            if self._editing_task_id == task.id:
                # Si ya está en edición, cancelar
                self._editing_task_id = None
            else:
                # Iniciar edición inline
                self._editing_task_id = task.id
                self._edit_task_in_form(task)
            self._load_tasks()  # Recargar para mostrar/ocultar formulario
            self.page.update()
        else:
            # Crear nueva tarea - modo formulario superior
            if self.form_container.visible:
                # Si está visible, ocultarlo
                self.form_container.visible = False
                self._editing_task_id = None
            else:
                # Si está oculto, mostrarlo y preparar para nueva tarea
                self._new_task_in_form()
                self.form_container.visible = True
            self.page.update()
    
    def _new_task_in_form(self):
        """Prepara el formulario para crear una nueva tarea."""
        # Limpiar campos del formulario
        self.form_title_field.value = ""
        self.form_description_field.value = ""
        self.form_due_date_field.value = ""
        self.form_subtasks_container.content.controls.clear()
        self._current_editing_task = None
        self._form_subtasks = []
        # Actualizar título del formulario
        if hasattr(self, '_form_title_text'):
            self._form_title_text.value = "Nueva Tarea"
    
    def _edit_task_in_form(self, task: Task):
        """Prepara el formulario para editar una tarea existente."""
        self.form_title_field.value = task.title
        self.form_description_field.value = task.description or ""
        self.form_due_date_field.value = task.due_date.isoformat() if task.due_date else ""
        # Cargar subtareas
        subtasks = self.task_service.get_subtasks(task.id)
        self._form_subtasks = subtasks
        self._rebuild_subtasks_in_form()
        self._current_editing_task = task
        # Actualizar título del formulario
        if hasattr(self, '_form_title_text'):
            self._form_title_text.value = "Editar Tarea"
    
    def _build_form_container(self) -> ft.Container:
        """Construye el contenedor del formulario."""
        is_dark = self.page.theme_mode == ft.ThemeMode.DARK
        bg_color = ft.Colors.WHITE if not is_dark else ft.Colors.BLACK
        btn_color = ft.Colors.RED_700 if not is_dark else ft.Colors.RED_500
        
        # Campos del formulario
        self.form_title_field = ft.TextField(
            label="Título",
            hint_text="Ingresa el título de la tarea",
            autofocus=True
        )
        
        self.form_description_field = ft.TextField(
            label="Descripción",
            hint_text="Descripción de la tarea (opcional)",
            multiline=True,
            min_lines=3,
            max_lines=5
        )
        
        self.form_due_date_field = ft.TextField(
            label="Fecha de vencimiento",
            hint_text="YYYY-MM-DD (opcional)"
        )
        
        # Campo para nueva subtarea
        self.form_new_subtask_field = ft.TextField(
            label="Nueva subtarea",
            hint_text="Ingresa el título de la subtarea",
            on_submit=lambda e: self._add_subtask_to_form(e)
        )
        
        # Contenedor de subtareas
        self._form_subtasks = []
        self.form_subtasks_container = ft.Container(
            content=ft.Column([], spacing=4)
        )
        
        # Variable para rastrear la tarea que se está editando
        self._current_editing_task = None
        
        def save_task(e):
            self._save_task_from_form()
        
        def cancel_form(e):
            self.form_container.visible = False
            self._editing_task_id = None
            self._load_tasks()
            self.page.update()
        
        def add_subtask(e):
            self._add_subtask_to_form(e)
        
        # Botones
        save_button = ft.ElevatedButton(
            "Guardar",
            icon=ft.Icons.SAVE,
            on_click=save_task,
            bgcolor=btn_color,
            color=ft.Colors.WHITE
        )
        
        cancel_button = ft.ElevatedButton(
            "Cancelar",
            icon=ft.Icons.CANCEL,
            on_click=cancel_form,
            color=ft.Colors.GREY
        )
        
        add_subtask_button = ft.ElevatedButton(
            "Agregar subtarea",
            icon=ft.Icons.ADD,
            on_click=add_subtask,
            bgcolor=btn_color,
            color=ft.Colors.WHITE
        )
        
        # Contenido del formulario
        form_content = ft.Column(
            [
                ft.Container(
                    content=ft.Row(
                        [
                            ft.Text(
                                "Nueva Tarea" if not self._current_editing_task else "Editar Tarea",
                                size=20,
                                weight=ft.FontWeight.BOLD,
                                color=ft.Colors.RED_700 if not is_dark else ft.Colors.RED_500
                            ),
                            ft.Row(
                                [cancel_button, save_button],
                                spacing=8
                            )
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                    ),
                    padding=16,
                    bgcolor=ft.Colors.SURFACE
                ),
                ft.Container(
                    content=ft.Column(
                        [
                            self.form_title_field,
                            self.form_description_field,
                            self.form_due_date_field,
                            ft.Divider(),
                            ft.Text(
                                "Subtareas",
                                size=16,
                                weight=ft.FontWeight.BOLD,
                                color=ft.Colors.RED_700 if not is_dark else ft.Colors.RED_500
                            ),
                            self.form_subtasks_container,
                            ft.Row(
                                [self.form_new_subtask_field, add_subtask_button],
                                spacing=8
                            )
                        ],
                        spacing=16,
                        scroll=ft.ScrollMode.AUTO,
                        expand=True
                    ),
                    padding=16,
                    expand=True,
                    bgcolor=bg_color
                )
            ],
            spacing=0,
            expand=True
        )
        
        container = ft.Container(
            content=form_content,
            visible=False,  # Oculto por defecto
            border=ft.border.all(2, btn_color),
            border_radius=8,
            margin=ft.margin.symmetric(horizontal=16, vertical=8)
        )
        
        return container
    
    def _build_inline_form(self, task: Task) -> ft.Container:
        """Construye un formulario inline para editar una tarea en su posición."""
        is_dark = self.page.theme_mode == ft.ThemeMode.DARK
        bg_color = ft.Colors.WHITE if not is_dark else ft.Colors.SURFACE
        btn_color = ft.Colors.RED_700 if not is_dark else ft.Colors.RED_500
        
        # Campos del formulario inline (crear nuevos para evitar conflictos)
        inline_title_field = ft.TextField(
            label="Título",
            hint_text="Ingresa el título de la tarea",
            value=task.title,
            autofocus=True
        )
        
        inline_description_field = ft.TextField(
            label="Descripción",
            hint_text="Descripción de la tarea (opcional)",
            multiline=True,
            min_lines=2,
            max_lines=4,
            value=task.description or ""
        )
        
        inline_due_date_field = ft.TextField(
            label="Fecha de vencimiento",
            hint_text="YYYY-MM-DD (opcional)",
            value=task.due_date.isoformat() if task.due_date else ""
        )
        
        # Cargar subtareas existentes
        existing_subtasks = self.task_service.get_subtasks(task.id) if task.id else []
        inline_subtasks_list = []
        for subtask in existing_subtasks:
            inline_subtasks_list.append(subtask)
        
        # Campo para nueva subtarea
        inline_new_subtask_field = ft.TextField(
            label="Nueva subtarea",
            hint_text="Ingresa el título de la subtarea",
            expand=True
        )
        
        # Contenedor de subtareas
        inline_subtasks_container = ft.Container(
            content=ft.Column([], spacing=4)
        )
        
        def rebuild_inline_subtasks():
            """Reconstruye la lista de subtareas en el formulario inline."""
            subtasks_col = ft.Column([], spacing=4)
            for idx, subtask in enumerate(inline_subtasks_list):
                subtask_row = ft.Row(
                    [
                        ft.Checkbox(
                            value=subtask.completed,
                            on_change=lambda e, i=idx: (setattr(inline_subtasks_list[i], 'completed', e.control.value), rebuild_inline_subtasks(), self.page.update())
                        ),
                        ft.Text(subtask.title, expand=True),
                        ft.IconButton(
                            icon=ft.Icons.DELETE,
                            icon_size=16,
                            on_click=lambda e, i=idx: (inline_subtasks_list.pop(i), rebuild_inline_subtasks(), self.page.update()),
                            tooltip="Eliminar",
                            icon_color=ft.Colors.RED
                        )
                    ],
                    spacing=8
                )
                subtasks_col.controls.append(subtask_row)
            inline_subtasks_container.content = subtasks_col
        
        def add_inline_subtask(e):
            """Agrega una subtarea al formulario inline."""
            title = inline_new_subtask_field.value.strip()
            if not title:
                return
            from app.data.models import Subtask
            inline_subtasks_list.append(Subtask(id=None, task_id=task.id, title=title, completed=False))
            inline_new_subtask_field.value = ""
            rebuild_inline_subtasks()
            self.page.update()
        
        # Reconstruir subtareas iniciales
        rebuild_inline_subtasks()
        
        def save_inline_task(e):
            """Guarda la tarea desde el formulario inline."""
            title = inline_title_field.value.strip()
            if not title:
                return
            
            description = inline_description_field.value.strip() if inline_description_field.value else None
            due_date_str = inline_due_date_field.value.strip() if inline_due_date_field.value else None
            
            due_date = None
            if due_date_str:
                try:
                    from datetime import datetime
                    due_date = datetime.strptime(due_date_str, "%Y-%m-%d").date()
                except:
                    pass
            
            try:
                # Actualizar tarea
                from app.data.models import Task
                updated_task = Task(
                    id=task.id,
                    title=title,
                    description=description,
                    due_date=due_date,
                    status=task.status,
                    created_at=task.created_at
                )
                self.task_service.update_task(updated_task)
                
                # Eliminar todas las subtareas existentes y crear las nuevas
                existing_subtasks_db = self.task_service.get_subtasks(task.id)
                for subtask in existing_subtasks_db:
                    if subtask.id:
                        self.task_service.delete_subtask(subtask.id)
                
                # Crear las nuevas subtareas
                for subtask in inline_subtasks_list:
                    if subtask.title.strip():
                        created_subtask = self.task_service.create_subtask(task.id, subtask.title)
                        # Si la subtarea estaba completada, actualizarla
                        if created_subtask and created_subtask.id and subtask.completed:
                            self.task_service.toggle_subtask(created_subtask.id)
                
                # Cancelar edición y recargar
                self._editing_task_id = None
                self._load_tasks()
                self.page.update()
            except Exception as ex:
                self._show_error(ex, "Error al guardar tarea")
        
        def cancel_inline_form(e):
            """Cancela la edición inline."""
            self._editing_task_id = None
            self._load_tasks()
            self.page.update()
        
        # Botones
        save_button = ft.ElevatedButton(
            "Guardar",
            icon=ft.Icons.SAVE,
            on_click=save_inline_task,
            bgcolor=btn_color,
            color=ft.Colors.WHITE
        )
        
        cancel_button = ft.ElevatedButton(
            "Cancelar",
            icon=ft.Icons.CANCEL,
            on_click=cancel_inline_form,
            color=ft.Colors.GREY
        )
        
        add_subtask_button = ft.ElevatedButton(
            "Agregar",
            icon=ft.Icons.ADD,
            on_click=add_inline_subtask,
            bgcolor=btn_color,
            color=ft.Colors.WHITE
        )
        
        # Contenido del formulario inline
        form_content = ft.Column(
            [
                ft.Container(
                    content=ft.Row(
                        [
                            ft.Text(
                                "Editar Tarea",
                                size=18,
                                weight=ft.FontWeight.BOLD,
                                color=btn_color
                            ),
                            ft.Row(
                                [cancel_button, save_button],
                                spacing=8
                            )
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                    ),
                    padding=16,
                    bgcolor=ft.Colors.SURFACE
                ),
                ft.Container(
                    content=ft.Column(
                        [
                            inline_title_field,
                            inline_description_field,
                            inline_due_date_field,
                            ft.Divider(),
                            ft.Text(
                                "Subtareas",
                                size=14,
                                weight=ft.FontWeight.BOLD,
                                color=btn_color
                            ),
                            inline_subtasks_container,
                            ft.Row(
                                [inline_new_subtask_field, add_subtask_button],
                                spacing=8
                            )
                        ],
                        spacing=12
                    ),
                    padding=16,
                    bgcolor=bg_color
                )
            ],
            spacing=0
        )
        
        return ft.Container(
            content=form_content,
            padding=16,
            bgcolor=bg_color,
            border_radius=8,
            border=ft.border.all(2, btn_color),
            margin=ft.margin.only(bottom=8)
        )
    
    def _add_subtask_to_form(self, e):
        """Agrega una subtarea al formulario."""
        title = self.form_new_subtask_field.value.strip()
        if not title:
            return
        
        # Crear subtarea temporal (sin ID aún)
        from app.data.models import Subtask
        subtask = Subtask(
            id=None,
            task_id=None,
            title=title,
            completed=False
        )
        self._form_subtasks.append(subtask)
        self._rebuild_subtasks_in_form()
        self.form_new_subtask_field.value = ""
        self.page.update()
    
    def _rebuild_subtasks_in_form(self):
        """Reconstruye la lista de subtareas en el formulario."""
        if not hasattr(self, 'form_subtasks_container'):
            return
        
        is_dark = self.page.theme_mode == ft.ThemeMode.DARK
        btn_color = ft.Colors.RED_700 if not is_dark else ft.Colors.RED_500
        
        subtasks_col = ft.Column([], spacing=4)
        for i, subtask in enumerate(self._form_subtasks):
            def delete_subtask(idx, e):
                self._form_subtasks.pop(idx)
                self._rebuild_subtasks_in_form()
                self.page.update()
            
            subtask_row = ft.Row(
                [
                    ft.Checkbox(
                        value=subtask.completed,
                        on_change=lambda e, idx=i: self._toggle_subtask_complete(idx, e)
                    ),
                    ft.Text(subtask.title, expand=True),
                    ft.IconButton(
                        icon=ft.Icons.DELETE,
                        icon_color=btn_color,
                        on_click=lambda e, idx=i: delete_subtask(idx, e),
                        tooltip="Eliminar subtarea"
                    )
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN
            )
            subtasks_col.controls.append(subtask_row)
        
        self.form_subtasks_container.content = subtasks_col
    
    def _toggle_subtask_complete(self, idx, e):
        """Cambia el estado de completado de una subtarea en el formulario."""
        if 0 <= idx < len(self._form_subtasks):
            self._form_subtasks[idx].completed = e.control.value
            self.page.update()
    
    def _save_task_from_form(self):
        """Guarda la tarea desde el formulario."""
        title = self.form_title_field.value.strip()
        if not title:
            return
        
        description = self.form_description_field.value.strip() if self.form_description_field.value else None
        due_date_str = self.form_due_date_field.value.strip() if self.form_due_date_field.value else None
        
        due_date = None
        if due_date_str:
            try:
                from datetime import datetime
                due_date = datetime.strptime(due_date_str, "%Y-%m-%d").date()
            except:
                pass
        
        try:
            if self._current_editing_task:
                # Editar tarea existente
                from app.data.models import Task
                updated_task = Task(
                    id=self._current_editing_task.id,
                    title=title,
                    description=description,
                    due_date=due_date,
                    status=self._current_editing_task.status,
                    created_at=self._current_editing_task.created_at
                )
                self.task_service.update_task(updated_task)
                
                # Eliminar todas las subtareas existentes y crear las nuevas
                existing_subtasks = self.task_service.get_subtasks(self._current_editing_task.id)
                for subtask in existing_subtasks:
                    if subtask.id:
                        self.task_service.delete_subtask(subtask.id)
                
                # Crear las nuevas subtareas
                for subtask in self._form_subtasks:
                    if subtask.title.strip():
                        self.task_service.create_subtask(self._current_editing_task.id, subtask.title)
            else:
                # Crear nueva tarea
                due_date_str = due_date.isoformat() if due_date else None
                task = self.task_service.create_task(
                    title=title,
                    description=description,
                    due_date=due_date_str
                )
                # Agregar subtareas
                for subtask in self._form_subtasks:
                    if subtask.title.strip():
                        self.task_service.create_subtask(task.id, subtask.title)
            
            # Ocultar formulario y recargar tareas
            self.form_container.visible = False
            self._editing_task_id = None
            self._load_tasks()
            self.page.update()
        except Exception as ex:
            self._show_error(ex, "Error al guardar tarea")
    
    def _show_error(self, error: Exception, context: str = ""):
        """Muestra una página de error."""
        try:
            from app.ui.error_view import ErrorView
            error_view = ErrorView(self.page, error, context)
            error_view_obj = error_view.build_view()
            
            # Verificar si ya existe una vista de error
            existing_error_view = None
            for i, view in enumerate(self.page.views):
                if view.route == "/error":
                    existing_error_view = i
                    break
            
            if existing_error_view is not None:
                # Reemplazar la vista de error existente
                self.page.views[existing_error_view] = error_view_obj
            else:
                # Agregar nueva vista de error
                self.page.views.append(error_view_obj)
            
            self.page.go("/error")
            self.page.update()
        except Exception as ex2:
            # Si no se puede mostrar la página de error, imprimir en consola
            print(f"Error crítico al mostrar página de error:")
            print(f"Error original: {error}")
            print(f"Error al mostrar: {ex2}")
            import traceback
            traceback.print_exc()

