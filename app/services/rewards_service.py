"""
Servicio de Recompensas
Gestiona las operaciones CRUD de recompensas
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from app.models.reward import Reward


class RewardsService:
    """Servicio para gestionar recompensas"""
    
    def __init__(self):
        """Inicializa el servicio"""
        self.rewards: Dict[str, Reward] = {}
    
    def create_reward(self, reward_data: Dict[str, Any]) -> Reward:
        """
        Crea una nueva recompensa
        
        Args:
            reward_data: Diccionario con datos de la recompensa
            
        Returns:
            Instancia de Reward creada
        """
        reward = Reward.from_dict(reward_data)
        self.rewards[reward.id] = reward
        return reward
    
    def get_reward(self, reward_id: str) -> Optional[Reward]:
        """
        Obtiene una recompensa por ID
        
        Args:
            reward_id: ID de la recompensa
            
        Returns:
            Instancia de Reward o None
        """
        return self.rewards.get(reward_id)
    
    def get_all_rewards(self, active_only: bool = False) -> List[Reward]:
        """
        Obtiene todas las recompensas
        
        Args:
            active_only: Si solo obtener recompensas activas
            
        Returns:
            Lista de recompensas
        """
        rewards = list(self.rewards.values())
        
        if active_only:
            rewards = [r for r in rewards if r.is_active]
        
        # Ordenar por puntos requeridos
        rewards.sort(key=lambda x: x.points_required)
        
        return rewards
    
    def get_rewards_by_category(self, category: str) -> List[Reward]:
        """
        Obtiene recompensas por categoría
        
        Args:
            category: Categoría de recompensas
            
        Returns:
            Lista de recompensas
        """
        return [r for r in self.rewards.values() if r.category == category]
    
    def update_reward(self, reward_id: str, reward_data: Dict[str, Any]) -> Optional[Reward]:
        """
        Actualiza una recompensa existente
        
        Args:
            reward_id: ID de la recompensa
            reward_data: Datos a actualizar
            
        Returns:
            Recompensa actualizada o None
        """
        reward = self.get_reward(reward_id)
        if not reward:
            return None
        
        reward.update(**reward_data)
        return reward
    
    def delete_reward(self, reward_id: str) -> bool:
        """
        Elimina una recompensa
        
        Args:
            reward_id: ID de la recompensa
            
        Returns:
            True si se eliminó, False si no existe
        """
        if reward_id in self.rewards:
            del self.rewards[reward_id]
            return True
        return False
    
    def get_unlocked_rewards(self, user_points: float) -> List[Reward]:
        """
        Obtiene las recompensas desbloqueadas por puntos que no han sido reclamadas
        
        Args:
            user_points: Puntos del usuario
            
        Returns:
            Lista de recompensas desbloqueadas y no reclamadas
        """
        return [
            r for r in self.get_all_rewards(active_only=True)
            if r.points_required <= user_points and not r.claimed
        ]
    
    def get_next_rewards(self, user_points: float, limit: int = 5) -> List[Reward]:
        """
        Obtiene las próximas recompensas a desbloquear
        
        Args:
            user_points: Puntos del usuario
            limit: Cantidad máxima de recompensas
            
        Returns:
            Lista de próximas recompensas
        """
        locked = [
            r for r in self.get_all_rewards(active_only=True)
            if r.points_required > user_points
        ]
        locked.sort(key=lambda x: x.points_required)
        return locked[:limit]
