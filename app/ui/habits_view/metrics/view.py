"""
Vista principal de métricas que orquesta calendario, gráficas y progreso.
"""
import flet as ft
from typing import Callable
from datetime import date
from app.data.models import Habit
from ...utils import load_completion_dates
from .calendar import create_calendar_view
from .charts import create_charts_view
from .progress import create_progress_view


def create_habit_metrics_view(
    page: ft.Page,
    habit: Habit,
    habit_service,
    completion_dates: set,
    on_completion_toggle: Callable[[int, date], None],
    on_refresh: Callable[[], None]
) -> ft.Container:
    """
    Crea una vista completa de métricas con calendario y gráficas.
    
    Args:
        page: Página de Flet
        habit: Hábito a mostrar
        habit_service: Servicio de hábitos
        completion_dates: Conjunto de fechas completadas
        on_completion_toggle: Callback para alternar cumplimiento
        on_refresh: Callback para refrescar datos
        
    Returns:
        Container con la vista de métricas
    """
    is_dark = page.theme_mode == ft.ThemeMode.DARK
    scheme = page.theme.color_scheme if page.theme else None
    primary = scheme.primary if scheme and scheme.primary else ft.Colors.RED_400
    
    # Obtener métricas
    metrics = habit_service.get_habit_metrics(habit.id)
    
    # Crear tabs para diferentes vistas
    # Usar una lista mutable para preservar el índice de la pestaña seleccionada
    selected_tab_index = [0]
    
    def on_tab_change(e):
        """Preserva el índice de la pestaña seleccionada."""
        selected_tab_index[0] = e.control.selected_index
    
    # Contenido de las tabs - crear con datos frescos
    # IMPORTANTE: Recargar completion_dates desde la BD para asegurar datos actualizados
    fresh_completion_dates = load_completion_dates(habit_service, habit.id)
    
    calendar_content = create_calendar_view(
        page, habit, habit_service, fresh_completion_dates, on_completion_toggle, on_refresh
    )
    
    charts_content = create_charts_view(
        page, habit, habit_service, fresh_completion_dates
    )
    
    # Recargar métricas frescas
    fresh_metrics = habit_service.get_habit_metrics(habit.id)
    progress_content = create_progress_view(
        page, habit, habit_service, fresh_metrics
    )
    
    tabs = ft.Tabs(
        selected_index=selected_tab_index[0],
        tabs=[
            ft.Tab(text="Calendario", icon=ft.Icons.CALENDAR_MONTH, content=calendar_content),
            ft.Tab(text="Gráficas", icon=ft.Icons.BAR_CHART, content=charts_content),
            ft.Tab(text="Progreso", icon=ft.Icons.TRENDING_UP, content=progress_content),
        ],
        expand=True,
        on_change=on_tab_change
    )
    
    return ft.Container(
        content=tabs,
        padding=20,
        expand=True
    )

