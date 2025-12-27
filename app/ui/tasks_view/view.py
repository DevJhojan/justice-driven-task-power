"""
Vista principal de tareas - Orquesta todos los módulos.
"""
import flet as ft
from typing import Optional
from app.data.models import Task, SubTask
from app.services.task_service import TaskService

from .utils import PRIORITIES, PRIORITY_ORDER
from .navigation import build_priority_navigation_bar
from .priority_sections import build_priority_section
from .task_management import (
    load_tasks_into_containers,
    toggle_task,
    delete_task as delete_task_func,
    save_task
)
from .subtask_management import toggle_subtask, delete_subtask
from .forms import navigate_to_task_form, navigate_to_subtask_form


class TasksView:
    """Vista dedicada para gestionar tareas con Matriz de Eisenhower."""
    
    def __init__(self, page: ft.Page, task_service: TaskService, on_go_back: callable):
        """
        Inicializa la vista de tareas.
        
        Args:
            page: Página de Flet.
            task_service: Servicio para gestionar tareas.
            on_go_back: Callback para volver a la vista anterior.
        """
        self.page = page
        self.task_service = task_service
        self.on_go_back = on_go_back
        
        # Cargar preferencia de vista desde SettingsService
        from app.services.settings_service import SettingsService
        self.settings_service = SettingsService()
        settings = self.settings_service.get_settings()
        self.current_view_mode = settings.tasks_view_mode
        
        # Filtros por sección de prioridad: {priority: filter_value}
        self.priority_filters = {
            'urgent_important': None,  # None=all, True=completed, False=pending
            'not_urgent_important': None,
            'urgent_not_important': None,
            'not_urgent_not_important': None
        }
        self.current_priority_section = 'urgent_important'  # Prioridad activa visible
        self.editing_task: Optional[Task] = None
        self.editing_subtask_task_id: Optional[int] = None
        self.editing_subtask = None
        
        # Contenedores principales para cada prioridad - responsive
        self.priority_containers = {
            'urgent_important': ft.Column([], spacing=0, scroll=ft.ScrollMode.AUTO),
            'not_urgent_important': ft.Column([], spacing=0, scroll=ft.ScrollMode.AUTO),
            'urgent_not_important': ft.Column([], spacing=0, scroll=ft.ScrollMode.AUTO),
            'not_urgent_not_important': ft.Column([], spacing=0, scroll=ft.ScrollMode.AUTO)
        }
        self.priority_section_refs = {}  # Referencias a los contenedores de sección para scroll
        self.main_scroll_container = None  # Contenedor principal con scroll
        self.main_scroll_listview = None  # Referencia directa al ListView para scroll programático
        self.priority_nav_container = None  # Referencia al contenedor de la barra de navegación
        self.main_view_container = None  # Referencia al contenedor principal de la vista
    
    def build_ui(self) -> ft.Container:
        """
        Construye la interfaz de usuario de tareas con Matriz de Eisenhower.
        
        Returns:
            Container con la vista completa de tareas.
        """
        from .utils import is_desktop_platform, get_screen_width
        
        is_desktop = is_desktop_platform(self.page)
        
        # Barra de navegación de prioridades (o solo botones de vista/agregar en lista_normal)
        priority_nav = build_priority_navigation_bar(
            self.page,
            self.current_priority_section,
            self._scroll_to_priority,
            self._show_new_task_form,
            self.current_view_mode,
            self._change_view_mode
        )
        # Guardar referencia a la barra de navegación para poder actualizarla
        self.priority_nav_container = priority_nav
        
        # Si está en modo lista_normal, mostrar solo un contenedor simple con todas las tareas
        if self.current_view_mode == "lista_normal":
            # Contenedor único para todas las tareas (sin separación por prioridad)
            # Usaremos el contenedor de la primera prioridad como contenedor único
            all_tasks_container = ft.Column([], spacing=0, scroll=ft.ScrollMode.AUTO, expand=True)
            self.priority_containers['urgent_important'] = all_tasks_container
            
            # Padding responsive para el contenedor principal
            main_padding = ft.padding.only(
                bottom=24 if is_desktop else 16,
                left=16 if is_desktop else 12,
                right=16 if is_desktop else 12,
                top=16 if is_desktop else 12
            )
            
            # Contenedor principal con scroll
            self.main_scroll_container = ft.Container(
                content=all_tasks_container,
                padding=main_padding,
                expand=True,
                width=None
            )
        else:
            # Construir las 4 secciones de prioridad (modo Matriz de Eisenhower o Kanban)
            priority_sections = [
                build_priority_section(
                    self.page,
                    priority,
                    self.priority_filters,
                    self.priority_containers[priority],
                    self._filter_priority_tasks,
                    self.priority_section_refs
                )
                for priority in PRIORITIES
            ]
            
            # Contenedor principal con scroll - responsive - más compacto
            section_spacing = 16 if is_desktop else 12  # Reducido de 24/16 a 16/12
            # Usar ListView para mejor soporte de scroll programático
            self.main_scroll_listview = ft.ListView(
                priority_sections,
                spacing=section_spacing,
                expand=True,
                padding=0
            )
            main_scroll_content = self.main_scroll_listview
            
            # Padding responsive para el contenedor principal - sin padding superior
            main_padding = ft.padding.only(
                bottom=24 if is_desktop else 16,
                left=0,
                right=0,
                top=0  # Sin padding superior para eliminar espacio en blanco
            )
            
            # Detectar ancho de pantalla para layout adaptable
            screen_width = get_screen_width(self.page)
            
            # En escritorio con pantalla grande, centrar con ancho máximo; en pantallas pequeñas, usar todo el ancho
            if is_desktop and isinstance(screen_width, (int, float)) and screen_width > 1200:
                self.main_scroll_container = ft.Container(
                    content=ft.Row(
                        [
                            ft.Container(width=0, expand=True),  # Espaciador izquierdo
                            ft.Container(
                                content=main_scroll_content,
                                width=1200,  # Ancho máximo para legibilidad en pantallas grandes
                                expand=False
                            ),
                            ft.Container(width=0, expand=True)  # Espaciador derecho
                        ],
                        alignment=ft.MainAxisAlignment.CENTER
                    ),
                    padding=main_padding,
                    expand=True
                )
            else:
                # En pantallas pequeñas o medianas, usar todo el ancho disponible
                self.main_scroll_container = ft.Container(
                    content=main_scroll_content,
                    padding=main_padding,
                    expand=True,
                    width=None
                )
        
        # Vista principal - sin spacing ni márgenes para acercar elementos
        main_view_container = ft.Container(
            content=ft.Column(
                [
                    priority_nav,
                    self.main_scroll_container
                ],
                spacing=0,
                expand=True
            ),
            expand=True,
            margin=ft.margin.only(top=0, bottom=0),  # Sin márgenes para eliminar espacio en blanco
            padding=0  # Sin padding adicional
        )
        # Guardar referencia al contenedor principal
        self.main_view_container = main_view_container
        return main_view_container
    
    def load_tasks(self):
        """Carga las tareas desde la base de datos y las distribuye por prioridad."""
        load_tasks_into_containers(
            self.page,
            self.task_service,
            self.priority_containers,
            self.priority_filters,
            self._toggle_task,
            self._edit_task,
            self._delete_task,
            self._toggle_subtask,
            self._show_add_subtask_dialog,
            self._delete_subtask,
            self._edit_subtask,
            self.current_view_mode
        )
    
    def _filter_priority_tasks(self, priority: str, filter_completed: Optional[bool]):
        """Filtra las tareas de una prioridad específica."""
        self.priority_filters[priority] = filter_completed
        self.load_tasks()
        # Reconstruir la sección para actualizar los botones de filtro
        self._rebuild_priority_section(priority)
    
    def _rebuild_priority_section(self, priority: str):
        """Reconstruye una sección de prioridad específica."""
        # Encontrar el ListView principal y reemplazar la sección
        if self.main_scroll_listview:
            # Encontrar el índice de la sección
            try:
                index = PRIORITY_ORDER[priority]
                # Reconstruir la sección
                new_section = build_priority_section(
                    self.page,
                    priority,
                    self.priority_filters,
                    self.priority_containers[priority],
                    self._filter_priority_tasks,
                    self.priority_section_refs
                )
                # Reemplazar en el ListView
                if index < len(self.main_scroll_listview.controls):
                    self.main_scroll_listview.controls[index] = new_section
                    self.priority_section_refs[priority] = new_section
            except (KeyError, IndexError):
                pass
        
        # Actualizar barra de navegación
        self._update_priority_navigation()
        self.page.update()
    
    def _update_priority_navigation(self):
        """Actualiza la barra de navegación de prioridades."""
        # Reconstruir la barra de navegación para reflejar el cambio de prioridad
        if self.main_view_container and self.main_view_container.content:
            main_column = self.main_view_container.content
            if isinstance(main_column, ft.Column) and len(main_column.controls) > 0:
                # Reconstruir la barra de navegación con el estado actualizado
                from .navigation import build_priority_navigation_bar
                new_nav = build_priority_navigation_bar(
                    self.page,
                    self.current_priority_section,
                    self._scroll_to_priority,
                    self._show_new_task_form,
                    self.current_view_mode,
                    self._change_view_mode
                )
                # Reemplazar la barra de navegación antigua
                main_column.controls[0] = new_nav
                self.priority_nav_container = new_nav
    
    def _change_view_mode(self, view_mode: str):
        """Cambia el modo de vista de las tareas."""
        self.current_view_mode = view_mode
        # Guardar preferencia
        self.settings_service.update_settings(tasks_view_mode=view_mode)
        # Reconstruir la UI completamente para reflejar el cambio de modo
        self._rebuild_ui_for_view_mode()
        # Recargar tareas con la nueva vista
        self.load_tasks()
        self.page.update()
    
    def _rebuild_ui_for_view_mode(self):
        """Reconstruye la UI cuando cambia el modo de vista."""
        from .utils import is_desktop_platform, get_screen_width
        
        is_desktop = is_desktop_platform(self.page)
        
        # Actualizar la barra de navegación
        new_nav = build_priority_navigation_bar(
            self.page,
            self.current_priority_section,
            self._scroll_to_priority,
            self._show_new_task_form,
            self.current_view_mode,
            self._change_view_mode
        )
        self.priority_nav_container = new_nav
        
        # Reconstruir el contenedor principal según el modo de vista
        if self.current_view_mode == "lista_normal":
            # Contenedor único para todas las tareas
            all_tasks_container = ft.Column([], spacing=0, scroll=ft.ScrollMode.AUTO, expand=True)
            self.priority_containers['urgent_important'] = all_tasks_container
            
            # Padding responsive
            main_padding = ft.padding.only(
                bottom=24 if is_desktop else 16,
                left=16 if is_desktop else 12,
                right=16 if is_desktop else 12,
                top=16 if is_desktop else 12
            )
            
            self.main_scroll_container = ft.Container(
                content=all_tasks_container,
                padding=main_padding,
                expand=True,
                width=None
            )
            self.main_scroll_listview = None  # No se usa en lista_normal
        else:
            # Reconstruir las 4 secciones de prioridad
            priority_sections = [
                build_priority_section(
                    self.page,
                    priority,
                    self.priority_filters,
                    self.priority_containers[priority],
                    self._filter_priority_tasks,
                    self.priority_section_refs
                )
                for priority in PRIORITIES
            ]
            
            section_spacing = 16 if is_desktop else 12
            self.main_scroll_listview = ft.ListView(
                priority_sections,
                spacing=section_spacing,
                expand=True,
                padding=0
            )
            main_scroll_content = self.main_scroll_listview
            
            main_padding = ft.padding.only(
                bottom=24 if is_desktop else 16,
                left=0,
                right=0,
                top=0
            )
            
            screen_width = get_screen_width(self.page)
            if is_desktop and isinstance(screen_width, (int, float)) and screen_width > 1200:
                self.main_scroll_container = ft.Container(
                    content=ft.Row(
                        [
                            ft.Container(width=0, expand=True),
                            ft.Container(
                                content=main_scroll_content,
                                width=1200,
                                expand=False
                            ),
                            ft.Container(width=0, expand=True)
                        ],
                        alignment=ft.MainAxisAlignment.CENTER
                    ),
                    padding=main_padding,
                    expand=True
                )
            else:
                self.main_scroll_container = ft.Container(
                    content=main_scroll_content,
                    padding=main_padding,
                    expand=True,
                    width=None
                )
        
        # Actualizar el contenedor principal de la vista
        if self.main_view_container and self.main_view_container.content:
            main_column = self.main_view_container.content
            if isinstance(main_column, ft.Column) and len(main_column.controls) >= 2:
                main_column.controls[0] = new_nav
                main_column.controls[1] = self.main_scroll_container
    
    def _scroll_to_priority(self, priority: str):
        """Hace scroll automático hasta la sección de prioridad especificada."""
        self.current_priority_section = priority
        
        # Actualizar la barra de navegación para reflejar el estado activo
        self._update_priority_navigation()
        
        # Obtener el índice de la sección
        target_index = PRIORITY_ORDER.get(priority, 0)
        
        # Hacer scroll al índice correspondiente usando la referencia directa al ListView
        if self.main_scroll_listview:
            try:
                # Intentar usar scroll_to con index (más preciso)
                self.main_scroll_listview.scroll_to(
                    index=target_index,
                    duration=500,
                    curve=ft.AnimationCurve.EASE_OUT
                )
            except (AttributeError, TypeError) as e:
                # Si scroll_to con index no está disponible o falla, usar offset
                print(f"Intentando scroll con offset (index no disponible): {e}")
                try:
                    # Calcular offset aproximado
                    estimated_offset = target_index * 500
                    self.main_scroll_listview.scroll_to(
                        offset=estimated_offset,
                        duration=500,
                        curve=ft.AnimationCurve.EASE_OUT
                    )
                except Exception as e2:
                    print(f"Error en scroll_to: {e2}")
        
        self.page.update()
    
    def _show_new_task_form(self, e):
        """Navega a la vista del formulario para crear una nueva tarea."""
        self.editing_task = None
        self._navigate_to_form_view()
    
    def _edit_task(self, task: Task):
        """Navega a la vista del formulario para editar una tarea."""
        self.editing_task = task
        self._navigate_to_form_view()
    
    def _navigate_to_form_view(self):
        """Navega a la vista del formulario."""
        navigate_to_task_form(
            self.page,
            self.editing_task,
            self._save_task,
            self._go_back_from_form
        )
    
    def _go_back_from_form(self, e=None):
        """Vuelve a la vista principal desde un formulario."""
        self.editing_task = None
        # Usar el callback proporcionado
        if self.on_go_back:
            self.on_go_back(e)
        else:
            # Fallback si no hay callback
            if len(self.page.views) > 1:
                self.page.views.pop()
            if self.page.views:
                self.page.go(self.page.views[-1].route)
            else:
                self.page.go("/")
            self.page.update()
    
    def _save_task(self, *args):
        """Guarda una tarea (crear o actualizar)."""
        save_task(self.task_service, *args)
        
        # Volver a la vista principal
        self._go_back_from_form()
        
        # Forzar actualización de la página antes de recargar tareas
        self.page.update()
        
        # Recargar las tareas después de volver
        self.load_tasks()
    
    def _toggle_task(self, task_id: int):
        """Cambia el estado de completado de una tarea."""
        toggle_task(self.task_service, task_id)
        self.load_tasks()
    
    def _delete_task(self, task_id: int):
        """Elimina una tarea."""
        deleted = delete_task_func(self.page, self.task_service, task_id)
        if deleted:
            self.load_tasks()
    
    def _toggle_subtask(self, subtask_id: int):
        """Cambia el estado de completado de una subtarea."""
        toggle_subtask(self.task_service, subtask_id)
        self.load_tasks()
    
    def _delete_subtask(self, subtask_id: int):
        """Elimina una subtarea."""
        delete_subtask(self.task_service, subtask_id)
        self.load_tasks()
    
    def _show_add_subtask_dialog(self, task_id: int):
        """Navega a la vista del formulario para agregar una subtarea."""
        # Guardar el task_id para usarlo al guardar
        self.editing_subtask_task_id = task_id
        self.editing_subtask = None
        self._navigate_to_subtask_form_view()
    
    def _edit_subtask(self, subtask):
        """Navega a la vista del formulario para editar una subtarea."""
        # Guardar la subtarea y el task_id para usarlos al guardar
        self.editing_subtask = subtask
        self.editing_subtask_task_id = subtask.task_id
        self._navigate_to_subtask_form_view()
    
    def _navigate_to_subtask_form_view(self):
        """Navega a la vista del formulario de subtarea."""
        navigate_to_subtask_form(
            self.page,
            self.task_service,
            self.editing_subtask,
            self.editing_subtask_task_id,
            self._go_back_from_form,
            self.load_tasks
        )
    
    # ==================== MÉTODOS DE COMPATIBILIDAD PARA HOME_VIEW ====================
    # Estos métodos se mantienen para compatibilidad con home_view.py que los llama directamente
    
    def _get_priority_colors(self, priority: str) -> dict:
        """Obtiene los colores para una prioridad específica (wrapper para compatibilidad)."""
        from .utils import get_priority_colors
        is_dark = self.page.theme_mode == ft.ThemeMode.DARK
        return get_priority_colors(priority, is_dark)
    
    def _build_priority_section(self, priority: str) -> ft.Container:
        """Construye una sección de prioridad (wrapper para compatibilidad)."""
        return build_priority_section(
            self.page,
            priority,
            self.priority_filters,
            self.priority_containers[priority],
            self._filter_priority_tasks,
            self.priority_section_refs
        )
    
    def _build_priority_navigation_bar(self) -> ft.Container:
        """Construye la barra de navegación de prioridades (wrapper para compatibilidad)."""
        return build_priority_navigation_bar(
            self.page,
            self.current_priority_section,
            self._scroll_to_priority,
            self._show_new_task_form,
            self.current_view_mode,
            self._change_view_mode
        )

