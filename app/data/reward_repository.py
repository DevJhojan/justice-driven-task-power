"""
Repositorio para gestión de recompensas en SQLite.
"""
from datetime import datetime
from typing import List, Optional

from app.data.database import Database
from app.data.models import Reward


class RewardRepository:
    """Repositorio para operaciones CRUD de recompensas."""
    
    def __init__(self, db: Database):
        """
        Inicializa el repositorio.
        
        Args:
            db: Instancia de Database.
        """
        self.db = db
    
    def create(self, reward: Reward) -> Reward:
        """
        Crea una nueva recompensa.
        
        Args:
            reward: Recompensa a crear.
        
        Returns:
            Recompensa creada con ID asignado.
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        now = datetime.now().isoformat()
        created_at = reward.created_at.isoformat() if reward.created_at else now
        
        cursor.execute("""
            INSERT INTO rewards (name, description, target_points, status, created_at, claimed_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            reward.name,
            reward.description,
            reward.target_points,
            reward.status,
            created_at,
            reward.claimed_at.isoformat() if reward.claimed_at else None
        ))
        
        reward_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return Reward(
            id=reward_id,
            name=reward.name,
            description=reward.description,
            target_points=reward.target_points,
            status=reward.status,
            created_at=reward.created_at,
            claimed_at=reward.claimed_at
        )
    
    def get_all(self) -> List[Reward]:
        """
        Obtiene todas las recompensas.
        
        Returns:
            Lista de recompensas.
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, name, description, target_points, status, created_at, claimed_at
            FROM rewards
            ORDER BY target_points ASC, created_at ASC
        """)
        
        rows = cursor.fetchall()
        conn.close()
        
        rewards = []
        for row in rows:
            created_at = datetime.fromisoformat(row['created_at']) if row['created_at'] else None
            claimed_at = datetime.fromisoformat(row['claimed_at']) if row['claimed_at'] else None
            
            rewards.append(Reward(
                id=row['id'],
                name=row['name'],
                description=row['description'],
                target_points=row['target_points'],
                status=row['status'],
                created_at=created_at,
                claimed_at=claimed_at
            ))
        
        return rewards
    
    def get_by_id(self, reward_id: int) -> Optional[Reward]:
        """
        Obtiene una recompensa por ID.
        
        Args:
            reward_id: ID de la recompensa.
        
        Returns:
            Recompensa si existe, None en caso contrario.
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, name, description, target_points, status, created_at, claimed_at
            FROM rewards
            WHERE id = ?
        """, (reward_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        
        created_at = datetime.fromisoformat(row['created_at']) if row['created_at'] else None
        claimed_at = datetime.fromisoformat(row['claimed_at']) if row['claimed_at'] else None
        
        return Reward(
            id=row['id'],
            name=row['name'],
            description=row['description'],
            target_points=row['target_points'],
            status=row['status'],
            created_at=created_at,
            claimed_at=claimed_at
        )
    
    def get_by_status(self, status: str) -> List[Reward]:
        """
        Obtiene recompensas por estado.
        
        Args:
            status: Estado de la recompensa (por_alcanzar, a_reclamar, reclamada).
        
        Returns:
            Lista de recompensas con el estado especificado.
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, name, description, target_points, status, created_at, claimed_at
            FROM rewards
            WHERE status = ?
            ORDER BY target_points ASC, created_at ASC
        """, (status,))
        
        rows = cursor.fetchall()
        conn.close()
        
        rewards = []
        for row in rows:
            created_at = datetime.fromisoformat(row['created_at']) if row['created_at'] else None
            claimed_at = datetime.fromisoformat(row['claimed_at']) if row['claimed_at'] else None
            
            rewards.append(Reward(
                id=row['id'],
                name=row['name'],
                description=row['description'],
                target_points=row['target_points'],
                status=row['status'],
                created_at=created_at,
                claimed_at=claimed_at
            ))
        
        return rewards
    
    def update(self, reward: Reward) -> Reward:
        """
        Actualiza una recompensa existente.
        
        Args:
            reward: Recompensa con los datos actualizados.
        
        Returns:
            Recompensa actualizada.
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE rewards
            SET name = ?, description = ?, target_points = ?, status = ?, claimed_at = ?
            WHERE id = ?
        """, (
            reward.name,
            reward.description,
            reward.target_points,
            reward.status,
            reward.claimed_at.isoformat() if reward.claimed_at else None,
            reward.id
        ))
        
        conn.commit()
        conn.close()
        
        return reward
    
    def delete(self, reward_id: int) -> bool:
        """
        Elimina una recompensa.
        
        Args:
            reward_id: ID de la recompensa a eliminar.
        
        Returns:
            True si se eliminó correctamente, False en caso contrario.
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM rewards WHERE id = ?", (reward_id,))
        
        deleted = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        return deleted

