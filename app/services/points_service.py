"""
Servicio para gestión de puntos y niveles del usuario.
"""
from enum import Enum
from typing import Tuple

from app.data.database import Database


class SkillLevel(Enum):
    """Niveles de habilidad basados en puntos."""
    NOBODY = ("Nobody", 0)
    BEGINNER = ("Beginner", 10)
    NOVICE = ("Novice", 100)
    INTERMEDIATE = ("Intermediate", 500)
    PROFICIENT = ("Proficient", 1000)
    ADVANCE = ("Advance", 5000)
    EXPERT = ("Expert", 10000)
    MASTER = ("Master", 50000)
    GURU = ("Guru", 100000)
    LEGENDARY = ("Legendary", 500000)
    LIKE_A_GOD = ("Like_a_God", 1000000)
    
    def __init__(self, display_name: str, min_points: int):
        self.display_name = display_name
        self.min_points = min_points
    
    @classmethod
    def from_points(cls, points: float) -> Tuple['SkillLevel', float]:
        """
        Obtiene el nivel basado en los puntos recibidos con sistema flotante.
        
        Args:
            points: Puntos totales del usuario.
        
        Returns:
            Tupla (nivel_base, subnivel_flotante)
        """
        if points <= 10:
            return cls.NOBODY, max(0.0, points / 10.0)
        if points <= 100:
            return cls.BEGINNER, 1.0 + ((points - 10) / 90.0)
        if points <= 500:
            return cls.NOVICE, 1.0 + ((points - 100) / 400.0)
        if points <= 1000:
            return cls.INTERMEDIATE, 1.0 + ((points - 500) / 500.0)
        if points <= 5000:
            return cls.PROFICIENT, 1.0 + ((points - 1000) / 4000.0)
        if points <= 10000:
            return cls.ADVANCE, 1.0 + ((points - 5000) / 5000.0)
        if points <= 50000:
            return cls.EXPERT, 1.0 + ((points - 10000) / 40000.0)
        if points <= 100000:
            return cls.MASTER, 1.0 + ((points - 50000) / 50000.0)
        if points <= 500000:
            return cls.GURU, 1.0 + ((points - 100000) / 400000.0)
        if points <= 1000000:
            return cls.LEGENDARY, 1.0 + ((points - 500000) / 500000.0)
        if points > 1000000:
            # Para Like_a_God, cada millón adicional es un subnivel
            return cls.LIKE_A_GOD, 1.0 + ((points - 1000000) / 1000000.0)
        else:
            return cls.NOBODY, 0.0
    
    def get_next_level(self) -> Tuple['SkillLevel', float]:
        """
        Obtiene el siguiente nivel y los puntos necesarios para alcanzarlo.
        
        Returns:
            Tupla (siguiente_nivel, puntos_necesarios)
        """
        levels = list(SkillLevel)
        current_index = levels.index(self)
        
        if current_index < len(levels) - 1:
            next_level = levels[current_index + 1]
            points_needed = float(next_level.min_points)
            return next_level, points_needed
        else:
            # Ya está en el nivel más alto
            return self, 0.0
    
    def get_display_name_with_sublevel(self, sublevel: float) -> str:
        """
        Obtiene el nombre del nivel con el subnivel flotante.
        
        Args:
            sublevel: Subnivel flotante (ej: 1.5, 2.3)
        
        Returns:
            Nombre completo del nivel (ej: "Beginner 1.50")
        """
        # Formatear el subnivel con 2 decimales
        sublevel_str = f"{sublevel:.2f}"
        return f"{self.display_name} {sublevel_str}"


class PointsService:
    """Servicio para gestionar puntos del usuario."""
    
    def __init__(self, db: Database):
        """
        Inicializa el servicio de puntos.
        
        Args:
            db: Instancia de Database.
        """
        self.db = db
        self._init_points_table()
    
    def _init_points_table(self):
        """Inicializa la tabla de puntos si no existe."""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_points (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                total_points REAL NOT NULL DEFAULT 0,
                last_updated TEXT
            )
        """)
        
        # Inicializar con 0 puntos si no existe
        cursor.execute("SELECT COUNT(*) as count FROM user_points")
        row = cursor.fetchone()
        if row['count'] == 0:
            from datetime import datetime
            cursor.execute("""
                INSERT INTO user_points (total_points, last_updated)
                VALUES (0, ?)
            """, (datetime.now().isoformat(),))
        
        conn.commit()
        conn.close()
    
    def get_total_points(self) -> float:
        """
        Obtiene el total de puntos del usuario.
        
        Returns:
            Total de puntos acumulados.
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT total_points FROM user_points ORDER BY id DESC LIMIT 1")
        row = cursor.fetchone()
        conn.close()
        
        return float(row['total_points']) if row else 0.0
    
    def add_points(self, points: float) -> float:
        """
        Agrega puntos al total del usuario.
        
        Args:
            points: Puntos a agregar (puede ser negativo).
        
        Returns:
            Nuevo total de puntos.
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        current_points = self.get_total_points()
        new_total = max(0.0, current_points + float(points))  # No permitir puntos negativos
        
        from datetime import datetime
        cursor.execute("""
            UPDATE user_points
            SET total_points = ?, last_updated = ?
            WHERE id = (SELECT id FROM user_points ORDER BY id DESC LIMIT 1)
        """, (new_total, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
        
        return new_total
    
    def get_level(self) -> Tuple[SkillLevel, float]:
        """
        Obtiene el nivel actual del usuario basado en sus puntos.
        
        Returns:
            Tupla (nivel_base, subnivel_flotante)
        """
        points = self.get_total_points()
        return SkillLevel.from_points(points)
    
    def get_level_info(self) -> dict:
        """
        Obtiene información completa del nivel actual con sistema flotante.
        
        Returns:
            Diccionario con nivel actual, puntos, siguiente nivel, etc.
        """
        points = self.get_total_points()
        current_level, sublevel = SkillLevel.from_points(points)
        next_level, points_needed = current_level.get_next_level()
        
        # Calcular progreso hacia el siguiente nivel
        progress = 0.0
        if current_level != SkillLevel.LIKE_A_GOD:
            current_min = float(current_level.min_points)
            if next_level != current_level:
                next_min = float(next_level.min_points)
                if next_min > current_min:
                    progress = ((points - current_min) / (next_min - current_min)) * 100.0
                    progress = min(100.0, max(0.0, progress))
            else:
                # Si estamos en el último subnivel del nivel actual
                progress = 100.0
        
        # Calcular puntos hacia el siguiente nivel
        points_to_next = 0.0
        if current_level != SkillLevel.LIKE_A_GOD and next_level != current_level:
            points_to_next = max(0.0, points_needed - points)
        elif current_level == SkillLevel.LIKE_A_GOD:
            # Para Like_a_God, el siguiente subnivel es cada millón adicional
            current_millions = (points - 1000000.0) / 1000000.0
            next_millions = int(current_millions) + 1
            points_to_next = (1000000.0 * next_millions) - points
        
        return {
            "current_level": current_level,
            "sublevel": sublevel,
            "level_display_name": current_level.get_display_name_with_sublevel(sublevel),
            "points": points,
            "next_level": next_level,
            "points_needed": points_needed,
            "progress": progress,
            "points_to_next": points_to_next
        }

