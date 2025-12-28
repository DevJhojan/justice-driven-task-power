"""
Servicio para gestión de recompensas.
"""
from datetime import datetime
from typing import List, Optional

from app.data.models import Reward
from app.data.reward_repository import RewardRepository


class RewardService:
    """Servicio para gestionar recompensas."""
    
    def __init__(self, reward_repository: RewardRepository, points_service):
        """
        Inicializa el servicio.
        
        Args:
            reward_repository: Repositorio de recompensas.
            points_service: Servicio de puntos para verificar estado de recompensas.
        """
        self.reward_repository = reward_repository
        self.points_service = points_service
    
    def create_reward(self, name: str, description: Optional[str], target_points: float) -> Reward:
        """
        Crea una nueva recompensa.
        
        Args:
            name: Nombre de la recompensa.
            description: Descripción opcional.
            target_points: Puntos objetivo requeridos.
        
        Returns:
            Recompensa creada.
        """
        if target_points <= 0:
            raise ValueError("Los puntos objetivo deben ser mayores a 0")
        
        reward = Reward(
            id=None,
            name=name.strip(),
            description=description.strip() if description else None,
            target_points=target_points,
            status="por_alcanzar",
            created_at=datetime.now()
        )
        
        return self.reward_repository.create(reward)
    
    def get_all_rewards(self) -> List[Reward]:
        """
        Obtiene todas las recompensas.
        
        Returns:
            Lista de recompensas.
        """
        return self.reward_repository.get_all()
    
    def get_rewards_by_status(self, status: str) -> List[Reward]:
        """
        Obtiene recompensas por estado.
        
        Args:
            status: Estado de la recompensa.
        
        Returns:
            Lista de recompensas con el estado especificado.
        """
        return self.reward_repository.get_by_status(status)
    
    def get_reward_by_id(self, reward_id: int) -> Optional[Reward]:
        """
        Obtiene una recompensa por ID.
        
        Args:
            reward_id: ID de la recompensa.
        
        Returns:
            Recompensa si existe, None en caso contrario.
        """
        return self.reward_repository.get_by_id(reward_id)
    
    def update_reward(self, reward: Reward) -> Reward:
        """
        Actualiza una recompensa.
        
        Args:
            reward: Recompensa con los datos actualizados.
        
        Returns:
            Recompensa actualizada.
        """
        return self.reward_repository.update(reward)
    
    def delete_reward(self, reward_id: int) -> bool:
        """
        Elimina una recompensa.
        
        Args:
            reward_id: ID de la recompensa a eliminar.
        
        Returns:
            True si se eliminó correctamente.
        """
        return self.reward_repository.delete(reward_id)
    
    def update_reward_statuses(self):
        """
        Actualiza el estado de todas las recompensas basándose en los puntos actuales.
        Este método debe llamarse cuando cambien los puntos del usuario.
        """
        if not self.points_service:
            return
        
        current_points = self.points_service.get_total_points()
        all_rewards = self.reward_repository.get_all()
        
        for reward in all_rewards:
            # Solo actualizar recompensas que no estén reclamadas
            if reward.status == "reclamada":
                continue
            
            # Si los puntos alcanzan o superan el objetivo, cambiar a "a_reclamar"
            if current_points >= reward.target_points:
                if reward.status != "a_reclamar":
                    reward.status = "a_reclamar"
                    self.reward_repository.update(reward)
            else:
                # Si no se alcanzan los puntos, cambiar a "por_alcanzar"
                if reward.status != "por_alcanzar":
                    reward.status = "por_alcanzar"
                    self.reward_repository.update(reward)
    
    def claim_reward(self, reward_id: int, reuse: bool = False, new_target_points: Optional[float] = None) -> Reward:
        """
        Reclama una recompensa.
        
        Args:
            reward_id: ID de la recompensa a reclamar.
            reuse: Si True, reutiliza la recompensa con nuevos puntos objetivo.
            new_target_points: Nuevos puntos objetivo si se reutiliza.
        
        Returns:
            Recompensa actualizada.
        
        Raises:
            ValueError: Si la recompensa no está en estado "a_reclamar" o si los nuevos puntos no son válidos.
        """
        reward = self.reward_repository.get_by_id(reward_id)
        if not reward:
            raise ValueError(f"Recompensa con ID {reward_id} no encontrada")
        
        if reward.status != "a_reclamar":
            raise ValueError(f"La recompensa no está disponible para reclamar (estado: {reward.status})")
        
        if reuse:
            if new_target_points is None:
                raise ValueError("Se deben proporcionar nuevos puntos objetivo para reutilizar la recompensa")
            
            current_points = self.points_service.get_total_points() if self.points_service else 0
            if new_target_points <= current_points:
                raise ValueError(f"Los nuevos puntos objetivo ({new_target_points}) deben ser mayores a los puntos actuales ({current_points})")
            
            # Reutilizar: actualizar puntos objetivo y cambiar estado a "por_alcanzar"
            reward.target_points = new_target_points
            reward.status = "por_alcanzar"
            reward.claimed_at = None  # Limpiar fecha de reclamación anterior
        else:
            # Marcar como reclamada
            reward.status = "reclamada"
            reward.claimed_at = datetime.now()
        
        return self.reward_repository.update(reward)
    
    def is_reward_available(self, reward: Reward) -> bool:
        """
        Verifica si una recompensa está disponible para reclamar.
        
        Args:
            reward: Recompensa a verificar.
        
        Returns:
            True si está disponible, False en caso contrario.
        """
        if not self.points_service:
            return False
        
        current_points = self.points_service.get_total_points()
        return current_points >= reward.target_points and reward.status == "a_reclamar"

