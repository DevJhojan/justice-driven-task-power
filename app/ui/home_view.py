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
from app.ui.settings_view import SettingsView


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
        
        # Inicializar vista de configuración como módulo separado
        firebase_error = ""
        try:
            if not FIREBASE_AVAILABLE:
                firebase_error = _firebase_import_error
        except:
            pass
        
        self.settings_view = SettingsView(
            page=page,
            settings_service=self.settings_service,
            sync_service=self.sync_service,
            firebase_auth_service=self.firebase_auth_service,
            firebase_sync_service=self.firebase_sync_service,
            firebase_available=FIREBASE_AVAILABLE,
            firebase_import_error=firebase_error,
            on_go_back=self._go_back,
            on_rebuild_tasks=lambda: (self._build_ui() if self.current_section == "tasks" else None, self.tasks_view.load_tasks() if self.current_section == "tasks" else None),
            on_rebuild_habits=lambda: (self._build_ui() if self.current_section == "habits" else None, self.habits_view.load_habits() if self.current_section == "habits" else None)
        )
        
        # Configurar callback para reconstruir vista de configuración
        self.settings_view.set_rebuild_settings_callback(lambda: self._build_ui() if self.current_section == "settings" else None)
        
        # Secciones: "tasks", "habits", "settings"
        self.current_section = "tasks"
        self.stats_card = None
        self.habit_stats_card = None
        self.title_bar = None  # Guardar referencia a la barra de título

        
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
    
    # ==================== MÉTODOS DE HÁBITOS (delegados a HabitsView) ====================
    
    def _build_habits_view(self):
        """Delega a HabitsView."""
        self._build_ui()
        self.habits_view.load_habits()
    
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
                vertical=4 if is_desktop else 3,  # Reducido aún más para eliminar espacio en blanco
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
        elif self.current_section == "settings":
            # Usar SettingsView para construir la vista de configuración
            # Solo el contenido, sin title_bar ni bottom_bar (se agregan en la estructura externa)
            settings_content = self.settings_view.build_ui()
            main_view = settings_content
        else:
            main_view = ft.Container(content=ft.Text("Sección no encontrada"), expand=True)
        
        # Actualizar la vista principal si es hábitos o settings
        if self.current_section in ["habits", "settings"] and self.home_view:
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
            self._build_ui()
        
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
    
    # ==================== MÉTODOS DE CONFIGURACIÓN (delegados a SettingsView) ====================
    # Todos los métodos de configuración han sido movidos a settings_view
    # Estos métodos ya no son necesarios aquí y se eliminan para evitar duplicación
    # Si necesitas cambiar el tema o color, usa self.settings_view directamente
    
    # ==================== FUNCIONES DE FIREBASE (delegadas a SettingsView) ====================
    # Todos los métodos de Firebase han sido movidos a settings_view
    # Estos métodos ya no son necesarios aquí y se eliminan para evitar duplicación
    
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
    
    # ==================== MÉTODOS DE CONFIGURACIÓN (delegados a SettingsView) ====================
    # Todos los métodos de configuración han sido movidos a settings_view
    # Estos métodos ya no son necesarios aquí y se eliminan para evitar duplicación
    # Si necesitas cambiar el tema o color, usa self.settings_view directamente
    
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
    

