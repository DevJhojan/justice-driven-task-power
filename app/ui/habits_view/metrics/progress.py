"""
Vista de progreso detallado del hábito (racha, progreso semanal y mensual).
"""
import flet as ft
from typing import Dict
from app.data.models import Habit


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
        metrics: Diccionario con métricas (se ignora, se recarga desde BD)
        
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
    
    progress_container = ft.Container(
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
            scroll=ft.ScrollMode.AUTO,
            expand=True
        ),
        padding=20,
        expand=True
    )
    
    # NO llamar a update() aquí - el contenedor se actualizará automáticamente cuando se agregue a la página
    
    return progress_container

