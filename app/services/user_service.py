"""
Servicio de Usuario
Gestiona las operaciones relacionadas con usuarios
"""

from typing import Optional, Dict, Any
from app.models.user import User
from app.logic.system_levels import LevelManager
from app.logic.system_points import PointsSystem


class UserService:
    """Servicio para gestionar usuarios"""
    
    def __init__(self):
        """Inicializa el servicio"""
        self.users: Dict[str, User] = {}
        self.level_manager = LevelManager()
    
    def create_user(self, username: str, email: str = "") -> User:
        """
        Crea un nuevo usuario
        
        Args:
            username: Nombre de usuario
            email: Correo electrónico (opcional)
            
        Returns:
            Instancia de User creada
        """
        user = User(username=username, email=email)
        self.users[user.id] = user
        
        # Crear entrada en el nivel manager
        self.level_manager.get_or_create_user_level(user.id)
        
        return user
    
    def get_user(self, user_id: str) -> Optional[User]:
        """
        Obtiene un usuario por ID
        
        Args:
            user_id: ID del usuario
            
        Returns:
            Instancia de User o None
        """
        return self.users.get(user_id)
    
    def update_user(self, user_id: str, user_data: Dict[str, Any]) -> Optional[User]:
        """
        Actualiza un usuario
        
        Args:
            user_id: ID del usuario
            user_data: Datos a actualizar
            
        Returns:
            Usuario actualizado o None
        """
        user = self.get_user(user_id)
        if not user:
            return None
        
        if "username" in user_data:
            user.username = user_data["username"]
        if "email" in user_data:
            user.email = user_data["email"]
        if "is_active" in user_data:
            user.is_active = user_data["is_active"]
        
        return user
    
    def add_points_to_user(self, user_id: str, action: str, amount: Optional[float] = None) -> bool:
        """
        Añade puntos a un usuario y actualiza su nivel
        
        Args:
            user_id: ID del usuario
            action: Acción realizada
            amount: Cantidad de puntos (opcional)
            
        Returns:
            True si hubo cambio de nivel
        """
        user = self.get_user(user_id)
        if not user:
            return False
        
        # Añadir puntos al nivel manager
        level_up = self.level_manager.add_points(user_id, action, amount)
        
        # Actualizar puntos del usuario
        user_level_info = self.level_manager.get_user_level_info(user_id)
        user.points = user_level_info["current_points"]
        user.level = user_level_info["current_level"]
        
        return level_up
    
    def get_user_stats(self, user_id: str) -> Dict[str, Any]:
        """
        Obtiene las estadísticas completas del usuario
        
        Args:
            user_id: ID del usuario
            
        Returns:
            Diccionario con estadísticas
        """
        user = self.get_user(user_id)
        if not user:
            return {}
        
        level_info = self.level_manager.get_user_level_info(user_id)
        
        return {
            "user_id": user.id,
            "username": user.username,
            "email": user.email,
            "level": user.level,
            "points": user.points,
            "icon": PointsSystem.get_level_icon(PointsSystem.get_level_by_points(user.points)),
            "color": PointsSystem.get_level_color(PointsSystem.get_level_by_points(user.points)),
            "progress_percent": level_info["progress_percent"],
            "points_in_current_level": level_info["points_in_current_level"],
            "total_for_next_level": level_info["total_for_next_level"],
            "next_level": level_info["next_level"],
            "total_actions": level_info["total_actions"],
        }
    
    def get_all_users(self) -> list[User]:
        """
        Obtiene todos los usuarios
        
        Returns:
            Lista de usuarios
        """
        return list(self.users.values())
    
    def get_ranking(self, limit: int = 10) -> list[Dict[str, Any]]:
        """
        Obtiene el ranking de usuarios
        
        Args:
            limit: Cantidad máxima de usuarios
            
        Returns:
            Lista de usuarios en ranking
        """
        return self.level_manager.get_ranking(limit)
