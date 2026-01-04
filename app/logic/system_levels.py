"""
Sistema de Niveles
Gestiona la lógica de niveles y progresión del usuario
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from app.logic.system_points import Level, PointsSystem, LEVEL_POINTS, LEVELS_ORDER


@dataclass
class UserLevel:
    """Información de nivel del usuario"""
    user_id: str
    current_points: float = 0.0
    current_level: Level = Level.NADIE
    previous_level: Level = Level.NADIE
    level_reached_at: datetime = field(default_factory=datetime.now)
    total_actions: int = 0
    
    def __post_init__(self):
        """Actualiza el nivel basado en puntos"""
        self.current_level = PointsSystem.get_level_by_points(self.current_points)
    
    def get_progress_percent(self) -> float:
        """
        Obtiene el porcentaje de progreso hacia el siguiente nivel
        
        Returns:
            Porcentaje (0-100)
        """
        points_in_current, total_for_next = PointsSystem.get_progress_to_next_level(self.current_points)
        
        if total_for_next == 0:
            return 100.0  # Máximo nivel alcanzado
        
        return (points_in_current / total_for_next) * 100.0
    
    def add_points(self, action: str, amount: Optional[float] = None) -> bool:
        """
        Añade puntos y verifica promoción de nivel
        
        Args:
            action: Acción realizada
            amount: Cantidad de puntos (opcional, usa POINTS_BY_ACTION si no se proporciona)
            
        Returns:
            True si se subió de nivel, False si no
        """
        old_level = self.current_level
        
        if amount is not None:
            self.current_points += amount
            print(f"[UserLevel] Añadiendo {amount} puntos manualmente")
        else:
            old_points = self.current_points
            self.current_points = PointsSystem.add_points(self.current_points, action)
            points_added = self.current_points - old_points
            print(f"[UserLevel] Acción '{action}': Puntos previos: {old_points}, Puntos añadidos: {points_added}, Puntos totales: {self.current_points}")
        
        self.current_level = PointsSystem.get_level_by_points(self.current_points)
        self.total_actions += 1
        
        # Verificar si hay promoción
        if self.current_level != old_level:
            self.previous_level = old_level
            self.level_reached_at = datetime.now()
            print(f"[UserLevel] ¡CAMBIO DE NIVEL! De {old_level.value} a {self.current_level.value}")
            return True
        
        return False
    
    def is_level_up(self, old_level: Level) -> bool:
        """
        Verifica si hubo cambio de nivel
        
        Args:
            old_level: Nivel anterior
            
        Returns:
            True si subió de nivel
        """
        return self.current_level != old_level
    
    def to_dict(self) -> dict:
        """Convierte a diccionario"""
        return {
            "user_id": self.user_id,
            "current_points": self.current_points,
            "current_level": self.current_level.value,
            "previous_level": self.previous_level.value,
            "level_reached_at": self.level_reached_at.isoformat(),
            "total_actions": self.total_actions,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'UserLevel':
        """Crea desde diccionario"""
        return cls(
            user_id=data["user_id"],
            current_points=data.get("current_points", 0.0),
            current_level=Level(data.get("current_level", Level.NADIE.value)),
            previous_level=Level(data.get("previous_level", Level.NADIE.value)),
            level_reached_at=datetime.fromisoformat(data.get("level_reached_at", datetime.now().isoformat())),
            total_actions=data.get("total_actions", 0),
        )


class LevelManager:
    """Gestor centralizado de niveles de usuarios"""
    
    def __init__(self):
        """Inicializa el gestor"""
        self.user_levels: dict[str, UserLevel] = {}
    
    def get_or_create_user_level(self, user_id: str) -> UserLevel:
        """
        Obtiene o crea el nivel de un usuario
        
        Args:
            user_id: ID del usuario
            
        Returns:
            UserLevel del usuario
        """
        if user_id not in self.user_levels:
            self.user_levels[user_id] = UserLevel(user_id=user_id)
        return self.user_levels[user_id]
    
    def add_points(self, user_id: str, action: str, amount: Optional[float] = None) -> bool:
        """
        Añade puntos a un usuario
        
        Args:
            user_id: ID del usuario
            action: Acción realizada
            amount: Cantidad (opcional)
            
        Returns:
            True si hubo promoción de nivel
        """
        user_level = self.get_or_create_user_level(user_id)
        return user_level.add_points(action, amount)
    
    def get_user_level_info(self, user_id: str) -> dict:
        """
        Obtiene información completa del nivel del usuario
        
        Args:
            user_id: ID del usuario
            
        Returns:
            Diccionario con información
        """
        user_level = self.get_or_create_user_level(user_id)
        points_in_current, total_for_next = PointsSystem.get_progress_to_next_level(user_level.current_points)
        next_level = PointsSystem.get_next_level(user_level.current_level)
        
        return {
            "user_id": user_id,
            "current_level": user_level.current_level.value,
            "current_points": user_level.current_points,
            "level_icon": PointsSystem.get_level_icon(user_level.current_level),
            "level_color": PointsSystem.get_level_color(user_level.current_level),
            "progress_percent": user_level.get_progress_percent(),
            "points_in_current_level": points_in_current,
            "total_for_next_level": total_for_next,
            "next_level": next_level.value if next_level else None,
            "next_level_points": LEVEL_POINTS.get(next_level, 0) if next_level else None,
            "total_actions": user_level.total_actions,
        }
    
    def get_ranking(self, limit: int = 10) -> list[dict]:
        """
        Obtiene el ranking de usuarios por puntos
        
        Args:
            limit: Cantidad máxima de usuarios
            
        Returns:
            Lista de usuarios ordenados por puntos
        """
        sorted_users = sorted(
            self.user_levels.values(),
            key=lambda x: x.current_points,
            reverse=True
        )
        
        return [
            {
                "rank": idx + 1,
                "user_id": user.user_id,
                "level": user.current_level.value,
                "points": user.current_points,
                "icon": PointsSystem.get_level_icon(user.current_level),
            }
            for idx, user in enumerate(sorted_users[:limit])
        ]
