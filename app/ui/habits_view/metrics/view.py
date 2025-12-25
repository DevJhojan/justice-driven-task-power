"""
Vista principal de métricas que orquesta calendario, gráficas y progreso.
"""
import flet as ft
from typing import Callable
from datetime import date
from app.data.models import Habit
from ..utils import load_completion_dates
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
    # Esto es crítico en móvil donde los datos pueden no estar sincronizados
    try:
        fresh_completion_dates = load_completion_dates(habit_service, habit.id)
        print(f"DEBUG: Cargados {len(fresh_completion_dates)} fechas de cumplimiento para hábito {habit.id}")
    except Exception as ex:
        print(f"ERROR: Error al cargar completion_dates: {ex}")
        import traceback
        traceback.print_exc()
        # Usar el set vacío como fallback
        fresh_completion_dates = set()
    
    calendar_content = create_calendar_view(
        page, habit, habit_service, fresh_completion_dates, on_completion_toggle, on_refresh
    )
    
    charts_content = create_charts_view(
        page, habit, habit_service, fresh_completion_dates
    )
    
    # Recargar métricas frescas
    try:
        fresh_metrics = habit_service.get_habit_metrics(habit.id)
        print(f"DEBUG: Métricas cargadas para hábito {habit.id}: streak={fresh_metrics.get('streak', 0)}")
    except Exception as ex:
        print(f"ERROR: Error al cargar métricas: {ex}")
        import traceback
        traceback.print_exc()
        # Usar métricas vacías como fallback
        fresh_metrics = {'streak': 0, 'completion_percentage': 0.0, 'total_completions': 0, 'current_streak_start': None, 'last_completion_date': None}
    
    progress_content = create_progress_view(
        page, habit, habit_service, fresh_metrics
    )
    
    # Crear tabs directamente - en móvil Flet debería manejar esto correctamente
    # pero necesitamos asegurar que el contenido de cada tab tenga expand=True
    tabs = ft.Tabs(
        selected_index=selected_tab_index[0],
        tabs=[
            ft.Tab(
                text="Calendario", 
                icon=ft.Icons.CALENDAR_MONTH, 
                content=ft.Container(content=calendar_content, expand=True)
            ),
            ft.Tab(
                text="Gráficas", 
                icon=ft.Icons.BAR_CHART, 
                content=ft.Container(content=charts_content, expand=True)
            ),
            ft.Tab(
                text="Progreso", 
                icon=ft.Icons.TRENDING_UP, 
                content=ft.Container(content=progress_content, expand=True)
            ),
        ],
        expand=True,
        on_change=on_tab_change,
        # Asegurar que los tabs sean scrollables en móvil si es necesario
        scrollable=True
    )
    
    # Contenedor principal - CRÍTICO: debe tener expand=True y no estar dentro de un Column con scroll
    # que limite su altura
    metrics_container = ft.Container(
        content=tabs,
        padding=ft.padding.only(left=10, right=10, top=10, bottom=10),
        expand=True
    )
    
    # Forzar actualización de la página para asegurar que las vistas se rendericen
    # Esto es especialmente importante en móvil donde puede haber problemas de renderizado inicial
    try:
        metrics_container.update()
        page.update()
    except Exception as ex:
        print(f"Advertencia al actualizar contenedor de métricas: {ex}")
    
    return metrics_container

