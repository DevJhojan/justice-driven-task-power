"""
Módulo para la gestión de hábitos (CRUD).
"""
import flet as ft
from typing import Optional
from datetime import date
from app.data.models import Habit
from app.services.habit_service import HabitService
from app.ui.widgets import create_habit_card, create_habit_empty_state, create_habit_statistics_card


def load_habits_into_container(
    page: ft.Page,
    habit_service: HabitService,
    habits_container: ft.Column,
    habit_stats_container: ft.Container,
    current_habit_filter: Optional[bool],
    on_toggle_completion: callable,
    on_edit: callable,
    on_delete: callable,
    on_view_details: callable
):
    """
    Carga los hábitos desde la base de datos y los muestra en el contenedor.
    
    Args:
        page: Página de Flet.
        habit_service: Servicio para gestionar hábitos.
        habits_container: Contenedor donde se mostrarán los hábitos.
        habit_stats_container: Contenedor de estadísticas.
        current_habit_filter: Filtro actual (None=all, True=active, False=inactive).
        on_toggle_completion: Callback para toggle de cumplimiento.
        on_edit: Callback para editar hábito.
        on_delete: Callback para eliminar hábito.
        on_view_details: Callback para ver detalles.
    """
    habits = habit_service.get_all_habits(current_habit_filter)
    
    # Asegurarse de que el contenedor existe
    if not habits_container:
        return
    
    habits_container.controls.clear()
    
    if not habits:
        habits_container.controls.append(create_habit_empty_state(page))
    else:
        for habit in habits:
            # Obtener métricas del hábito
            metrics = habit_service.get_habit_metrics(habit.id)
            
            card = create_habit_card(
                habit,
                metrics,
                on_toggle_completion=on_toggle_completion,
                on_edit=on_edit,
                on_delete=on_delete,
                on_view_details=on_view_details,
                page=page
            )
            habits_container.controls.append(card)
    
    # Actualizar estadísticas
    if habit_stats_container:
        stats = habit_service.get_statistics()
        habit_stats_container.content = create_habit_statistics_card(stats, page)
        try:
            habit_stats_container.update()
        except:
            pass
    
    try:
        habits_container.update()
    except:
        pass
    page.update()


def toggle_habit_completion(page: ft.Page, habit_service: HabitService, habit_id: int) -> bool:
    """
    Alterna el cumplimiento de un hábito para hoy.
    
    Args:
        page: Página de Flet.
        habit_service: Servicio para gestionar hábitos.
        habit_id: ID del hábito.
    
    Returns:
        True si se completó, False si se eliminó el cumplimiento.
    """
    completion = habit_service.toggle_completion(habit_id, date.today())
    
    # Mostrar mensaje
    if completion:
        page.snack_bar = ft.SnackBar(
            content=ft.Text("¡Hábito completado!"),
            bgcolor=ft.Colors.RED_700
        )
    else:
        page.snack_bar = ft.SnackBar(
            content=ft.Text("Cumplimiento eliminado"),
            bgcolor=ft.Colors.GREY_700
        )
    page.snack_bar.open = True
    page.update()
    
    return completion


def delete_habit(page: ft.Page, habit_service: HabitService, habit_id: int) -> bool:
    """
    Elimina un hábito.
    
    Args:
        page: Página de Flet.
        habit_service: Servicio para gestionar hábitos.
        habit_id: ID del hábito a eliminar.
    
    Returns:
        True si se eliminó correctamente, False en caso contrario.
    """
    if habit_id is None:
        return False
    
    try:
        deleted = habit_service.delete_habit(int(habit_id))
        if deleted:
            page.snack_bar = ft.SnackBar(
                content=ft.Text("Hábito eliminado correctamente"),
                bgcolor=ft.Colors.RED_700
            )
            page.snack_bar.open = True
        else:
            page.snack_bar = ft.SnackBar(
                content=ft.Text("No se pudo eliminar el hábito"),
                bgcolor=ft.Colors.RED
            )
            page.snack_bar.open = True
        page.update()
        return deleted
    except Exception as ex:
        page.snack_bar = ft.SnackBar(
            content=ft.Text(f"Error: {str(ex)}"),
            bgcolor=ft.Colors.RED
        )
        page.snack_bar.open = True
        page.update()
        return False


def save_habit(habit_service: HabitService, *args):
    """
    Guarda un hábito (crear o actualizar).
    
    Args:
        habit_service: Servicio para gestionar hábitos.
        *args: Si el primer argumento es un Habit, es actualización. 
               Si no, son (title, description, frequency, target_days) para crear.
    """
    # Si el primer argumento es un objeto Habit, es una actualización
    if args and isinstance(args[0], Habit):
        # Actualizar hábito existente
        habit = args[0]
        habit_service.update_habit(habit)
    else:
        # Crear nuevo hábito
        title, description, frequency, target_days = args
        habit_service.create_habit(title, description, frequency, target_days)

