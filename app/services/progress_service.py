"""
Servicio de Progreso Local
Sistema de puntos y niveles sin requerir autenticación de usuarios
"""

from typing import Optional, Dict
from app.logic.system_points import PointsSystem, Level, LEVEL_POINTS, POINTS_BY_ACTION


class ProgressService:
    """Servicio singleton para gestionar el progreso local del usuario"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ProgressService, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Inicializa el servicio de progreso"""
        if not ProgressService._initialized:
            self.current_points: float = 0.0
            self.current_level: Level = Level.NADIE
            self.total_actions: int = 0
            ProgressService._initialized = True
            print("[ProgressService] Servicio inicializado")
    
    def add_points(self, action: str, amount: Optional[float] = None) -> Dict:
        """
        Añade puntos por una acción
        
        Args:
            action: Tipo de acción realizada
            amount: Cantidad específica de puntos (opcional)
            
        Returns:
            Diccionario con información actualizada
        """
        old_level = self.current_level
        old_points = self.current_points
        
        # Añadir puntos
        if amount is not None:
            points_added = amount
            self.current_points += amount
        else:
            points_added = POINTS_BY_ACTION.get(action, 0.0)
            self.current_points += points_added
        
        # Actualizar nivel
        self.current_level = PointsSystem.get_level_by_points(self.current_points)
        self.total_actions += 1
        
        # Verificar si hubo cambio de nivel
        level_up = self.current_level != old_level
        
        print(f"[ProgressService] Acción '{action}': +{points_added} puntos | Total: {self.current_points:.2f}")
        
        if level_up:
            print(f"[ProgressService] ¡NIVEL SUBIDO! {old_level.value} → {self.current_level.value}")
        
        return self.get_stats(include_level_up=level_up, old_level=old_level)
    
    def get_stats(self, include_level_up: bool = False, old_level: Optional[Level] = None) -> Dict:
        """
        Obtiene las estadísticas actuales
        
        Args:
            include_level_up: Si incluir información de subida de nivel
            old_level: Nivel anterior (si hubo subida)
            
        Returns:
            Diccionario con todas las estadísticas
        """
        points_in_current, total_for_next = PointsSystem.get_progress_to_next_level(self.current_points)
        next_level = PointsSystem.get_next_level(self.current_level)
        
        progress_percent = 0.0
        if total_for_next > 0:
            progress_percent = (points_in_current / total_for_next) * 100.0
        elif next_level is None:
            progress_percent = 100.0  # Nivel máximo
        
        stats = {
            "points": self.current_points,
            "level": self.current_level.value,
            "level_icon": PointsSystem.get_level_icon(self.current_level),
            "level_color": PointsSystem.get_level_color(self.current_level),
            "progress_percent": progress_percent,
            "points_in_current_level": points_in_current,
            "total_for_next_level": total_for_next,
            "next_level": next_level.value if next_level else None,
            "next_level_points": LEVEL_POINTS.get(next_level, 0) if next_level else None,
            "total_actions": self.total_actions,
        }
        
        if include_level_up and old_level:
            stats["level_up"] = True
            stats["old_level"] = old_level.value
        
        return stats
    
    def reset_progress(self):
        """Reinicia todo el progreso"""
        self.current_points = 0.0
        self.current_level = Level.NADIE
        self.total_actions = 0
        print("[ProgressService] Progreso reiniciado")
    
    def set_points(self, points: float):
        """
        Establece manualmente los puntos
        
        Args:
            points: Cantidad de puntos a establecer
        """
        self.current_points = points
        self.current_level = PointsSystem.get_level_by_points(self.current_points)
        print(f"[ProgressService] Puntos establecidos manualmente: {points:.2f} | Nivel: {self.current_level.value}")
