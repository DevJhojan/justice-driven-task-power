"""
Vista de métricas de hábitos.
Muestra estadísticas detalladas de todos los hábitos con calendario editable y gráficos.
"""
import flet as ft
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional
from collections import defaultdict
import calendar

from app.services.habit_service import HabitService
from app.services.points_service import PointsService


class HabitsMetricsView:
    """Vista para mostrar métricas de hábitos."""
    
    def __init__(self, page: ft.Page, habit_service: HabitService, points_service: Optional[PointsService] = None):
        """
        Inicializa la vista de métricas.
        
        Args:
            page: Página de Flet.
            habit_service: Servicio de hábitos.
            points_service: Servicio de puntos (opcional).
        """
        self.page = page
        self.habit_service = habit_service
        self.points_service = points_service
        self.metrics_container = None
        self.selected_habit = None  # Hábito seleccionado para el calendario
        self.current_month = date.today().replace(day=1)  # Mes actual para el calendario
    
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
            # Agregar calendario y gráficos para cada hábito
            self.metrics_container.controls.append(
                self._build_habit_calendar_and_charts(habit, title_color)
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
    
    def _build_habit_calendar_and_charts(self, habit, title_color) -> ft.Container:
        """Construye el calendario editable y gráficos para un hábito."""
        is_dark = self.page.theme_mode == ft.ThemeMode.DARK
        bg_color = ft.Colors.SURFACE if is_dark else ft.Colors.WHITE
        
        # Calendario del mes actual
        calendar_widget = self._build_calendar(habit, title_color)
        
        # Gráficos
        charts = self._build_charts(habit, title_color)
        
        return ft.Container(
            content=ft.Column(
                [
                    ft.Text(
                        f"📅 Calendario y Gráficos - {habit.title}",
                        size=16,
                        weight=ft.FontWeight.BOLD,
                        color=title_color
                    ),
                    ft.Divider(height=1),
                    calendar_widget,
                    ft.Divider(height=20),
                    charts
                ],
                spacing=12
            ),
            padding=16,
            bgcolor=bg_color,
            border_radius=8,
            border=ft.border.all(1, ft.Colors.OUTLINE),
            margin=ft.margin.only(top=8)
        )
    
    def _build_calendar(self, habit, title_color) -> ft.Container:
        """Construye un calendario editable para el hábito."""
        is_dark = self.page.theme_mode == ft.ThemeMode.DARK
        completions = self.habit_service.get_completions(habit.id)
        
        # Obtener el primer día del mes y el número de días
        first_day = self.current_month
        days_in_month = calendar.monthrange(first_day.year, first_day.month)[1]
        first_weekday = first_day.weekday()  # 0 = Lunes, 6 = Domingo
        
        # Encabezados de los días de la semana
        weekdays = ["L", "M", "X", "J", "V", "S", "D"]
        weekday_headers = [
            ft.Container(
                content=ft.Text(
                    day,
                    size=12,
                    weight=ft.FontWeight.BOLD,
                    text_align=ft.TextAlign.CENTER,
                    color=title_color
                ),
                alignment=ft.alignment.center,
                width=40,
                height=30
            )
            for day in weekdays
        ]
        
        # Navegación del calendario
        prev_month_btn = ft.IconButton(
            icon=ft.Icons.CHEVRON_LEFT,
            icon_color=title_color,
            on_click=lambda e, h=habit: self._change_month(h, -1)
        )
        next_month_btn = ft.IconButton(
            icon=ft.Icons.CHEVRON_RIGHT,
            icon_color=title_color,
            on_click=lambda e, h=habit: self._change_month(h, 1)
        )
        
        month_year_text = ft.Text(
            f"{calendar.month_name[first_day.month]} {first_day.year}",
            size=14,
            weight=ft.FontWeight.BOLD,
            color=title_color
        )
        
        # Días del calendario
        calendar_days = []
        
        # Espacios vacíos antes del primer día
        for _ in range(first_weekday):
            calendar_days.append(ft.Container(width=40, height=40))
        
        # Días del mes
        for day in range(1, days_in_month + 1):
            current_date = date(first_day.year, first_day.month, day)
            is_completed = current_date in completions
            is_today = current_date == date.today()
            is_future = current_date > date.today()
            
            # Color del día
            if is_completed:
                day_color = ft.Colors.GREEN_400 if not is_dark else ft.Colors.GREEN_700
                border_color = ft.Colors.GREEN_600 if not is_dark else ft.Colors.GREEN_500
            elif is_today:
                day_color = ft.Colors.RED_100 if not is_dark else ft.Colors.RED_900
                border_color = ft.Colors.RED_700 if not is_dark else ft.Colors.RED_600
            elif is_future:
                day_color = ft.Colors.GREY_200 if not is_dark else ft.Colors.GREY_800
                border_color = ft.Colors.GREY_400 if not is_dark else ft.Colors.GREY_600
            else:
                day_color = ft.Colors.WHITE if not is_dark else ft.Colors.BLACK
                border_color = ft.Colors.OUTLINE
            
            day_btn = ft.Container(
                content=ft.Text(
                    str(day),
                    size=12,
                    weight=ft.FontWeight.BOLD if is_today else ft.FontWeight.NORMAL,
                    text_align=ft.TextAlign.CENTER,
                    color=ft.Colors.BLACK if is_completed or (not is_dark and not is_future) else ft.Colors.WHITE if is_future else ft.Colors.GREY
                ),
                width=40,
                height=40,
                alignment=ft.alignment.center,
                bgcolor=day_color,
                border_radius=8,
                border=ft.border.all(2 if is_today else 1, border_color),
                on_click=lambda e, d=current_date, h=habit: self._toggle_date(h, d) if not is_future else None,
                data=current_date
            )
            calendar_days.append(day_btn)
        
        # Agrupar días en semanas (filas de 7)
        week_rows = []
        for i in range(0, len(calendar_days), 7):
            week_rows.append(
                ft.Row(
                    calendar_days[i:i+7],
                    spacing=4,
                    alignment=ft.MainAxisAlignment.CENTER
                )
            )
        
        return ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [prev_month_btn, month_year_text, next_month_btn],
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=8
                    ),
                    ft.Row(weekday_headers, spacing=4, alignment=ft.MainAxisAlignment.CENTER),
                    *week_rows
                ],
                spacing=8,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER
            ),
            padding=8
        )
    
    def _build_charts(self, habit, title_color) -> ft.Column:
        """Construye gráficos para mostrar el progreso del hábito."""
        is_dark = self.page.theme_mode == ft.ThemeMode.DARK
        
        # Datos para los últimos 30 días
        today = date.today()
        last_30_days = []
        completions = self.habit_service.get_completions(habit.id)
        
        for i in range(29, -1, -1):
            check_date = today - timedelta(days=i)
            last_30_days.append({
                'date': check_date,
                'completed': check_date in completions
            })
        
        # Gráfico de barras para los últimos 30 días
        bars = []
        for day_data in last_30_days:
            height = 30 if day_data['completed'] else 5
            bar_color = ft.Colors.GREEN_400 if day_data['completed'] else ft.Colors.GREY_300
            if is_dark:
                bar_color = ft.Colors.GREEN_700 if day_data['completed'] else ft.Colors.GREY_700
            
            bars.append(
                ft.Container(
                    width=8,
                    height=height,
                    bgcolor=bar_color,
                    border_radius=4,
                    tooltip=day_data['date'].strftime("%d/%m") if day_data['completed'] else None
                )
            )
        
        # Gráfico de línea para completaciones semanales (últimas 12 semanas)
        weekly_data = []
        for i in range(11, -1, -1):
            week_end = today - timedelta(weeks=i, days=today.weekday())
            week_start = week_end - timedelta(days=6)
            week_completions = sum(1 for d in completions if week_start <= d <= week_end)
            weekly_data.append(week_completions)
        
        max_weekly = max(weekly_data) if weekly_data else 1
        weekly_chart_height = 100
        
        weekly_bars = []
        for count in weekly_data:
            height = int((count / max_weekly) * weekly_chart_height) if max_weekly > 0 else 0
            weekly_bars.append(
                ft.Container(
                    width=20,
                    height=max(height, 5) if height > 0 else 5,
                    bgcolor=title_color,
                    border_radius=4,
                    alignment=ft.alignment.bottom_center,
                    tooltip=f"{count} completaciones"
                )
            )
        
        # Estadísticas para los gráficos
        completed_count_30 = sum(1 for d in last_30_days if d['completed'])
        completion_rate_30 = (completed_count_30 / 30) * 100
        
        return ft.Column(
            [
                ft.Text(
                    "📊 Gráficos de Progreso",
                    size=14,
                    weight=ft.FontWeight.BOLD,
                    color=title_color
                ),
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Text(
                                "Últimos 30 días",
                                size=12,
                                weight=ft.FontWeight.BOLD,
                                color=ft.Colors.GREY_700 if not is_dark else ft.Colors.GREY_400
                            ),
                            ft.Row(
                                bars,
                                spacing=2,
                                alignment=ft.MainAxisAlignment.CENTER,
                                wrap=False
                            ),
                            ft.Text(
                                f"Completado: {completed_count_30}/30 días ({completion_rate_30:.1f}%)",
                                size=10,
                                color=ft.Colors.GREY_600 if not is_dark else ft.Colors.GREY_500,
                                text_align=ft.TextAlign.CENTER
                            )
                        ],
                        spacing=8,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER
                    ),
                    padding=8
                ),
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Text(
                                "Últimas 12 semanas",
                                size=12,
                                weight=ft.FontWeight.BOLD,
                                color=ft.Colors.GREY_700 if not is_dark else ft.Colors.GREY_400
                            ),
                            ft.Container(
                                content=ft.Row(
                                    weekly_bars,
                                    spacing=4,
                                    alignment=ft.MainAxisAlignment.CENTER,
                                    vertical_alignment=ft.CrossAxisAlignment.END
                                ),
                                height=weekly_chart_height,
                                alignment=ft.alignment.bottom_center
                            ),
                            ft.Text(
                                f"Promedio: {sum(weekly_data) / len(weekly_data):.1f} completaciones/semana",
                                size=10,
                                color=ft.Colors.GREY_600 if not is_dark else ft.Colors.GREY_500,
                                text_align=ft.TextAlign.CENTER
                            )
                        ],
                        spacing=8,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER
                    ),
                    padding=8
                )
            ],
            spacing=12
        )
    
    def _toggle_date(self, habit, date_to_toggle: date):
        """Alterna el estado de completación de un hábito para una fecha específica."""
        if date_to_toggle > date.today():
            return  # No permitir marcar fechas futuras
        
        self.habit_service.toggle_completion(habit.id, date_to_toggle, self.points_service)
        
        # Recargar las métricas para actualizar el calendario
        self._load_metrics()
    
    def _change_month(self, habit, direction: int):
        """Cambia el mes mostrado en el calendario."""
        if direction > 0:
            # Siguiente mes
            if self.current_month.month == 12:
                self.current_month = self.current_month.replace(year=self.current_month.year + 1, month=1)
            else:
                self.current_month = self.current_month.replace(month=self.current_month.month + 1)
        else:
            # Mes anterior
            if self.current_month.month == 1:
                self.current_month = self.current_month.replace(year=self.current_month.year - 1, month=12)
            else:
                self.current_month = self.current_month.replace(month=self.current_month.month - 1)
        
        # Recargar las métricas para actualizar el calendario
        self._load_metrics()
    
    def _go_back(self, e):
        """Regresa a la vista anterior."""
        self.page.go("/")

