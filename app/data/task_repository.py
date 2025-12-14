"""
Repositorio para operaciones CRUD de tareas en la base de datos.
"""
from datetime import datetime
from typing import List, Optional
from app.data.database import Database
from app.data.models import Task


class TaskRepository:
    """Repositorio para gestionar tareas en la base de datos."""
    
    def __init__(self, database: Database):
        """
        Inicializa el repositorio.
        
        Args:
            database: Instancia de Database.
        """
        self.db = database
    
    def create(self, task: Task) -> Task:
        """
        Crea una nueva tarea en la base de datos.
        
        Args:
            task: Tarea a crear.
            
        Returns:
            Tarea creada con ID asignado.
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        now = datetime.now().isoformat()
        
        cursor.execute('''
            INSERT INTO tasks (title, description, completed, priority, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            task.title,
            task.description,
            1 if task.completed else 0,
            task.priority,
            now,
            now
        ))
        
        task.id = cursor.lastrowid
        task.created_at = datetime.now()
        task.updated_at = datetime.now()
        
        conn.commit()
        conn.close()
        
        return task
    
    def get_by_id(self, task_id: int) -> Optional[Task]:
        """
        Obtiene una tarea por su ID.
        
        Args:
            task_id: ID de la tarea.
            
        Returns:
            Tarea encontrada o None.
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM tasks WHERE id = ?', (task_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return self._row_to_task(row)
        return None
    
    def get_all(self, filter_completed: Optional[bool] = None) -> List[Task]:
        """
        Obtiene todas las tareas.
        
        Args:
            filter_completed: Si se proporciona, filtra por estado de completado.
            
        Returns:
            Lista de tareas.
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        if filter_completed is not None:
            cursor.execute('''
                SELECT * FROM tasks 
                WHERE completed = ?
                ORDER BY created_at DESC
            ''', (1 if filter_completed else 0,))
        else:
            cursor.execute('SELECT * FROM tasks ORDER BY created_at DESC')
        
        rows = cursor.fetchall()
        conn.close()
        
        return [self._row_to_task(row) for row in rows]
    
    def update(self, task: Task) -> Task:
        """
        Actualiza una tarea existente.
        
        Args:
            task: Tarea con los datos actualizados.
            
        Returns:
            Tarea actualizada.
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        now = datetime.now().isoformat()
        
        cursor.execute('''
            UPDATE tasks 
            SET title = ?, description = ?, completed = ?, priority = ?, updated_at = ?
            WHERE id = ?
        ''', (
            task.title,
            task.description,
            1 if task.completed else 0,
            task.priority,
            now,
            task.id
        ))
        
        task.updated_at = datetime.now()
        
        conn.commit()
        conn.close()
        
        return task
    
    def delete(self, task_id: int) -> bool:
        """
        Elimina una tarea por su ID.
        
        Args:
            task_id: ID de la tarea a eliminar.
            
        Returns:
            True si se eliminó, False si no existía.
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
        deleted = cursor.rowcount > 0
        
        conn.commit()
        conn.close()
        
        return deleted
    
    def toggle_complete(self, task_id: int) -> Optional[Task]:
        """
        Cambia el estado de completado de una tarea.
        
        Args:
            task_id: ID de la tarea.
            
        Returns:
            Tarea actualizada o None si no existe.
        """
        task = self.get_by_id(task_id)
        if task:
            task.completed = not task.completed
            return self.update(task)
        return None
    
    def _row_to_task(self, row) -> Task:
        """
        Convierte una fila de la base de datos a un objeto Task.
        
        Args:
            row: Fila de SQLite.
            
        Returns:
            Objeto Task.
        """
        created_at = None
        updated_at = None
        
        if row['created_at']:
            created_at = datetime.fromisoformat(row['created_at'])
        if row['updated_at']:
            updated_at = datetime.fromisoformat(row['updated_at'])
        
        return Task(
            id=row['id'],
            title=row['title'],
            description=row['description'],
            completed=bool(row['completed']),
            created_at=created_at,
            updated_at=updated_at,
            priority=row['priority']
        )

