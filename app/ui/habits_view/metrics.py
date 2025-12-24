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
    # Usar una lista mutable para preservar el índice de la pestaña seleccionada
    selected_tab_index = [0]
    
    def on_tab_change(e):
        """Preserva el índice de la pestaña seleccionada."""
        selected_tab_index[0] = e.control.selected_index
    
    # Contenido de las tabs - crear con datos frescos
    # IMPORTANTE: Recargar completion_dates desde la BD para asegurar datos actualizados
    fresh_completions = habit_service.repository.get_completions(habit.id)
    fresh_completion_dates = {c.completion_date.date() for c in fresh_completions}
    
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


def create_calendar_view(
    page: ft.Page,
    habit: Habit,
    habit_service,
    completion_dates: set,
    on_completion_toggle: Callable[[int, date], None],
    on_refresh: Callable[[], None]
) -> ft.Container:
    """
    Crea una vista de calendario interactivo para mostrar y editar cumplimientos.
    
    Args:
        page: Página de Flet
        habit: Hábito
        habit_service: Servicio de hábitos para recargar datos
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
        # OFFLINE-FIRST: Recargar siempre desde SQLite local para tener datos frescos
        completions = habit_service.repository.get_completions(habit.id)
        current_completion_dates = {c.completion_date.date() for c in completions}
        
        today = date.today()
        for day in range(1, days_in_month + 1):
            day_date = date(year, month, day)
            is_completed = day_date in current_completion_dates
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
            
            # Solo permitir toggle en días pasados o el día actual (no futuros)
            if is_future:
                # Día futuro: no se puede marcar
                day_button = ft.Container(
                    content=ft.Text(
                        str(day),
                        size=14,
                        color=text_color,
                        text_align=ft.TextAlign.CENTER
                    ),
                    width=40,
                    height=40,
                    bgcolor=bg_color,
                    border_radius=20,
                    alignment=ft.alignment.center,
                    tooltip=f"{day_date.strftime('%d/%m/%Y')} - No se pueden marcar días futuros",
                    opacity=0.4  # Hacer más visible que está deshabilitado
                )
            else:
                # Día pasado o actual: se puede marcar
                def make_toggle_handler(d):
                    def handler(e):
                        # OFFLINE-FIRST: Todo se maneja localmente en SQLite
                        # No hay llamadas a Firebase aquí, solo operaciones locales
                        try:
                            # Alternar el cumplimiento en la base de datos local
                            on_completion_toggle(habit.id, d)
                            
                            # Recargar datos frescos desde SQLite local
                            completions = habit_service.repository.get_completions(habit.id)
                            fresh_completion_dates = {c.completion_date.date() for c in completions}
                            
                            # Actualizar el set de completion_dates
                            completion_dates.clear()
                            completion_dates.update(fresh_completion_dates)
                            
                            # Reconstruir el calendario con datos frescos
                            build_calendar(current_month[0], current_year[0])
                            
                            # Refrescar otras vistas (gráficas, etc.)
                            on_refresh()
                            
                            # Actualizar la página
                            page.update()
                        except Exception as ex:
                            # Si hay error, intentar actualizar el calendario de todas formas
                            print(f"Error al alternar cumplimiento (offline): {ex}")
                            try:
                                # Recargar datos y reconstruir
                                completions = habit_service.repository.get_completions(habit.id)
                                completion_dates.clear()
                                completion_dates.update({c.completion_date.date() for c in completions})
                                build_calendar(current_month[0], current_year[0])
                                page.update()
                            except Exception as ex2:
                                print(f"Error al reconstruir calendario: {ex2}")
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
    
    # Función para actualizar datos del calendario
    def refresh_calendar_data(e):
        """Recarga los datos del calendario desde la base de datos."""
        print("DEBUG: Botón de actualizar presionado")
        try:
            print(f"DEBUG: Recargando datos para hábito {habit.id}")
            # Recargar datos frescos desde SQLite
            completions = habit_service.repository.get_completions(habit.id)
            fresh_completion_dates = {c.completion_date.date() for c in completions}
            print(f"DEBUG: Fechas encontradas: {len(fresh_completion_dates)} - {sorted(fresh_completion_dates)}")
            
            # Actualizar el set de completion_dates (esto es importante para las otras vistas)
            completion_dates.clear()
            completion_dates.update(fresh_completion_dates)
            print(f"DEBUG: completion_dates actualizado: {len(completion_dates)} fechas")
            
            # Reconstruir el calendario con datos frescos
            print("DEBUG: Reconstruyendo calendario...")
            build_calendar(current_month[0], current_year[0])
            
            # Actualizar el contenedor del calendario explícitamente
            calendar_container.update()
            print("DEBUG: Contenedor del calendario actualizado")
            
            # Refrescar otras vistas (gráficas, progreso, etc.)
            # Esto reconstruye toda la vista de métricas con los datos actualizados
            print("DEBUG: Refrescando otras vistas...")
            if on_refresh:
                on_refresh()
                print("DEBUG: on_refresh() ejecutado")
            
            # Actualizar la página
            print("DEBUG: Actualizando página...")
            page.update()
            
            # Mostrar mensaje de confirmación
            print("DEBUG: Mostrando mensaje de confirmación...")
            page.snack_bar = ft.SnackBar(
                content=ft.Text("Datos actualizados correctamente"),
                bgcolor=primary,
                duration=2000
            )
            page.snack_bar.open = True
            page.update()
            print("DEBUG: Actualización completada")
        except Exception as ex:
            print(f"ERROR: Error al actualizar datos del calendario: {ex}")
            import traceback
            traceback.print_exc()
            try:
                page.snack_bar = ft.SnackBar(
                    content=ft.Text(f"Error al actualizar: {str(ex)}"),
                    bgcolor=ft.Colors.RED,
                    duration=3000
                )
                page.snack_bar.open = True
                page.update()
            except:
                pass
    
    # Botón de actualizar datos
    refresh_button = ft.ElevatedButton(
        "Actualizar datos",
        icon=ft.Icons.REFRESH,
        on_click=refresh_calendar_data,
        bgcolor=primary,
        color=ft.Colors.WHITE
    )
    
    # Construir calendario inicial
    build_calendar(current_month[0], current_year[0])
    
    return ft.Container(
        content=ft.Column(
            [
                ft.Row(
                    [
                        ft.Text(
                            "Calendario de Cumplimientos",
                            size=18,
                            weight=ft.FontWeight.BOLD,
                            expand=True
                        ),
                        refresh_button
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN
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
        completion_dates: Conjunto de fechas completadas (se ignora, se recarga desde BD)
        
    Returns:
        Container con las gráficas
    """
    is_dark = page.theme_mode == ft.ThemeMode.DARK
    scheme = page.theme.color_scheme if page.theme else None
    primary = scheme.primary if scheme and scheme.primary else ft.Colors.RED_400
    
    # OFFLINE-FIRST: Recargar datos frescos desde SQLite local
    completions = habit_service.repository.get_completions(habit.id)
    fresh_completion_dates = {c.completion_date.date() for c in completions}
    
    # Gráfica de barras - Últimos 30 días
    today = date.today()
    last_30_days = []
    for i in range(29, -1, -1):
        day = today - timedelta(days=i)
        last_30_days.append({
            'date': day,
            'completed': day in fresh_completion_dates
        })
    
    # Crear barras (más grandes y visibles)
    max_height = 120
    bars = []
    for day_data in last_30_days:
        height = max_height if day_data['completed'] else 8
        color = primary if day_data['completed'] else (ft.Colors.GREY_300 if not is_dark else ft.Colors.GREY_700)
        
        bars.append(
            ft.Container(
                content=ft.Column(
                    [
                        ft.Container(
                            width=14,
                            height=height,
                            bgcolor=color,
                            border_radius=7,
                            border=ft.border.all(1, ft.Colors.GREY_400 if not day_data['completed'] and not is_dark else ft.Colors.GREY_600) if not day_data['completed'] else None
                        ),
                        ft.Text(
                            str(day_data['date'].day),
                            size=10,
                            weight=ft.FontWeight.BOLD if day_data['completed'] else None,
                            text_align=ft.TextAlign.CENTER,
                            color=ft.Colors.WHITE if is_dark else ft.Colors.BLACK87
                        )
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=4,
                    tight=True
                ),
                width=18,
                tooltip=f"{day_data['date'].strftime('%d/%m/%Y')} - {'Completado' if day_data['completed'] else 'No completado'}"
            )
        )
    
    bar_chart = ft.Container(
        content=ft.Row(
            bars,
            spacing=3,
            alignment=ft.MainAxisAlignment.CENTER,
            wrap=False,
            scroll=ft.ScrollMode.HIDDEN
        ),
        padding=ft.padding.symmetric(vertical=10, horizontal=5),
        border=ft.border.all(1, ft.Colors.GREY_300 if not is_dark else ft.Colors.GREY_700),
        border_radius=8,
        bgcolor=ft.Colors.GREY_50 if not is_dark else ft.Colors.GREY_900
    )
    
    # Gráfica de progreso semanal - Últimas 8 semanas
    weekly_data = []
    for week_offset in range(7, -1, -1):
        week_start = today - timedelta(weeks=week_offset, days=today.weekday())
        week_end = week_start + timedelta(days=6)
        
        week_completions = sum(1 for i in range(7) if (week_start + timedelta(days=i)) in fresh_completion_dates)
        weekly_data.append({
            'week': f"Sem {week_offset + 1}",
            'completions': week_completions,
            'target': habit.target_days
        })
    
    # Crear gráfica de barras para semanas (más grande y clara)
    max_completions = max([d['completions'] for d in weekly_data] + [habit.target_days] + [1])
    week_bars = []
    for week_data in weekly_data:
        height = int((week_data['completions'] / max_completions) * 120) if max_completions > 0 else 0
        target_height = int((week_data['target'] / max_completions) * 120) if max_completions > 0 else 0
        
        week_bars.append(
            ft.Container(
                content=ft.Column(
                    [
                        ft.Stack(
                            [
                                # Barra de objetivo (fondo)
                                ft.Container(
                                    width=35,
                                    height=target_height,
                                    bgcolor=ft.Colors.ORANGE_200 if not is_dark else ft.Colors.ORANGE_800,
                                    border_radius=6,
                                    bottom=0,
                                    border=ft.border.all(1, ft.Colors.ORANGE_400 if not is_dark else ft.Colors.ORANGE_600)
                                ),
                                # Barra de completados (frente)
                                ft.Container(
                                    width=35,
                                    height=height,
                                    bgcolor=primary,
                                    border_radius=6,
                                    bottom=0,
                                    border=ft.border.all(1, ft.Colors.RED_600 if not is_dark else ft.Colors.RED_800)
                                )
                            ],
                            width=35,
                            height=120
                        ),
                        ft.Container(height=4),  # Espacio
                        ft.Text(
                            week_data['week'],
                            size=11,
                            weight=ft.FontWeight.BOLD,
                            text_align=ft.TextAlign.CENTER,
                            color=ft.Colors.WHITE if is_dark else ft.Colors.BLACK87
                        ),
                        ft.Text(
                            f"{week_data['completions']}/{week_data['target']}",
                            size=10,
                            text_align=ft.TextAlign.CENTER,
                            color=primary,
                            weight=ft.FontWeight.BOLD
                        )
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=2,
                    tight=True
                ),
                width=45,
                tooltip=f"{week_data['week']}: {week_data['completions']}/{week_data['target']} completados"
            )
        )
    
    weekly_chart = ft.Container(
        content=ft.Row(
            week_bars,
            spacing=6,
            alignment=ft.MainAxisAlignment.CENTER,
            wrap=False,
            scroll=ft.ScrollMode.HIDDEN
        ),
        padding=ft.padding.symmetric(vertical=10, horizontal=5),
        border=ft.border.all(1, ft.Colors.GREY_300 if not is_dark else ft.Colors.GREY_700),
        border_radius=8,
        bgcolor=ft.Colors.GREY_50 if not is_dark else ft.Colors.GREY_900
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
                bar_chart,
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
                weekly_chart
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
    
    # OFFLINE-FIRST: Recargar métricas frescas desde SQLite local
    metrics = habit_service.get_habit_metrics(habit.id)
    
    # Obtener progreso mensual
    monthly = habit_service.get_monthly_progress(habit.id)
    
    # Obtener progreso semanal
    weekly = habit_service.get_weekly_progress(habit.id)
    
    # Calcular valores del progreso mensual
    completed_days = monthly.get('completions_count', 0)
    total_days = monthly.get('total_days', 1)
    completion_percentage = (completed_days / total_days * 100) if total_days > 0 else 0.0
    
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
                                f"{completed_days}/{total_days} días",
                                size=24,
                                weight=ft.FontWeight.BOLD,
                                color=primary
                            ),
                            ft.ProgressBar(
                                value=completion_percentage / 100.0,
                                color=primary,
                                bgcolor=ft.Colors.GREY_300 if not is_dark else ft.Colors.GREY_700
                            ),
                            ft.Text(
                                f"{completion_percentage:.1f}% de cumplimiento",
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

