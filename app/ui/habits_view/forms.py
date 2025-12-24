"""
Módulo para la navegación y construcción de formularios de hábitos.
"""
import flet as ft
from typing import Optional
from datetime import date
from app.data.models import Habit
from app.ui.habit_form import HabitForm
from app.ui.habits_view.metrics import create_habit_metrics_view


def navigate_to_habit_form(
    page: ft.Page,
    editing_habit: Optional[Habit],
    on_save: callable,
    on_go_back: callable
):
    """
    Navega a la vista del formulario de hábito.
    
    Args:
        page: Página de Flet.
        editing_habit: Hábito a editar (None si es nuevo).
        on_save: Callback cuando se guarda el hábito.
        on_go_back: Callback para volver.
    """
    title = "Editar Hábito" if editing_habit else "Nuevo Hábito"
    
    # Crear el formulario
    form = HabitForm(
        on_save=on_save,
        on_cancel=on_go_back,
        habit=editing_habit
    )
    
    # Detectar el tema actual
    is_dark = page.theme_mode == ft.ThemeMode.DARK
    bgcolor = ft.Colors.BLACK if is_dark else ft.Colors.GREY_50
    
    # Crear la barra de título con botón de volver
    back_button = ft.IconButton(
        icon=ft.Icons.ARROW_BACK,
        on_click=lambda e: on_go_back(),
        icon_color=ft.Colors.RED_400,
        tooltip="Volver"
    )
    
    title_bar = ft.Container(
        content=ft.Row(
            [
                back_button,
                ft.Text(
                    title,
                    size=24,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.RED_400,
                    expand=True
                )
            ],
            alignment=ft.MainAxisAlignment.START,
            vertical_alignment=ft.CrossAxisAlignment.CENTER
        ),
        padding=ft.padding.symmetric(vertical=16, horizontal=20),
        bgcolor=ft.Colors.BLACK87 if is_dark else ft.Colors.RED_50
    )
    
    # Construir la vista del formulario
    form_view = ft.View(
        route="/habit-form",
        controls=[
            title_bar,
            ft.Container(
                content=form.build(),
                expand=True,
                padding=20
            )
        ],
        bgcolor=bgcolor
    )
    
    # Agregar la vista y navegar a ella
    page.views.append(form_view)
    page.go("/habit-form")


