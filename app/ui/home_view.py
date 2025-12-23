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
from app.ui.tasks_view import TasksView
from app.ui.habits_view import HabitsView


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
        
        # Inicializar vista de tareas como módulo separado
        self.tasks_view = TasksView(
            page=page,
            task_service=self.task_service,
            on_go_back=self._go_back
        )
        
        # Inicializar vista de hábitos como módulo separado
        self.habits_view = HabitsView(
            page=page,
            habit_service=self.habit_service,
            on_go_back=self._go_back
        )
        
        # Secciones: "tasks", "habits", "settings"
        self.current_section = "tasks"
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
        self.tasks_view.load_tasks()
    
    # ==================== MÉTODOS DE TAREAS (delegados a TasksView) ====================
    
    def _get_priority_colors(self, priority: str) -> dict:
        """Delega a TasksView."""
        return self.tasks_view._get_priority_colors(priority)
    
    def _build_priority_section(self, priority: str) -> ft.Container:
        """Delega a TasksView."""
        return self.tasks_view._build_priority_section(priority)
    
    def _build_priority_navigation_bar(self) -> ft.Container:
        """Delega a TasksView."""
        return self.tasks_view._build_priority_navigation_bar()
    
    def _load_tasks(self):
        """Delega a TasksView."""
        return self.tasks_view.load_tasks()
    
    def _filter_priority_tasks(self, priority: str, filter_completed: Optional[bool]):
        """Delega a TasksView."""
        return self.tasks_view._filter_priority_tasks(priority, filter_completed)
    
    def _rebuild_priority_section(self, priority: str):
        """Delega a TasksView."""
        return self.tasks_view._rebuild_priority_section(priority)
    
    def _update_priority_navigation(self):
        """Delega a TasksView."""
        return self.tasks_view._update_priority_navigation()
    
    def _scroll_to_priority(self, priority: str):
        """Delega a TasksView."""
        return self.tasks_view._scroll_to_priority(priority)
    
    def _show_new_task_form(self, e):
        """Delega a TasksView."""
        return self.tasks_view._show_new_task_form(e)
    
    def _edit_task(self, task: Task):
        """Delega a TasksView."""
        return self.tasks_view._edit_task(task)
    
    def _navigate_to_form_view(self):
        """Delega a TasksView."""
        return self.tasks_view._navigate_to_form_view()
    
    def _save_task(self, *args):
        """Delega a TasksView."""
        return self.tasks_view._save_task(*args)
    
    def _toggle_task(self, task_id: int):
        """Delega a TasksView."""
        return self.tasks_view._toggle_task(task_id)
    
    def _delete_task(self, task_id: int):
        """Delega a TasksView."""
        return self.tasks_view._delete_task(task_id)
    
    def _toggle_subtask(self, subtask_id: int):
        """Delega a TasksView."""
        return self.tasks_view._toggle_subtask(subtask_id)
    
    def _delete_subtask(self, subtask_id: int):
        """Delega a TasksView."""
        return self.tasks_view._delete_subtask(subtask_id)
    
    def _show_add_subtask_dialog(self, task_id: int):
        """Delega a TasksView."""
        return self.tasks_view._show_add_subtask_dialog(task_id)
    
    def _edit_subtask(self, subtask):
        """Delega a TasksView."""
        return self.tasks_view._edit_subtask(subtask)
    
    def _navigate_to_subtask_form_view(self):
        """Delega a TasksView."""
        return self.tasks_view._navigate_to_subtask_form_view()
    
    # ==================== MÉTODOS DE HÁBITOS ====================
        """Construye una sección de prioridad con su filtro y tareas."""
        colors = self._get_priority_colors(priority)
        is_dark = self.page.theme_mode == ft.ThemeMode.DARK
        current_filter = self.tasks_view.priority_filters[priority]
        
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
        title_padding_vertical = 10 if is_wide else 8  # Reducido de 14/10 a 10/8
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
            margin=ft.margin.only(top=0)  # Sin margen superior para acercar más
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
            key=f"priority_section_{priority}",  # Key para referencia de scroll
            margin=ft.margin.only(
                bottom=16 if is_desktop else 12,  # Reducido de 24/16 a 16/12
                top=0  # Sin margen superior para acercar más
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
        
        # Botón de agregar tarea - solo mostrar en la sección de tareas
        add_button = None
        if self.current_section == "tasks":
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
            vertical=4 if is_wide_screen else 3,  # Reducido aún más: de 8/6 a 4/3
            horizontal=20 if is_wide_screen else 12
        )
        button_spacing = 10 if is_wide_screen else 6
        
        # Crear Row con botones de prioridad y botón de agregar
        row_controls = buttons.copy()
        if add_button:
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
            margin=ft.margin.only(bottom=0)  # Sin margen inferior para acercar más a las tareas
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
                    )
                ],
                alignment=ft.MainAxisAlignment.START,
                vertical_alignment=ft.CrossAxisAlignment.CENTER
            ),
            padding=ft.padding.symmetric(
                vertical=8 if is_desktop else 6,  # Reducido aún más: de 12/10 a 8/6
                horizontal=32 if is_desktop else 20
            ),
            bgcolor=ft.Colors.BLACK87 if self.page.theme_mode == ft.ThemeMode.DARK else ft.Colors.RED_50,
            margin=ft.margin.only(bottom=0)  # Sin margen inferior para acercar a los botones
        )
        
        # Crear la barra inferior de navegación
        self._build_bottom_bar()
        
        # Construir la vista según la sección actual
        if self.current_section == "tasks":
            # Usar TasksView para construir la vista de tareas
            main_view = self.tasks_view.build_ui()
        elif self.current_section == "habits":
            # Usar HabitsView para construir la vista de hábitos
            main_view = self.habits_view.build_ui(self.title_bar, self.bottom_bar, self.home_view)
        else:
            # Vista de configuración (se construirá en _build_settings_view)
            main_view = ft.Container(content=ft.Text("Cargando configuración..."), expand=True)
        
        # Actualizar la vista principal si es hábitos
        if self.current_section == "habits" and self.home_view:
            is_dark = self.page.theme_mode == ft.ThemeMode.DARK
            bgcolor = ft.Colors.BLACK if is_dark else ft.Colors.GREY_50
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
            self.tasks_view.load_tasks()
        elif section == "habits":
            # Mostrar la vista de hábitos
            self._build_ui()
            self.habits_view.load_habits()
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
        """Delega a HabitsView."""
        self._build_ui()
        self.habits_view.load_habits()

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
                    # Solo mostrar la sección si Firebase está disponible
                    *self._build_firebase_sync_section(preview_color, is_dark),

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
                    ),
                    
                    # Botón discreto para copiar error (solo si hay error de Firebase)
                    *self._get_error_copy_button(preview_color, is_dark)
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

    def _build_firebase_sync_section(self, preview_color, is_dark):
        """
        Construye la sección de autenticación y sincronización con Firebase.
        Retorna una lista de widgets. Si hay error, retorna lista vacía (no muestra nada).
        """
        sync_settings = self.sync_service.get_sync_settings()
        is_authenticated = sync_settings.is_authenticated
        
        if not FIREBASE_AVAILABLE or not self.firebase_auth_service:
            # Si hay error, NO mostrar la sección de autenticación
            # El botón para copiar el error se mostrará al final mediante _get_error_copy_button
            return []
        
        # Si Firebase está disponible, mostrar la sección completa
        return [
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
        ]
    
    def _get_error_copy_button(self, preview_color, is_dark):
        """
        Retorna un botón discreto para copiar el error si Firebase no está disponible.
        Si Firebase está disponible, retorna lista vacía.
        """
        if FIREBASE_AVAILABLE and self.firebase_auth_service:
            return []
        
        # Construir el mensaje de error completo
        error_msg = (
            "Firebase no está disponible porque el módulo 'requests' no se empaquetó correctamente en el APK.\n\n"
            "Solución:\n"
            "1. Reconstruye el APK ejecutando:\n"
            "   ./build_android.sh --apk\n\n"
            "2. Verifica que requests>=2.31.0 esté en:\n"
            "   - requirements.txt\n"
            "   - pyproject.toml (sección dependencies)\n\n"
            "3. Asegúrate de que main.py importa requests explícitamente."
        )
        
        # Obtener el error de importación si existe
        import_error = ""
        try:
            # Acceder a la variable del módulo
            import app.ui.home_view as home_view_module
            import_error = getattr(home_view_module, '_firebase_import_error', '')
        except:
            pass
        
        full_error = f"{error_msg}\n\nError técnico: {import_error}" if import_error else error_msg
        
        # Retornar un botón discreto al final
        return [
            ft.Container(
                content=ft.Row(
                    [
                        ft.IconButton(
                            icon=ft.Icons.CONTENT_COPY,
                            tooltip="Copiar información de error",
                            icon_size=16,
                            on_click=lambda e: self._copy_error_to_clipboard(full_error, None),
                            style=ft.ButtonStyle(
                                color=ft.Colors.GREY_600 if not is_dark else ft.Colors.GREY_400,
                            )
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.END,
                ),
                padding=ft.padding.only(top=8),
            )
        ]
    
    def _build_firebase_auth_section(self, preview_color, is_dark):
        """Construye la sección de autenticación y sincronización con Firebase."""
        sync_settings = self.sync_service.get_sync_settings()
        is_authenticated = sync_settings.is_authenticated
        
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
            self.tasks_view.load_tasks()
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
            self.tasks_view.load_tasks()
        elif self.current_section == "habits":
            self._build_ui()
            self.habits_view.load_habits()
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
    
    # ==================== MÉTODOS DE HÁBITOS (delegados a HabitsView) ====================
    
    def _load_habits(self):
        """Delega a HabitsView."""
        return self.habits_view.load_habits()
    
    def _filter_habits(self, filter_active: Optional[bool]):
        """Delega a HabitsView."""
        return self.habits_view._filter_habits(filter_active)
    
    def _update_habit_filters(self):
        """Delega a HabitsView."""
        return self.habits_view._update_habit_filters()
    
    def _show_new_habit_form(self, e):
        """Delega a HabitsView."""
        return self.habits_view._show_new_habit_form(e)
    
    def _edit_habit(self, habit: Habit):
        """Delega a HabitsView."""
        return self.habits_view._edit_habit(habit)
    
    def _navigate_to_habit_form_view(self):
        """Delega a HabitsView."""
        return self.habits_view._navigate_to_habit_form_view()
    
    def _save_habit(self, *args):
        """Delega a HabitsView."""
        return self.habits_view._save_habit(*args)
    
    def _toggle_habit_completion(self, habit_id: int):
        """Delega a HabitsView."""
        return self.habits_view._toggle_habit_completion(habit_id)
    
    def _delete_habit(self, habit_id: int):
        """Delega a HabitsView."""
        return self.habits_view._delete_habit(habit_id)
    
    def _view_habit_details(self, habit: Habit):
        """Delega a HabitsView."""
        return self.habits_view._view_habit_details(habit)
    

