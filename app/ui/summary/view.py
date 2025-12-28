"""
Vista de resumen con estadísticas generales.
"""
import flet as ft
from datetime import date

from app.services.task_service import TaskService
from app.services.habit_service import HabitService
from app.services.goal_service import GoalService
from app.services.points_service import PointsService


class SummaryView:
    """Vista de resumen con estadísticas de tareas, hábitos y metas."""
    
    def __init__(self, page: ft.Page, task_service: TaskService,
                 habit_service: HabitService, goal_service: GoalService,
                 points_service: PointsService = None):
        """
        Inicializa la vista de resumen.
        
        Args:
            page: Página de Flet.
            task_service: Servicio de tareas.
            habit_service: Servicio de hábitos.
            goal_service: Servicio de metas.
            points_service: Servicio de puntos (opcional).
        """
        self.page = page
        self.task_service = task_service
        self.habit_service = habit_service
        self.goal_service = goal_service
        self.points_service = points_service
    
    def build_ui(self) -> ft.Container:
        """
        Construye la interfaz de usuario del resumen.
        
        Returns:
            Container con la vista de resumen.
        """
        # Determinar tema
        is_dark = self.page.theme_mode == ft.ThemeMode.DARK
        bg_color = ft.Colors.BLACK if is_dark else ft.Colors.WHITE
        surface_color = ft.Colors.SURFACE if is_dark else ft.Colors.WHITE
        title_color = ft.Colors.RED_700 if not is_dark else ft.Colors.RED_500
        
        title_bar = ft.Container(
            content=ft.Row(
                [
                    ft.Text(
                        "📊 Resumen",
                        size=24,
                        weight=ft.FontWeight.BOLD,
                        color=title_color
                    )
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN
            ),
            padding=16,
            bgcolor=surface_color
        )
        
        # Obtener estadísticas
        stats = self._calculate_stats()
        
        # Contenedor principal con scroll
        content = ft.Column(
            [
                # Sección de nivel y puntos
                self._build_level_card() if self.points_service else ft.Container(),
                
                # Estadísticas de Tareas
                self._build_section_card(
                    "📋 Tareas",
                    [
                        ("Total", str(stats['tasks']['total']), ft.Colors.BLUE),
                        ("Pendientes", str(stats['tasks']['pending']), ft.Colors.ORANGE),
                        ("Completadas", str(stats['tasks']['completed']), ft.Colors.GREEN),
                    ]
                ),
                
                # Estadísticas de Hábitos
                self._build_section_card(
                    "🔁 Hábitos",
                    [
                        ("Total", str(stats['habits']['total']), ft.Colors.PURPLE),
                        ("Completados hoy", str(stats['habits']['completed_today']), ft.Colors.GREEN),
                        ("Racha promedio", f"{stats['habits']['avg_streak']:.1f} días", ft.Colors.AMBER),
                    ]
                ),
                
                # Estadísticas de Metas
                self._build_section_card(
                    "🎯 Metas",
                    [
                        ("Total", str(stats['goals']['total']), ft.Colors.RED),
                        ("Con progreso", str(stats['goals']['with_progress']), ft.Colors.GREEN),
                        ("Progreso promedio", f"{stats['goals']['avg_progress']:.1f}%", ft.Colors.BLUE),
                    ]
                ),
                
                # Resumen general
                self._build_summary_card(stats)
            ],
            spacing=16,
            scroll=ft.ScrollMode.AUTO,
            expand=True
        )
        
        # Vista principal
        return ft.Container(
            content=ft.Column(
                [
                    title_bar,
                    ft.Container(
                        content=content,
                        padding=16,
                        expand=True,
                        bgcolor=bg_color
                    )
                ],
                spacing=0,
                expand=True
            ),
            expand=True,
            bgcolor=bg_color
        )
    
    def _calculate_stats(self) -> dict:
        """
        Calcula las estadísticas de tareas, hábitos y metas.
        
        Returns:
            Diccionario con las estadísticas calculadas.
        """
        # Estadísticas de tareas
        all_tasks = self.task_service.get_all_tasks()
        pending_tasks = self.task_service.get_pending_tasks()
        completed_tasks = self.task_service.get_completed_tasks()
        
        # Estadísticas de hábitos
        all_habits = self.habit_service.get_all_habits()
        completed_today = sum(1 for habit in all_habits 
                             if self.habit_service.is_completed_today(habit.id))
        streaks = [self.habit_service.get_streak(habit.id) for habit in all_habits]
        avg_streak = sum(streaks) / len(streaks) if streaks else 0
        
        # Estadísticas de metas
        all_goals = self.goal_service.get_all_goals()
        goals_with_progress = [g for g in all_goals if g.current_value > 0]
        progress_percentages = [self.goal_service.get_progress_percentage(g.id) 
                               for g in all_goals if g.target_value]
        avg_progress = sum(progress_percentages) / len(progress_percentages) if progress_percentages else 0
        
        return {
            'tasks': {
                'total': len(all_tasks),
                'pending': len(pending_tasks),
                'completed': len(completed_tasks)
            },
            'habits': {
                'total': len(all_habits),
                'completed_today': completed_today,
                'avg_streak': avg_streak
            },
            'goals': {
                'total': len(all_goals),
                'with_progress': len(goals_with_progress),
                'avg_progress': avg_progress
            }
        }
    
    def _build_section_card(self, title: str, stats: list) -> ft.Container:
        """
        Construye una tarjeta de estadísticas para una sección.
        
        Args:
            title: Título de la sección.
            stats: Lista de tuplas (label, value, color).
        
        Returns:
            Container con la tarjeta de estadísticas.
        """
        is_dark = self.page.theme_mode == ft.ThemeMode.DARK
        bg_color = ft.Colors.SURFACE if is_dark else ft.Colors.WHITE
        text_color = ft.Colors.GREY_400 if is_dark else ft.Colors.GREY_700
        
        stat_items = []
        for label, value, color in stats:
            stat_items.append(
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Text(
                                value,
                                size=32,
                                weight=ft.FontWeight.BOLD,
                                color=color
                            ),
                            ft.Text(
                                label,
                                size=12,
                                color=text_color
                            )
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=4,
                        tight=True
                    ),
                    padding=16,
                    expand=True
                )
            )
        
        return ft.Container(
            content=ft.Column(
                [
                    ft.Text(
                        title,
                        size=18,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.RED_700 if not is_dark else ft.Colors.RED_500
                    ),
                    ft.Row(
                        stat_items,
                        spacing=8,
                        alignment=ft.MainAxisAlignment.SPACE_EVENLY
                    )
                ],
                spacing=12
            ),
            padding=20,
            bgcolor=bg_color,
            border_radius=12,
            border=ft.border.all(1, ft.Colors.OUTLINE)
        )
    
    def _build_summary_card(self, stats: dict) -> ft.Container:
        """
        Construye una tarjeta de resumen general.
        
        Args:
            stats: Diccionario con todas las estadísticas.
        
        Returns:
            Container con la tarjeta de resumen.
        """
        is_dark = self.page.theme_mode == ft.ThemeMode.DARK
        bg_color = ft.Colors.SURFACE if is_dark else ft.Colors.WHITE
        text_color = ft.Colors.GREY_400 if is_dark else ft.Colors.GREY_700
        
        total_items = (
            stats['tasks']['total'] +
            stats['habits']['total'] +
            stats['goals']['total']
        )
        
        completion_rate = 0
        if stats['tasks']['total'] > 0:
            completion_rate = (stats['tasks']['completed'] / stats['tasks']['total']) * 100
        
        return ft.Container(
            content=ft.Column(
                [
                    ft.Text(
                        "📈 Resumen General",
                        size=18,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.RED_700 if not is_dark else ft.Colors.RED_500
                    ),
                    ft.Divider(),
                    ft.Row(
                        [
                            ft.Column(
                                [
                                    ft.Text(
                                        str(total_items),
                                        size=28,
                                        weight=ft.FontWeight.BOLD,
                                        color=ft.Colors.BLUE
                                    ),
                                    ft.Text(
                                        "Items totales",
                                        size=12,
                                        color=text_color
                                    )
                                ],
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                spacing=4,
                                expand=True
                            ),
                            ft.Column(
                                [
                                    ft.Text(
                                        f"{completion_rate:.1f}%",
                                        size=28,
                                        weight=ft.FontWeight.BOLD,
                                        color=ft.Colors.GREEN
                                    ),
                                    ft.Text(
                                        "Tareas completadas",
                                        size=12,
                                        color=text_color
                                    )
                                ],
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                spacing=4,
                                expand=True
                            )
                        ],
                        spacing=16,
                        alignment=ft.MainAxisAlignment.SPACE_EVENLY
                    )
                ],
                spacing=12
            ),
            padding=20,
            bgcolor=bg_color,
            border_radius=12,
            border=ft.border.all(2, ft.Colors.RED_700 if not is_dark else ft.Colors.RED_500)
        )
    
    def _build_level_card(self) -> ft.Container:
        """Construye una tarjeta con información de nivel y puntos."""
        if not self.points_service:
            return ft.Container()
        
        level_info = self.points_service.get_level_info()
        current_level = level_info["current_level"]
        level_display_name = level_info["level_display_name"]
        points = level_info["points"]
        next_level = level_info["next_level"]
        progress = level_info["progress"]
        points_to_next = level_info["points_to_next"]
        
        is_dark = self.page.theme_mode == ft.ThemeMode.DARK
        bg_color = ft.Colors.SURFACE if is_dark else ft.Colors.WHITE
        text_color = ft.Colors.GREY_400 if is_dark else ft.Colors.GREY_700
        
        # Color según el nivel (gradiente de colores)
        level_colors = {
            "Nobody": ft.Colors.GREY,
            "Beginner": ft.Colors.BLUE,
            "Novice": ft.Colors.CYAN,
            "Intermediate": ft.Colors.GREEN,
            "Proficient": ft.Colors.LIME,
            "Advance": ft.Colors.AMBER,
            "Expert": ft.Colors.ORANGE,
            "Master": ft.Colors.RED,
            "Guru": ft.Colors.PURPLE,
            "Legendary": ft.Colors.PINK,
            "Like_a_God": ft.Colors.YELLOW
        }
        level_color = level_colors.get(current_level.display_name, ft.Colors.PRIMARY)
        
        return ft.Container(
            content=ft.Column(
                [
                    ft.Text(
                        "🏆 Tu Nivel",
                        size=18,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.RED_700 if not is_dark else ft.Colors.RED_500
                    ),
                    ft.Container(
                        content=ft.Column(
                            [
                                ft.Text(
                                    level_display_name,
                                    size=32,
                                    weight=ft.FontWeight.BOLD,
                                    color=level_color,
                                    text_align=ft.TextAlign.CENTER
                                ),
                                ft.Text(
                                    f"{points:,.1f} puntos",
                                    size=16,
                                    color=text_color,
                                    text_align=ft.TextAlign.CENTER
                                )
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=4
                        ),
                        padding=16
                    ),
                    ft.ProgressBar(
                        value=progress / 100.0 if progress > 0 else 0,
                        color=level_color,
                        bgcolor=ft.Colors.GREY_300 if not is_dark else ft.Colors.GREY_700,
                        height=20
                    ),
                    ft.Text(
                        f"Próximo nivel: {next_level.display_name} ({points_to_next:,.1f} puntos)",
                        size=12,
                        color=text_color,
                        text_align=ft.TextAlign.CENTER
                    ) if current_level != next_level else ft.Text(
                        "¡Nivel máximo alcanzado!",
                        size=12,
                        color=level_color,
                        text_align=ft.TextAlign.CENTER,
                        weight=ft.FontWeight.BOLD
                    )
                ],
                spacing=12,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER
            ),
            padding=20,
            bgcolor=bg_color,
            border_radius=12,
            border=ft.border.all(2, level_color)
        )

