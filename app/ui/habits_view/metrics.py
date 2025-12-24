"""
Módulo para mostrar métricas avanzadas de hábitos con calendario y gráficas.
"""
import flet as ft
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional, Callable
from calendar import monthrange
from app.data.models import Habit


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
    tabs = ft.Tabs(
        selected_index=0,
        tabs=[
            ft.Tab(text="Calendario", icon=ft.Icons.CALENDAR_MONTH),
            ft.Tab(text="Gráficas", icon=ft.Icons.BAR_CHART),
            ft.Tab(text="Progreso", icon=ft.Icons.TRENDING_UP),
        ],
        expand=True
    )
    
    # Contenido de las tabs
    calendar_content = create_calendar_view(
        page, habit, completion_dates, on_completion_toggle, on_refresh
    )
    
    charts_content = create_charts_view(
        page, habit, habit_service, completion_dates
    )
    
    progress_content = create_progress_view(
        page, habit, habit_service, metrics
    )
    
    # Asignar contenido a las tabs
    tabs.tabs[0].content = calendar_content
    tabs.tabs[1].content = charts_content
    tabs.tabs[2].content = progress_content
    
    return ft.Container(
        content=tabs,
        padding=20,
        expand=True
    )


def create_calendar_view(
    page: ft.Page,
    habit: Habit,
    completion_dates: set,
    on_completion_toggle: Callable[[int, date], None],
    on_refresh: Callable[[], None]
) -> ft.Container:
    """
    Crea una vista de calendario interactivo para mostrar y editar cumplimientos.
    
    Args:
        page: Página de Flet
        habit: Hábito
        completion_dates: Conjunto de fechas completadas
        on_completion_toggle: Callback para alternar cumplimiento
        on_refresh: Callback para refrescar
        
    Returns:
        Container con el calendario
    """
    is_dark = page.theme_mode == ft.ThemeMode.DARK
    scheme = page.theme.color_scheme if page.theme else None
    primary = scheme.primary if scheme and scheme.primary else ft.Colors.RED_400
    
    # Estado del calendario (mes y año actual)
    current_date = date.today()
    current_month = [current_date.month]
    current_year = [current_date.year]
    
    # Contenedor del calendario
    calendar_container = ft.Container()
    
    def build_calendar(month: int, year: int):
        """Construye el calendario para un mes específico."""
        # Obtener primer día del mes y número de días
        first_day = date(year, month, 1)
        days_in_month = monthrange(year, month)[1]
        first_weekday = first_day.weekday()  # 0 = Lunes, 6 = Domingo
        
        # Crear grid del calendario
        calendar_grid = ft.Column(spacing=4)
        
        # Encabezado con mes/año y controles de navegación
        month_names = [
            "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
            "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
        ]
        
        def prev_month(e):
            if current_month[0] == 1:
                current_month[0] = 12
                current_year[0] -= 1
            else:
                current_month[0] -= 1
            build_calendar(current_month[0], current_year[0])
            page.update()
        
        def next_month(e):
            if current_month[0] == 12:
                current_month[0] = 1
                current_year[0] += 1
            else:
                current_month[0] += 1
            build_calendar(current_month[0], current_year[0])
            page.update()
        
        header = ft.Row(
            [
                ft.IconButton(
                    icon=ft.Icons.CHEVRON_LEFT,
                    on_click=prev_month,
                    icon_color=primary
                ),
                ft.Text(
                    f"{month_names[month - 1]} {year}",
                    size=20,
                    weight=ft.FontWeight.BOLD,
                    expand=True,
                    text_align=ft.TextAlign.CENTER
                ),
                ft.IconButton(
                    icon=ft.Icons.CHEVRON_RIGHT,
                    on_click=next_month,
                    icon_color=primary
                )
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
        )
        
        # Días de la semana
        weekdays = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
        weekday_row = ft.Row(
            [ft.Container(
                content=ft.Text(day, size=12, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
                expand=True,
                padding=8
            ) for day in weekdays],
            spacing=4
        )
        
        # Grid de días
        days_grid = ft.Column(spacing=4)
        current_row = ft.Row(spacing=4)
        
        # Agregar espacios vacíos para el primer día
        for _ in range(first_weekday):
            current_row.controls.append(
                ft.Container(width=40, height=40)
            )
        
        # Agregar días del mes
        today = date.today()
        for day in range(1, days_in_month + 1):
            day_date = date(year, month, day)
            is_completed = day_date in completion_dates
            is_today = day_date == today
            is_future = day_date > today
            
            # Color según el estado
            if is_completed:
                bg_color = primary
                text_color = ft.Colors.WHITE
            elif is_today:
                bg_color = ft.Colors.GREY_300 if not is_dark else ft.Colors.GREY_700
                text_color = primary
            elif is_future:
                bg_color = ft.Colors.TRANSPARENT
                text_color = ft.Colors.GREY_400 if is_dark else ft.Colors.GREY_500
            else:
                bg_color = ft.Colors.TRANSPARENT
                text_color = ft.Colors.WHITE if is_dark else ft.Colors.BLACK87
            
            def make_toggle_handler(d):
                def handler(e):
                    on_completion_toggle(habit.id, d)
                    # Actualizar el estado local
                    if d in completion_dates:
                        completion_dates.remove(d)
                    else:
                        completion_dates.add(d)
                    build_calendar(current_month[0], current_year[0])
                    on_refresh()
                    page.update()
                return handler
            
            day_button = ft.Container(
                content=ft.Text(
                    str(day),
                    size=14,
                    weight=ft.FontWeight.BOLD if is_today else None,
                    color=text_color,
                    text_align=ft.TextAlign.CENTER
                ),
                width=40,
                height=40,
                bgcolor=bg_color,
                border_radius=20,
                alignment=ft.alignment.center,
                on_click=make_toggle_handler(day_date),
                tooltip=f"{day_date.strftime('%d/%m/%Y')} - {'Completado' if is_completed else 'No completado'}"
            )
            
            current_row.controls.append(day_button)
            
            # Nueva fila cada 7 días
            if len(current_row.controls) == 7:
                days_grid.controls.append(current_row)
                current_row = ft.Row(spacing=4)
        
        # Agregar última fila si tiene elementos
        if current_row.controls:
            # Completar con espacios vacíos
            while len(current_row.controls) < 7:
                current_row.controls.append(ft.Container(width=40, height=40))
            days_grid.controls.append(current_row)
        
        # Construir el calendario completo
        calendar_container.content = ft.Column(
            [
                header,
                weekday_row,
                days_grid
            ],
            spacing=8,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER
        )
    
    # Construir calendario inicial
    build_calendar(current_month[0], current_year[0])
    
    return ft.Container(
        content=ft.Column(
            [
                ft.Text(
                    "Calendario de Cumplimientos",
                    size=18,
                    weight=ft.FontWeight.BOLD,
                    text_align=ft.TextAlign.CENTER
                ),
                ft.Text(
                    "Toca un día para marcar/desmarcar como completado",
                    size=12,
                    color=ft.Colors.GREY_600 if not is_dark else ft.Colors.GREY_400,
                    text_align=ft.TextAlign.CENTER
                ),
                ft.Divider(),
                calendar_container
            ],
            spacing=16,
            scroll=ft.ScrollMode.AUTO
        ),
        padding=20,
        expand=True
    )


def create_charts_view(
    page: ft.Page,
    habit: Habit,
    habit_service,
    completion_dates: set
) -> ft.Container:
    """
    Crea gráficas de progreso del hábito.
    
    Args:
        page: Página de Flet
        habit: Hábito
        habit_service: Servicio de hábitos
        completion_dates: Conjunto de fechas completadas
        
    Returns:
        Container con las gráficas
    """
    is_dark = page.theme_mode == ft.ThemeMode.DARK
    scheme = page.theme.color_scheme if page.theme else None
    primary = scheme.primary if scheme and scheme.primary else ft.Colors.RED_400
    
    # Gráfica de barras - Últimos 30 días
    today = date.today()
    last_30_days = []
    for i in range(29, -1, -1):
        day = today - timedelta(days=i)
        last_30_days.append({
            'date': day,
            'completed': day in completion_dates
        })
    
    # Crear barras
    max_height = 100
    bars = []
    for day_data in last_30_days:
        height = max_height if day_data['completed'] else 5
        color = primary if day_data['completed'] else (ft.Colors.GREY_300 if not is_dark else ft.Colors.GREY_700)
        
        bars.append(
            ft.Container(
                content=ft.Column(
                    [
                        ft.Container(
                            width=8,
                            height=height,
                            bgcolor=color,
                            border_radius=4
                        ),
                        ft.Text(
                            day_data['date'].day,
                            size=8,
                            text_align=ft.TextAlign.CENTER
                        )
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=4,
                    tight=True
                ),
                width=12,
                tooltip=f"{day_data['date'].strftime('%d/%m/%Y')} - {'Completado' if day_data['completed'] else 'No completado'}"
            )
        )
    
    bar_chart = ft.Row(
        bars,
        spacing=2,
        alignment=ft.MainAxisAlignment.CENTER,
        wrap=False
    )
    
    # Gráfica de progreso semanal - Últimas 8 semanas
    weekly_data = []
    for week_offset in range(7, -1, -1):
        week_start = today - timedelta(weeks=week_offset, days=today.weekday())
        week_end = week_start + timedelta(days=6)
        
        week_completions = sum(1 for i in range(7) if (week_start + timedelta(days=i)) in completion_dates)
        weekly_data.append({
            'week': f"Sem {week_offset + 1}",
            'completions': week_completions,
            'target': habit.target_days
        })
    
    # Crear gráfica de líneas para semanas
    max_completions = max([d['completions'] for d in weekly_data] + [habit.target_days] + [1])
    week_bars = []
    for week_data in weekly_data:
        height = int((week_data['completions'] / max_completions) * 80) if max_completions > 0 else 0
        target_height = int((week_data['target'] / max_completions) * 80) if max_completions > 0 else 0
        
        week_bars.append(
            ft.Container(
                content=ft.Column(
                    [
                        ft.Stack(
                            [
                                # Barra de objetivo
                                ft.Container(
                                    width=30,
                                    height=target_height,
                                    bgcolor=ft.Colors.ORANGE_300 if not is_dark else ft.Colors.ORANGE_700,
                                    border_radius=4,
                                    bottom=0
                                ),
                                # Barra de completados
                                ft.Container(
                                    width=30,
                                    height=height,
                                    bgcolor=primary,
                                    border_radius=4,
                                    bottom=0
                                )
                            ],
                            width=30,
                            height=80
                        ),
                        ft.Text(
                            week_data['week'],
                            size=10,
                            text_align=ft.TextAlign.CENTER
                        ),
                        ft.Text(
                            f"{week_data['completions']}/{week_data['target']}",
                            size=9,
                            text_align=ft.TextAlign.CENTER,
                            color=ft.Colors.GREY_600 if not is_dark else ft.Colors.GREY_400
                        )
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=4,
                    tight=True
                ),
                width=40,
                tooltip=f"{week_data['week']}: {week_data['completions']}/{week_data['target']} completados"
            )
        )
    
    weekly_chart = ft.Row(
        week_bars,
        spacing=4,
        alignment=ft.MainAxisAlignment.CENTER,
        wrap=False
    )
    
    return ft.Container(
        content=ft.Column(
            [
                ft.Text(
                    "Gráficas de Progreso",
                    size=18,
                    weight=ft.FontWeight.BOLD,
                    text_align=ft.TextAlign.CENTER
                ),
                ft.Divider(),
                ft.Text(
                    "Últimos 30 días",
                    size=14,
                    weight=ft.FontWeight.BOLD
                ),
                ft.Container(
                    content=bar_chart,
                    padding=20,
                    border=ft.border.all(1, ft.Colors.GREY_300 if not is_dark else ft.Colors.GREY_700),
                    border_radius=8
                ),
                ft.Divider(height=20),
                ft.Text(
                    "Últimas 8 semanas",
                    size=14,
                    weight=ft.FontWeight.BOLD
                ),
                ft.Row(
                    [
                        ft.Container(
                            width=12,
                            height=12,
                            bgcolor=primary,
                            border_radius=2
                        ),
                        ft.Text("Completados", size=12),
                        ft.Container(width=20),
                        ft.Container(
                            width=12,
                            height=12,
                            bgcolor=ft.Colors.ORANGE_300 if not is_dark else ft.Colors.ORANGE_700,
                            border_radius=2
                        ),
                        ft.Text("Objetivo", size=12)
                    ],
                    alignment=ft.MainAxisAlignment.CENTER
                ),
                ft.Container(
                    content=weekly_chart,
                    padding=20,
                    border=ft.border.all(1, ft.Colors.GREY_300 if not is_dark else ft.Colors.GREY_700),
                    border_radius=8
                )
            ],
            spacing=16,
            scroll=ft.ScrollMode.AUTO
        ),
        padding=20,
        expand=True
    )


def create_progress_view(
    page: ft.Page,
    habit: Habit,
    habit_service,
    metrics: Dict
) -> ft.Container:
    """
    Crea una vista de progreso detallado.
    
    Args:
        page: Página de Flet
        habit: Hábito
        habit_service: Servicio de hábitos
        metrics: Diccionario con métricas
        
    Returns:
        Container con la vista de progreso
    """
    is_dark = page.theme_mode == ft.ThemeMode.DARK
    scheme = page.theme.color_scheme if page.theme else None
    primary = scheme.primary if scheme and scheme.primary else ft.Colors.RED_400
    
    # Obtener progreso mensual
    monthly = habit_service.get_monthly_progress(habit.id)
    
    # Obtener progreso semanal
    weekly = habit_service.get_weekly_progress(habit.id)
    
    return ft.Container(
        content=ft.Column(
            [
                ft.Text(
                    "Progreso Detallado",
                    size=18,
                    weight=ft.FontWeight.BOLD,
                    text_align=ft.TextAlign.CENTER
                ),
                ft.Divider(),
                # Racha actual
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Text(
                                "Racha Actual",
                                size=16,
                                weight=ft.FontWeight.BOLD
                            ),
                            ft.Text(
                                f"{metrics['streak']} días",
                                size=32,
                                weight=ft.FontWeight.BOLD,
                                color=primary
                            ),
                            ft.Text(
                                f"Iniciada: {metrics['current_streak_start'].strftime('%d/%m/%Y') if metrics['current_streak_start'] else 'N/A'}",
                                size=12,
                                color=ft.Colors.GREY_600 if not is_dark else ft.Colors.GREY_400
                            )
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=8
                    ),
                    padding=20,
                    border=ft.border.all(1, primary),
                    border_radius=8
                ),
                # Progreso semanal
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Text(
                                "Esta Semana",
                                size=16,
                                weight=ft.FontWeight.BOLD
                            ),
                            ft.Text(
                                f"{weekly['completions_count']}/{weekly['target_days']} días",
                                size=24,
                                weight=ft.FontWeight.BOLD,
                                color=primary
                            ),
                            ft.ProgressBar(
                                value=weekly['completions_count'] / weekly['target_days'] if weekly['target_days'] > 0 else 0,
                                color=primary,
                                bgcolor=ft.Colors.GREY_300 if not is_dark else ft.Colors.GREY_700
                            )
                        ],
                        spacing=8
                    ),
                    padding=20,
                    border=ft.border.all(1, ft.Colors.GREY_300 if not is_dark else ft.Colors.GREY_700),
                    border_radius=8
                ),
                # Progreso mensual
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Text(
                                "Este Mes",
                                size=16,
                                weight=ft.FontWeight.BOLD
                            ),
                            ft.Text(
                                f"{monthly['completed_days']}/{monthly['total_days']} días",
                                size=24,
                                weight=ft.FontWeight.BOLD,
                                color=primary
                            ),
                            ft.ProgressBar(
                                value=monthly['completed_days'] / monthly['total_days'] if monthly['total_days'] > 0 else 0,
                                color=primary,
                                bgcolor=ft.Colors.GREY_300 if not is_dark else ft.Colors.GREY_700
                            ),
                            ft.Text(
                                f"{monthly['completion_percentage']:.1f}% de cumplimiento",
                                size=12,
                                color=ft.Colors.GREY_600 if not is_dark else ft.Colors.GREY_400
                            )
                        ],
                        spacing=8
                    ),
                    padding=20,
                    border=ft.border.all(1, ft.Colors.GREY_300 if not is_dark else ft.Colors.GREY_700),
                    border_radius=8
                )
            ],
            spacing=16,
            scroll=ft.ScrollMode.AUTO
        ),
        padding=20,
        expand=True
    )

