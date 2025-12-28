"""
Repositorio para gestión de metas en la base de datos.
"""
import sqlite3
from datetime import datetime
from typing import List, Optional

from app.data.database import Database
from app.data.models import Goal


class GoalRepository:
    """Repositorio para operaciones CRUD de metas."""
    
    def __init__(self, db: Database):
        """
        Inicializa el repositorio.
        
        Args:
            db: Instancia de Database.
        """
        self.db = db
    
    def create(self, goal: Goal) -> Goal:
        """
        Crea una nueva meta.
        
        Args:
            goal: Meta a crear (id debe ser None).
        
        Returns:
            Meta creada con el id asignado.
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        now = datetime.now().isoformat()
        cursor.execute("""
            INSERT INTO goals (title, description, target_value, current_value, unit, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            goal.title,
            goal.description,
            goal.target_value,
            goal.current_value,
            goal.unit,
            now,
            now
        ))
        
        goal_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        goal.id = goal_id
        goal.created_at = datetime.fromisoformat(now)
        goal.updated_at = datetime.fromisoformat(now)
        return goal
    
    def get_by_id(self, goal_id: int) -> Optional[Goal]:
        """
        Obtiene una meta por su ID.
        
        Args:
            goal_id: ID de la meta.
        
        Returns:
            Meta si existe, None en caso contrario.
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM goals WHERE id = ?", (goal_id,))
        row = cursor.fetchone()
        conn.close()
        
        return self._row_to_goal(row) if row else None
    
    def get_all(self) -> List[Goal]:
        """
        Obtiene todas las metas.
        
        Returns:
            Lista de todas las metas.
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM goals ORDER BY created_at DESC")
        rows = cursor.fetchall()
        conn.close()
        
        return [self._row_to_goal(row) for row in rows]
    
    def update(self, goal: Goal) -> Goal:
        """
        Actualiza una meta existente.
        
        Args:
            goal: Meta a actualizar (debe tener id).
        
        Returns:
            Meta actualizada.
        """
        if goal.id is None:
            raise ValueError("La meta debe tener un id para ser actualizada")
        
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        now = datetime.now().isoformat()
        cursor.execute("""
            UPDATE goals
            SET title = ?, description = ?, target_value = ?, current_value = ?, unit = ?, updated_at = ?
            WHERE id = ?
        """, (
            goal.title,
            goal.description,
            goal.target_value,
            goal.current_value,
            goal.unit,
            now,
            goal.id
        ))
        
        conn.commit()
        conn.close()
        
        goal.updated_at = datetime.fromisoformat(now)
        return goal
    
    def delete(self, goal_id: int) -> bool:
        """
        Elimina una meta.
        
        Args:
            goal_id: ID de la meta a eliminar.
        
        Returns:
            True si se eliminó, False si no existía.
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM goals WHERE id = ?", (goal_id,))
        deleted = cursor.rowcount > 0
        
        conn.commit()
        conn.close()
        
        return deleted
    
    def _row_to_goal(self, row: sqlite3.Row) -> Goal:
        """
        Convierte una fila de la base de datos en un objeto Goal.
        
        Args:
            row: Fila de la base de datos.
        
        Returns:
            Objeto Goal.
        """
        created_at = None
        if row['created_at']:
            created_at = datetime.fromisoformat(row['created_at'])
        
        updated_at = None
        if row['updated_at']:
            updated_at = datetime.fromisoformat(row['updated_at'])
        
        return Goal(
            id=row['id'],
            title=row['title'],
            description=row['description'],
            target_value=row['target_value'],
            current_value=row['current_value'] or 0.0,
            unit=row['unit'],
            created_at=created_at,
            updated_at=updated_at
        )

