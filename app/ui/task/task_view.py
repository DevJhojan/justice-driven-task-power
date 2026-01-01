"""
Vista de Tareas (Tasks) de la aplicación
Gestión completa de tareas con filtros, búsqueda y CRUD
"""

import flet as ft
from typing import Optional, List
from app.models.task import Task
from app.services.task_service import TaskService
from app.ui.task.components import TaskForm, TaskList, TaskFilters
from app.utils.helpers.responsives import get_responsive_padding, get_responsive_size


class TaskView:
    """Vista principal de gestión de tareas"""
    
    def __init__(self, page: ft.Page):
        """
        Inicializa la vista de tareas
        
        Args:
            page: Página de Flet
        """
        self.page = page
        self.task_service = TaskService()
        
        # Estado
        self.tasks: List[Task] = []
        self.filtered_tasks: List[Task] = []
        self.selected_task: Optional[Task] = None
        self.is_form_visible = False
        
        # Componentes
        self.task_list: Optional[TaskList] = None
        self.task_filters: Optional[TaskFilters] = None
        self.task_filters_container: Optional[ft.Container] = None
        self.form_container: Optional[ft.Container] = None
        self.main_content: Optional[ft.Column] = None
        self.fab: Optional[ft.FloatingActionButton] = None
        
    def build(self) -> ft.Container:
        """
        Construye y retorna el widget principal de la vista
        
        Returns:
            Container con el contenido de la vista de tareas
        """
        # Cargar tareas de forma síncrona (inicial vacío)
        # Los datos se cargarán cuando se llame a initialize()
        self.tasks = []
        self.filtered_tasks = []
        
        # Header
        header = self._build_header()
        
        # Filtros - guardar referencia al contenedor
        self.task_filters = TaskFilters(
            page=self.page,
            on_filter_change=self._handle_filter_change,
        )
        self.task_filters_container = self.task_filters.build()
        
        # Lista de tareas
        self.task_list = TaskList(
            page=self.page,
            tasks=self.filtered_tasks,
            on_task_click=self._handle_task_click,
            on_task_edit=self._handle_task_edit,
            on_task_delete=self._handle_task_delete,
            on_subtask_toggle=self._handle_subtask_toggle,
        )
        
        # Contenedor del formulario (inicialmente oculto)
        self.form_container = ft.Container(
            visible=False,
            padding=get_responsive_padding(page=self.page),
        )
        
        # Contenido principal - usar la referencia guardada
        self.main_content = ft.Column(
            controls=[
                header,
                self.task_filters_container,
                ft.Divider(height=1, color=ft.Colors.RED_900),
                self.task_list.build(),
            ],
            spacing=16,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )
        
        # FAB para crear tarea
        self.fab = ft.FloatingActionButton(
            icon=ft.Icons.ADD,
            bgcolor=ft.Colors.RED_700,
            on_click=self._show_create_form,
            tooltip="Nueva Tarea",
        )
        
        return ft.Container(
            content=ft.Stack(
                controls=[
                    self.main_content,
                    self.form_container,
                    ft.Container(
                        content=self.fab,
                        alignment=ft.Alignment(1, 1),  # bottom_right
                        padding=20,
                    ),
                ],
            ),
            padding=get_responsive_padding(page=self.page),
            expand=True,
            bgcolor=ft.Colors.GREY_900,
        )
    
    async def initialize(self):
        """
        Inicializa la vista cargando datos async.
        Debe llamarse después de build() y agregar la vista al page.
        """
        await self._load_tasks()
        if self.task_list:
            self.task_list.set_tasks(self.filtered_tasks)
        self._update_header()
        self.page.update()
    
    def _build_header(self) -> ft.Container:
        """Construye el header de la vista"""
        title_size = get_responsive_size(page=self.page, mobile=24, tablet=28, desktop=32)
        
        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(
                        ft.Icons.TASK_ALT,
                        size=40,
                        color=ft.Colors.RED_400,
                    ),
                    ft.Column(
                        controls=[
                            ft.Text(
                                "Mis Tareas",
                                size=title_size,
                                weight=ft.FontWeight.BOLD,
                                color=ft.Colors.WHITE,
                            ),
                            ft.Text(
                                f"{len(self.tasks)} tareas totales",
                                size=14,
                                color=ft.Colors.WHITE70,
                            ),
                        ],
                        spacing=4,
                        expand=True,
                    ),
                ],
                spacing=16,
            ),
            padding=ft.padding.only(bottom=16),
        )
    
    async def _load_tasks(self):
        """Carga todas las tareas desde el servicio"""
        self.tasks = await self.task_service.get_all_tasks()
        self.filtered_tasks = self.tasks.copy()
    
    def _handle_filter_change(self, filters: dict):
        """Maneja cambios en los filtros"""
        # Aplicar filtros a las tareas actuales
        assert self.task_filters is not None
        self.filtered_tasks = self.task_filters.apply_filters(self.tasks)
        if self.task_list:
            self.task_list.set_tasks(self.filtered_tasks)
    
    def _handle_task_click(self, task_id: str):
        """Maneja clic en una tarea"""
        task = next((t for t in self.tasks if t.id == task_id), None)
        if task:
            self.selected_task = task
            # Aquí podrías mostrar un diálogo con detalles
            self._show_task_details(task)
    
    def _handle_task_edit(self, task_id: str):
        """Maneja edición de una tarea"""
        task = next((t for t in self.tasks if t.id == task_id), None)
        if task:
            self._show_edit_form(task)
    
    def _handle_task_delete(self, task_id: str):
        """Maneja eliminación de una tarea"""
        async def confirm_delete(e):
            if await self.task_service.delete_task(task_id):
                await self._load_tasks()
                if self.task_list:
                    self.task_list.set_tasks(self.filtered_tasks)
                # No usar set_tasks en task_filters - no existe ese método
                # Los filtros se aplican automáticamente con apply_filters
                self._update_header()
                self._show_snackbar("Tarea eliminada correctamente", ft.Colors.GREEN_400)
            else:
                self._show_snackbar("Error al eliminar la tarea", ft.Colors.RED_400)
            dialog.open = False
            self.page.update()
        
        def cancel_delete(e):
            dialog.open = False
            self.page.update()
        
        dialog = ft.AlertDialog(
            title=ft.Text("Confirmar eliminación"),
            content=ft.Text("¿Estás seguro de que deseas eliminar esta tarea?"),
            actions=[
                ft.TextButton("Cancelar", on_click=cancel_delete),
                ft.TextButton("Eliminar", on_click=confirm_delete, style=ft.ButtonStyle(color=ft.Colors.RED_400)),
            ],
        )
        
        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()
    
    async def _handle_subtask_toggle(self, task_id: str, subtask_id: str):
        """Maneja toggle de subtarea"""
        # Encontrar tarea y subtarea, togglear y actualizar
        task = next((t for t in self.tasks if t.id == task_id), None)
        if task:
            for subtask in task.subtasks:
                if subtask.id == subtask_id:
                    subtask.completed = not subtask.completed
                    # Actualizar en el servicio
                    task_dict = {
                        "title": task.title,
                        "description": task.description,
                        "status": task.status,
                        "urgent": task.urgent,
                        "important": task.important,
                        "due_date": task.due_date,
                        "tags": task.tags,
                        "subtasks": [s.__dict__ for s in task.subtasks],
                    }
                    await self.task_service.update_task(task_id, task_dict)
                    await self._load_tasks()
                    if self.task_list:
                        self.task_list.set_tasks(self.filtered_tasks)
                    break
    
    def _show_create_form(self, e):
        """Muestra el formulario de creación"""
        self._show_form(None)
    
    def _show_edit_form(self, task: Task):
        """Muestra el formulario de edición"""
        self._show_form(task)
    
    def _show_form(self, task: Optional[Task]):
        """Muestra el formulario de tarea"""
        async def handle_save(saved_task: Task):
            # Convertir Task a dict para el servicio
            task_dict = {
                "title": saved_task.title,
                "description": saved_task.description,
                "status": saved_task.status,
                "urgent": saved_task.urgent,
                "important": saved_task.important,
                "due_date": saved_task.due_date,
                "tags": saved_task.tags,
                "subtasks": [s.__dict__ for s in saved_task.subtasks] if saved_task.subtasks else [],
            }
            
            if task:
                # Editar
                if await self.task_service.update_task(saved_task.id, task_dict):
                    self._show_snackbar("Tarea actualizada correctamente", ft.Colors.GREEN_400)
            else:
                # Crear
                if await self.task_service.create_task(task_dict):
                    self._show_snackbar("Tarea creada correctamente", ft.Colors.GREEN_400)
            
            await self._load_tasks()
            if self.task_list:
                self.task_list.set_tasks(self.filtered_tasks)
            # No usar set_tasks en task_filters - no existe ese método
            self._update_header()
            self._hide_form()
        
        def handle_cancel():
            self._hide_form()
        
        form = TaskForm(
            page=self.page,
            task=task,
            on_save=handle_save,
            on_cancel=handle_cancel,
        )
        
        # Verificar que los containers no sean None antes de acceder a sus propiedades
        assert self.form_container is not None
        assert self.main_content is not None
        assert self.fab is not None
        
        self.form_container.content = form.build()
        self.form_container.visible = True
        self.main_content.visible = False
        self.fab.visible = False
        self.page.update()
    
    def _hide_form(self):
        """Oculta el formulario"""
        # Verificar que los containers no sean None antes de acceder a sus propiedades
        assert self.form_container is not None
        assert self.main_content is not None
        assert self.fab is not None
        
        self.form_container.visible = False
        self.main_content.visible = True
        self.fab.visible = True
        self.page.update()
    
    def _show_task_details(self, task: Task):
        """Muestra detalles de una tarea en un diálogo"""
        from app.ui.task.components.status_badge import create_status_badge
        from app.ui.task.components.priority_badge import create_priority_badge
        
        def close_dialog(e):
            dialog.open = False
            self.page.update()
        
        details = ft.Column(
            controls=[
                ft.Row([
                    create_status_badge(task.status, page=self.page),
                    create_priority_badge(task.urgent, task.important, page=self.page),
                ]),
                ft.Text(task.description or "Sin descripción", size=14),
                ft.Divider(),
                ft.Text(f"Fecha: {task.due_date.strftime('%d/%m/%Y') if task.due_date else 'Sin fecha'}", size=12),
                ft.Text(f"Subtareas: {len(task.subtasks)}", size=12),
                ft.Text(f"Tags: {', '.join(task.tags) if task.tags else 'Sin tags'}", size=12),
            ],
            spacing=8,
        )
        
        dialog = ft.AlertDialog(
            title=ft.Text(task.title),
            content=details,
            actions=[
                ft.TextButton("Cerrar", on_click=close_dialog),
            ],
        )
        
        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()
    
    def _update_header(self):
        """Actualiza el contador en el header"""
        if self.main_content and len(self.main_content.controls) > 0:
            header = self.main_content.controls[0]
            if isinstance(header, ft.Container):
                row = header.content
                if isinstance(row, ft.Row) and len(row.controls) > 1:
                    col = row.controls[1]
                    if isinstance(col, ft.Column) and len(col.controls) > 1:
                        col.controls[1].value = f"{len(self.tasks)} tareas totales"
                        self.page.update()
    
    def _show_snackbar(self, message: str, color: str):
        """Muestra mensaje en snackbar"""
        snackbar = ft.SnackBar(
            content=ft.Text(message, color=ft.Colors.WHITE),
            bgcolor=color,
        )
        self.page.overlay.append(snackbar)
        snackbar.open = True
        self.page.update()


