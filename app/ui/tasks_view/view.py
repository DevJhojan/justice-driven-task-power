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
    
    def build_ui(self) -> ft.Container:
        """
        Construye la interfaz de usuario de tareas con Matriz de Eisenhower.
        
        Returns:
            Container con la vista completa de tareas.
        """
        from .utils import is_desktop_platform, get_screen_width
        
        is_desktop = is_desktop_platform(self.page)
        
        # Barra de navegación de prioridades
        priority_nav = build_priority_navigation_bar(
            self.page,
            self.current_priority_section,
            self._scroll_to_priority,
            self._show_new_task_form
        )
        
        # Construir las 4 secciones de prioridad
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
        
        # Contenedor principal con scroll - responsive
        section_spacing = 24 if is_desktop else 16
        # Usar ListView para mejor soporte de scroll programático
        self.main_scroll_listview = ft.ListView(
            priority_sections,
            spacing=section_spacing,
            expand=True,
            padding=0
        )
        main_scroll_content = self.main_scroll_listview
        
        # Padding responsive para el contenedor principal - reducido
        main_padding = ft.padding.only(
            bottom=24 if is_desktop else 16,
            left=0,
            right=0,
            top=0
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
        
        # Vista principal - sin spacing para acercar elementos
        return ft.Container(
            content=ft.Column(
                [
                    priority_nav,
                    self.main_scroll_container
                ],
                spacing=0,
                expand=True
            ),
            expand=True
        )
    
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
            self._edit_subtask
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
        # Esta función se implementará si es necesario para actualizar la navegación
        pass
    
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
            self._show_new_task_form
        )

