"""
Vista principal de la aplicación de tareas.
"""
import flet as ft
from typing import Optional
from app.data.models import Task
from app.services.task_service import TaskService
from app.ui.widgets import create_task_card, create_empty_state, create_statistics_card
from app.ui.task_form import TaskForm


class HomeView:
    """Vista principal de la aplicación."""
    
    def __init__(self, page: ft.Page):
        """
        Inicializa la vista principal.
        
        Args:
            page: Página de Flet.
        """
        self.page = page
        self.task_service = TaskService()
        self.current_filter: Optional[bool] = None
        self.editing_task: Optional[Task] = None
        
        # Contenedores principales
        self.tasks_container = ft.Column([], spacing=0, scroll=ft.ScrollMode.AUTO, expand=True)
        self.stats_card = None
        self.form_container = ft.Container(visible=False, expand=True)
        
        self._build_ui()
        self._load_tasks()
    
    def _build_ui(self):
        """Construye la interfaz de usuario."""
        # Botón para cambiar tema
        # Determinar el icono inicial según el tema actual
        initial_icon = ft.Icons.DARK_MODE if self.page.theme_mode == ft.ThemeMode.LIGHT else ft.Icons.LIGHT_MODE
        initial_tooltip = "Cambiar a tema oscuro" if self.page.theme_mode == ft.ThemeMode.LIGHT else "Cambiar a tema claro"
        
        self.theme_button = ft.IconButton(
            icon=initial_icon,
            tooltip=initial_tooltip,
            on_click=self._toggle_theme,
            icon_color=ft.Colors.RED_400
        )
        
        # Barra de título
        title_bar = ft.Container(
            content=ft.Row(
                [
                    ft.Text(
                        "Mis Tareas",
                        size=28,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.RED_400,
                        expand=True
                    ),
                    self.theme_button
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER
            ),
            padding=ft.padding.symmetric(vertical=16, horizontal=20),
            bgcolor=ft.Colors.BLACK87 if self.page.theme_mode == ft.ThemeMode.DARK else ft.Colors.RED_50
        )
        
        # Botón flotante para agregar tarea - color adaptativo
        is_dark = self.page.theme_mode == ft.ThemeMode.DARK
        fab_bgcolor = ft.Colors.RED_700 if is_dark else ft.Colors.RED_600
        
        self.fab = ft.FloatingActionButton(
            icon=ft.Icons.ADD,
            text="Nueva Tarea",
            on_click=self._show_new_task_form,
            bgcolor=fab_bgcolor,
            foreground_color=ft.Colors.WHITE
        )
        
        # Filtros - colores adaptativos según el tema
        is_dark = self.page.theme_mode == ft.ThemeMode.DARK
        active_bg = ft.Colors.RED_700 if is_dark else ft.Colors.RED_600
        inactive_bg = ft.Colors.GREY_800 if is_dark else ft.Colors.RED_100
        text_color = ft.Colors.WHITE
        
        filter_row = ft.Row(
            [
                ft.ElevatedButton(
                    text="Todas",
                    on_click=lambda e: self._filter_tasks(None),
                    bgcolor=active_bg if self.current_filter is None else inactive_bg,
                    color=text_color
                ),
                ft.ElevatedButton(
                    text="Pendientes",
                    on_click=lambda e: self._filter_tasks(False),
                    bgcolor=active_bg if self.current_filter is False else inactive_bg,
                    color=text_color
                ),
                ft.ElevatedButton(
                    text="Completadas",
                    on_click=lambda e: self._filter_tasks(True),
                    bgcolor=active_bg if self.current_filter is True else inactive_bg,
                    color=text_color
                )
            ],
            spacing=8,
            scroll=ft.ScrollMode.AUTO
        )
        
        # Contenedor de estadísticas
        stats_container = ft.Container(
            content=create_statistics_card(self.task_service.get_statistics(), self.page),
            visible=True
        )
        self.stats_container = stats_container
        
        # Vista principal (lista de tareas)
        main_view = ft.Container(
            content=ft.Column(
                [
                    stats_container,
                    filter_row,
                    self.tasks_container
                ],
                spacing=8,
                expand=True
            ),
            padding=16,
            expand=True
        )
        
        # Layout principal
        self.page.add(
            ft.Column(
                [
                    title_bar,
                    ft.Row(
                        [
                            main_view,
                            self.form_container
                        ],
                        expand=True,
                        spacing=0
                    )
                ],
                spacing=0,
                expand=True
            )
        )
        
        self.page.floating_action_button = self.fab
    
    def _load_tasks(self):
        """Carga las tareas desde la base de datos."""
        tasks = self.task_service.get_all_tasks(self.current_filter)
        self.tasks_container.controls.clear()
        
        if not tasks:
            self.tasks_container.controls.append(create_empty_state(self.page))
        else:
            for task in tasks:
                card = create_task_card(
                    task,
                    on_toggle=self._toggle_task,
                    on_edit=self._edit_task,
                    on_delete=self._delete_task,
                    page=self.page
                )
                self.tasks_container.controls.append(card)
        
        # Actualizar estadísticas
        stats = self.task_service.get_statistics()
        self.stats_container.content = create_statistics_card(stats, self.page)
        
        self.tasks_container.update()
        self.stats_container.update()
        self.page.update()
    
    def _filter_tasks(self, filter_completed: Optional[bool]):
        """Filtra las tareas por estado."""
        self.current_filter = filter_completed
        self._load_tasks()
        self._rebuild_filters()
    
    def _rebuild_filters(self):
        """Reconstruye los botones de filtro con los colores correctos."""
        # Esta función se puede mejorar para actualizar los colores dinámicamente
        self._load_tasks()
    
    def _show_new_task_form(self, e):
        """Muestra el formulario para crear una nueva tarea."""
        self.editing_task = None
        form = TaskForm(
            on_save=self._save_task,
            on_cancel=self._hide_form
        )
        self.form_container.content = form.build()
        self.form_container.visible = True
        self.fab.visible = False
        self.page.update()
    
    def _edit_task(self, task: Task):
        """Muestra el formulario para editar una tarea."""
        self.editing_task = task
        form = TaskForm(
            on_save=self._save_task,
            on_cancel=self._hide_form,
            task=task
        )
        self.form_container.content = form.build()
        self.form_container.visible = True
        self.fab.visible = False
        self.page.update()
    
    def _hide_form(self):
        """Oculta el formulario."""
        self.form_container.visible = False
        self.fab.visible = True
        self.editing_task = None
        self.page.update()
    
    def _save_task(self, *args):
        """Guarda una tarea (crear o actualizar)."""
        # Si el primer argumento es un objeto Task, es una actualización
        if args and isinstance(args[0], Task):
            # Actualizar tarea existente
            task = args[0]
            self.task_service.update_task(task)
        else:
            # Crear nueva tarea
            title, description, priority = args
            self.task_service.create_task(title, description, priority)
        
        self._hide_form()
        self._load_tasks()
    
    def _toggle_task(self, task_id: int):
        """Cambia el estado de completado de una tarea."""
        self.task_service.toggle_task_complete(task_id)
        self._load_tasks()
    
    def _delete_task(self, task_id: int):
        """Elimina una tarea."""
        if task_id is None:
            return
        
        # Eliminar directamente primero para verificar que funciona
        try:
            deleted = self.task_service.delete_task(int(task_id))
            if deleted:
                self._load_tasks()
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text("Tarea eliminada correctamente"),
                    bgcolor=ft.Colors.RED_700
                )
                self.page.snack_bar.open = True
            else:
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text("No se pudo eliminar la tarea"),
                    bgcolor=ft.Colors.RED
                )
                self.page.snack_bar.open = True
        except Exception as ex:
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"Error: {str(ex)}"),
                bgcolor=ft.Colors.RED
            )
            self.page.snack_bar.open = True
        
        self.page.update()
    
    def _toggle_theme(self, e):
        """Cambia entre tema claro y oscuro."""
        if self.page.theme_mode == ft.ThemeMode.LIGHT:
            self.page.theme_mode = ft.ThemeMode.DARK
            self.page.bgcolor = ft.Colors.BLACK
            self.theme_button.icon = ft.Icons.LIGHT_MODE
            self.theme_button.tooltip = "Cambiar a tema claro"
            # Actualizar FAB
            self.fab.bgcolor = ft.Colors.RED_700
        else:
            self.page.theme_mode = ft.ThemeMode.LIGHT
            self.page.bgcolor = ft.Colors.GREY_50
            self.theme_button.icon = ft.Icons.DARK_MODE
            self.theme_button.tooltip = "Cambiar a tema oscuro"
            # Actualizar FAB
            self.fab.bgcolor = ft.Colors.RED_600
        
        # Solo recargar las tareas para actualizar los colores adaptativos
        # No reconstruir toda la UI para evitar duplicados
        self._load_tasks()
        self.page.update()

