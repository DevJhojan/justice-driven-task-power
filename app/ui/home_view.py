"""
Vista principal de la aplicación con barra de navegación inferior.
"""
import flet as ft

from app.ui.tasks.view_tasks import TasksView
from app.ui.habits.view_habits import HabitsView
from app.ui.goals.view_goals import GoalsView
from app.ui.settings.view_settings import SettingsView
from app.ui.summary.view_summary import SummaryView


class HomeView:
    """Vista principal con navegación inferior."""
    
    def __init__(self, page: ft.Page):
        """
        Inicializa la vista principal.
        
        Args:
            page: Página de Flet.
        """
        self.page = page
        self.current_section = "summary"  # Sección inicial
        
        # Inicializar servicios y repositorios
        from app.data.database import get_db
        from app.data.task_repository import TaskRepository
        from app.data.habit_repository import HabitRepository
        from app.data.goal_repository import GoalRepository
        from app.data.subtask_repository import SubtaskRepository
        from app.services.task_service import TaskService
        from app.services.habit_service import HabitService
        from app.services.goal_service import GoalService
        
        db = get_db()
        self.task_service = TaskService(TaskRepository(db), SubtaskRepository(db))
        self.habit_service = HabitService(HabitRepository(db))
        self.goal_service = GoalService(GoalRepository(db))
        
        # Servicio de puntos y niveles
        from app.services.points_service import PointsService
        self.points_service = PointsService(db)
        
        # Servicio de configuración del usuario
        from app.services.user_settings_service import UserSettingsService
        self.user_settings_service = UserSettingsService(db)
        
        # Servicio de recompensas
        from app.data.reward_repository import RewardRepository
        from app.services.reward_service import RewardService
        reward_repository = RewardRepository(db)
        self.reward_service = RewardService(reward_repository, self.points_service)
        
        # Servicio de sincronización con Firebase
        # Guardar como atributo de HomeView para mantener la misma instancia
        self.firebase_sync_service = None
        try:
            from app.services.firebase_sync_service import FirebaseSyncService
            self.firebase_sync_service = FirebaseSyncService(
                db, self.task_service, self.habit_service, self.goal_service,
                self.points_service, self.user_settings_service, self.reward_service
            )
        except ImportError as e:
            print(f"Firebase no disponible (import error): {e}")
            # Continuar sin Firebase
        except Exception as e:
            print(f"Error al inicializar Firebase: {e}")
            import traceback
            traceback.print_exc()
            # Continuar sin Firebase - la app debe funcionar sin él
        
        # Inicializar vistas
        self.tasks_view = TasksView(page, self.task_service, self.points_service)
        self.habits_view = HabitsView(page, self.habit_service, self.points_service)
        self.goals_view = GoalsView(page, self.goal_service, self.points_service)
        self.settings_view = SettingsView(
            page,
            on_name_changed=self.refresh_header,
            firebase_sync_service=self.firebase_sync_service
        )
        self.summary_view = SummaryView(page, self.task_service, self.habit_service, self.goal_service, self.points_service, self.reward_service)
        
        # NO construir UI aquí - se construirá después de configurar los handlers en main.py
    
    def _build_ui(self):
        """Construye la interfaz de usuario."""
        # Crear encabezado con nombre de usuario
        header = self._build_header()
        
        # Obtener el contenido de la sección actual
        content = self._get_section_content()
        
        # Crear barra de navegación inferior
        bottom_nav = self._build_bottom_navigation()
        
        # Crear la vista principal
        main_view = ft.View(
            route="/",
            controls=[
                ft.Column(
                    [
                        header,
                        content,
                        bottom_nav
                    ],
                    spacing=0,
                    expand=True
                )
            ],
            bgcolor=ft.Colors.WHITE if self.page.theme_mode == ft.ThemeMode.LIGHT else ft.Colors.BLACK
        )
        
        # Si ya existe una vista principal, reemplazarla
        # Si no, agregar nueva vista (solo si no hay vistas)
        main_view_index = None
        for i, view in enumerate(self.page.views):
            if view.route == "/":
                main_view_index = i
                break
        
        if main_view_index is not None:
            # Reemplazar la vista principal existente
            self.page.views[main_view_index] = main_view
        else:
            # Si no hay vista principal, agregar
            if len(self.page.views) == 0:
                # No hay vistas, agregar la principal
                self.page.views.append(main_view)
            else:
                # Hay otras vistas, agregar la principal al final
                self.page.views.append(main_view)
        
        self.page.go("/")
        self.page.update()
    
    def _build_header(self) -> ft.Container:
        """Construye el encabezado con el nombre del usuario y nivel."""
        user_name = self.user_settings_service.get_user_name()
        is_dark = self.page.theme_mode == ft.ThemeMode.DARK
        # Usar rojos para el header
        bg_color = ft.Colors.RED_700 if not is_dark else ft.Colors.RED_900
        text_color = ft.Colors.WHITE
        
        # Obtener nivel y puntos
        level_text = ""
        if hasattr(self, 'points_service') and self.points_service:
            level_info = self.points_service.get_level_info()
            level_display_name = level_info.get('level_display_name', 'Nadie')
            level_text = f" | {level_display_name}"
        
        return ft.Container(
            content=ft.Row(
                [
                    ft.Column(
                        [
                    ft.Text(
                                f"{user_name}{level_text}",
                                size=20,
                                weight=ft.FontWeight.BOLD,
                                color=text_color
                    )
                ],
                        spacing=0
                    )
                ],
                alignment=ft.MainAxisAlignment.START
            ),
            padding=ft.padding.symmetric(horizontal=20, vertical=16),
            bgcolor=bg_color
        )
    
    def _get_section_content(self) -> ft.Control:
        """Obtiene el contenido de la sección actual."""
        if self.current_section == "tasks":
            return self.tasks_view.build_ui()
        elif self.current_section == "habits":
            return self.habits_view.build_ui()
        elif self.current_section == "goals":
            return self.goals_view.build_ui()
        elif self.current_section == "summary":
            return self.summary_view.build_ui()
        elif self.current_section == "settings":
            return self.settings_view.build_ui()
        else:
            return ft.Container(
                content=ft.Text("Sección no encontrada"),
            expand=True,
                alignment=ft.alignment.center
            )
    
    def _build_bottom_navigation(self) -> ft.Container:
        """Construye la barra de navegación inferior."""
        # Determinar color según el tema
        is_dark = self.page.theme_mode == ft.ThemeMode.DARK
        bg_color = ft.Colors.SURFACE if is_dark else ft.Colors.WHITE
        # Usar rojos para la selección
        selected_color = ft.Colors.RED_700 if not is_dark else ft.Colors.RED_600
        
        # Iconos y textos para cada sección
        nav_items = [
            ("summary", ft.Icons.BAR_CHART, "Resumen"),
            ("tasks", ft.Icons.ASSIGNMENT, "Tareas"),
            ("habits", ft.Icons.REPEAT, "Hábitos"),
            ("goals", ft.Icons.FLAG, "Metas"),
            ("settings", ft.Icons.SETTINGS, "Config")
        ]
        
        unselected_icon_color = ft.Colors.RED_800 if not is_dark else ft.Colors.RED_400
        
        buttons = []
        for section, icon, label in nav_items:
            is_selected = self.current_section == section
            button = ft.ElevatedButton(
            content=ft.Column(
                [
                        ft.Icon(icon, size=24, color=ft.Colors.WHITE if is_selected else unselected_icon_color),
                        ft.Text(label, size=12, color=ft.Colors.WHITE if is_selected else unselected_icon_color)
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=4,
                tight=True
            ),
                bgcolor=selected_color if is_selected else None,
                color=ft.Colors.WHITE if is_selected else None,
                on_click=lambda e, s=section: self._navigate_to_section(s),
                style=ft.ButtonStyle(
                    shape=ft.RoundedRectangleBorder(radius=8),
                    padding=12
                ),
                expand=True
            )
            buttons.append(button)
        
        return ft.Container(
            content=ft.Row(
                buttons,
                spacing=8,
                alignment=ft.MainAxisAlignment.SPACE_EVENLY
            ),
            bgcolor=bg_color,
            padding=ft.padding.symmetric(horizontal=16, vertical=8),
            border=ft.border.only(
                top=ft.border.BorderSide(1, ft.Colors.OUTLINE)
            )
        )
    
    def _navigate_to_section(self, section: str):
        """Navega a una sección específica."""
        self.current_section = section
        self._build_ui()
        # No llamar a page.update() aquí, ya que _build_ui() lo hace
    
    def refresh_all(self):
        """Refresca todas las vistas después de guardar."""
        self._build_ui()
    
    def refresh_header(self):
        """Refresca el encabezado (útil cuando se cambia el nombre del usuario)."""
        self._build_ui()

