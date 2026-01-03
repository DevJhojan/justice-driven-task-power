"""
Servicio de Progreso Local
Sistema de puntos y niveles sin requerir autenticación de usuarios
con persistencia en SQLite mediante DatabaseService.
"""

from datetime import datetime
from typing import Optional, Dict
from app.logic.system_points import PointsSystem, Level, LEVEL_POINTS, POINTS_BY_ACTION
from app.services.database_service import DatabaseService

PROGRESS_TABLE = "progress_state"
PROGRESS_ID = "global_progress"


class ProgressService:
    """Servicio singleton para gestionar el progreso local del usuario"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ProgressService, cls).__new__(cls)
        return cls._instance
    
    def __init__(self, database_service: Optional[DatabaseService] = None):
        """Inicializa el servicio de progreso"""
        if not ProgressService._initialized:
            self.current_points: float = 0.0
            self.current_level: Level = Level.NADIE
            self.total_actions: int = 0
            self.database_service: Optional[DatabaseService] = database_service
            self._db_ready: bool = False
            ProgressService._initialized = True
            print("[ProgressService] Servicio inicializado")
        elif database_service is not None:
            # Permitir adjuntar un DatabaseService después de la primera creación
            self.database_service = database_service

    # ------------------------------------------------------------------
    # Inicialización y persistencia
    # ------------------------------------------------------------------
    async def _ensure_db_ready(self):
        """Garantiza que la tabla y el estado estén listos en la base de datos"""
        if self._db_ready:
            return

        if self.database_service is None:
            self.database_service = DatabaseService()

        # Crear tabla si no existe
        await self.database_service.connect()
        create_query = f"""
        CREATE TABLE IF NOT EXISTS {PROGRESS_TABLE} (
            id TEXT PRIMARY KEY,
            current_points REAL NOT NULL DEFAULT 0,
            current_level TEXT NOT NULL DEFAULT 'Nadie',
            total_actions INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
        await self.database_service.execute(create_query)
        await self.database_service.commit()

        # Insertar registro base si no existe (evita violar UNIQUE)
        now = datetime.now().isoformat()
        await self.database_service.execute(
            f"""
            INSERT OR IGNORE INTO {PROGRESS_TABLE}
            (id, current_points, current_level, total_actions, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (PROGRESS_ID, self.current_points, self.current_level.value, self.total_actions, now, now),
        )
        await self.database_service.commit()

        # Cargar estado
        record = await self.database_service.get(PROGRESS_TABLE, PROGRESS_ID)
        if record:
            self.current_points = float(record.get("current_points", 0.0))
            try:
                self.current_level = Level(record.get("current_level", Level.NADIE.value))
            except Exception:
                self.current_level = Level.NADIE
            self.total_actions = int(record.get("total_actions", 0))

        self._db_ready = True

    async def _persist_state(self):
        """Guarda el estado actual en la base de datos"""
        if self.database_service is None:
            return
        now = datetime.now().isoformat()
        await self.database_service.execute(
            f"""
            INSERT INTO {PROGRESS_TABLE} (id, current_points, current_level, total_actions, created_at, updated_at)
            VALUES (?, ?, ?, ?, COALESCE((SELECT created_at FROM {PROGRESS_TABLE} WHERE id=?), ?), ?)
            ON CONFLICT(id) DO UPDATE SET
                current_points=excluded.current_points,
                current_level=excluded.current_level,
                total_actions=excluded.total_actions,
                updated_at=excluded.updated_at
            """,
            (
                PROGRESS_ID,
                self.current_points,
                self.current_level.value,
                self.total_actions,
                PROGRESS_ID,
                now,
                now,
            ),
        )
        await self.database_service.commit()

    async def ensure_persistence(self):
        """Punto de entrada público para preparar la BD"""
        await self._ensure_db_ready()
    
    async def add_points(self, action: str, amount: Optional[float] = None) -> Dict:
        """
        Añade puntos por una acción y persiste el estado
        
        Args:
            action: Tipo de acción realizada
            amount: Cantidad específica de puntos (opcional)
            
        Returns:
            Diccionario con información actualizada
        """
        await self._ensure_db_ready()

        old_level = self.current_level

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

        await self._persist_state()
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
    
    async def reset_progress(self):
        """Reinicia todo el progreso y lo persiste"""
        await self._ensure_db_ready()
        self.current_points = 0.0
        self.current_level = Level.NADIE
        self.total_actions = 0
        await self._persist_state()
        print("[ProgressService] Progreso reiniciado")
    
    async def set_points(self, points: float):
        """
        Establece manualmente los puntos y los persiste
        
        Args:
            points: Cantidad de puntos a establecer
        """
        await self._ensure_db_ready()
        self.current_points = points
        self.current_level = PointsSystem.get_level_by_points(self.current_points)
        await self._persist_state()
        print(f"[ProgressService] Puntos establecidos manualmente: {points:.2f} | Nivel: {self.current_level.value}")

    async def load_stats(self) -> Dict:
        """Asegura carga desde BD y retorna stats actuales"""
        await self._ensure_db_ready()
        return self.get_stats()
