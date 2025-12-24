"""
Vista de gráficas de progreso del hábito (últimos 30 días y últimas 8 semanas).
"""
import flet as ft
from datetime import date, timedelta
from app.data.models import Habit
from ...utils import load_completion_dates


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
    fresh_completion_dates = load_completion_dates(habit_service, habit.id)
    
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
    max_height = 150
    bar_width = 20
    bars = []
    for day_data in last_30_days:
        height = max_height if day_data['completed'] else 10
        color = primary if day_data['completed'] else (ft.Colors.GREY_300 if not is_dark else ft.Colors.GREY_700)
        border_color = ft.Colors.GREY_400 if not is_dark else ft.Colors.GREY_600
        
        bars.append(
            ft.Container(
                content=ft.Column(
                    [
                        ft.Container(
                            width=bar_width,
                            height=height,
                            bgcolor=color,
                            border_radius=10,
                            border=ft.border.all(2, border_color if not day_data['completed'] else primary),
                            alignment=ft.alignment.center if day_data['completed'] else None
                        ),
                        ft.Container(height=4),  # Espacio
                        ft.Text(
                            str(day_data['date'].day),
                            size=11,
                            weight=ft.FontWeight.BOLD if day_data['completed'] else ft.FontWeight.NORMAL,
                            text_align=ft.TextAlign.CENTER,
                            color=primary if day_data['completed'] else (ft.Colors.GREY_600 if not is_dark else ft.Colors.GREY_400)
                        )
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=0,
                    tight=True
                ),
                width=bar_width + 4,
                tooltip=f"{day_data['date'].strftime('%d/%m/%Y')} - {'✓ Completado' if day_data['completed'] else '✗ No completado'}"
            )
        )
    
    bar_chart = ft.Container(
        content=ft.Column(
            [
                ft.Text(
                    "Últimos 30 Días",
                    size=14,
                    weight=ft.FontWeight.BOLD,
                    text_align=ft.TextAlign.CENTER,
                    color=primary
                ),
                ft.Container(height=8),
                ft.Row(
                    bars,
                    spacing=4,
                    alignment=ft.MainAxisAlignment.CENTER,
                    wrap=False,
                    scroll=ft.ScrollMode.HIDDEN
                )
            ],
            spacing=0
        ),
        padding=ft.padding.symmetric(vertical=15, horizontal=10),
        border=ft.border.all(2, ft.Colors.GREY_300 if not is_dark else ft.Colors.GREY_700),
        border_radius=8,
        bgcolor=ft.Colors.GREY_50 if not is_dark else ft.Colors.GREY_900
    )
    
    # Gráfica de progreso semanal - Últimas 8 semanas
    # Ajustar según el tipo de hábito
    is_daily = habit.frequency == 'daily'
    # Para hábitos diarios, el objetivo es 7 días por semana (todos los días)
    # Para hábitos semanales/personalizados, usar el target_days del hábito
    if is_daily:
        target_days = 7  # Siempre 7 días para hábitos diarios
    else:
        # Para hábitos semanales/personalizados, usar el target_days del hábito
        # Asegurar que sea al menos 1 y máximo 7
        target_days = max(1, min(7, habit.target_days)) if habit.target_days and habit.target_days > 0 else 7
    
    max_height_weekly = 150
    
    weekly_data = []
    for week_offset in range(7, -1, -1):
        week_start = today - timedelta(weeks=week_offset, days=today.weekday())
        week_end = week_start + timedelta(days=6)
        
        week_completions = sum(1 for i in range(7) if (week_start + timedelta(days=i)) in fresh_completion_dates)
        weekly_data.append({
            'week': f"Sem {week_offset + 1}",
            'completions': week_completions,
            'target': target_days,
            'week_start': week_start
        })
    
    # Crear gráfica de barras para semanas (más grande y clara)
    # Usar el máximo entre completions y target_days para escalar correctamente
    max_value = max([d['completions'] for d in weekly_data] + [target_days] + [1])
    week_bars = []
    for week_data in weekly_data:
        # Calcular altura de la barra de completados
        height = int((week_data['completions'] / max_value) * max_height_weekly) if max_value > 0 else 0
        # Calcular altura de la barra de objetivo (siempre debe ser target_days / max_value)
        target_height = int((target_days / max_value) * max_height_weekly) if max_value > 0 else 0
        # Asegurar que target_height sea al menos la altura mínima visible
        if target_height < 10 and target_days > 0:
            target_height = 10
        
        # Mostrar siempre "completados/objetivo"
        # Para hábitos diarios: "X/7" (días completados / 7 días de la semana)
        # Para hábitos semanales/personalizados: "X/Y" (días completados / días objetivo)
        # Usar target_days directamente para asegurar que siempre muestre el objetivo correcto
        completion_text = f"{week_data['completions']}/{target_days}"
        tooltip_text = f"{week_data['week']}: {week_data['completions']}/{target_days} días completados (objetivo: {target_days} días/semana)"
        
        week_bars.append(
            ft.Container(
                content=ft.Column(
                    [
                        ft.Stack(
                            [
                                # Barra de objetivo (fondo) - mostrar siempre
                                ft.Container(
                                    width=40,
                                    height=target_height,
                                    bgcolor=ft.Colors.ORANGE_200 if not is_dark else ft.Colors.ORANGE_800,
                                    border_radius=8,
                                    bottom=0,
                                    border=ft.border.all(2, ft.Colors.ORANGE_400 if not is_dark else ft.Colors.ORANGE_600)
                                ),
                                # Barra de completados (frente)
                                ft.Container(
                                    width=40,
                                    height=max(height, 10) if height > 0 else 10,
                                    bgcolor=primary if week_data['completions'] > 0 else (ft.Colors.GREY_300 if not is_dark else ft.Colors.GREY_700),
                                    border_radius=8,
                                    bottom=0,
                                    border=ft.border.all(2, primary if week_data['completions'] > 0 else (ft.Colors.GREY_400 if not is_dark else ft.Colors.GREY_600))
                                )
                            ],
                            width=40,
                            height=max_height_weekly
                        ),
                        ft.Container(height=6),  # Espacio
                        ft.Text(
                            week_data['week'],
                            size=11,
                            weight=ft.FontWeight.BOLD,
                            text_align=ft.TextAlign.CENTER,
                            color=ft.Colors.WHITE if is_dark else ft.Colors.BLACK87
                        ),
                        ft.Text(
                            completion_text,
                            size=12,
                            text_align=ft.TextAlign.CENTER,
                            color=primary,
                            weight=ft.FontWeight.BOLD
                        )
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=2,
                    tight=True
                ),
                width=50,
                tooltip=tooltip_text
            )
        )
    
    # Título para la gráfica semanal según el tipo de hábito
    if is_daily:
        weekly_title = f"Últimas 8 Semanas - Días Completados/Objetivo (7 días/semana)"
    else:
        weekly_title = f"Últimas 8 Semanas - Días Completados/Objetivo ({target_days} días/semana)"
    
    weekly_chart = ft.Container(
        content=ft.Column(
            [
                ft.Text(
                    weekly_title,
                    size=14,
                    weight=ft.FontWeight.BOLD,
                    text_align=ft.TextAlign.CENTER,
                    color=primary
                ),
                ft.Container(height=8),
                ft.Row(
                    week_bars,
                    spacing=8,
                    alignment=ft.MainAxisAlignment.CENTER,
                    wrap=False,
                    scroll=ft.ScrollMode.HIDDEN
                )
            ],
            spacing=0
        ),
        padding=ft.padding.symmetric(vertical=15, horizontal=10),
        border=ft.border.all(2, ft.Colors.GREY_300 if not is_dark else ft.Colors.GREY_700),
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

