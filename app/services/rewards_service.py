"""
Servicio de Recompensas
Gestiona las operaciones CRUD de recompensas con persistencia en BD
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
import asyncio
from app.models.reward import Reward
from app.services.database_service import DatabaseService


class RewardsService:
    """Servicio para gestionar recompensas con persistencia en BD"""
    
    def __init__(self, database_service: Optional[DatabaseService] = None):
        """
        Inicializa el servicio
        
        Args:
            database_service: Servicio de base de datos (opcional)
        """
        self.rewards: Dict[str, Reward] = {}
        self.database_service = database_service or DatabaseService()
        self._initialized = False
        self._valid_categories = {
            "Recompensas pequeñas",
            "Recompensas medianas",
            "Recompensas grandes",
            "Recompensas épicas",
        }
    
    async def initialize(self):
        """Inicializa la BD y carga las recompensas existentes"""
        if self._initialized:
            return
        
        try:
            await self.database_service.connect()
            
            # Crear tabla si no existe
            await self.database_service.execute("""
                CREATE TABLE IF NOT EXISTS rewards (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    description TEXT,
                    points_required REAL NOT NULL,
                    icon TEXT,
                    color TEXT,
                    is_active INTEGER DEFAULT 1,
                    category TEXT,
                    claimed INTEGER DEFAULT 0,
                    created_at TEXT,
                    updated_at TEXT
                )
            """)
            await self.database_service.commit()
            
            # Cargar recompensas desde BD
            await self._load_from_db()

            # Migrar recompensas existentes a las categorías actuales
            await self._migrate_rewards_data()
            
            # Agregar recompensas por defecto si no hay ninguna
            await self._ensure_default_rewards()
            
            self._initialized = True
            print("[RewardsService] BD inicializada y cargada")
        except Exception as e:
            print(f"[RewardsService] Error al inicializar: {e}")
    
    async def _load_from_db(self):
        """Carga todas las recompensas desde la base de datos"""
        try:
            rewards = await self.database_service.get_all("rewards")
            self.rewards.clear()
            for reward_dict in rewards:
                reward = Reward.from_dict(reward_dict)
                self.rewards[reward.id] = reward
            print(f"[RewardsService] Cargadas {len(self.rewards)} recompensas desde BD")
        except Exception as e:
            print(f"[RewardsService] Error al cargar desde BD: {e}")
    
    async def _ensure_default_rewards(self):
        """Agrega las recompensas por defecto si no existen"""
        if len(self.rewards) > 0:
            return
        
        defaults = [
            {
                "title": "Insignia Novato",
                "description": "Completa tu primera tarea",
                "points_required": 1.0,
                "icon": "🎖️",
                "color": "#4CAF50",
                "is_active": True,
                "category": "Recompensas pequeñas",
            },
            {
                "title": "Racha de Productividad",
                "description": "Completa 5 tareas",
                "points_required": 5.0,
                "icon": "🔥",
                "color": "#FF9800",
                "is_active": True,
                "category": "Recompensas medianas",
            },
            {
                "title": "Maestro del Tiempo",
                "description": "Completa 10 tareas a tiempo",
                "points_required": 10.0,
                "icon": "⏱️",
                "color": "#2196F3",
                "is_active": True,
                "category": "Recompensas grandes",
            },
        ]
        
        for data in defaults:
            reward = Reward.from_dict(data)
            self.rewards[reward.id] = reward
            try:
                db_data = reward.to_dict()
                await self.database_service.create("rewards", db_data)
            except Exception as e:
                print(f"[RewardsService] Error al guardar recompensa por defecto: {e}")
        
        print(f"[RewardsService] Agregadas {len(defaults)} recompensas por defecto")
    
    def create_reward(self, reward_data: Dict[str, Any]) -> Reward:
        """
        Crea una nueva recompensa (versión síncrona)
        
        Args:
            reward_data: Diccionario con datos de la recompensa
            
        Returns:
            Instancia de Reward creada
        """
        reward = Reward.from_dict(reward_data)
        self.rewards[reward.id] = reward
        
        try:
            # Guardar en BD de forma asíncrona
            asyncio.create_task(self._save_to_db(reward))
        except Exception as e:
            print(f"[RewardsService] Error al agendar guardado en BD: {e}")
        
        return reward
    
    async def _save_to_db(self, reward: Reward):
        """Guarda una recompensa en BD de forma asíncrona"""
        try:
            db_data = reward.to_dict()
            await self.database_service.create("rewards", db_data)
            print(f"[RewardsService] Recompensa '{reward.title}' guardada en BD")
        except Exception as e:
            print(f"[RewardsService] Error al guardar en BD: {e}")
    
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
        
        try:
            # Actualizar en BD de forma asíncrona
            asyncio.create_task(self._update_in_db(reward_id, reward))
        except Exception as e:
            print(f"[RewardsService] Error al agendar actualización en BD: {e}")
        
        return reward

    async def _migrate_rewards_data(self):
        """Normaliza recompensas existentes a las categorías actuales y persiste cambios."""
        if not self.rewards:
            return

        legacy_map = {
            "badge": "Recompensas pequeñas",
            "achievement": "Recompensas medianas",
            "milestone": "Recompensas grandes",
            None: "Recompensas pequeñas",
            "": "Recompensas pequeñas",
        }

        updated = 0
        for reward in list(self.rewards.values()):
            new_category = legacy_map.get(reward.category, reward.category)
            if new_category not in self._valid_categories:
                new_category = "Recompensas pequeñas"

            if new_category != reward.category:
                reward.update(category=new_category)
                self.rewards[reward.id] = reward
                try:
                    await self.database_service.update("rewards", reward.id, reward.to_dict())
                    updated += 1
                except Exception as e:
                    print(f"[RewardsService] Error al migrar recompensa '{reward.title}': {e}")

        if updated:
            print(f"[RewardsService] Migradas {updated} recompensas a las nuevas categorías")
    
    async def _update_in_db(self, reward_id: str, reward: Reward):
        """Actualiza una recompensa en BD de forma asíncrona"""
        try:
            db_data = reward.to_dict()
            await self.database_service.update("rewards", reward_id, db_data)
            print(f"[RewardsService] Recompensa '{reward.title}' actualizada en BD")
        except Exception as e:
            print(f"[RewardsService] Error al actualizar en BD: {e}")
    
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
            
            try:
                # Eliminar de BD de forma asíncrona
                asyncio.create_task(self._delete_from_db(reward_id))
            except Exception as e:
                print(f"[RewardsService] Error al agendar eliminación en BD: {e}")
            
            return True
        return False
    
    async def _delete_from_db(self, reward_id: str):
        """Elimina una recompensa de BD de forma asíncrona"""
        try:
            await self.database_service.delete("rewards", reward_id)
            print(f"[RewardsService] Recompensa eliminada de BD")
        except Exception as e:
            print(f"[RewardsService] Error al eliminar de BD: {e}")
    
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
