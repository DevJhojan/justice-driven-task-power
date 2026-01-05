"""
Sistema de Puntos
Define los puntos requeridos para cada nivel del sistema de gamificación
"""

from enum import Enum
from typing import Optional


class Level(Enum):
    """Niveles del sistema de gamificación"""
    NADIE = "Nadie"
    DESCONOCIDO = "Desconocido"
    NOVATO = "Novato"
    CONOCIDO = "Conocido"
    RESPETADO = "Respetado"
    INFLUYENTE = "Influyente"
    LIDER = "Líder"
    LEGENDARIO = "Legendario"
    TODOPODEROSO = "Todopoderoso"
    COMO_DIOS = "Como Dios"


# Mapeo de niveles a puntos requeridos
LEVEL_POINTS = {
    Level.NADIE: 0.0,
    Level.DESCONOCIDO: 50.0,
    Level.NOVATO: 100.0,
    Level.CONOCIDO: 500.0,
    Level.RESPETADO: 1000.0,
    Level.INFLUYENTE: 5000.0,
    Level.LIDER: 10000.0,
    Level.LEGENDARIO: 50000.0,
    Level.TODOPODEROSO: 100000.0,
    Level.COMO_DIOS: 500000.0,
}

# Orden de niveles
LEVELS_ORDER = [
    Level.NADIE,
    Level.DESCONOCIDO,
    Level.NOVATO,
    Level.CONOCIDO,
    Level.RESPETADO,
    Level.INFLUYENTE,
    Level.LIDER,
    Level.LEGENDARIO,
    Level.TODOPODEROSO,
    Level.COMO_DIOS,
]

# Puntos por acciones (personalizables)
POINTS_BY_ACTION = {
    "task_completed": 0.05,
    "subtask_completed": 0.02,
    "habit_daily_completed": 0.01,
    "habit_weekly_completed": 0.02,
    "habit_monthly_completed": 0.04,
    "habit_semiannual_completed": 0.06,
    "habit_annual_completed": 0.12,
    "goal_achieved": 0.50,
    "daily_streak": 0.10,
}

# Colores para cada nivel
LEVEL_COLORS = {
    Level.NADIE: "#808080",           # Gris
    Level.DESCONOCIDO: "#8B7355",     # Marrón
    Level.NOVATO: "#4CAF50",          # Verde claro
    Level.CONOCIDO: "#2196F3",        # Azul
    Level.RESPETADO: "#9C27B0",       # Púrpura
    Level.INFLUYENTE: "#FF6F00",      # Naranja oscuro
    Level.LIDER: "#F44336",           # Rojo
    Level.LEGENDARIO: "#FFD700",      # Oro
    Level.TODOPODEROSO: "#E91E63",    # Rosa
    Level.COMO_DIOS: "#9C27B0",       # Púrpura real
}

# Iconos para cada nivel (emojis)
LEVEL_ICONS = {
    Level.NADIE: "👤",
    Level.DESCONOCIDO: "🔍",
    Level.NOVATO: "🌱",
    Level.CONOCIDO: "📚",
    Level.RESPETADO: "🏆",
    Level.INFLUYENTE: "⭐",
    Level.LIDER: "👑",
    Level.LEGENDARIO: "🔥",
    Level.TODOPODEROSO: "⚡",
    Level.COMO_DIOS: "🌟",
}


class PointsSystem:
    """Sistema de gestión de puntos y niveles"""
    
    @staticmethod
    def get_level_by_points(points: float) -> Level:
        """
        Obtiene el nivel actual basado en los puntos
        
        Args:
            points: Puntos totales del usuario
            
        Returns:
            Level correspondiente
        """
        level = Level.NADIE
        for lvl in LEVELS_ORDER:
            if points >= LEVEL_POINTS[lvl]:
                level = lvl
            else:
                break
        return level
    
    @staticmethod
    def get_points_for_level(level: Level) -> float:
        """
        Obtiene los puntos requeridos para un nivel
        
        Args:
            level: Nivel
            
        Returns:
            Puntos requeridos
        """
        return LEVEL_POINTS.get(level, 0.0)
    
    @staticmethod
    def get_next_level(current_level: Level) -> Optional[Level]:
        """
        Obtiene el siguiente nivel
        
        Args:
            current_level: Nivel actual
            
        Returns:
            Siguiente nivel o None si es el último
        """
        try:
            current_index = LEVELS_ORDER.index(current_level)
            if current_index < len(LEVELS_ORDER) - 1:
                return LEVELS_ORDER[current_index + 1]
        except ValueError:
            pass
        return None
    
    @staticmethod
    def get_points_to_next_level(current_points: float) -> float:
        """
        Obtiene los puntos faltantes para el siguiente nivel
        
        Args:
            current_points: Puntos actuales
            
        Returns:
            Puntos faltantes para el siguiente nivel
        """
        current_level = PointsSystem.get_level_by_points(current_points)
        next_level = PointsSystem.get_next_level(current_level)
        
        if next_level is None:
            return 0.0  # Ya está en el máximo nivel
        
        next_points = LEVEL_POINTS[next_level]
        return max(0.0, next_points - current_points)
    
    @staticmethod
    def get_progress_to_next_level(current_points: float) -> tuple[float, float]:
        """
        Obtiene el progreso hacia el siguiente nivel
        
        Args:
            current_points: Puntos actuales
            
        Returns:
            Tupla (puntos_en_nivel_actual, puntos_totales_para_siguiente)
        """
        current_level = PointsSystem.get_level_by_points(current_points)
        current_level_points = LEVEL_POINTS[current_level]
        next_level = PointsSystem.get_next_level(current_level)
        
        if next_level is None:
            return (current_points - current_level_points, 0.0)
        
        next_level_points = LEVEL_POINTS[next_level]
        points_in_current = current_points - current_level_points
        total_for_next = next_level_points - current_level_points
        
        return (points_in_current, total_for_next)
    
    @staticmethod
    def add_points(current_points: float, action: str) -> float:
        """
        Añade puntos basados en una acción
        
        Args:
            current_points: Puntos actuales
            action: Acción realizada (key en POINTS_BY_ACTION)
            
        Returns:
            Nuevos puntos totales
        """
        points_to_add = POINTS_BY_ACTION.get(action, 0)
        return current_points + points_to_add
    
    @staticmethod
    def get_level_color(level: Level) -> str:
        """
        Obtiene el color para un nivel
        
        Args:
            level: Nivel
            
        Returns:
            Color en formato hex
        """
        return LEVEL_COLORS.get(level, "#808080")
    
    @staticmethod
    def get_level_icon(level: Level) -> str:
        """
        Obtiene el icono para un nivel
        
        Args:
            level: Nivel
            
        Returns:
            Emoji/icono
        """
        return LEVEL_ICONS.get(level, "👤")
