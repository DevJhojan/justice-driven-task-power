"""
Servicio de lógica de negocio para hábitos.
"""
from datetime import date, datetime, timedelta
from typing import List, Optional, Set

from app.data.models import Habit
from app.data.habit_repository import HabitRepository


class HabitService:
    """Servicio para gestión de hábitos."""
    
    def __init__(self, habit_repository: HabitRepository):
        """
        Inicializa el servicio.
        
        Args:
            habit_repository: Repositorio de hábitos.
        """
        self.repository = habit_repository
    
    def create_habit(self, title: str, description: Optional[str] = None) -> Habit:
        """
        Crea un nuevo hábito.
        
        Args:
            title: Título del hábito.
            description: Descripción del hábito.
        
        Returns:
            Hábito creado.
        """
        habit = Habit(
            id=None,
            title=title,
            description=description
        )
        
        return self.repository.create(habit)
    
    def get_habit(self, habit_id: int) -> Optional[Habit]:
        """
        Obtiene un hábito por su ID.
        
        Args:
            habit_id: ID del hábito.
        
        Returns:
            Hábito si existe, None en caso contrario.
        """
        return self.repository.get_by_id(habit_id)
    
    def get_all_habits(self) -> List[Habit]:
        """
        Obtiene todos los hábitos.
        
        Returns:
            Lista de todos los hábitos.
        """
        return self.repository.get_all()
    
    def update_habit(self, habit: Habit) -> Habit:
        """
        Actualiza un hábito.
        
        Args:
            habit: Hábito a actualizar.
        
        Returns:
            Hábito actualizado.
        """
        return self.repository.update(habit)
    
    def delete_habit(self, habit_id: int) -> bool:
        """
        Elimina un hábito.
        
        Args:
            habit_id: ID del hábito a eliminar.
        
        Returns:
            True si se eliminó, False si no existía.
        """
        return self.repository.delete(habit_id)
    
    def toggle_completion(self, habit_id: int, completion_date: Optional[date] = None,
                         points_service=None) -> bool:
        """
        Alterna el estado de completación de un hábito para una fecha.
        Si está completado, lo marca como no completado y viceversa.
        
        Args:
            habit_id: ID del hábito.
            completion_date: Fecha de completación. Si es None, usa hoy.
            points_service: Servicio de puntos para agregar puntos al completar.
        
        Returns:
            True si ahora está completado, False si se desmarcó.
        """
        if completion_date is None:
            completion_date = date.today()
        
        completions = self.repository.get_completions(habit_id)
        
        if completion_date in completions:
            # Ya está completado, desmarcar
            self.repository.remove_completion(habit_id, completion_date)
            if points_service:
                points_service.add_points(-0.01)  # Restar 0.01 puntos al desmarcar
            return False
        else:
            # No está completado, marcar
            self.repository.add_completion(habit_id, completion_date)
            if points_service:
                points_service.add_points(0.01)  # 0.01 puntos por completar un hábito
            return True
    
    def get_completions(self, habit_id: int) -> Set[date]:
        """
        Obtiene todas las fechas en las que se completó un hábito.
        
        Args:
            habit_id: ID del hábito.
        
        Returns:
            Conjunto de fechas de completación.
        """
        return self.repository.get_completions(habit_id)
    
    def get_completion_count(self, habit_id: int) -> int:
        """
        Obtiene el número total de completaciones de un hábito.
        
        Args:
            habit_id: ID del hábito.
        
        Returns:
            Número de completaciones.
        """
        return self.repository.get_completion_count(habit_id)
    
    def get_streak(self, habit_id: int) -> int:
        """
        Calcula la racha actual (streak) de un hábito.
        La racha es el número de días consecutivos completados hasta hoy.
        
        Args:
            habit_id: ID del hábito.
        
        Returns:
            Número de días consecutivos.
        """
        completions = self.repository.get_completions(habit_id)
        if not completions:
            return 0
        
        today = date.today()
        streak = 0
        current_date = today
        
        # Contar hacia atrás desde hoy
        while current_date in completions:
            streak += 1
            current_date = current_date - timedelta(days=1)
        
        # Si hoy no está completado, la racha es 0
        if today not in completions and streak > 0:
            return 0
        
        return streak
    
    def is_completed_today(self, habit_id: int) -> bool:
        """
        Verifica si un hábito fue completado hoy.
        
        Args:
            habit_id: ID del hábito.
        
        Returns:
            True si está completado hoy, False en caso contrario.
        """
        completions = self.repository.get_completions(habit_id)
        return date.today() in completions

