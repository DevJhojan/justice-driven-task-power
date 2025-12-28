"""
Vista de métricas de hábitos.
Muestra estadísticas detalladas de todos los hábitos.
"""
import flet as ft
from datetime import date, datetime, timedelta
from typing import Dict, List
from collections import defaultdict

from app.services.habit_service import HabitService


class HabitsMetricsView:
    """Vista para mostrar métricas de hábitos."""
    
    def __init__(self, page: ft.Page, habit_service: HabitService):
        """
        Inicializa la vista de métricas.
        
        Args:
            page: Página de Flet.
            habit_service: Servicio de hábitos.
        """
        self.page = page
        self.habit_service = habit_service
        self.metrics_container = None
    
    def build_view(self) -> ft.View:
        """Construye la vista de métricas."""
        is_dark = self.page.theme_mode == ft.ThemeMode.DARK
        bg_color = ft.Colors.WHITE if not is_dark else ft.Colors.BLACK
        title_color = ft.Colors.RED_700 if not is_dark else ft.Colors.RED_500
        
        # Barra superior
        header = ft.Container(
            content=ft.Row(
                [
                    ft.IconButton(
                        icon=ft.Icons.ARROW_BACK,
                        icon_color=title_color,
                        on_click=self._go_back,
                        tooltip="Volver"
                    ),
                    ft.Text(
                        "📊 Métricas de Hábitos",
                        size=20,
                        weight=ft.FontWeight.BOLD,
                        color=title_color,
                        expand=True
                    )
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN
            ),
            padding=16,
            bgcolor=ft.Colors.SURFACE if is_dark else ft.Colors.WHITE,
            border=ft.border.only(bottom=ft.border.BorderSide(1, ft.Colors.OUTLINE))
        )
        
        # Contenedor de métricas
        self.metrics_container = ft.Column(
            [],
            spacing=16,
            scroll=ft.ScrollMode.AUTO,
            expand=True
        )
        
        # Cargar métricas
        self._load_metrics()
        
        # Contenido principal
        content = ft.Container(
            content=self.metrics_container,
            padding=16,
            expand=True
        )
        
        return ft.View(
            route="/habits-metrics",
            controls=[
                ft.Column(
                    [header, content],
                    spacing=0,
                    expand=True
                )
            ],
            bgcolor=bg_color
        )
    
    def _load_metrics(self):
        """Carga y muestra las métricas."""
        if self.metrics_container is None:
            return
        
        self.metrics_container.controls.clear()
        
        habits = self.habit_service.get_all_habits()
        
        if not habits:
            self.metrics_container.controls.append(
                ft.Container(
                    content=ft.Text(
                        "No hay hábitos para mostrar métricas.",
                        size=16,
                        text_align=ft.TextAlign.CENTER
                    ),
                    alignment=ft.alignment.center,
                    padding=32
                )
            )
            return
        
        is_dark = self.page.theme_mode == ft.ThemeMode.DARK
        title_color = ft.Colors.RED_700 if not is_dark else ft.Colors.RED_500
        
        # Métricas generales
        total_habits = len(habits)
        total_completions = sum(
            self.habit_service.get_completion_count(h.id) for h in habits
        )
        total_streaks = sum(
            self.habit_service.get_streak(h.id) for h in habits
        )
        avg_streak = total_streaks / total_habits if total_habits > 0 else 0
        
        # Métricas de la semana
        week_start = date.today() - timedelta(days=date.today().weekday())
        week_completions = self._get_week_completions(habits, week_start)
        
        # Métricas del mes
        month_start = date.today().replace(day=1)
        month_completions = self._get_month_completions(habits, month_start)
        
        # Resumen general
        self.metrics_container.controls.append(
            self._build_summary_card(
                "📈 Resumen General",
                [
                    ("Total de hábitos", f"{total_habits}"),
                    ("Completaciones totales", f"{total_completions}"),
                    ("Racha promedio", f"{avg_streak:.1f} días"),
                    ("Completaciones esta semana", f"{week_completions}"),
                    ("Completaciones este mes", f"{month_completions}")
                ],
                title_color
            )
        )
        
        # Métricas por hábito
        self.metrics_container.controls.append(
            ft.Container(
                content=ft.Text(
                    "📋 Métricas por Hábito",
                    size=18,
                    weight=ft.FontWeight.BOLD,
                    color=title_color
                ),
                padding=ft.padding.only(top=8, bottom=8)
            )
        )
        
        for habit in habits:
            self.metrics_container.controls.append(
                self._build_habit_metrics_card(habit, title_color)
            )
        
        if self.page:
            self.page.update()
    
    def _get_week_completions(self, habits: List, week_start: date) -> int:
        """Obtiene el número de completaciones de esta semana."""
        week_end = week_start + timedelta(days=6)
        total = 0
        
        for habit in habits:
            completions = self.habit_service.get_completions(habit.id)
            for completion_date in completions:
                if week_start <= completion_date <= week_end:
                    total += 1
        
        return total
    
    def _get_month_completions(self, habits: List, month_start: date) -> int:
        """Obtiene el número de completaciones de este mes."""
        if month_start.month == 12:
            month_end = date(month_start.year + 1, 1, 1) - timedelta(days=1)
        else:
            month_end = date(month_start.year, month_start.month + 1, 1) - timedelta(days=1)
        
        total = 0
        
        for habit in habits:
            completions = self.habit_service.get_completions(habit.id)
            for completion_date in completions:
                if month_start <= completion_date <= month_end:
                    total += 1
        
        return total
    
    def _get_max_streak(self, habit_id: int) -> int:
        """Calcula la racha máxima de un hábito."""
        completions = sorted(self.habit_service.get_completions(habit_id))
        
        if not completions:
            return 0
        
        max_streak = 1
        current_streak = 1
        
        for i in range(1, len(completions)):
            if (completions[i] - completions[i-1]).days == 1:
                current_streak += 1
                max_streak = max(max_streak, current_streak)
            else:
                current_streak = 1
        
        return max_streak
    
    def _get_completion_rate(self, habit_id: int, days: int = 30) -> float:
        """Calcula el porcentaje de completación en los últimos N días."""
        end_date = date.today()
        start_date = end_date - timedelta(days=days - 1)
        
        completions = self.habit_service.get_completions(habit_id)
        completion_count = sum(
            1 for d in completions if start_date <= d <= end_date
        )
        
        return (completion_count / days) * 100 if days > 0 else 0
    
    def _build_summary_card(self, title: str, items: List[tuple], title_color) -> ft.Container:
        """Construye una tarjeta de resumen."""
        is_dark = self.page.theme_mode == ft.ThemeMode.DARK
        bg_color = ft.Colors.SURFACE if is_dark else ft.Colors.WHITE
        
        content_items = [
            ft.Text(
                title,
                size=16,
                weight=ft.FontWeight.BOLD,
                color=title_color
            )
        ]
        
        for label, value in items:
            content_items.append(
                ft.Row(
                    [
                        ft.Text(f"{label}:", size=14, expand=True),
                        ft.Text(
                            value,
                            size=14,
                            weight=ft.FontWeight.BOLD,
                            color=title_color
                        )
                    ],
                    spacing=8
                )
            )
        
        return ft.Container(
            content=ft.Column(content_items, spacing=8),
            padding=16,
            bgcolor=bg_color,
            border_radius=8,
            border=ft.border.all(1, ft.Colors.OUTLINE)
        )
    
    def _build_habit_metrics_card(self, habit, title_color) -> ft.Container:
        """Construye una tarjeta de métricas para un hábito."""
        is_dark = self.page.theme_mode == ft.ThemeMode.DARK
        bg_color = ft.Colors.SURFACE if is_dark else ft.Colors.WHITE
        
        completion_count = self.habit_service.get_completion_count(habit.id)
        current_streak = self.habit_service.get_streak(habit.id)
        max_streak = self._get_max_streak(habit.id)
        completion_rate_30 = self._get_completion_rate(habit.id, 30)
        completion_rate_7 = self._get_completion_rate(habit.id, 7)
        
        # Calcular días desde creación
        days_active = 0
        if habit.created_at:
            created_date = habit.created_at.date() if hasattr(habit.created_at, 'date') else habit.created_at
            days_active = (date.today() - created_date).days + 1
        
        return ft.Container(
            content=ft.Column(
                [
                    ft.Text(
                        habit.title,
                        size=16,
                        weight=ft.FontWeight.BOLD,
                        color=title_color
                    ),
                    ft.Divider(height=1),
                    ft.Row(
                        [
                            ft.Column(
                                [
                                    ft.Text("Completaciones", size=12, color=ft.Colors.GREY_700),
                                    ft.Text(
                                        str(completion_count),
                                        size=18,
                                        weight=ft.FontWeight.BOLD,
                                        color=title_color
                                    )
                                ],
                                spacing=4
                            ),
                            ft.Column(
                                [
                                    ft.Text("Racha actual", size=12, color=ft.Colors.GREY_700),
                                    ft.Text(
                                        f"{current_streak} días",
                                        size=18,
                                        weight=ft.FontWeight.BOLD,
                                        color=title_color
                                    )
                                ],
                                spacing=4
                            ),
                            ft.Column(
                                [
                                    ft.Text("Racha máxima", size=12, color=ft.Colors.GREY_700),
                                    ft.Text(
                                        f"{max_streak} días",
                                        size=18,
                                        weight=ft.FontWeight.BOLD,
                                        color=title_color
                                    )
                                ],
                                spacing=4
                            )
                        ],
                        spacing=16,
                        expand=True
                    ),
                    ft.Divider(height=1),
                    ft.Row(
                        [
                            ft.Column(
                                [
                                    ft.Text("Últimos 7 días", size=12, color=ft.Colors.GREY_700),
                                    ft.Text(
                                        f"{completion_rate_7:.1f}%",
                                        size=14,
                                        weight=ft.FontWeight.BOLD,
                                        color=ft.Colors.GREEN if completion_rate_7 >= 70 else ft.Colors.ORANGE if completion_rate_7 >= 50 else ft.Colors.RED
                                    )
                                ],
                                spacing=4,
                                expand=True
                            ),
                            ft.Column(
                                [
                                    ft.Text("Últimos 30 días", size=12, color=ft.Colors.GREY_700),
                                    ft.Text(
                                        f"{completion_rate_30:.1f}%",
                                        size=14,
                                        weight=ft.FontWeight.BOLD,
                                        color=ft.Colors.GREEN if completion_rate_30 >= 70 else ft.Colors.ORANGE if completion_rate_30 >= 50 else ft.Colors.RED
                                    )
                                ],
                                spacing=4,
                                expand=True
                            )
                        ],
                        spacing=16
                    )
                ],
                spacing=12
            ),
            padding=16,
            bgcolor=bg_color,
            border_radius=8,
            border=ft.border.all(1, ft.Colors.OUTLINE)
        )
    
    def _go_back(self, e):
        """Regresa a la vista anterior."""
        self.page.go("/")

