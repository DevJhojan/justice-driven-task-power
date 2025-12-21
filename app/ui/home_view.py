"""
Vista principal de la aplicación de tareas.
"""
import os
import flet as ft
from typing import Optional
from datetime import date, datetime
from pathlib import Path
from app.data.models import Task, SubTask, Habit
from app.services.task_service import TaskService
from app.services.habit_service import HabitService
from app.services.settings_service import SettingsService, apply_theme_to_page
from app.services.sync_service import SyncService

# Importación de Firebase - si falla, se manejará en tiempo de ejecución
try:
    from app.services.firebase_auth_service import FirebaseAuthService
    from app.services.firebase_sync_service import FirebaseSyncService
    FIREBASE_AVAILABLE = True
except (ImportError, ModuleNotFoundError) as e:
    # Si falla la importación, Firebase no está disponible
    FirebaseAuthService = None
    FirebaseSyncService = None
    FIREBASE_AVAILABLE = False
    _firebase_import_error = str(e)
from app.ui.widgets import (
    create_task_card, create_empty_state, create_statistics_card,
    create_habit_card, create_habit_empty_state, create_habit_statistics_card
)
from app.ui.task_form import TaskForm
from app.ui.habit_form import HabitForm


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
        self.habit_service = HabitService()
        self.settings_service = SettingsService()
        self.sync_service = SyncService()
        
        # Inicializar servicios de Firebase
        try:
            if FIREBASE_AVAILABLE and FirebaseAuthService:
                self.firebase_auth_service = FirebaseAuthService()
                self.firebase_sync_service = FirebaseSyncService(self.firebase_auth_service)
            else:
                self.firebase_auth_service = None
                self.firebase_sync_service = None
        except Exception as e:
            self.firebase_auth_service = None
            self.firebase_sync_service = None
            print(f"Error al inicializar Firebase: {e}")
        
        # Filtros por sección de prioridad: {priority: filter_value}
        self.priority_filters = {
            'urgent_important': None,  # None=all, True=completed, False=pending
            'not_urgent_important': None,
            'urgent_not_important': None,
            'not_urgent_not_important': None
        }
        self.current_priority_section = 'urgent_important'  # Prioridad activa visible
        self.current_habit_filter: Optional[bool] = None  # None=all, True=active, False=inactive
        self.editing_task: Optional[Task] = None
        self.editing_subtask_task_id: Optional[int] = None
        self.editing_subtask = None
        self.editing_habit: Optional[Habit] = None
        # Secciones: "tasks", "habits", "settings"
        self.current_section = "tasks"
        
        # Contenedores principales para cada prioridad - responsive
        # En escritorio, las tarjetas se mostrarán en grid; en móvil en columna
        self.priority_containers = {
            'urgent_important': ft.Column([], spacing=0, scroll=ft.ScrollMode.AUTO),
            'not_urgent_important': ft.Column([], spacing=0, scroll=ft.ScrollMode.AUTO),
            'urgent_not_important': ft.Column([], spacing=0, scroll=ft.ScrollMode.AUTO),
            'not_urgent_not_important': ft.Column([], spacing=0, scroll=ft.ScrollMode.AUTO)
        }
        self.priority_section_refs = {}  # Referencias a los contenedores de sección para scroll
        self.main_scroll_container = None  # Contenedor principal con scroll
        self.habits_container = ft.Column([], spacing=0, scroll=ft.ScrollMode.AUTO, expand=True)
        self.stats_card = None
        self.habit_stats_card = None
        self.title_bar = None  # Guardar referencia a la barra de título
        

        # Diálogo para seleccionar matiz (paleta de colores)
        # Debe tener al menos title, content o actions para que Flet no lance AssertionError.
        self.accent_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(""),
            content=ft.Container(),
            actions=[],
        )
        if self.accent_dialog not in self.page.overlay:
            self.page.overlay.append(self.accent_dialog)

        
        # Variable para almacenar bytes del ZIP durante la exportación
        self._export_zip_bytes = None

        self.page.update()

        self._build_ui()
        self._load_tasks()
    
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
        # Usar tamaño de fuente responsive basado en ancho de pantalla
        try:
            screen_width = self.page.width if (hasattr(self.page, 'width') and self.page.width is not None and isinstance(self.page.width, (int, float))) else 1024
        except (AttributeError, TypeError):
            screen_width = 1024
        is_wide = screen_width > 600 if isinstance(screen_width, (int, float)) else False
        
        title_size = 22 if is_wide else 18
        title_padding_vertical = 14 if is_wide else 10
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
            expand=True
        )
        
        # Botones de filtro para esta sección - responsive
        active_bg = colors['primary']
        inactive_bg = ft.Colors.GREY_800 if is_dark else ft.Colors.GREY_100
        text_color = ft.Colors.WHITE
        button_height = 40 if is_desktop else 36
        button_padding = ft.padding.symmetric(vertical=12 if is_desktop else 8, horizontal=24 if is_desktop else 16)
        
        # Botones de filtro responsive - se adaptan al ancho disponible
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
                    expand=True if is_desktop else False,
                    min_width=80 if not is_desktop else None
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
                    expand=True if is_desktop else False,
                    min_width=100 if not is_desktop else None
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
                    expand=True if is_desktop else False,
                    min_width=110 if not is_desktop else None
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
            key=f"priority_section_{priority}",  # Key para referencia de scroll
            margin=ft.margin.only(bottom=24 if is_desktop else 16),
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
                tooltip=colors['text'],
                constraints=ft.BoxConstraints(
                    min_width=60,  # Ancho mínimo para legibilidad
                    max_width=None  # Sin máximo para que se expanda
                )
            )
            buttons.append(button)
        
        # Contenedor responsive
        nav_padding = ft.padding.symmetric(
            vertical=14 if is_wide_screen else 10,
            horizontal=20 if is_wide_screen else 12
        )
        button_spacing = 10 if is_wide_screen else 6
        
        return ft.Container(
            content=ft.Row(
                buttons,
                spacing=button_spacing,
                scroll=ft.ScrollMode.AUTO if not is_wide_screen else ft.ScrollMode.HIDDEN,
                wrap=False,
                expand=True
            ),
            padding=nav_padding,
            bgcolor=bgcolor,
            border=ft.border.only(bottom=ft.BorderSide(1, ft.Colors.GREY_300 if not is_dark else ft.Colors.GREY_700)),
            expand=True
        )
    
    def _build_ui(self):
        """Construye la interfaz de usuario con Matriz de Eisenhower."""
        # Detectar si es escritorio o móvil para hacer responsive
        is_desktop = self.page.platform == ft.PagePlatform.WINDOWS or self.page.platform == ft.PagePlatform.LINUX or self.page.platform == ft.PagePlatform.MACOS
        
        # Barra de título - responsive
        scheme = self.page.theme.color_scheme if self.page.theme else None
        title_color = scheme.primary if scheme and scheme.primary else ft.Colors.RED_400
        title_size = 32 if is_desktop else 28
        title_padding = ft.padding.symmetric(
            vertical=20 if is_desktop else 16,
            horizontal=32 if is_desktop else 20
        )
        button_size = 48 if is_desktop else 40

        self.title_bar = ft.Container(
            content=ft.Row(
                [
                    ft.Text(
                        "Mis Tareas" if self.current_section == "tasks"
                        else "Mis Hábitos" if self.current_section == "habits"
                        else "Configuración",
                        size=title_size,
                        weight=ft.FontWeight.BOLD,
                        color=title_color,
                        expand=True
                    ),
                    ft.IconButton(
                        icon=ft.Icons.ADD,
                        on_click=self._show_new_task_form,
                        bgcolor=title_color,
                        icon_color=ft.Colors.WHITE,
                        tooltip="Nueva Tarea",
                        width=button_size,
                        height=button_size,
                        icon_size=24 if is_desktop else 20
                    )
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER
            ),
            padding=title_padding,
            bgcolor=ft.Colors.BLACK87 if self.page.theme_mode == ft.ThemeMode.DARK else ft.Colors.RED_50
        )
        
        # Crear la barra inferior de navegación
        self._build_bottom_bar()
        
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
        main_scroll_content = ft.Column(
            priority_sections,
            spacing=section_spacing,
            scroll=ft.ScrollMode.AUTO,
            expand=True
        )
        
        # Padding responsive para el contenedor principal
        main_padding = ft.padding.only(
            bottom=24 if is_desktop else 16,
            left=0,
            right=0
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
                width=None  # Sin ancho fijo para que se adapte
            )
        
        # Vista principal
        main_view = ft.Container(
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
        
        # Guardar referencia a la vista principal
        self.home_view = ft.View(
            route="/",
            controls=[
                ft.Column(
                    [
                        self.title_bar,
                        main_view,
                        self.bottom_bar
                    ],
                    spacing=0,
                    expand=True
                )
            ],
            bgcolor=ft.Colors.BLACK if self.page.theme_mode == ft.ThemeMode.DARK else ft.Colors.GREY_50
        )
        
        # Configurar las vistas de la página
        self.page.views.clear()
        self.page.views.append(self.home_view)
        self.page.go("/")
        self.page.update()
    
    def _build_bottom_bar(self):
        """Construye la barra inferior de navegación."""
        is_dark = self.page.theme_mode == ft.ThemeMode.DARK
        bgcolor = ft.Colors.BLACK87 if is_dark else ft.Colors.WHITE

        scheme = self.page.theme.color_scheme if self.page.theme else None
        selected_color = scheme.primary if scheme and scheme.primary else ft.Colors.RED_400
        unselected_color = ft.Colors.GREY_500 if is_dark else ft.Colors.GREY_600
        
        # Botón de Mis Tareas
        tasks_button = ft.Container(
            content=ft.Column(
                [
                    ft.Icon(
                        ft.Icons.TASK_ALT if self.current_section == "tasks" else ft.Icons.TASK,
                        color=selected_color if self.current_section == "tasks" else unselected_color,
                        size=24
                    ),
                    ft.Text(
                        "Mis Tareas",
                        size=12,
                        color=selected_color if self.current_section == "tasks" else unselected_color,
                        weight=ft.FontWeight.BOLD if self.current_section == "tasks" else None
                    )
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=4,
                tight=True
            ),
            on_click=lambda e: self._navigate_to_section("tasks"),
            padding=12,
            expand=True,
            border=ft.border.only(
                top=ft.BorderSide(3, selected_color if self.current_section == "tasks" else ft.Colors.TRANSPARENT)
            )
        )
        
        # Botón de Mis Hábitos
        habits_button = ft.Container(
            content=ft.Column(
                [
                    ft.Icon(
                        ft.Icons.CALENDAR_VIEW_DAY if self.current_section == "habits" else ft.Icons.CALENDAR_VIEW_WEEK,
                        color=selected_color if self.current_section == "habits" else unselected_color,
                        size=24
                    ),
                    ft.Text(
                        "Mis Hábitos",
                        size=12,
                        color=selected_color if self.current_section == "habits" else unselected_color,
                        weight=ft.FontWeight.BOLD if self.current_section == "habits" else None
                    )
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=4,
                tight=True
            ),
            on_click=lambda e: self._navigate_to_section("habits"),
            padding=12,
            expand=True,
            border=ft.border.only(
                top=ft.BorderSide(3, selected_color if self.current_section == "habits" else ft.Colors.TRANSPARENT)
            )
        )
        
        # Botón de Configuración
        settings_button = ft.Container(
            content=ft.Column(
                [
                    ft.Icon(
                        ft.Icons.SETTINGS,
                        color=selected_color if self.current_section == "settings" else unselected_color,
                        size=24
                    ),
                    ft.Text(
                        "Configuración",
                        size=12,
                        color=selected_color if self.current_section == "settings" else unselected_color,
                        weight=ft.FontWeight.BOLD if self.current_section == "settings" else None
                    )
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=4,
                tight=True
            ),
            on_click=lambda e: self._navigate_to_section("settings"),
            padding=12,
            expand=True,
            border=ft.border.only(
                top=ft.BorderSide(3, selected_color if self.current_section == "settings" else ft.Colors.TRANSPARENT)
            )
        )

        self.bottom_bar = ft.Container(
            content=ft.Row(
                [
                    tasks_button,
                    habits_button,
                    settings_button
                ],
                alignment=ft.MainAxisAlignment.SPACE_AROUND,
                spacing=0
            ),
            bgcolor=bgcolor,
            border=ft.border.only(
                top=ft.BorderSide(1, ft.Colors.GREY_800 if is_dark else ft.Colors.GREY_300)
            ),
            padding=0
        )
    
    def _navigate_to_section(self, section: str):
        """Navega a una sección específica."""
        self.current_section = section
        
        if section == "tasks":
            # Mostrar la vista de tareas
            self._build_ui()
            self._load_tasks()
        elif section == "habits":
            # Mostrar la vista de hábitos
            self._build_habits_view()
            self._load_habits()
        elif section == "settings":
            # Mostrar la vista de configuración
            self._build_settings_view()
        
        # Actualizar el título
        if self.title_bar:
            title_text = self.title_bar.content.controls[0]  # El texto está en el índice 0 ahora
            if isinstance(title_text, ft.Text):
                if section == "tasks":
                    title_text.value = "Mis Tareas"
                elif section == "habits":
                    title_text.value = "Mis Hábitos"
                else:
                    title_text.value = "Configuración"
        
        # Actualizar la barra inferior
        self._build_bottom_bar()
        # Actualizar la barra en la vista
        if self.home_view and len(self.home_view.controls) > 0:
            column = self.home_view.controls[0]
            if isinstance(column, ft.Column) and len(column.controls) > 2:
                column.controls[2] = self.bottom_bar
        
        self.page.update()
    
    def _build_habits_view(self):
        """Construye la vista de hábitos."""
        is_dark = self.page.theme_mode == ft.ThemeMode.DARK
        bgcolor = ft.Colors.BLACK if is_dark else ft.Colors.GREY_50

        scheme = self.page.theme.color_scheme if self.page.theme else None
        primary = scheme.primary if scheme and scheme.primary else ft.Colors.RED_700
        secondary = scheme.secondary if scheme and scheme.secondary else ft.Colors.RED_600
        
        # Botón para agregar nuevo hábito - color adaptativo
        new_habit_button_bg = primary
        
        # Botón "+" para agregar hábito
        self.new_habit_button = ft.IconButton(
            icon=ft.Icons.ADD,
            on_click=self._show_new_habit_form,
            bgcolor=new_habit_button_bg,
            icon_color=ft.Colors.WHITE,
            tooltip="Nuevo Hábito",
            width=40,
            height=40
        )
        
        # Filtros para hábitos (Activos/Inactivos/Todos)
        active_bg = primary
        inactive_bg = ft.Colors.GREY_800 if is_dark else ft.Colors.GREY_100
        text_color = ft.Colors.WHITE
        
        # Contenedor de estadísticas de hábitos
        habit_stats_container = ft.Container(
            content=create_habit_statistics_card(self.habit_service.get_statistics(), self.page),
            visible=True
        )
        self.habit_stats_container = habit_stats_container
        
        # Filtros de hábitos
        habit_filter_row = ft.Row(
            [
                ft.ElevatedButton(
                    text="Todos",
                    on_click=lambda e: self._filter_habits(None),
                    bgcolor=active_bg,
                    color=text_color,
                    height=40
                ),
                ft.ElevatedButton(
                    text="Activos",
                    on_click=lambda e: self._filter_habits(True),
                    bgcolor=inactive_bg,
                    color=text_color,
                    height=40
                ),
                ft.ElevatedButton(
                    text="Inactivos",
                    on_click=lambda e: self._filter_habits(False),
                    bgcolor=inactive_bg,
                    color=text_color,
                    height=40
                ),
                self.new_habit_button
            ],
            spacing=8,
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER
        )
        
        # Vista principal (lista de hábitos)
        main_view = ft.Container(
            content=ft.Column(
                [
                    habit_stats_container,
                    habit_filter_row,
                    self.habits_container
                ],
                spacing=8,
                expand=True
            ),
            padding=16,
            expand=True
        )
        
        # Actualizar la vista principal
        self.home_view.controls = [
            ft.Column(
                [
                    self.title_bar,
                    main_view,
                    self.bottom_bar
                ],
                spacing=0,
                expand=True
            )
        ]
        self.home_view.bgcolor = bgcolor
        
        # Cargar hábitos
        self._load_habits()

    def _build_settings_view(self):
        """Construye la vista de configuración (placeholder)."""
        is_dark = self.page.theme_mode == ft.ThemeMode.DARK
        bgcolor = ft.Colors.BLACK if is_dark else ft.Colors.GREY_50

        scheme = self.page.theme.color_scheme if self.page.theme else None
        preview_color = scheme.primary if scheme and scheme.primary else ft.Colors.RED_600

        # ==================== Sección 1: Apariencia ====================
        # Controles de apariencia (tema y color principal)
        current_settings = self.settings_service.get_settings()

        # Botón de luna/sol para alternar tema
        theme_icon = (
            ft.Icons.DARK_MODE if current_settings.theme_mode == "dark" else ft.Icons.LIGHT_MODE
        )
        theme_icon_button = ft.IconButton(
            icon=theme_icon,
            tooltip="Cambiar modo de tema",
            on_click=self._toggle_theme,
        )

        # ==================== Sección 2: Autenticación y Sincronización con Firebase ====================
        sync_settings = self.sync_service.get_sync_settings()
        is_authenticated = sync_settings.is_authenticated

        settings_content = ft.Container(
            content=ft.Column(
                [
                    ft.Text(
                        "Configuración",
                        size=24,
                        weight=ft.FontWeight.BOLD,
                        color=preview_color
                    ),
                    ft.Divider(),

                    # Sección Apariencia
                    ft.Text(
                        "Apariencia",
                        size=18,
                        weight=ft.FontWeight.BOLD,
                        color=preview_color
                    ),
                    ft.Text(
                        "Ajusta el modo de tema y el color principal de la aplicación.",
                        size=14,
                        color=ft.Colors.GREY_600
                    ),
                    ft.Row(
                        [
                            ft.Text("Modo de tema", size=14),
                            theme_icon_button,
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    ft.Text(
                        "Color principal",
                        size=14,
                        weight=ft.FontWeight.BOLD
                    ),
                    ft.Row(
                        [
                            ft.Container(
                                content=ft.Icon(ft.Icons.CIRCLE, color=preview_color, size=20),
                                border=ft.border.all(1, ft.Colors.GREY_400),
                                border_radius=20,
                                padding=6,
                            ),
                            ft.ElevatedButton(
                                text="Elegir matiz",
                                icon=ft.Icons.COLOR_LENS,
                                on_click=self._open_accent_dialog,
                            )
                        ],
                        spacing=12,
                        alignment=ft.MainAxisAlignment.START,
                    ),

                    ft.Divider(),

                    # ==================== Sección 2: Autenticación y Sincronización con Firebase ====================
                    ft.Text(
                        "Autenticación y Sincronización",
                        size=18,
                        weight=ft.FontWeight.BOLD,
                        color=preview_color
                    ),
                    ft.Text(
                        "Autentícate con Firebase para sincronizar tus datos en la nube. "
                        "Tus datos se guardan localmente y se sincronizan cuando lo solicites.",
                        size=14,
                        color=ft.Colors.GREY_600
                    ),
                    self._build_firebase_auth_section(preview_color, is_dark),

                    ft.Divider(),

                    # ==================== Sección 5: Información de la aplicación ====================
                    ft.Text(
                        "Información de la aplicación",
                        size=18,
                        weight=ft.FontWeight.BOLD,
                        color=preview_color
                    ),
                    ft.Text(
                        "Información sobre la versión y el estado de la aplicación.",
                        size=14,
                        color=ft.Colors.GREY_600
                    ),
                    ft.Container(
                        content=ft.Row(
                            [
                                ft.Icon(
                                    ft.Icons.INFO_OUTLINE,
                                    color=preview_color,
                                    size=20
                                ),
                                ft.Column(
                                    [
                                        ft.Text(
                                            "Versión",
                                            size=12,
                                            color=ft.Colors.GREY_600 if not is_dark else ft.Colors.GREY_400,
                                            weight=ft.FontWeight.BOLD
                                        ),
                                        ft.Text(
                                            self._get_app_version(),
                                            size=16,
                                            color=preview_color,
                                            weight=ft.FontWeight.BOLD
                                        )
                                    ],
                                    spacing=4
                                )
                            ],
                            spacing=12,
                            alignment=ft.MainAxisAlignment.START
                        ),
                        padding=ft.padding.symmetric(vertical=8, horizontal=0)
                    )
                ],
                spacing=16,
                expand=True,
                scroll=ft.ScrollMode.AUTO,
            ),
            padding=20,
            expand=True
        )

        # Actualizar la vista principal
        self.home_view.controls = [
            ft.Column(
                [
                    self.title_bar,
                    settings_content,
                    self.bottom_bar
                ],
                spacing=0,
                expand=True
            )
        ]
        self.home_view.bgcolor = bgcolor
        self.page.update()

    def _build_firebase_auth_section(self, preview_color, is_dark):
        """Construye la sección de autenticación y sincronización con Firebase."""
        sync_settings = self.sync_service.get_sync_settings()
        is_authenticated = sync_settings.is_authenticated
        
        if not FIREBASE_AVAILABLE or not self.firebase_auth_service:
            return ft.Container(
                content=ft.Column(
                    [
                        ft.Text(
                            "Firebase no está disponible",
                            size=14,
                            color=ft.Colors.RED,
                            weight=ft.FontWeight.BOLD
                        ),
                        ft.Text(
                            "Las dependencias de Firebase no están instaladas. "
                            "Instala con: pip install requests",
                            size=12,
                            color=ft.Colors.GREY_600 if not is_dark else ft.Colors.GREY_400
                        )
                    ],
                    spacing=8
                )
            )
        
        if is_authenticated:
            # Usuario autenticado: mostrar información y botón de sincronización
            user_email = sync_settings.email or "Usuario"
            
            sync_button = ft.ElevatedButton(
                text="Sincronizar",
                icon=ft.Icons.CLOUD_SYNC,
                on_click=self._start_firebase_sync,
                bgcolor=preview_color,
                color=ft.Colors.WHITE,
            )
            
            logout_button = ft.OutlinedButton(
                text="Cerrar sesión",
                icon=ft.Icons.LOGOUT,
                on_click=self._logout_firebase,
                style=ft.ButtonStyle(color=ft.Colors.RED)
            )
            
            return ft.Column(
                [
                    ft.Text(
                        f"✓ Conectado como: {user_email}",
                        size=14,
                        color=ft.Colors.GREEN if not is_dark else ft.Colors.GREEN_300,
                        weight=ft.FontWeight.BOLD
                    ),
                    ft.Text(
                        "Tus datos se guardan localmente y se sincronizan en la nube cuando lo solicites.",
                        size=12,
                        color=ft.Colors.GREY_600 if not is_dark else ft.Colors.GREY_400
                    ),
                    ft.Row(
                        [sync_button, logout_button],
                        spacing=8,
                        alignment=ft.MainAxisAlignment.START
                    )
                ],
                spacing=8
            )
        else:
            # Usuario no autenticado: mostrar botones de login y registro
            login_button = ft.ElevatedButton(
                text="Iniciar sesión",
                icon=ft.Icons.LOGIN,
                on_click=self._show_login_dialog,
                bgcolor=preview_color,
                color=ft.Colors.WHITE,
            )
            
            register_button = ft.OutlinedButton(
                text="Registrarse",
                icon=ft.Icons.PERSON_ADD,
                on_click=self._show_register_dialog,
                style=ft.ButtonStyle(color=preview_color)
            )
            
            return ft.Column(
                [
                    ft.Row(
                        [login_button, register_button],
                        spacing=8,
                        alignment=ft.MainAxisAlignment.START
                    ),
                    ft.Text(
                        "Crea una cuenta o inicia sesión para sincronizar tus datos en la nube.",
                        size=12,
                        color=ft.Colors.GREY_600 if not is_dark else ft.Colors.GREY_400,
                        italic=True
                    )
                ],
                spacing=8
            )

    def _get_app_version(self) -> str:
        """
        Obtiene la versión de la aplicación desde pyproject.toml.
        
        Returns:
            Versión de la aplicación o "Desconocida" si no se puede obtener.
        """
        try:
            root_dir = Path(__file__).parent.parent.parent
            pyproject_path = root_dir / 'pyproject.toml'
            
            if pyproject_path.exists():
                with open(pyproject_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.strip().startswith('version'):
                            # Extraer la versión del formato: version = "0.2.5"
                            version = line.split('=')[1].strip().strip('"').strip("'")
                            return version
            
            return "Desconocida"
        except Exception:
            return "Desconocida"

    # ==================== FUNCIONES DE FIREBASE ====================
    
    def _show_login_dialog(self, e):
        """Navega a la página de inicio de sesión."""
        self._show_auth_page(mode="login")
    
    def _show_auth_page(self, mode="login"):
        """
        Muestra una página completa de autenticación (login o registro).
        
        Args:
            mode: "login" o "register"
        """
        is_login = mode == "login"
        
        # Campos del formulario
        email_field = ft.TextField(
            label="Correo electrónico",
            hint_text="tu@email.com",
            autofocus=True,
            keyboard_type=ft.KeyboardType.EMAIL,
            expand=True
        )
        
        password_field = ft.TextField(
            label="Contraseña",
            hint_text="Mínimo 6 caracteres",
            password=True,
            can_reveal_password=True,
            expand=True
        )
        
        confirm_password_field = ft.TextField(
            label="Confirmar contraseña",
            hint_text="Repite la contraseña",
            password=True,
            can_reveal_password=True,
            expand=True,
            visible=not is_login  # Solo visible en modo registro
        )
        
        error_text = ft.Text("", color=ft.Colors.RED, size=12, selectable=True, weight=ft.FontWeight.W_500)
        loading_indicator = ft.ProgressRing(visible=False)
        
        # Botón para copiar el error al portapapeles
        copy_error_button = ft.IconButton(
            icon=ft.Icons.COPY,
            tooltip="Copiar error al portapapeles",
            icon_size=18,
            icon_color=ft.Colors.RED,
            on_click=lambda e: self._copy_error_to_clipboard(error_text.value, error_text)
        )
        
        # Contenedor del error (se mostrará cuando haya error)
        error_container = ft.Container(
            content=ft.Row(
                [
                    ft.Container(
                        content=error_text,
                        expand=True,
                        padding=ft.padding.only(right=5)
                    ),
                    copy_error_button
                ],
                spacing=5,
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER
            ),
            visible=False,
            bgcolor=ft.Colors.RED_50 if self.page.theme_mode != ft.ThemeMode.DARK else ft.Colors.RED_900,
            padding=10,
            border_radius=5,
            border=ft.border.all(1, ft.Colors.RED_300 if self.page.theme_mode != ft.ThemeMode.DARK else ft.Colors.RED_700)
        )
        
        # Botón de submit (se define antes para poder usarlo en submit_auth)
        submit_button = ft.ElevatedButton(
            text="Iniciar sesión" if is_login else "Registrarse",
            icon=ft.Icons.LOGIN if is_login else ft.Icons.PERSON_ADD,
            expand=True,
            height=50
        )
        
        def submit_auth(e):
            """Procesa el inicio de sesión o registro."""
            email = email_field.value.strip()
            password = password_field.value
            confirm_password = confirm_password_field.value if not is_login else ""
            
            # Validaciones
            if not email:
                error_text.value = "El correo electrónico es requerido"
                error_container.visible = True
                error_text.update()
                error_container.update()
                return
            
            if not password:
                error_text.value = "La contraseña es requerida"
                error_container.visible = True
                error_text.update()
                error_container.update()
                return
            
            if not is_login:
                if len(password) < 6:
                    error_text.value = "La contraseña debe tener al menos 6 caracteres"
                    error_container.visible = True
                    error_text.update()
                    error_container.update()
                    return
                
                if password != confirm_password:
                    error_text.value = "Las contraseñas no coinciden"
                    error_container.visible = True
                    error_text.update()
                    error_container.update()
                    return
            
            # Mostrar indicador de carga
            error_container.visible = False
            loading_indicator.visible = True
            submit_button.disabled = True
            self.page.update()
            
            try:
                if not self.firebase_auth_service:
                    raise RuntimeError("Firebase no está disponible")
                
                # Ejecutar login o registro
                if is_login:
                    result = self.firebase_auth_service.login(email, password)
                    success_message = f"✓ Sesión iniciada: {result.get('user', {}).get('email')}"
                else:
                    result = self.firebase_auth_service.register(email, password)
                    success_message = f"✓ Usuario registrado: {result.get('user', {}).get('email')}"
                
                # Guardar estado de sincronización
                user = result.get('user', {})
                self.sync_service.update_sync_settings(
                    is_authenticated=True,
                    email=user.get('email'),
                    user_id=user.get('uid')
                )
                
                # Volver a configuración
                self._go_back()
                
                # Mostrar éxito
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text(success_message),
                    bgcolor=ft.Colors.GREEN,
                    duration=3000
                )
                self.page.snack_bar.open = True
                
                # Refrescar vista de configuración
                if self.current_section == "settings":
                    self._build_settings_view()
                    self.page.update()
                
            except ValueError as ve:
                error_text.value = str(ve)
                error_container.visible = True
                loading_indicator.visible = False
                submit_button.disabled = False
                error_text.update()
                error_container.update()
                self.page.update()
            except Exception as ex:
                error_text.value = f"Error: {str(ex)}"
                error_container.visible = True
                loading_indicator.visible = False
                submit_button.disabled = False
                error_text.update()
                error_container.update()
                self.page.update()
        
        # Asignar el handler al botón
        submit_button.on_click = submit_auth
        
        switch_button = ft.TextButton(
            text="¿No tienes cuenta? Regístrate" if is_login else "¿Ya tienes cuenta? Inicia sesión",
            on_click=lambda e: self._show_auth_page("register" if is_login else "login")
        )
        
        # Construir la vista
        auth_view = ft.View(
            route="/auth",
            appbar=ft.AppBar(
                title=ft.Text("Iniciar sesión" if is_login else "Registrarse"),
                leading=ft.IconButton(
                    icon=ft.Icons.ARROW_BACK,
                    on_click=lambda e: self._go_back()
                ),
                bgcolor=self.page.theme.primary_color if self.page.theme else ft.Colors.BLUE_700
            ),
            padding=20,
            scroll=ft.ScrollMode.AUTO,
            controls=[
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Text(
                                "Inicia sesión para sincronizar tus datos" if is_login else "Crea una cuenta para sincronizar tus datos",
                                size=16,
                                weight=ft.FontWeight.BOLD,
                                text_align=ft.TextAlign.CENTER
                            ),
                            ft.Divider(height=20),
                            email_field,
                            password_field,
                            confirm_password_field,
                            error_container,
                            ft.Row(
                                [loading_indicator, submit_button],
                                spacing=10,
                                alignment=ft.MainAxisAlignment.CENTER
                            ),
                            ft.Divider(height=20),
                            switch_button
                        ],
                        spacing=15,
                        horizontal_alignment=ft.CrossAxisAlignment.STRETCH
                    ),
                    padding=20,
                    border_radius=10,
                    bgcolor=ft.Colors.GREY_900 if self.page.theme_mode == ft.ThemeMode.DARK else ft.Colors.GREY_100
                )
            ]
        )
        
        self.page.views.append(auth_view)
        self.page.go("/auth")
        self.page.update()
    
    def _show_register_dialog(self, e):
        """Navega a la página de registro."""
        self._show_auth_page(mode="register")
    
    def _copy_error_to_clipboard(self, error_message: str, error_text_widget=None):
        """
        Copia el mensaje de error al portapapeles.
        
        Args:
            error_message: Mensaje de error a copiar
            error_text_widget: Widget de texto del error (opcional, para compatibilidad)
        """
        try:
            if not error_message:
                return
            
            self.page.set_clipboard(error_message)
            
            # Mostrar confirmación
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text("✓ Error copiado al portapapeles"),
                bgcolor=ft.Colors.GREEN,
                duration=2000
            )
            self.page.snack_bar.open = True
            self.page.update()
        except Exception as ex:
            # Si falla, mostrar error
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"No se pudo copiar: {str(ex)}"),
                bgcolor=ft.Colors.RED,
                duration=3000
            )
            self.page.snack_bar.open = True
            self.page.update()
    
    def _logout_firebase(self, e):
        """Cierra la sesión de Firebase."""
        try:
            if self.firebase_auth_service:
                self.firebase_auth_service.logout()
            
            # Limpiar configuración de sincronización
            self.sync_service.clear_sync_settings()
            
            # Mostrar mensaje
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text("✓ Sesión cerrada"),
                bgcolor=ft.Colors.GREEN,
                duration=2000
            )
            self.page.snack_bar.open = True
            
            # Refrescar vista de configuración
            if self.current_section == "settings":
                self._build_settings_view()
            
        except Exception as ex:
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"Error al cerrar sesión: {str(ex)}"),
                bgcolor=ft.Colors.RED,
                duration=3000
            )
            self.page.snack_bar.open = True
        finally:
            self.page.update()
    
    def _start_firebase_sync(self, e):
        """Muestra página para seleccionar dirección de sincronización."""
        if not self.firebase_sync_service:
            self._show_sync_results_page(
                success=False,
                error_message="Firebase no está disponible"
            )
            return
        
        # Verificar autenticación
        if not self.firebase_auth_service.is_authenticated():
            self._show_sync_results_page(
                success=False,
                error_message="Debes iniciar sesión primero para sincronizar"
            )
            return
        
        # Mostrar página de selección de dirección
        self._show_sync_direction_page()
    
    def _show_sync_direction_page(self):
        """Muestra una página para seleccionar la dirección de sincronización."""
        is_dark = self.page.theme_mode == ft.ThemeMode.DARK
        scheme = self.page.theme.color_scheme if self.page.theme else None
        primary_color = scheme.primary if scheme and scheme.primary else ft.Colors.BLUE_700
        
        def upload_to_cloud(e):
            """Sube datos locales a Firebase."""
            self._show_sync_loading_page()
            try:
                result = self.firebase_sync_service.upload_to_cloud()
                self._show_sync_results_page(
                    success=result.success,
                    sync_result=result
                )
            except Exception as ex:
                self._show_sync_results_page(
                    success=False,
                    error_message=str(ex)
                )
        
        def download_from_cloud(e):
            """Descarga datos de Firebase al local."""
            self._show_sync_loading_page()
            try:
                result = self.firebase_sync_service.download_from_cloud()
                
                # Refrescar vistas si se descargaron datos
                if result.tasks_downloaded > 0 and self.current_section == "tasks":
                    self._load_tasks()
                if result.habits_downloaded > 0 and self.current_section == "habits":
                    self._load_habits()
                
                self._show_sync_results_page(
                    success=result.success,
                    sync_result=result
                )
            except Exception as ex:
                self._show_sync_results_page(
                    success=False,
                    error_message=str(ex)
                )
        
        # Botones de acción
        upload_button = ft.ElevatedButton(
            text="Subir datos locales a la nube",
            icon=ft.Icons.CLOUD_UPLOAD,
            on_click=upload_to_cloud,
            expand=True,
            height=60,
            bgcolor=ft.Colors.BLUE,
            color=ft.Colors.WHITE,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=10)
            )
        )
        
        download_button = ft.ElevatedButton(
            text="Descargar datos de la nube al local",
            icon=ft.Icons.CLOUD_DOWNLOAD,
            on_click=download_from_cloud,
            expand=True,
            height=60,
            bgcolor=ft.Colors.GREEN,
            color=ft.Colors.WHITE,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=10)
            )
        )
        
        # Construir la vista
        direction_view = ft.View(
            route="/sync-direction",
            appbar=ft.AppBar(
                title=ft.Text("Sincronización"),
                leading=ft.IconButton(
                    icon=ft.Icons.ARROW_BACK,
                    on_click=lambda e: self._go_back()
                ),
                bgcolor=primary_color
            ),
            padding=20,
            scroll=ft.ScrollMode.AUTO,
            controls=[
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Icon(
                                ft.Icons.SYNC,
                                size=64,
                                color=primary_color
                            ),
                            ft.Text(
                                "Selecciona la dirección de sincronización",
                                size=22,
                                weight=ft.FontWeight.BOLD,
                                text_align=ft.TextAlign.CENTER
                            ),
                            ft.Divider(height=30),
                            ft.Container(
                                content=ft.Column(
                                    [
                                        ft.Row(
                                            [
                                                ft.Icon(ft.Icons.PHONE_ANDROID, size=32, color=ft.Colors.BLUE),
                                                ft.Column(
                                                    [
                                                        ft.Text(
                                                            "Datos locales",
                                                            size=16,
                                                            weight=ft.FontWeight.BOLD
                                                        ),
                                                        ft.Text(
                                                            "Tareas y hábitos guardados en tu dispositivo",
                                                            size=12,
                                                            color=ft.Colors.GREY_600 if not is_dark else ft.Colors.GREY_400
                                                        )
                                                    ],
                                                    spacing=5
                                                )
                                            ],
                                            spacing=15
                                        ),
                                        ft.Divider(height=20),
                                        ft.Row(
                                            [
                                                ft.Icon(ft.Icons.CLOUD, size=32, color=ft.Colors.GREEN),
                                                ft.Column(
                                                    [
                                                        ft.Text(
                                                            "Datos en la nube",
                                                            size=16,
                                                            weight=ft.FontWeight.BOLD
                                                        ),
                                                        ft.Text(
                                                            "Tareas y hábitos guardados en Firebase",
                                                            size=12,
                                                            color=ft.Colors.GREY_600 if not is_dark else ft.Colors.GREY_400
                                                        )
                                                    ],
                                                    spacing=5
                                                )
                                            ],
                                            spacing=15
                                        )
                                    ],
                                    spacing=10
                                ),
                                padding=20,
                                bgcolor=ft.Colors.BLUE_50 if not is_dark else ft.Colors.BLUE_900,
                                border_radius=10,
                                border=ft.border.all(1, ft.Colors.BLUE_200 if not is_dark else ft.Colors.BLUE_700)
                            ),
                            ft.Divider(height=30),
                            ft.Text(
                                "¿Qué deseas hacer?",
                                size=18,
                                weight=ft.FontWeight.BOLD,
                                text_align=ft.TextAlign.CENTER
                            ),
                            upload_button,
                            download_button,
                            ft.Divider(height=20),
                            ft.Container(
                                content=ft.Row(
                                    [
                                        ft.Icon(ft.Icons.INFO_OUTLINE, size=20, color=ft.Colors.ORANGE),
                                        ft.Container(
                                            content=ft.Text(
                                                "Subir: Respalda tus datos locales en Firebase.\n"
                                                "Descargar: Trae datos de Firebase a tu dispositivo.",
                                                size=12,
                                                color=ft.Colors.GREY_600 if not is_dark else ft.Colors.GREY_400
                                            ),
                                            expand=True
                                        )
                                    ],
                                    spacing=10
                                ),
                                padding=15,
                                bgcolor=ft.Colors.ORANGE_50 if not is_dark else ft.Colors.ORANGE_900,
                                border_radius=10
                            )
                        ],
                        spacing=20,
                        horizontal_alignment=ft.CrossAxisAlignment.STRETCH
                    ),
                    padding=20,
                    border_radius=10,
                    bgcolor=ft.Colors.GREY_900 if is_dark else ft.Colors.GREY_100
                )
            ]
        )
        
        self.page.views.append(direction_view)
        self.page.go("/sync-direction")
        self.page.update()
    
    def _show_sync_loading_page(self):
        """Muestra una página de carga durante la sincronización."""
        is_dark = self.page.theme_mode == ft.ThemeMode.DARK
        scheme = self.page.theme.color_scheme if self.page.theme else None
        primary_color = scheme.primary if scheme and scheme.primary else ft.Colors.BLUE_700
        
        loading_view = ft.View(
            route="/sync-loading",
            appbar=ft.AppBar(
                title=ft.Text("Sincronizando..."),
                bgcolor=primary_color
            ),
            padding=20,
            controls=[
                ft.Container(
                    content=ft.Column(
                        [
                            ft.ProgressRing(width=64, height=64),
                            ft.Divider(height=30),
                            ft.Text(
                                "Sincronizando datos con Firebase...",
                                size=18,
                                weight=ft.FontWeight.BOLD,
                                text_align=ft.TextAlign.CENTER
                            ),
                            ft.Text(
                                "Por favor espera",
                                size=14,
                                color=ft.Colors.GREY_600 if not is_dark else ft.Colors.GREY_400,
                                text_align=ft.TextAlign.CENTER
                            )
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=15
                    ),
                    padding=40,
                    alignment=ft.alignment.center
                )
            ]
        )
        
        self.page.views.append(loading_view)
        self.page.go("/sync-loading")
        self.page.update()
    
    def _show_sync_results_page(self, success: bool, sync_result=None, error_message: str = None):
        """
        Muestra una página completa con los resultados de la sincronización.
        
        Args:
            success: True si la sincronización fue exitosa
            sync_result: Objeto SyncResult con los detalles de la sincronización
            error_message: Mensaje de error si success=False
        """
        is_dark = self.page.theme_mode == ft.ThemeMode.DARK
        scheme = self.page.theme.color_scheme if self.page.theme else None
        primary_color = scheme.primary if scheme and scheme.primary else ft.Colors.BLUE_700
        
        # Remover la página de carga si existe
        if len(self.page.views) > 1 and self.page.views[-1].route == "/sync-loading":
            self.page.views.pop()
        
        # Contenido de la página
        content_controls = []
        
        if success and sync_result:
            # Página de éxito
            icon_color = ft.Colors.GREEN
            title_text = "✓ Sincronización completada"
            title_color = ft.Colors.GREEN
            
            # Estadísticas
            stats = []
            
            if sync_result.tasks_uploaded > 0:
                stats.append(ft.ListTile(
                    leading=ft.Icon(ft.Icons.UPLOAD, color=ft.Colors.BLUE),
                    title=ft.Text(f"Tareas subidas: {sync_result.tasks_uploaded}"),
                    subtitle=ft.Text("Datos locales respaldados en Firebase")
                ))
            
            if sync_result.tasks_downloaded > 0:
                stats.append(ft.ListTile(
                    leading=ft.Icon(ft.Icons.DOWNLOAD, color=ft.Colors.GREEN),
                    title=ft.Text(f"Tareas descargadas: {sync_result.tasks_downloaded}"),
                    subtitle=ft.Text("Datos remotos agregados localmente")
                ))
            
            if sync_result.habits_uploaded > 0:
                stats.append(ft.ListTile(
                    leading=ft.Icon(ft.Icons.UPLOAD, color=ft.Colors.BLUE),
                    title=ft.Text(f"Hábitos subidos: {sync_result.habits_uploaded}"),
                    subtitle=ft.Text("Datos locales respaldados en Firebase")
                ))
            
            if sync_result.habits_downloaded > 0:
                stats.append(ft.ListTile(
                    leading=ft.Icon(ft.Icons.DOWNLOAD, color=ft.Colors.GREEN),
                    title=ft.Text(f"Hábitos descargados: {sync_result.habits_downloaded}"),
                    subtitle=ft.Text("Datos remotos agregados localmente")
                ))
            
            if not stats:
                stats.append(ft.Text(
                    "No hubo cambios que sincronizar. Los datos ya están actualizados.",
                    size=14,
                    color=ft.Colors.GREY_600 if not is_dark else ft.Colors.GREY_400,
                    text_align=ft.TextAlign.CENTER
                ))
            
            content_controls.extend(stats)
            
            # Advertencias si las hay
            if sync_result.errors:
                content_controls.append(ft.Divider(height=20))
                content_controls.append(ft.Text(
                    f"⚠ Advertencias ({len(sync_result.errors)}):",
                    size=16,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.ORANGE
                ))
                
                for error in sync_result.errors:
                    error_text = ft.Text(error, size=12, selectable=True)
                    copy_button = ft.IconButton(
                        icon=ft.Icons.COPY,
                        tooltip="Copiar advertencia",
                        icon_size=18,
                        icon_color=ft.Colors.ORANGE,
                        on_click=lambda e, err=error: self._copy_error_to_clipboard(err, None)
                    )
                    
                    content_controls.append(
                        ft.Container(
                            content=ft.Row(
                                [
                                    ft.Container(content=error_text, expand=True, padding=ft.padding.only(right=5)),
                                    copy_button
                                ],
                                spacing=5,
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                            ),
                            padding=10,
                            bgcolor=ft.Colors.ORANGE_50 if not is_dark else ft.Colors.ORANGE_900,
                            border_radius=5,
                            border=ft.border.all(1, ft.Colors.ORANGE_300 if not is_dark else ft.Colors.ORANGE_700)
                        )
                    )
        
        else:
            # Página de error
            icon_color = ft.Colors.RED
            title_text = "✗ Error en la sincronización"
            title_color = ft.Colors.RED
            
            error_msg = error_message or "Error desconocido durante la sincronización"
            if sync_result and sync_result.errors:
                error_msg = "\n".join(sync_result.errors)
            
            # Texto del error (seleccionable)
            error_text = ft.Text(
                error_msg,
                size=14,
                selectable=True,
                weight=ft.FontWeight.W_500
            )
            
            # Botón para copiar error
            copy_button = ft.IconButton(
                icon=ft.Icons.COPY,
                tooltip="Copiar error al portapapeles",
                icon_size=20,
                icon_color=ft.Colors.RED,
                on_click=lambda e: self._copy_error_to_clipboard(error_msg, None)
            )
            
            content_controls.append(
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Row(
                                [
                                    ft.Container(content=error_text, expand=True, padding=ft.padding.only(right=5)),
                                    copy_button
                                ],
                                spacing=5,
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                            )
                        ],
                        spacing=10
                    ),
                    padding=15,
                    bgcolor=ft.Colors.RED_50 if not is_dark else ft.Colors.RED_900,
                    border_radius=10,
                    border=ft.border.all(2, ft.Colors.RED_300 if not is_dark else ft.Colors.RED_700)
                )
            )
        
        # Botón para volver
        back_button = ft.ElevatedButton(
            text="Volver",
            icon=ft.Icons.ARROW_BACK,
            on_click=lambda e: self._go_back(),
            expand=True,
            height=50,
            bgcolor=primary_color,
            color=ft.Colors.WHITE
        )
        
        # Construir la vista
        results_view = ft.View(
            route="/sync-results",
            appbar=ft.AppBar(
                title=ft.Text("Resultados de sincronización"),
                leading=ft.IconButton(
                    icon=ft.Icons.ARROW_BACK,
                    on_click=lambda e: self._go_back()
                ),
                bgcolor=primary_color
            ),
            padding=20,
            scroll=ft.ScrollMode.AUTO,
            controls=[
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Icon(
                                ft.Icons.CHECK_CIRCLE if success else ft.Icons.ERROR,
                                size=64,
                                color=icon_color
                            ),
                            ft.Text(
                                title_text,
                                size=24,
                                weight=ft.FontWeight.BOLD,
                                color=title_color,
                                text_align=ft.TextAlign.CENTER
                            ),
                            ft.Divider(height=30),
                            *content_controls,
                            ft.Divider(height=30),
                            back_button
                        ],
                        spacing=15,
                        horizontal_alignment=ft.CrossAxisAlignment.STRETCH
                    ),
                    padding=20,
                    border_radius=10,
                    bgcolor=ft.Colors.GREY_900 if is_dark else ft.Colors.GREY_100
                )
            ]
        )
        
        self.page.views.append(results_view)
        self.page.go("/sync-results")
        self.page.update()
    
    def _go_back(self, e=None):
        """Vuelve a la vista anterior."""
        if len(self.page.views) > 1:
            self.page.views.pop()
            top_view = self.page.views[-1]
            self.page.go(top_view.route)
        else:
            # Si no hay vista anterior, ir a la principal
            self.page.go("/")
        self.page.update()
    

    def _show_storage_permission_dialog(self):
        """Muestra una página informativa sobre permisos de almacenamiento en Android/iOS."""
        if self.page.platform != ft.PagePlatform.ANDROID and self.page.platform != ft.PagePlatform.IOS:
            return  # Solo en móvil

        # Crear página de permisos
        is_dark = self.page.theme_mode == ft.ThemeMode.DARK
        scheme = self.page.theme.color_scheme if self.page.theme else None
        primary_color = scheme.primary if scheme and scheme.primary else ft.Colors.BLUE_700
        
        def test_permission(e):
            """Intenta activar el FilePicker para solicitar permisos."""
            try:
                # Usar el export_file_picker para activar permisos
                # Esto debería mostrar el diálogo de permisos de Android
                self.export_file_picker.save_file(file_name="test_permission.zip")
                
                # Mostrar mensaje informativo
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text("Si aparece un diálogo de permisos, acepta para continuar."),
                    bgcolor=ft.Colors.BLUE,
                    duration=3000
                )
                self.page.snack_bar.open = True
                self.page.update()
            except Exception as ex:
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text(f"Error al solicitar permisos: {str(ex)}"),
                    bgcolor=ft.Colors.RED,
                    duration=4000
                )
                self.page.snack_bar.open = True
                self.page.update()
        
        def close_permission_page(e):
            """Cierra la página de permisos y vuelve a la vista principal."""
            self._go_back()
        
        # Botones
        test_button = ft.ElevatedButton(
            text="Probar permisos ahora",
            icon=ft.Icons.STORAGE,
            on_click=test_permission,
            expand=True,
            height=50,
            bgcolor=primary_color,
            color=ft.Colors.WHITE
        )
        
        understood_button = ft.OutlinedButton(
            text="Entendido",
            icon=ft.Icons.CHECK,
            on_click=close_permission_page,
            expand=True,
            height=50,
            style=ft.ButtonStyle(color=primary_color)
        )
        
        # Construir la página
        permission_view = ft.View(
            route="/storage-permissions",
            appbar=ft.AppBar(
                title=ft.Text("Permisos de almacenamiento"),
                leading=ft.IconButton(
                    icon=ft.Icons.ARROW_BACK,
                    on_click=close_permission_page
                ),
                bgcolor=primary_color
            ),
            padding=20,
            scroll=ft.ScrollMode.AUTO,
            controls=[
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Icon(
                                ft.Icons.STORAGE,
                                size=64,
                                color=primary_color
                            ),
                            ft.Text(
                                "Permisos de almacenamiento",
                                size=24,
                                weight=ft.FontWeight.BOLD,
                                text_align=ft.TextAlign.CENTER
                            ),
                            ft.Divider(height=20),
                            ft.Text(
                                "Para usar las funciones de importar y exportar datos, "
                                "la aplicación necesita acceso al almacenamiento de tu dispositivo.",
                                size=16,
                                text_align=ft.TextAlign.CENTER
                            ),
                            ft.Divider(height=20),
                            ft.Container(
                                content=ft.Column(
                                    [
                                        ft.Row(
                                            [
                                                ft.Icon(ft.Icons.INFO_OUTLINE, color=ft.Colors.BLUE),
                                                ft.Text(
                                                    "¿Cuándo se solicitan?",
                                                    size=16,
                                                    weight=ft.FontWeight.BOLD
                                                )
                                            ],
                                            spacing=10
                                        ),
                                        ft.Text(
                                            "Los permisos se solicitarán automáticamente cuando uses "
                                            "las funciones de importar o exportar por primera vez.",
                                            size=14,
                                            color=ft.Colors.GREY_600 if not is_dark else ft.Colors.GREY_400
                                        )
                                    ],
                                    spacing=10
                                ),
                                padding=15,
                                bgcolor=ft.Colors.BLUE_50 if not is_dark else ft.Colors.BLUE_900,
                                border_radius=10,
                                border=ft.border.all(1, ft.Colors.BLUE_200 if not is_dark else ft.Colors.BLUE_700)
                            ),
                            ft.Divider(height=20),
                            ft.Container(
                                content=ft.Column(
                                    [
                                        ft.Row(
                                            [
                                                ft.Icon(ft.Icons.LIGHTBULB_OUTLINE, color=ft.Colors.ORANGE),
                                                ft.Text(
                                                    "Recomendación",
                                                    size=16,
                                                    weight=ft.FontWeight.BOLD
                                                )
                                            ],
                                            spacing=10
                                        ),
                                        ft.Text(
                                            "Guarda los backups en la carpeta 'Descargas' "
                                            "para mayor compatibilidad con diferentes dispositivos Android.",
                                            size=14,
                                            color=ft.Colors.GREY_600 if not is_dark else ft.Colors.GREY_400
                                        )
                                    ],
                                    spacing=10
                                ),
                                padding=15,
                                bgcolor=ft.Colors.ORANGE_50 if not is_dark else ft.Colors.ORANGE_900,
                                border_radius=10,
                                border=ft.border.all(1, ft.Colors.ORANGE_200 if not is_dark else ft.Colors.ORANGE_700)
                            ),
                            ft.Divider(height=30),
                            ft.Column(
                                [
                                    test_button,
                                    understood_button
                                ],
                                spacing=10,
                                horizontal_alignment=ft.CrossAxisAlignment.STRETCH
                            )
                        ],
                        spacing=15,
                        horizontal_alignment=ft.CrossAxisAlignment.STRETCH
                    ),
                    padding=20,
                    border_radius=10,
                    bgcolor=ft.Colors.GREY_900 if is_dark else ft.Colors.GREY_100
                )
            ]
        )
        
        self.page.views.append(permission_view)
        self.page.go("/storage-permissions")
        self.page.update()
    
    def _load_tasks(self):
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
                                    margin=ft.margin.only(right=12 if idx < len(row_tasks) - 1 else 0),
                                    width=None,  # Sin ancho fijo para que sea flexible
                                    constraints=ft.BoxConstraints(
                                        min_width=300,  # Ancho mínimo para legibilidad
                                        max_width=None  # Sin máximo para que se expanda
                                    )
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
                                width=None  # Sin ancho fijo
                            )
                        )
        
        self.page.update()
    
    def _filter_tasks(self, filter_completed: Optional[bool]):
        """Filtra las tareas por estado (mantenido para compatibilidad)."""
        # Aplicar el filtro a todas las prioridades
        for priority in self.priority_filters:
            self.priority_filters[priority] = filter_completed
        self._load_tasks()
    
    def _filter_priority_tasks(self, priority: str, filter_completed: Optional[bool]):
        """Filtra las tareas de una prioridad específica."""
        self.priority_filters[priority] = filter_completed
        self._load_tasks()
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
        # Reconstruir la barra de navegación con el estado actualizado
        if self.home_view and len(self.home_view.controls) > 0:
            main_column = self.home_view.controls[0]
            if isinstance(main_column, ft.Column) and len(main_column.controls) > 1:
                main_view = main_column.controls[1]
                if isinstance(main_view, ft.Container) and main_view.content:
                    main_content = main_view.content
                    if isinstance(main_content, ft.Column) and len(main_content.controls) > 0:
                        # Reemplazar la barra de navegación
                        new_nav = self._build_priority_navigation_bar()
                        main_content.controls[0] = new_nav
    
    def _scroll_to_priority(self, priority: str):
        """Hace scroll automático hasta la sección de prioridad especificada."""
        self.current_priority_section = priority
        
        # Actualizar la barra de navegación para reflejar el estado activo
        self._update_priority_navigation()
        
        # Nota: Flet no tiene scroll programático directo en versiones actuales
        # El scroll manual funcionará correctamente, y los botones sirven como navegación visual
        # En futuras versiones de Flet se puede implementar scroll programático
        
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
            on_cancel=self._go_back,
            task=self.editing_task
        )
        
        # Detectar el tema actual
        is_dark = self.page.theme_mode == ft.ThemeMode.DARK
        bgcolor = ft.Colors.BLACK if is_dark else ft.Colors.GREY_50
        
        # Crear la barra de título con botón de volver
        back_button = ft.IconButton(
            icon=ft.Icons.ARROW_BACK,
            on_click=lambda e: self._go_back(),
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
        self.editing_habit = None
        # Remover la última vista (el formulario)
        if len(self.page.views) > 1:
            self.page.views.pop()
        # Navegar a la vista principal
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
        # El contenedor debería estar disponible ya que no se reconstruye la UI
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
        # Alternar modo y persistir a través del servicio de ajustes
        current = self.settings_service.get_settings()
        new_mode = "light" if current.theme_mode == "dark" else "dark"
        updated = self.settings_service.update_settings(theme_mode=new_mode)
        apply_theme_to_page(self.page, updated)

        # Reconstruir vista según sección actual
        if self.current_section == "tasks":
            self._build_ui()
            self._load_tasks()
        elif self.current_section == "habits":
            self._build_habits_view()
        elif self.current_section == "settings":
            self._build_settings_view()

        self.page.update()

    def _open_accent_dialog(self, e):
        """Abre el diálogo con la paleta de matices disponibles."""
        current_settings = self.settings_service.get_settings()

        # Secciones de colores con sus opciones
        sections: list[tuple[str, list[tuple[str, str, str]]]] = [
            (
                "Azules",
                [
                    ("dodger_blue", "#1E90FF", "DodgerBlue"),
                    ("primary_blue", "#007BFF", "Primary Blue"),
                    ("bootstrap_blue", "#0D6EFD", "Bootstrap Blue"),
                    ("deep_blue", "#0056B3", "Deep Blue"),
                    ("deepsky_blue", "#00BFFF", "DeepSkyBlue"),
                    ("steel_blue", "#4682B4", "SteelBlue"),
                    ("navy_dark", "#003366", "Navy Dark"),
                ],
            ),
            (
                "Verdes",
                [
                    ("success_green", "#28A745", "Success Green"),
                    ("emerald", "#2ECC71", "Emerald"),
                    ("bright_green", "#00C853", "Bright Green"),
                    ("material_green", "#4CAF50", "Material Green"),
                    ("turquoise", "#1ABC9C", "Turquoise"),
                    ("green_sea", "#16A085", "Green Sea"),
                    ("dark_teal", "#00695C", "Dark Teal"),
                ],
            ),
            (
                "Rojos",
                [
                    ("danger_red", "#DC3545", "Danger Red"),
                    ("alizarin", "#E74C3C", "Alizarin"),
                    ("dark_red", "#C0392B", "Dark Red"),
                    ("soft_red", "#FF5252", "Soft Red"),
                    ("deep_red", "#B71C1C", "Deep Red"),
                    ("vivid_red", "#FF1744", "Vivid Red"),
                ],
            ),
            (
                "Amarillos / Naranjas",
                [
                    ("amber", "#FFC107", "Amber"),
                    ("soft_yellow", "#FFD54F", "Soft Yellow"),
                    ("orange", "#FF9800", "Orange"),
                    ("deep_orange", "#FF5722", "Deep Orange"),
                    ("sun_orange", "#F39C12", "Sun Orange"),
                    ("golden", "#FFB300", "Golden"),
                ],
            ),
            (
                "Morados / Rosas",
                [
                    ("ui_purple", "#6F42C1", "Purple UI"),
                    ("amethyst", "#9B59B6", "Amethyst"),
                    ("dark_purple", "#8E44AD", "Dark Purple"),
                    ("vibrant_purple", "#E056FD", "Vibrant Purple"),
                    ("ui_pink", "#D63384", "Pink"),
                    ("hot_pink", "#FF69B4", "Hot Pink"),
                ],
            ),
            (
                "Grises / Neutros",
                [
                    ("dark_gray", "#212529", "Dark Gray"),
                    ("charcoal", "#343A40", "Charcoal"),
                    ("medium_gray", "#495057", "Medium Gray"),
                    ("secondary_gray", "#6C757D", "Secondary Gray"),
                    ("light_gray", "#ADB5BD", "Light Gray"),
                    ("soft_gray", "#DEE2E6", "Soft Gray"),
                    ("almost_white", "#F8F9FA", "Almost White"),
                ],
            ),
            (
                "Blancos / Negros",
                [
                    ("black", "#000000", "Black"),
                    ("white", "#FFFFFF", "White"),
                    ("soft_white", "#FAFAFA", "Soft White"),
                    ("true_dark", "#121212", "True Dark Mode"),
                ],
            ),
            (
                "Colores gamer / UI",
                [
                    ("neon_cyan", "#00E5FF", "Neon Cyan"),
                    ("neon_green", "#76FF03", "Neon Green"),
                    ("neon_pink", "#FF4081", "Neon Pink"),
                    ("electric_purple", "#651FFF", "Electric Purple"),
                    ("tech_blue", "#00B0FF", "Tech Blue"),
                    ("mint_neon", "#1DE9B6", "Mint Neon"),
                    ("orange_neon", "#FF9100", "Orange Neon"),
                ],
            ),
        ]

        section_controls: list[ft.Control] = []

        for title, options in sections:
            # Título de sección
            section_controls.append(
                ft.Text(
                    title,
                    size=16,
                    weight=ft.FontWeight.BOLD,
                )
            )

            # Botones de la sección, organizados en filas
            buttons: list[ft.Container] = []
            for value, color, label in options:
                selected = value == current_settings.accent_color
                buttons.append(
                    ft.Container(
                        content=ft.IconButton(
                            icon=ft.Icons.CIRCLE,
                            icon_color=color,
                            tooltip=label,
                            data=value,
                            on_click=self._on_accent_button_click,
                        ),
                        border=ft.border.all(
                            2,
                            color if selected else ft.Colors.TRANSPARENT,
                        ),
                        border_radius=20,
                        padding=4,
                    )
                )

            # Agrupar botones en filas de 4 para mejor uso de espacio
            for i in range(0, len(buttons), 4):
                section_controls.append(
                    ft.Row(
                        controls=buttons[i : i + 4],
                        spacing=8,
                        alignment=ft.MainAxisAlignment.START,
                    )
                )

            # Separador entre secciones
            section_controls.append(ft.Divider())

        # Contenido scrollable ocupando ~70% del ancho de la pantalla
        try:
            content_width = self.page.width * 0.7 if (hasattr(self.page, 'width') and self.page.width is not None and isinstance(self.page.width, (int, float))) else None
        except (AttributeError, TypeError):
            content_width = None

        self.accent_dialog.title = ft.Text("Selecciona un matiz")
        self.accent_dialog.content = ft.Container(
            width=content_width,
            content=ft.Column(
                controls=section_controls,
                spacing=8,
                scroll=ft.ScrollMode.AUTO,
            ),
        )
        self.accent_dialog.actions = [
            ft.TextButton("Cerrar", on_click=lambda ev: self._close_accent_dialog())
        ]
        self.accent_dialog.open = True
        self.page.dialog = self.accent_dialog
        self.page.update()

    def _on_accent_button_click(self, e: ft.ControlEvent):
        """Cambio de color principal desde la grid de matices."""
        value = e.control.data
        # La validación se hace de forma implícita en SettingsService mediante AccentColorLiteral,
        # aquí solo comprobamos que exista algún valor.
        if not value:
            return

        updated = self.settings_service.update_settings(accent_color=value)
        apply_theme_to_page(self.page, updated)

        # Reconstruir la vista actual respetando la sección activa
        if self.current_section == "tasks":
            self._build_ui()
            self._load_tasks()
        elif self.current_section == "habits":
            self._build_habits_view()
        elif self.current_section == "settings":
            self._build_settings_view()

        # Cerrar el diálogo de selección si está abierto
        self._close_accent_dialog()
        self.page.update()

    def _close_accent_dialog(self):
        """Cierra el diálogo de selección de matiz si está abierto."""
        if hasattr(self, "accent_dialog"):
            self.accent_dialog.open = False
            self.page.update()
    
    def _toggle_subtask(self, subtask_id: int):
        """Cambia el estado de completado de una subtarea."""
        self.task_service.toggle_subtask_complete(subtask_id)
        self._load_tasks()
    
    def _delete_subtask(self, subtask_id: int):
        """Elimina una subtarea."""
        self.task_service.delete_subtask(subtask_id)
        self._load_tasks()
    
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
        from datetime import datetime
        
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
                        # Mostrar error en la página en lugar de actualizar el campo
                        self.page.snack_bar = ft.SnackBar(
                            content=ft.Text("Error: No se encontró la tarea padre"),
                            bgcolor=ft.Colors.RED
                        )
                        self.page.snack_bar.open = True
                        self.page.update()
                        return
                
                self._go_back_from_form()
                self._load_tasks()
            except Exception as ex:
                # Mostrar error en la página en lugar de actualizar el campo
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text(f"Error: {str(ex)}"),
                    bgcolor=ft.Colors.RED
                )
                self.page.snack_bar.open = True
                self.page.update()
        
        # Crear la barra de título con botón de volver
        back_button = ft.IconButton(
            icon=ft.Icons.ARROW_BACK,
            on_click=lambda e: self._go_back(),
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
            on_click=lambda e: self._go_back(),
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
    
    # ==================== MÉTODOS PARA HÁBITOS ====================
    
    def _load_habits(self):
        """Carga los hábitos desde la base de datos."""
        habits = self.habit_service.get_all_habits(self.current_habit_filter)
        
        # Asegurarse de que el contenedor existe
        if not hasattr(self, 'habits_container') or self.habits_container is None:
            return
        
        self.habits_container.controls.clear()
        
        if not habits:
            self.habits_container.controls.append(create_habit_empty_state(self.page))
        else:
            for habit in habits:
                # Obtener métricas del hábito
                metrics = self.habit_service.get_habit_metrics(habit.id)
                
                card = create_habit_card(
                    habit,
                    metrics,
                    on_toggle_completion=self._toggle_habit_completion,
                    on_edit=self._edit_habit,
                    on_delete=self._delete_habit,
                    on_view_details=self._view_habit_details,
                    page=self.page
                )
                self.habits_container.controls.append(card)
        
        # Actualizar estadísticas
        if hasattr(self, 'habit_stats_container') and self.habit_stats_container:
            stats = self.habit_service.get_statistics()
            self.habit_stats_container.content = create_habit_statistics_card(stats, self.page)
            try:
                self.habit_stats_container.update()
            except:
                pass
        
        try:
            self.habits_container.update()
        except:
            pass
        self.page.update()
    
    def _filter_habits(self, filter_active: Optional[bool]):
        """Filtra los hábitos por estado activo/inactivo."""
        self.current_habit_filter = filter_active
        self._load_habits()
        # Actualizar colores de los botones de filtro
        self._update_habit_filters()
    
    def _update_habit_filters(self):
        """Actualiza los colores de los botones de filtro de hábitos."""
        is_dark = self.page.theme_mode == ft.ThemeMode.DARK
        active_bg = ft.Colors.RED_700 if is_dark else ft.Colors.RED_600
        inactive_bg = ft.Colors.GREY_800 if is_dark else ft.Colors.RED_100
        text_color = ft.Colors.WHITE
        
        if hasattr(self, 'habit_filter_all_btn'):
            self.habit_filter_all_btn.bgcolor = active_bg if self.current_habit_filter is None else inactive_bg
            self.habit_filter_all_btn.update()
        if hasattr(self, 'habit_filter_active_btn'):
            self.habit_filter_active_btn.bgcolor = active_bg if self.current_habit_filter is True else inactive_bg
            self.habit_filter_active_btn.update()
        if hasattr(self, 'habit_filter_inactive_btn'):
            self.habit_filter_inactive_btn.bgcolor = active_bg if self.current_habit_filter is False else inactive_bg
            self.habit_filter_inactive_btn.update()
    
    def _show_new_habit_form(self, e):
        """Navega a la vista del formulario para crear un nuevo hábito."""
        self.editing_habit = None
        self._navigate_to_habit_form_view()
    
    def _edit_habit(self, habit: Habit):
        """Navega a la vista del formulario para editar un hábito."""
        self.editing_habit = habit
        self._navigate_to_habit_form_view()
    
    def _navigate_to_habit_form_view(self):
        """Navega a la vista del formulario de hábito."""
        title = "Editar Hábito" if self.editing_habit else "Nuevo Hábito"
        
        # Crear el formulario
        form = HabitForm(
            on_save=self._save_habit,
            on_cancel=self._go_back,
            habit=self.editing_habit
        )
        
        # Detectar el tema actual
        is_dark = self.page.theme_mode == ft.ThemeMode.DARK
        bgcolor = ft.Colors.BLACK if is_dark else ft.Colors.GREY_50
        
        # Crear la barra de título con botón de volver
        back_button = ft.IconButton(
            icon=ft.Icons.ARROW_BACK,
            on_click=lambda e: self._go_back(),
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
            route="/habit-form",
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
        self.page.go("/habit-form")
    
    def _save_habit(self, *args):
        """Guarda un hábito (crear o actualizar)."""
        # Si el primer argumento es un objeto Habit, es una actualización
        if args and isinstance(args[0], Habit):
            # Actualizar hábito existente
            habit = args[0]
            self.habit_service.update_habit(habit)
        else:
            # Crear nuevo hábito
            title, description, frequency, target_days = args
            self.habit_service.create_habit(title, description, frequency, target_days)
        
        # Volver a la vista principal
        self._go_back_from_form()
        
        # Forzar actualización de la página antes de recargar hábitos
        self.page.update()
        
        # Recargar los hábitos después de volver
        self._load_habits()
    
    def _toggle_habit_completion(self, habit_id: int):
        """Alterna el cumplimiento de un hábito para hoy."""
        completion = self.habit_service.toggle_completion(habit_id, date.today())
        self._load_habits()
        
        # Mostrar mensaje
        if completion:
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text("¡Hábito completado!"),
                bgcolor=ft.Colors.RED_700
            )
        else:
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text("Cumplimiento eliminado"),
                bgcolor=ft.Colors.GREY_700
            )
        self.page.snack_bar.open = True
        self.page.update()
    
    def _delete_habit(self, habit_id: int):
        """Elimina un hábito."""
        if habit_id is None:
            return
        
        try:
            deleted = self.habit_service.delete_habit(int(habit_id))
            if deleted:
                self._load_habits()
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text("Hábito eliminado correctamente"),
                    bgcolor=ft.Colors.RED_700
                )
                self.page.snack_bar.open = True
            else:
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text("No se pudo eliminar el hábito"),
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
    
    def _view_habit_details(self, habit: Habit):
        """Muestra la vista de detalles de un hábito con historial y métricas."""
        # Obtener métricas completas
        metrics = self.habit_service.get_habit_metrics(habit.id)
        weekly_progress = self.habit_service.get_weekly_progress(habit.id)
        monthly_progress = self.habit_service.get_monthly_progress(habit.id)
        
        # Detectar el tema actual
        is_dark = self.page.theme_mode == ft.ThemeMode.DARK
        bgcolor = ft.Colors.BLACK if is_dark else ft.Colors.GREY_50
        
        # Crear la barra de título con botón de volver
        back_button = ft.IconButton(
            icon=ft.Icons.ARROW_BACK,
            on_click=lambda e: self._go_back(),
            icon_color=ft.Colors.RED_400,
            tooltip="Volver"
        )
        
        title_bar = ft.Container(
            content=ft.Row(
                [
                    back_button,
                    ft.Text(
                        habit.title,
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
        
        # Construir contenido de detalles
        details_content = ft.Container(
            content=ft.Column(
                [
                    # Descripción
                    ft.Text(
                        habit.description if habit.description else "Sin descripción",
                        size=14,
                        color=ft.Colors.GREY_500 if is_dark else ft.Colors.GREY_600
                    ),
                    ft.Divider(),
                    # Métricas principales
                    ft.Text(
                        "Métricas",
                        size=20,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.RED_400
                    ),
                    ft.Row(
                        [
                            ft.Container(
                                content=ft.Column(
                                    [
                                        ft.Text(
                                            str(metrics['streak']),
                                            size=32,
                                            weight=ft.FontWeight.BOLD,
                                            color=ft.Colors.RED_400
                                        ),
                                        ft.Text("Días seguidos", size=12)
                                    ],
                                    horizontal_alignment=ft.CrossAxisAlignment.CENTER
                                ),
                                expand=True
                            ),
                            ft.VerticalDivider(),
                            ft.Container(
                                content=ft.Column(
                                    [
                                        ft.Text(
                                            f"{metrics['completion_percentage']:.1f}%",
                                            size=32,
                                            weight=ft.FontWeight.BOLD,
                                            color=ft.Colors.RED_500
                                        ),
                                        ft.Text("Cumplimiento", size=12)
                                    ],
                                    horizontal_alignment=ft.CrossAxisAlignment.CENTER
                                ),
                                expand=True
                            ),
                            ft.VerticalDivider(),
                            ft.Container(
                                content=ft.Column(
                                    [
                                        ft.Text(
                                            str(metrics['total_completions']),
                                            size=32,
                                            weight=ft.FontWeight.BOLD,
                                            color=ft.Colors.RED_600
                                        ),
                                        ft.Text("Total", size=12)
                                    ],
                                    horizontal_alignment=ft.CrossAxisAlignment.CENTER
                                ),
                                expand=True
                            )
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_EVENLY
                    ),
                    ft.Divider(),
                    # Información adicional
                    ft.Text(
                        f"Frecuencia: {habit.frequency.capitalize()}",
                        size=14
                    ),
                    ft.Text(
                        f"Último cumplimiento: {metrics['last_completion_date'].strftime('%d/%m/%Y') if metrics['last_completion_date'] else 'Nunca'}",
                        size=14
                    )
                ],
                spacing=16,
                scroll=ft.ScrollMode.AUTO
            ),
            padding=20,
            expand=True
        )
        
        # Construir la vista de detalles
        details_view = ft.View(
            route="/habit-details",
            controls=[
                title_bar,
                details_content
            ],
            bgcolor=bgcolor
        )
        
        # Agregar la vista y navegar a ella
        self.page.views.append(details_view)
        self.page.go("/habit-details")

