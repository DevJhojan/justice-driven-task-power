"""
Servicio de lógica de negocio para objetivos.
"""
from typing import List, Optional
from datetime import datetime
from app.data.database import Database
from app.data.goal_repository import GoalRepository
from app.data.models import Goal


class GoalService:
    """Servicio para gestionar la lógica de negocio de objetivos."""
    
    def __init__(self):
        """Inicializa el servicio con la base de datos y repositorio."""
        self.db = Database()
        self.repository = GoalRepository(self.db)
    
    def create_goal(
        self, 
        title: str, 
        description: str = "", 
        frequency: str = "monthly",
        target_date: Optional[datetime] = None
    ) -> Goal:
        """
        Crea un nuevo objetivo.
        
        Args:
            title: Título del objetivo.
            description: Descripción del objetivo.
            frequency: Frecuencia ('daily', 'weekly', 'monthly', 'quarterly', 'semiannual', 'annual').
            target_date: Fecha objetivo (opcional).
            
        Returns:
            Objetivo creado.
        """
        if not title or not title.strip():
            raise ValueError("El título del objetivo no puede estar vacío")
        
        valid_frequencies = ['daily', 'weekly', 'monthly', 'quarterly', 'semiannual', 'annual']
        if frequency not in valid_frequencies:
            frequency = 'monthly'
        
        goal = Goal(
            id=None,
            title=title.strip(),
            description=description.strip(),
            frequency=frequency,
            target_date=target_date,
            completed=False,
            created_at=None,
            updated_at=None
        )
        
        return self.repository.create(goal)
    
    def get_all_goals(
        self, 
        filter_completed: Optional[bool] = None,
        filter_frequency: Optional[str] = None
    ) -> List[Goal]:
        """
        Obtiene todos los objetivos, opcionalmente filtrados por estado o frecuencia.
        
        Args:
            filter_completed: Si se proporciona, filtra por estado de completado.
            filter_frequency: Si se proporciona, filtra por frecuencia.
            
        Returns:
            Lista de objetivos.
        """
        return self.repository.get_all(filter_completed, filter_frequency)
    
    def get_goal(self, goal_id: int) -> Optional[Goal]:
        """
        Obtiene un objetivo por su ID.
        
        Args:
            goal_id: ID del objetivo.
            
        Returns:
            Objetivo encontrado o None.
        """
        return self.repository.get_by_id(goal_id)
    
    def update_goal(self, goal: Goal) -> Goal:
        """
        Actualiza un objetivo existente.
        
        Args:
            goal: Objetivo con los datos actualizados.
            
        Returns:
            Objetivo actualizado.
        """
        if not goal.title or not goal.title.strip():
            raise ValueError("El título del objetivo no puede estar vacío")
        
        goal.title = goal.title.strip()
        goal.description = goal.description.strip()
        
        valid_frequencies = ['daily', 'weekly', 'monthly', 'quarterly', 'semiannual', 'annual']
        if goal.frequency not in valid_frequencies:
            goal.frequency = 'monthly'
        
        return self.repository.update(goal)
    
    def delete_goal(self, goal_id: int) -> bool:
        """
        Elimina un objetivo.
        
        Args:
            goal_id: ID del objetivo a eliminar.
            
        Returns:
            True si se eliminó, False si no existía.
        """
        return self.repository.delete(goal_id)
    
    def toggle_goal_complete(self, goal_id: int) -> Optional[Goal]:
        """
        Cambia el estado de completado de un objetivo.
        
        Args:
            goal_id: ID del objetivo.
            
        Returns:
            Objetivo actualizado o None si no existe.
        """
        return self.repository.toggle_complete(goal_id)
    
    def get_statistics(self) -> dict:
        """
        Obtiene estadísticas generales de todos los objetivos.
        
        Returns:
            Diccionario con estadísticas.
        """
        all_goals = self.repository.get_all()
        total = len(all_goals)
        completed = sum(1 for goal in all_goals if goal.completed)
        pending = total - completed
        
        # Estadísticas por frecuencia
        frequency_stats = {}
        for frequency in ['daily', 'weekly', 'monthly', 'quarterly', 'semiannual', 'annual']:
            frequency_goals = [g for g in all_goals if g.frequency == frequency]
            frequency_stats[frequency] = {
                'total': len(frequency_goals),
                'completed': sum(1 for g in frequency_goals if g.completed),
                'pending': len(frequency_goals) - sum(1 for g in frequency_goals if g.completed)
            }
        
        return {
            'total': total,
            'completed': completed,
            'pending': pending,
            'by_frequency': frequency_stats
        }

