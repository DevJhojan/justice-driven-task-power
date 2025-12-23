"""
Vista de tareas - Módulo separado para gestionar todas las funcionalidades de tareas.
"""
import flet as ft
from typing import Optional
from datetime import datetime
from app.data.models import Task, SubTask
from app.services.task_service import TaskService
from app.ui.widgets import create_task_card
from app.ui.task_form import TaskForm


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
    
    def _get_priority_colors(self, priority: str) -> dict:
        """Obtiene los colores para una prioridad específica."""
        is_dark = self.page.theme_mode == ft.ThemeMode.DARK
        colors = {
            'urgent_important': {
                'primary': ft.Colors.RED_600,
                'light': ft.Colors.RED_50 if not is_dark else ft.Colors.RED_900,
                'bg': ft.Colors.RED_100 if not is_dark else ft.Colors.RED_900,
                'text': '🔴 Urgente e Importante'
            },
            'not_urgent_important': {
                'primary': ft.Colors.GREEN_600,
                'light': ft.Colors.GREEN_50 if not is_dark else ft.Colors.GREEN_900,
                'bg': ft.Colors.GREEN_100 if not is_dark else ft.Colors.GREEN_900,
                'text': '🟢 No Urgente e Importante'
            },
            'urgent_not_important': {
                'primary': ft.Colors.ORANGE_600,
                'light': ft.Colors.ORANGE_50 if not is_dark else ft.Colors.ORANGE_900,
                'bg': ft.Colors.ORANGE_100 if not is_dark else ft.Colors.ORANGE_900,
                'text': '🟡 Urgente y No Importante'
            },
            'not_urgent_not_important': {
                'primary': ft.Colors.GREY_500,
                'light': ft.Colors.GREY_50 if not is_dark else ft.Colors.GREY_800,
                'bg': ft.Colors.GREY_100 if not is_dark else ft.Colors.GREY_800,
                'text': '⚪ No Urgente y No Importante'
            }
        }
        return colors.get(priority, colors['not_urgent_important'])
    
    def _build_priority_section(self, priority: str) -> ft.Container:
        """Construye una sección de prioridad con su filtro y tareas."""
        colors = self._get_priority_colors(priority)
        is_dark = self.page.theme_mode == ft.ThemeMode.DARK
        current_filter = self.priority_filters[priority]
        
        # Detectar si es escritorio o móvil
        is_desktop = self.page.platform == ft.PagePlatform.WINDOWS or self.page.platform == ft.PagePlatform.LINUX or self.page.platform == ft.PagePlatform.MACOS
        
        # Título de la sección - responsive y adaptable
        try:
            screen_width = self.page.width if (hasattr(self.page, 'width') and self.page.width is not None and isinstance(self.page.width, (int, float))) else 1024
        except (AttributeError, TypeError):
            screen_width = 1024
        is_wide = screen_width > 600 if isinstance(screen_width, (int, float)) else False
        
        title_size = 22 if is_wide else 18
        title_padding_vertical = 10 if is_wide else 8
        title_padding_horizontal = 20 if is_wide else 12
        
        section_title = ft.Container(
            content=ft.Row(
                [
                    ft.Text(
                        colors['text'],
                        size=title_size,
                        weight=ft.FontWeight.BOLD,
                        color=colors['primary'],
                        expand=True,
                        max_lines=2,
                        overflow=ft.TextOverflow.ELLIPSIS,
                        selectable=False
                    )
                ],
                expand=True,
                wrap=False
            ),
            padding=ft.padding.symmetric(
                vertical=title_padding_vertical,
                horizontal=title_padding_horizontal
            ),
            bgcolor=colors['light'],
            border=ft.border.only(bottom=ft.BorderSide(2, colors['primary'])),
            expand=True,
            margin=ft.margin.only(top=0)
        )
        
        # Botones de filtro para esta sección - responsive
        active_bg = colors['primary']
        inactive_bg = ft.Colors.GREY_800 if is_dark else ft.Colors.GREY_100
        text_color = ft.Colors.WHITE
        button_height = 40 if is_desktop else 36
        button_padding = ft.padding.symmetric(vertical=12 if is_desktop else 8, horizontal=24 if is_desktop else 16)
        
        # Botones de filtro responsive
        filter_buttons = ft.Row(
            [
                ft.ElevatedButton(
                    text="Todas",
                    on_click=lambda e, p=priority: self._filter_priority_tasks(p, None),
                    bgcolor=active_bg if current_filter is None else inactive_bg,
                    color=text_color,
                    height=button_height,
                    style=ft.ButtonStyle(
                        shape=ft.RoundedRectangleBorder(radius=8)
                    ),
                    expand=True if is_desktop else False
                ),
                ft.ElevatedButton(
                    text="Pendientes",
                    on_click=lambda e, p=priority: self._filter_priority_tasks(p, False),
                    bgcolor=active_bg if current_filter is False else inactive_bg,
                    color=text_color,
                    height=button_height,
                    style=ft.ButtonStyle(
                        shape=ft.RoundedRectangleBorder(radius=8)
                    ),
                    expand=True if is_desktop else False
                ),
                ft.ElevatedButton(
                    text="Completadas",
                    on_click=lambda e, p=priority: self._filter_priority_tasks(p, True),
                    bgcolor=active_bg if current_filter is True else inactive_bg,
                    color=text_color,
                    height=button_height,
                    style=ft.ButtonStyle(
                        shape=ft.RoundedRectangleBorder(radius=8)
                    ),
                    expand=True if is_desktop else False
                )
            ],
            spacing=12 if is_desktop else 8,
            scroll=ft.ScrollMode.AUTO if not is_desktop else ft.ScrollMode.HIDDEN,
            wrap=False,
            expand=True
        )
        
        # Contenedor de tareas para esta prioridad
        tasks_container = self.priority_containers[priority]
        
        # Contenedor completo de la sección - responsive y adaptable
        section_padding = 20 if is_desktop else 12
        section_container = ft.Container(
            content=ft.Column(
                [
                    section_title,
                    ft.Container(
                        content=filter_buttons,
                        padding=button_padding,
                        expand=True
                    ),
                    ft.Container(
                        content=tasks_container,
                        padding=ft.padding.symmetric(
                            horizontal=section_padding
                        ),
                        expand=True
                    )
                ],
                spacing=0,
                expand=True
            ),
            key=f"priority_section_{priority}",
            margin=ft.margin.only(
                bottom=16 if is_desktop else 12,
                top=0
            ),
            expand=True
        )
        
        # Guardar referencia para scroll
        self.priority_section_refs[priority] = section_container
        
        return section_container
    
    def _build_priority_navigation_bar(self) -> ft.Container:
        """Construye la barra de navegación con 4 botones para las prioridades."""
        is_dark = self.page.theme_mode == ft.ThemeMode.DARK
        is_desktop = self.page.platform == ft.PagePlatform.WINDOWS or self.page.platform == ft.PagePlatform.LINUX or self.page.platform == ft.PagePlatform.MACOS
        bgcolor = ft.Colors.BLACK87 if is_dark else ft.Colors.WHITE
        
        buttons = []
        priorities = [
            ('urgent_important', '🔴', 'Urgente e\nImportante'),
            ('not_urgent_important', '🟢', 'No Urgente e\nImportante'),
            ('urgent_not_important', '🟡', 'Urgente y No\nImportante'),
            ('not_urgent_not_important', '⚪', 'No Urgente y No\nImportante')
        ]
        
        # Detectar ancho de pantalla para ajustar tamaños
        try:
            screen_width = self.page.width if (hasattr(self.page, 'width') and self.page.width is not None and isinstance(self.page.width, (int, float))) else 1024
        except (AttributeError, TypeError):
            screen_width = 1024
        is_wide_screen = screen_width > 600 if isinstance(screen_width, (int, float)) else False
        
        for priority_key, emoji, label in priorities:
            colors = self._get_priority_colors(priority_key)
            is_active = self.current_priority_section == priority_key
            
            # Tamaños responsive basados en ancho de pantalla
            emoji_size = 22 if is_wide_screen else 18
            text_size = 10 if is_wide_screen else 9
            button_padding = 10 if is_wide_screen else 6
            
            button = ft.Container(
                content=ft.Column(
                    [
                        ft.Text(emoji, size=emoji_size),
                        ft.Text(
                            label,
                            size=text_size,
                            text_align=ft.TextAlign.CENTER,
                            max_lines=2,
                            overflow=ft.TextOverflow.ELLIPSIS,
                            selectable=False
                        )
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=4,
                    tight=True
                ),
                on_click=lambda e, p=priority_key: self._scroll_to_priority(p),
                padding=button_padding,
                bgcolor=colors['primary'] if is_active else bgcolor,
                border=ft.border.all(2, colors['primary'] if is_active else ft.Colors.TRANSPARENT),
                border_radius=8,
                expand=True,
                tooltip=colors['text']
            )
            buttons.append(button)
        
        # Botón de agregar tarea
        scheme = self.page.theme.color_scheme if self.page.theme else None
        title_color = scheme.primary if scheme and scheme.primary else ft.Colors.RED_400
        button_size = 40 if is_wide_screen else 36
        icon_size = 20 if is_wide_screen else 18
        
        add_button = ft.IconButton(
            icon=ft.Icons.ADD,
            on_click=self._show_new_task_form,
            bgcolor=title_color,
            icon_color=ft.Colors.WHITE,
            tooltip="Nueva Tarea",
            width=button_size,
            height=button_size,
            icon_size=icon_size
        )
        
        # Contenedor responsive con padding vertical mínimo
        nav_padding = ft.padding.symmetric(
            vertical=4 if is_wide_screen else 3,
            horizontal=20 if is_wide_screen else 12
        )
        button_spacing = 10 if is_wide_screen else 6
        
        # Crear Row con botones de prioridad y botón de agregar
        row_controls = buttons.copy()
        row_controls.append(add_button)
        
        return ft.Container(
            content=ft.Row(
                row_controls,
                spacing=button_spacing,
                scroll=ft.ScrollMode.AUTO if not is_wide_screen else ft.ScrollMode.HIDDEN,
                wrap=False,
                expand=True
            ),
            padding=nav_padding,
            bgcolor=bgcolor,
            border=ft.border.only(bottom=ft.BorderSide(1, ft.Colors.GREY_300 if not is_dark else ft.Colors.GREY_700)),
            expand=True,
            margin=ft.margin.only(bottom=0)
        )
    
    def build_ui(self) -> ft.Container:
        """
        Construye la interfaz de usuario de tareas con Matriz de Eisenhower.
        
        Returns:
            Container con la vista completa de tareas.
        """
        is_desktop = self.page.platform == ft.PagePlatform.WINDOWS or self.page.platform == ft.PagePlatform.LINUX or self.page.platform == ft.PagePlatform.MACOS
        
        # Barra de navegación de prioridades
        priority_nav = self._build_priority_navigation_bar()
        
        # Construir las 4 secciones de prioridad
        priority_sections = [
            self._build_priority_section('urgent_important'),
            self._build_priority_section('not_urgent_important'),
            self._build_priority_section('urgent_not_important'),
            self._build_priority_section('not_urgent_not_important')
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
        try:
            screen_width = self.page.width if (hasattr(self.page, 'width') and self.page.width is not None and isinstance(self.page.width, (int, float))) else 1024
        except (AttributeError, TypeError):
            screen_width = 1024
        
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
        # Cargar todas las tareas sin filtro global
        all_tasks = self.task_service.get_all_tasks(None)
        
        # Limpiar todos los contenedores de prioridad
        for priority in self.priority_containers:
            self.priority_containers[priority].controls.clear()
        
        # Distribuir tareas por prioridad y aplicar filtro de cada sección
        for priority in ['urgent_important', 'not_urgent_important', 'urgent_not_important', 'not_urgent_not_important']:
            container = self.priority_containers[priority]
            filter_value = self.priority_filters[priority]
            
            # Filtrar tareas de esta prioridad
            priority_tasks = [t for t in all_tasks if t.priority == priority]
            
            # Aplicar filtro de completado si existe
            if filter_value is not None:
                priority_tasks = [t for t in priority_tasks if t.completed == filter_value]
            
            # Agregar tareas al contenedor
            if not priority_tasks:
                # Mostrar estado vacío solo si hay filtro activo
                if filter_value is not None:
                    empty_text = "Completadas" if filter_value else "Pendientes"
                    container.controls.append(
                        ft.Container(
                            content=ft.Text(
                                f"No hay tareas {empty_text.lower()} en esta prioridad",
                                size=14,
                                color=ft.Colors.GREY_500,
                                text_align=ft.TextAlign.CENTER
                            ),
                            padding=20,
                            alignment=ft.alignment.center
                        )
                    )
            else:
                # Detectar ancho de pantalla para decidir layout
                is_desktop = self.page.platform == ft.PagePlatform.WINDOWS or self.page.platform == ft.PagePlatform.LINUX or self.page.platform == ft.PagePlatform.MACOS
                try:
                    screen_width = self.page.width if (hasattr(self.page, 'width') and self.page.width is not None and isinstance(self.page.width, (int, float))) else 1024
                except (AttributeError, TypeError):
                    screen_width = 1024
                use_grid = is_desktop and isinstance(screen_width, (int, float)) and screen_width > 800 and len(priority_tasks) > 1
                
                if use_grid:
                    # En escritorio con suficiente ancho, mostrar en grid de 2 columnas
                    tasks_per_row = 2
                    for i in range(0, len(priority_tasks), tasks_per_row):
                        row_tasks = priority_tasks[i:i + tasks_per_row]
                        row_cards = []
                        for idx, task in enumerate(row_tasks):
                            card = create_task_card(
                                task,
                                on_toggle=self._toggle_task,
                                on_edit=self._edit_task,
                                on_delete=self._delete_task,
                                on_toggle_subtask=self._toggle_subtask,
                                on_add_subtask=self._show_add_subtask_dialog,
                                on_delete_subtask=self._delete_subtask,
                                on_edit_subtask=self._edit_subtask,
                                page=self.page
                            )
                            # Contenedor flexible que se adapta al ancho disponible
                            row_cards.append(
                                ft.Container(
                                    content=card,
                                    expand=True,
                                    margin=ft.margin.only(right=12 if idx < len(row_tasks) - 1 else 0)
                                )
                            )
                        
                        # Crear fila con las tarjetas - adaptable
                        container.controls.append(
                            ft.Row(
                                row_cards,
                                spacing=12,
                                wrap=False,
                                expand=True,
                                scroll=ft.ScrollMode.AUTO if not is_desktop else ft.ScrollMode.HIDDEN
                            )
                        )
                else:
                    # En móvil, tablet pequeña o pantallas estrechas, mostrar en columna simple
                    for task in priority_tasks:
                        card = create_task_card(
                            task,
                            on_toggle=self._toggle_task,
                            on_edit=self._edit_task,
                            on_delete=self._delete_task,
                            on_toggle_subtask=self._toggle_subtask,
                            on_add_subtask=self._show_add_subtask_dialog,
                            on_delete_subtask=self._delete_subtask,
                            on_edit_subtask=self._edit_subtask,
                            page=self.page
                        )
                        # Asegurar que la tarjeta use todo el ancho disponible
                        container.controls.append(
                            ft.Container(
                                content=card,
                                expand=True,
                                width=None
                            )
                        )
        
        self.page.update()
    
    def _filter_priority_tasks(self, priority: str, filter_completed: Optional[bool]):
        """Filtra las tareas de una prioridad específica."""
        self.priority_filters[priority] = filter_completed
        self.load_tasks()
        # Reconstruir la sección para actualizar los botones de filtro
        self._rebuild_priority_section(priority)
    
    def _rebuild_priority_section(self, priority: str):
        """Reconstruye una sección de prioridad específica."""
        # Encontrar el contenedor principal y reemplazar la sección
        if self.main_scroll_container and self.main_scroll_container.content:
            main_column = self.main_scroll_container.content
            if isinstance(main_column, ft.Column):
                # Encontrar el índice de la sección
                priorities_order = ['urgent_important', 'not_urgent_important', 'urgent_not_important', 'not_urgent_not_important']
                try:
                    index = priorities_order.index(priority)
                    # Reconstruir la sección
                    new_section = self._build_priority_section(priority)
                    main_column.controls[index] = new_section
                    self.priority_section_refs[priority] = new_section
                except ValueError:
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
        
        # Mapeo de prioridades a índices en el ListView
        priority_index_map = {
            'urgent_important': 0,
            'not_urgent_important': 1,
            'urgent_not_important': 2,
            'not_urgent_not_important': 3
        }
        
        # Obtener el índice de la sección
        target_index = priority_index_map.get(priority, 0)
        
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
        title = "Editar Tarea" if self.editing_task else "Nueva Tarea"
        
        # Crear el formulario
        form = TaskForm(
            on_save=self._save_task,
            on_cancel=self._go_back_from_form,
            task=self.editing_task
        )
        
        # Detectar el tema actual
        is_dark = self.page.theme_mode == ft.ThemeMode.DARK
        bgcolor = ft.Colors.BLACK if is_dark else ft.Colors.GREY_50
        
        # Crear la barra de título con botón de volver
        back_button = ft.IconButton(
            icon=ft.Icons.ARROW_BACK,
            on_click=lambda e: self._go_back_from_form(),
            icon_color=ft.Colors.RED_400,
            tooltip="Volver"
        )
        
        title_bar = ft.Container(
            content=ft.Row(
                [
                    back_button,
                    ft.Text(
                        title,
                        size=24,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.RED_400,
                        expand=True
                    )
                ],
                alignment=ft.MainAxisAlignment.START,
                vertical_alignment=ft.CrossAxisAlignment.CENTER
            ),
            padding=ft.padding.symmetric(vertical=16, horizontal=20),
            bgcolor=ft.Colors.BLACK87 if is_dark else ft.Colors.RED_50
        )
        
        # Construir la vista del formulario
        form_view = ft.View(
            route="/form",
            controls=[
                title_bar,
                ft.Container(
                    content=form.build(),
                    expand=True,
                    padding=20
                )
            ],
            bgcolor=bgcolor
        )
        
        # Agregar la vista y navegar a ella
        self.page.views.append(form_view)
        self.page.go("/form")
    
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
        # Si el primer argumento es un objeto Task, es una actualización
        if args and isinstance(args[0], Task):
            # Actualizar tarea existente
            task = args[0]
            self.task_service.update_task(task)
        else:
            # Crear nueva tarea
            title, description, priority = args
            self.task_service.create_task(title, description, priority)
        
        # Volver a la vista principal
        self._go_back_from_form()
        
        # Forzar actualización de la página antes de recargar tareas
        self.page.update()
        
        # Recargar las tareas después de volver
        self.load_tasks()
    
    def _toggle_task(self, task_id: int):
        """Cambia el estado de completado de una tarea."""
        self.task_service.toggle_task_complete(task_id)
        self.load_tasks()
    
    def _delete_task(self, task_id: int):
        """Elimina una tarea."""
        if task_id is None:
            return
        
        try:
            deleted = self.task_service.delete_task(int(task_id))
            if deleted:
                self.load_tasks()
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
    
    def _toggle_subtask(self, subtask_id: int):
        """Cambia el estado de completado de una subtarea."""
        self.task_service.toggle_subtask_complete(subtask_id)
        self.load_tasks()
    
    def _delete_subtask(self, subtask_id: int):
        """Elimina una subtarea."""
        self.task_service.delete_subtask(subtask_id)
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
        # Determinar si es edición o creación
        is_editing = self.editing_subtask is not None
        
        # Crear campos del formulario con valores iniciales si es edición
        subtask_title_field = ft.TextField(
            label="Título de la subtarea",
            hint_text="Ingresa el título de la subtarea",
            autofocus=True,
            expand=True,
            value=self.editing_subtask.title if is_editing else ""
        )
        
        subtask_description_field = ft.TextField(
            label="Descripción",
            hint_text="Ingresa una descripción (opcional)",
            multiline=True,
            min_lines=3,
            max_lines=5,
            expand=True,
            value=self.editing_subtask.description if is_editing and self.editing_subtask.description else ""
        )
        
        # Formatear fecha límite si existe
        deadline_value = ""
        if is_editing and self.editing_subtask.deadline:
            try:
                deadline_value = self.editing_subtask.deadline.strftime("%Y-%m-%d %H:%M")
            except:
                deadline_value = ""
        
        subtask_deadline_field = ft.TextField(
            label="Fecha límite",
            hint_text="YYYY-MM-DD HH:MM (opcional)",
            expand=True,
            helper_text="Formato: 2024-12-31 23:59",
            value=deadline_value
        )
        
        # Detectar el tema actual
        is_dark = self.page.theme_mode == ft.ThemeMode.DARK
        bgcolor = ft.Colors.BLACK if is_dark else ft.Colors.GREY_50
        title_bar_bgcolor = ft.Colors.BLACK87 if is_dark else ft.Colors.RED_50
        
        def save_subtask(e):
            title = subtask_title_field.value
            description = subtask_description_field.value or ""
            deadline_str = subtask_deadline_field.value or ""
            
            if not title or not title.strip():
                subtask_title_field.error_text = "El título es obligatorio"
                subtask_title_field.update()
                return
            
            # Validar y parsear fecha límite
            deadline = None
            if deadline_str.strip():
                try:
                    # Intentar parsear diferentes formatos
                    formats = [
                        "%Y-%m-%d %H:%M",
                        "%Y-%m-%d",
                        "%d/%m/%Y %H:%M",
                        "%d/%m/%Y"
                    ]
                    parsed = False
                    for fmt in formats:
                        try:
                            deadline = datetime.strptime(deadline_str.strip(), fmt)
                            parsed = True
                            break
                        except ValueError:
                            continue
                    
                    if not parsed:
                        subtask_deadline_field.error_text = "Formato inválido. Use YYYY-MM-DD HH:MM"
                        subtask_deadline_field.update()
                        return
                except Exception as ex:
                    subtask_deadline_field.error_text = f"Error al parsear fecha: {str(ex)}"
                    subtask_deadline_field.update()
                    return
            
            try:
                if is_editing:
                    # Actualizar subtarea existente
                    self.editing_subtask.title = title.strip()
                    self.editing_subtask.description = description.strip()
                    self.editing_subtask.deadline = deadline
                    self.task_service.update_subtask(self.editing_subtask)
                else:
                    # Crear nueva subtarea
                    task_id = getattr(self, 'editing_subtask_task_id', None)
                    if task_id:
                        self.task_service.create_subtask(
                            task_id, 
                            title.strip(), 
                            description.strip(),
                            deadline
                        )
                    else:
                        # Mostrar error en la página
                        self.page.snack_bar = ft.SnackBar(
                            content=ft.Text("Error: No se encontró la tarea padre"),
                            bgcolor=ft.Colors.RED
                        )
                        self.page.snack_bar.open = True
                        self.page.update()
                        return
                
                self._go_back_from_form()
                self.load_tasks()
            except Exception as ex:
                # Mostrar error en la página
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text(f"Error: {str(ex)}"),
                    bgcolor=ft.Colors.RED
                )
                self.page.snack_bar.open = True
                self.page.update()
        
        # Crear la barra de título con botón de volver
        back_button = ft.IconButton(
            icon=ft.Icons.ARROW_BACK,
            on_click=lambda e: self._go_back_from_form(),
            icon_color=ft.Colors.RED_400,
            tooltip="Volver"
        )
        
        title_bar = ft.Container(
            content=ft.Row(
                [
                    back_button,
                    ft.Text(
                        "Editar Subtarea" if is_editing else "Nueva Subtarea",
                        size=24,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.RED_400,
                        expand=True
                    )
                ],
                alignment=ft.MainAxisAlignment.START,
                vertical_alignment=ft.CrossAxisAlignment.CENTER
            ),
            padding=ft.padding.symmetric(vertical=16, horizontal=20),
            bgcolor=title_bar_bgcolor
        )
        
        # Botones de acción
        save_button = ft.ElevatedButton(
            text="Guardar",
            icon=ft.Icons.SAVE,
            on_click=save_subtask,
            color=ft.Colors.WHITE,
            bgcolor=ft.Colors.RED_700,
            expand=True
        )
        
        cancel_button = ft.OutlinedButton(
            text="Cancelar",
            icon=ft.Icons.CANCEL,
            on_click=lambda e: self._go_back_from_form(),
            expand=True
        )
        
        # Construir la vista del formulario
        form_view = ft.View(
            route="/subtask-form",
            controls=[
                title_bar,
                ft.Container(
                    content=ft.Column(
                        [
                            subtask_title_field,
                            subtask_description_field,
                            subtask_deadline_field,
                            ft.Row(
                                [
                                    save_button,
                                    cancel_button
                                ],
                                spacing=8,
                                alignment=ft.MainAxisAlignment.END
                            )
                        ],
                        spacing=16,
                        expand=True,
                        scroll=ft.ScrollMode.AUTO
                    ),
                    expand=True,
                    padding=20
                )
            ],
            bgcolor=bgcolor
        )
        
        # Agregar la vista y navegar a ella
        self.page.views.append(form_view)
        self.page.go("/subtask-form")

