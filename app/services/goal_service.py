"""
Servicio de lógica de negocio para metas.
"""
from typing import List, Optional

from app.data.models import Goal
from app.data.goal_repository import GoalRepository


class GoalService:
    """Servicio para gestión de metas."""
    
    def __init__(self, goal_repository: GoalRepository):
        """
        Inicializa el servicio.
        
        Args:
            goal_repository: Repositorio de metas.
        """
        self.repository = goal_repository
    
    def create_goal(self, title: str, description: Optional[str] = None,
                   target_value: Optional[float] = None, unit: Optional[str] = None,
                   current_value: float = 0.0, period: str = "mes", points_service=None) -> Goal:
        """
        Crea una nueva meta.
        
        Args:
            title: Título de la meta.
            description: Descripción de la meta.
            target_value: Valor objetivo.
            unit: Unidad de medida (ej: "tareas", "días", "horas").
            current_value: Valor inicial actual.
            period: Período de la meta (semana, mes, trimestre, semestre, anual).
            points_service: Servicio de puntos para agregar puntos si se completa la meta.
        
        Returns:
            Meta creada.
        """
        goal = Goal(
            id=None,
            title=title,
            description=description,
            target_value=target_value,
            current_value=current_value,
            unit=unit,
            period=period
        )
        
        created_goal = self.repository.create(goal)
        
        # Si la meta se crea ya completa, otorgar puntos
        if target_value and current_value >= target_value:
            if points_service:
                points_service.add_points(1.00)  # 1.00 puntos por completar una meta
        
        return created_goal
    
    def get_goal(self, goal_id: int) -> Optional[Goal]:
        """
        Obtiene una meta por su ID.
        
        Args:
            goal_id: ID de la meta.
        
        Returns:
            Meta si existe, None en caso contrario.
        """
        return self.repository.get_by_id(goal_id)
    
    def get_all_goals(self) -> List[Goal]:
        """
        Obtiene todas las metas.
        
        Returns:
            Lista de todas las metas.
        """
        return self.repository.get_all()
    
    def update_goal(self, goal: Goal) -> Goal:
        """
        Actualiza una meta.
        
        Args:
            goal: Meta a actualizar.
        
        Returns:
            Meta actualizada.
        """
        return self.repository.update(goal)
    
    def update_progress(self, goal_id: int, current_value: float, points_service=None) -> bool:
        """
        Actualiza el progreso de una meta.
        
        Args:
            goal_id: ID de la meta.
            current_value: Nuevo valor de progreso.
            points_service: Servicio de puntos para agregar puntos si se completa la meta.
        
        Returns:
            True si se actualizó correctamente, False si no existe.
        """
        goal = self.repository.get_by_id(goal_id)
        if goal is None:
            return False
        
        # Verificar si la meta estaba completa antes y ahora se completó
        was_completed = goal.target_value and goal.current_value >= goal.target_value
        goal.current_value = current_value
        self.repository.update(goal)
        
        # Si tiene target_value y ahora está completa (y antes no lo estaba), dar puntos
        if goal.target_value and current_value >= goal.target_value and not was_completed:
            if points_service:
                points_service.add_points(1.00)  # 1.00 puntos por completar una meta
        
        return True
    
    def increment_progress(self, goal_id: int, increment: float = 1.0, points_service=None) -> bool:
        """
        Incrementa el progreso de una meta.
        
        Args:
            goal_id: ID de la meta.
            increment: Cantidad a incrementar.
            points_service: Servicio de puntos para agregar puntos si se completa la meta.
        
        Returns:
            True si se actualizó correctamente, False si no existe.
        """
        goal = self.repository.get_by_id(goal_id)
        if goal is None:
            return False
        
        # Verificar si la meta estaba completa antes
        was_completed = goal.target_value and goal.current_value >= goal.target_value
        goal.current_value += increment
        self.repository.update(goal)
        
        # Si tiene target_value y ahora está completa (y antes no lo estaba), dar puntos
        if goal.target_value and goal.current_value >= goal.target_value and not was_completed:
            if points_service:
                points_service.add_points(1.00)  # 1.00 puntos por completar una meta
        
        return True
    
    def get_progress_percentage(self, goal_id: int) -> float:
        """
        Obtiene el porcentaje de progreso de una meta.
        
        Args:
            goal_id: ID de la meta.
        
        Returns:
            Porcentaje de progreso (0-100). Si no hay valor objetivo, retorna 0.
        """
        goal = self.repository.get_by_id(goal_id)
        if goal is None or goal.target_value is None or goal.target_value == 0:
            return 0.0
        
        percentage = (goal.current_value / goal.target_value) * 100
        return min(100.0, max(0.0, percentage))
    
    def delete_goal(self, goal_id: int) -> bool:
        """
        Elimina una meta.
        
        Args:
            goal_id: ID de la meta a eliminar.
        
        Returns:
            True si se eliminó, False si no existía.
        """
        return self.repository.delete(goal_id)

