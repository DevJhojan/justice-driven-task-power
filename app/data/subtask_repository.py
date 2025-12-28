"""
Repositorio para gestión de subtareas en la base de datos.
"""
import sqlite3
from datetime import datetime
from typing import List, Optional

from app.data.database import Database
from app.data.models import Subtask


class SubtaskRepository:
    """Repositorio para operaciones CRUD de subtareas."""
    
    def __init__(self, db: Database):
        """
        Inicializa el repositorio.
        
        Args:
            db: Instancia de Database.
        """
        self.db = db
    
    def create(self, subtask: Subtask) -> Subtask:
        """
        Crea una nueva subtarea.
        
        Args:
            subtask: Subtarea a crear (id debe ser None).
        
        Returns:
            Subtarea creada con el id asignado.
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        now = datetime.now().isoformat()
        cursor.execute("""
            INSERT INTO subtasks (task_id, title, completed, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
        """, (
            subtask.task_id,
            subtask.title,
            1 if subtask.completed else 0,
            now,
            now
        ))
        
        subtask_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        subtask.id = subtask_id
        subtask.created_at = datetime.fromisoformat(now)
        subtask.updated_at = datetime.fromisoformat(now)
        return subtask
    
    def get_by_id(self, subtask_id: int) -> Optional[Subtask]:
        """
        Obtiene una subtarea por su ID.
        
        Args:
            subtask_id: ID de la subtarea.
        
        Returns:
            Subtarea si existe, None en caso contrario.
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM subtasks WHERE id = ?", (subtask_id,))
        row = cursor.fetchone()
        conn.close()
        
        return self._row_to_subtask(row) if row else None
    
    def get_by_task_id(self, task_id: int) -> List[Subtask]:
        """
        Obtiene todas las subtareas de una tarea.
        
        Args:
            task_id: ID de la tarea.
        
        Returns:
            Lista de subtareas de la tarea.
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM subtasks WHERE task_id = ? ORDER BY created_at ASC", (task_id,))
        rows = cursor.fetchall()
        conn.close()
        
        return [self._row_to_subtask(row) for row in rows]
    
    def update(self, subtask: Subtask) -> Subtask:
        """
        Actualiza una subtarea existente.
        
        Args:
            subtask: Subtarea a actualizar (debe tener id).
        
        Returns:
            Subtarea actualizada.
        """
        if subtask.id is None:
            raise ValueError("La subtarea debe tener un id para ser actualizada")
        
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        now = datetime.now().isoformat()
        cursor.execute("""
            UPDATE subtasks
            SET title = ?, completed = ?, updated_at = ?
            WHERE id = ?
        """, (
            subtask.title,
            1 if subtask.completed else 0,
            now,
            subtask.id
        ))
        
        conn.commit()
        conn.close()
        
        subtask.updated_at = datetime.fromisoformat(now)
        return subtask
    
    def delete(self, subtask_id: int) -> bool:
        """
        Elimina una subtarea.
        
        Args:
            subtask_id: ID de la subtarea a eliminar.
        
        Returns:
            True si se eliminó, False si no existía.
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM subtasks WHERE id = ?", (subtask_id,))
        deleted = cursor.rowcount > 0
        
        conn.commit()
        conn.close()
        
        return deleted
    
    def delete_by_task_id(self, task_id: int) -> int:
        """
        Elimina todas las subtareas de una tarea.
        
        Args:
            task_id: ID de la tarea.
        
        Returns:
            Número de subtareas eliminadas.
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM subtasks WHERE task_id = ?", (task_id,))
        count = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        return count
    
    def _row_to_subtask(self, row: sqlite3.Row) -> Subtask:
        """
        Convierte una fila de la base de datos en un objeto Subtask.
        
        Args:
            row: Fila de la base de datos.
        
        Returns:
            Objeto Subtask.
        """
        created_at = None
        if row['created_at']:
            created_at = datetime.fromisoformat(row['created_at'])
        
        updated_at = None
        if row['updated_at']:
            updated_at = datetime.fromisoformat(row['updated_at'])
        
        return Subtask(
            id=row['id'],
            task_id=row['task_id'],
            title=row['title'],
            completed=bool(row['completed']),
            created_at=created_at,
            updated_at=updated_at
        )

