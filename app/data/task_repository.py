"""
Repositorio para gestión de tareas en la base de datos.
"""
import sqlite3
from datetime import datetime
from typing import List, Optional

from app.data.database import Database
from app.data.models import Task


class TaskRepository:
    """Repositorio para operaciones CRUD de tareas."""
    
    def __init__(self, db: Database):
        """
        Inicializa el repositorio.
        
        Args:
            db: Instancia de Database.
        """
        self.db = db
    
    def create(self, task: Task) -> Task:
        """
        Crea una nueva tarea.
        
        Args:
            task: Tarea a crear (id debe ser None).
        
        Returns:
            Tarea creada con el id asignado.
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        now = datetime.now().isoformat()
        cursor.execute("""
            INSERT INTO tasks (title, description, due_date, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            task.title,
            task.description,
            task.due_date.isoformat() if task.due_date else None,
            task.status,
            now,
            now
        ))
        
        task_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        task.id = task_id
        task.created_at = datetime.fromisoformat(now)
        task.updated_at = datetime.fromisoformat(now)
        return task
    
    def get_by_id(self, task_id: int) -> Optional[Task]:
        """
        Obtiene una tarea por su ID.
        
        Args:
            task_id: ID de la tarea.
        
        Returns:
            Tarea si existe, None en caso contrario.
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        row = cursor.fetchone()
        conn.close()
        
        return self._row_to_task(row) if row else None
    
    def get_all(self) -> List[Task]:
        """
        Obtiene todas las tareas.
        
        Returns:
            Lista de todas las tareas.
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM tasks ORDER BY created_at DESC")
        rows = cursor.fetchall()
        conn.close()
        
        return [self._row_to_task(row) for row in rows]
    
    def get_by_status(self, status: str) -> List[Task]:
        """
        Obtiene todas las tareas con un estado específico.
        
        Args:
            status: Estado de las tareas ('pendiente' o 'completada').
        
        Returns:
            Lista de tareas con el estado especificado.
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM tasks WHERE status = ? ORDER BY created_at DESC", (status,))
        rows = cursor.fetchall()
        conn.close()
        
        return [self._row_to_task(row) for row in rows]
    
    def update(self, task: Task) -> Task:
        """
        Actualiza una tarea existente.
        
        Args:
            task: Tarea a actualizar (debe tener id).
        
        Returns:
            Tarea actualizada.
        """
        if task.id is None:
            raise ValueError("La tarea debe tener un id para ser actualizada")
        
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        now = datetime.now().isoformat()
        cursor.execute("""
            UPDATE tasks
            SET title = ?, description = ?, due_date = ?, status = ?, updated_at = ?
            WHERE id = ?
        """, (
            task.title,
            task.description,
            task.due_date.isoformat() if task.due_date else None,
            task.status,
            now,
            task.id
        ))
        
        conn.commit()
        conn.close()
        
        task.updated_at = datetime.fromisoformat(now)
        return task
    
    def delete(self, task_id: int) -> bool:
        """
        Elimina una tarea.
        
        Args:
            task_id: ID de la tarea a eliminar.
        
        Returns:
            True si se eliminó, False si no existía.
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        deleted = cursor.rowcount > 0
        
        conn.commit()
        conn.close()
        
        return deleted
    
    def _row_to_task(self, row: sqlite3.Row) -> Task:
        """
        Convierte una fila de la base de datos en un objeto Task.
        
        Args:
            row: Fila de la base de datos.
        
        Returns:
            Objeto Task.
        """
        from datetime import date
        
        due_date = None
        if row['due_date']:
            due_date = date.fromisoformat(row['due_date'])
        
        created_at = None
        if row['created_at']:
            created_at = datetime.fromisoformat(row['created_at'])
        
        updated_at = None
        if row['updated_at']:
            updated_at = datetime.fromisoformat(row['updated_at'])
        
        return Task(
            id=row['id'],
            title=row['title'],
            description=row['description'],
            due_date=due_date,
            status=row['status'],
            created_at=created_at,
            updated_at=updated_at
        )

