"""
Vista de calendario interactivo para mostrar y editar cumplimientos de hábitos.
"""
import flet as ft
from datetime import date
from typing import Callable
from calendar import monthrange
from app.data.models import Habit
from ..utils import load_completion_dates


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
        current_completion_dates = load_completion_dates(habit_service, habit.id)
        
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
                            fresh_completion_dates = load_completion_dates(habit_service, habit.id)
                            
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
                                fresh_completion_dates = load_completion_dates(habit_service, habit.id)
                                completion_dates.clear()
                                completion_dates.update(fresh_completion_dates)
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
        try:
            # Recargar datos frescos desde SQLite
            fresh_completion_dates = load_completion_dates(habit_service, habit.id)
            
            # Actualizar el set de completion_dates (esto es importante para las otras vistas)
            completion_dates.clear()
            completion_dates.update(fresh_completion_dates)
            
            # Reconstruir el calendario con datos frescos
            build_calendar(current_month[0], current_year[0])
            
            # Actualizar el contenedor del calendario explícitamente
            calendar_container.update()
            
            # Refrescar otras vistas (gráficas, progreso, etc.)
            # Esto reconstruye toda la vista de métricas con los datos actualizados
            if on_refresh:
                on_refresh()
            
            # Actualizar la página
            page.update()
            
            # Mostrar mensaje de confirmación
            page.snack_bar = ft.SnackBar(
                content=ft.Text("Datos actualizados correctamente"),
                bgcolor=primary,
                duration=2000
            )
            page.snack_bar.open = True
            page.update()
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