def navigate_to_habit_details(
    page: ft.Page,
    habit_service,
    habit: Habit,
    on_go_back: callable
):
    """
    Muestra la vista de detalles de un hábito con historial y métricas.
    
    Args:
        page: Página de Flet.
        habit_service: Servicio para gestionar hábitos.
        habit: Hábito a mostrar.
        on_go_back: Callback para volver.
    """
    # Obtener métricas completas (100% offline, solo desde SQLite local)
    # OFFLINE-FIRST: Todas las métricas se calculan desde la base de datos local
    metrics = habit_service.get_habit_metrics(habit.id)
    
    # Detectar el tema actual
    is_dark = page.theme_mode == ft.ThemeMode.DARK
    bgcolor = ft.Colors.BLACK if is_dark else ft.Colors.GREY_50
    
    # Crear la barra de título con botón de volver
    back_button = ft.IconButton(
        icon=ft.Icons.ARROW_BACK,
        on_click=lambda e: on_go_back(),
        icon_color=ft.Colors.RED_400,
        tooltip="Volver"
    )
    
    title_bar = ft.Container(
        content=ft.Row(
            [
                back_button,
                ft.Text(
                    habit.title,
                    size=24,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.RED_400,
                    expand=True
                )
            ],
            alignment=ft.MainAxisAlignment.START,
            vertical_alignment=ft.CrossAxisAlignment.CENTER
        ),
        padding=ft.padding.symmetric(vertical=16, horizontal=20),
        bgcolor=ft.Colors.BLACK87 if is_dark else ft.Colors.RED_50
    )
    
    # Contenedor para la vista de métricas (se actualizará dinámicamente)
    metrics_container = ft.Container()
    
    def load_completion_dates():
        """Carga las fechas de cumplimiento actuales."""
        completions = habit_service.repository.get_completions(habit.id)
        return {c.completion_date.date() for c in completions}
    
    # Callback para alternar cumplimiento (100% offline, solo SQLite local)
    def toggle_completion(habit_id: int, completion_date: date):
        """
        Alterna el cumplimiento de un hábito para una fecha específica.
        OFFLINE-FIRST: Solo opera en la base de datos local SQLite.
        No hay llamadas a Firebase aquí.
        """
        # OFFLINE-FIRST: Solo operaciones locales en SQLite
        habit_service.toggle_completion(habit_id, completion_date)
        # No necesitamos reconstruir aquí porque el handler del calendario ya lo hace
    
    def rebuild_metrics_view():
        """Reconstruye la vista de métricas con datos actualizados."""
        print("DEBUG rebuild_metrics_view: Iniciando reconstrucción...")
        try:
            # OFFLINE-FIRST: Recargar el hábito completo desde SQLite local
            # Esto asegura que todos los datos estén actualizados (completions, etc.)
            updated_habit = habit_service.get_habit(habit.id)
            if updated_habit:
                # Actualizar el objeto habit con los datos frescos
                habit.completions = updated_habit.completions
                habit.updated_at = updated_habit.updated_at
                # Usar el hábito actualizado
                habit_to_use = updated_habit
                print(f"DEBUG rebuild_metrics_view: Hábito actualizado, {len(updated_habit.completions)} completions")
            else:
                # Si no se encuentra, usar el original
                habit_to_use = habit
                print("DEBUG rebuild_metrics_view: Usando hábito original")
            
            # Recargar fechas de cumplimiento
            completion_dates = load_completion_dates()
            print(f"DEBUG rebuild_metrics_view: {len(completion_dates)} fechas de cumplimiento cargadas")
            
            # Reconstruir la vista de métricas con el hábito actualizado
            print("DEBUG rebuild_metrics_view: Creando nueva vista de métricas...")
            metrics_view = create_habit_metrics_view(
                page=page,
                habit=habit_to_use,
                habit_service=habit_service,
                completion_dates=completion_dates,
                on_completion_toggle=toggle_completion,
                on_refresh=rebuild_metrics_view
            )
            metrics_container.content = metrics_view
            print("DEBUG rebuild_metrics_view: Vista reconstruida, actualizando página...")
            page.update()
            print("DEBUG rebuild_metrics_view: Reconstrucción completada")
        except Exception as ex:
            print(f"ERROR: Error al reconstruir métricas: {ex}")
            import traceback
            traceback.print_exc()
            # Intentar actualizar de todas formas
            page.update()
    
    # Cargar fechas iniciales
    completion_dates = load_completion_dates()
    
    # Crear vista de métricas avanzadas inicial
    metrics_view = create_habit_metrics_view(
        page=page,
        habit=habit,
        habit_service=habit_service,
        completion_dates=completion_dates,
        on_completion_toggle=toggle_completion,
        on_refresh=rebuild_metrics_view
    )
    
    metrics_container.content = metrics_view
    
    # Construir contenido de detalles con métricas básicas y avanzadas
    details_content = ft.Container(
        content=ft.Column(
            [
                # Descripción
                ft.Text(
                    habit.description if habit.description else "Sin descripción",
                    size=14,
                    color=ft.Colors.GREY_500 if is_dark else ft.Colors.GREY_600
                ),
                ft.Divider(),
                # Métricas principales (resumen)
                ft.Text(
                    "Resumen",
                    size=20,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.RED_400
                ),
                ft.Row(
                    [
                        ft.Container(
                            content=ft.Column(
                                [
                                    ft.Text(
                                        str(metrics['streak']),
                                        size=32,
                                        weight=ft.FontWeight.BOLD,
                                        color=ft.Colors.RED_400
                                    ),
                                    ft.Text("Días seguidos", size=12)
                                ],
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER
                            ),
                            expand=True
                        ),
                        ft.VerticalDivider(),
                        ft.Container(
                            content=ft.Column(
                                [
                                    ft.Text(
                                        f"{metrics['completion_percentage']:.1f}%",
                                        size=32,
                                        weight=ft.FontWeight.BOLD,
                                        color=ft.Colors.RED_500
                                    ),
                                    ft.Text("Cumplimiento", size=12)
                                ],
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER
                            ),
                            expand=True
                        ),
                        ft.VerticalDivider(),
                        ft.Container(
                            content=ft.Column(
                                [
                                    ft.Text(
                                        str(metrics['total_completions']),
                                        size=32,
                                        weight=ft.FontWeight.BOLD,
                                        color=ft.Colors.RED_600
                                    ),
                                    ft.Text("Total", size=12)
                                ],
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER
                            ),
                            expand=True
                        )
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_EVENLY
                ),
                ft.Divider(),
                # Información adicional
                ft.Text(
                    f"Frecuencia: {habit.frequency.capitalize()}",
                    size=14
                ),
                ft.Text(
                    f"Último cumplimiento: {metrics['last_completion_date'].strftime('%d/%m/%Y') if metrics['last_completion_date'] else 'Nunca'}",
                    size=14
                ),
                ft.Divider(),
                # Métricas avanzadas (calendario y gráficas)
                metrics_container
            ],
            spacing=16,
            scroll=ft.ScrollMode.AUTO
        ),
        padding=20,
        expand=True
    )
    
    # Construir la vista de detalles
    details_view = ft.View(
        route="/habit-details",
        controls=[
            title_bar,
            details_content
        ],
        bgcolor=bgcolor
    )
    
    # Agregar la vista y navegar a ella
    page.views.append(details_view)
    page.go("/habit-details")

