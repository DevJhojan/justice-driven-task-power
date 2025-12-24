"""
Repositorio para operaciones CRUD de tareas en la base de datos.
"""
from datetime import datetime
from typing import List, Optional
from app.data.database import Database
from app.data.models import Task, SubTask


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
        
        # Si la tarea tiene un ID, intentar insertarlo (útil para sincronización)
        if task.id is not None:
            # Verificar si ya existe una tarea con ese ID
            cursor.execute('SELECT id FROM tasks WHERE id = ?', (task.id,))
            if cursor.fetchone():
                # Ya existe, actualizar en lugar de crear
                conn.close()
                return self.update(task)
            
            # Insertar con ID específico
            cursor.execute('''
                INSERT INTO tasks (id, title, description, completed, priority, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                task.id,
                task.title,
                task.description,
                1 if task.completed else 0,
                task.priority,
                task.created_at.isoformat() if task.created_at else now,
                task.updated_at.isoformat() if task.updated_at else now
            ))
        else:
            # Insertar sin ID (auto-increment)
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
        
        if not task.created_at:
            task.created_at = datetime.now()
        if not task.updated_at:
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
            task = self._row_to_task(row)
            # Cargar subtareas
            task.subtasks = self.get_subtasks(task_id)
            return task
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
        
        tasks = [self._row_to_task(row) for row in rows]
        # Cargar subtareas para cada tarea
        for task in tasks:
            task.subtasks = self.get_subtasks(task.id)
        return tasks
    
    def update(self, task: Task) -> Task:
        """
        Actualiza una tarea existente y sincroniza sus subtareas.
        
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
        
        # Sincronizar subtareas si están presentes
        if task.subtasks is not None:
            self._sync_subtasks(task.id, task.subtasks)
        
        conn.commit()
        conn.close()
        
        return task
    
    def _sync_subtasks(self, task_id: int, remote_subtasks: List[SubTask]) -> None:
        """
        Sincroniza las subtareas de una tarea con las subtareas remotas.
        
        Args:
            task_id: ID de la tarea
            remote_subtasks: Lista de subtareas remotas a sincronizar
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        # Obtener subtareas locales actuales
        cursor.execute('SELECT id FROM subtasks WHERE task_id = ?', (task_id,))
        local_subtask_ids = {row['id'] for row in cursor.fetchall()}
        
        # IDs de subtareas remotas
        remote_subtask_ids = {st.id for st in remote_subtasks if st.id is not None}
        
        # Eliminar subtareas locales que no están en las remotas
        subtasks_to_delete = local_subtask_ids - remote_subtask_ids
        for subtask_id in subtasks_to_delete:
            cursor.execute('DELETE FROM subtasks WHERE id = ?', (subtask_id,))
        
        # Sincronizar cada subtarea remota
        for remote_subtask in remote_subtasks:
            if remote_subtask.id and remote_subtask.id in local_subtask_ids:
                # Actualizar subtarea existente
                now = datetime.now().isoformat()
                deadline_str = remote_subtask.deadline.isoformat() if remote_subtask.deadline else None
                cursor.execute('''
                    UPDATE subtasks 
                    SET title = ?, description = ?, deadline = ?, completed = ?, updated_at = ?
                    WHERE id = ?
                ''', (
                    remote_subtask.title,
                    remote_subtask.description or "",
                    deadline_str,
                    1 if remote_subtask.completed else 0,
                    now,
                    remote_subtask.id
                ))
            else:
                # Crear nueva subtarea
                now = datetime.now().isoformat()
                deadline_str = remote_subtask.deadline.isoformat() if remote_subtask.deadline else None
                
                if remote_subtask.id:
                    # Insertar con ID específico
                    cursor.execute('''
                        INSERT INTO subtasks (id, task_id, title, description, deadline, completed, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        remote_subtask.id,
                        task_id,
                        remote_subtask.title,
                        remote_subtask.description or "",
                        deadline_str,
                        1 if remote_subtask.completed else 0,
                        remote_subtask.created_at.isoformat() if remote_subtask.created_at else now,
                        remote_subtask.updated_at.isoformat() if remote_subtask.updated_at else now
                    ))
                else:
                    # Insertar sin ID (auto-increment)
                    cursor.execute('''
                        INSERT INTO subtasks (task_id, title, description, deadline, completed, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        task_id,
                        remote_subtask.title,
                        remote_subtask.description or "",
                        deadline_str,
                        1 if remote_subtask.completed else 0,
                        now,
                        now
                    ))
        
        conn.commit()
        conn.close()
    
    def delete(self, task_id: int) -> bool:
        """
        Elimina una tarea por su ID y registra la eliminación para sincronización.
        
        Args:
            task_id: ID de la tarea a eliminar.
            
        Returns:
            True si se eliminó, False si no existía.
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        # Verificar que la tarea existe antes de eliminarla
        cursor.execute('SELECT id FROM tasks WHERE id = ?', (task_id,))
        exists = cursor.fetchone() is not None
        
        if not exists:
            conn.close()
            return False
        
        # Eliminar la tarea
        cursor.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
        deleted = cursor.rowcount > 0
        
        if deleted:
            # Registrar la eliminación para sincronización
            from datetime import datetime
            deleted_at = datetime.now().isoformat()
            cursor.execute('''
                INSERT OR REPLACE INTO deleted_items (item_type, item_id, deleted_at, synced_at)
                VALUES (?, ?, ?, NULL)
            ''', ('task', task_id, deleted_at))
        
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
    
    def get_subtasks(self, task_id: int) -> List[SubTask]:
        """
        Obtiene todas las subtareas de una tarea.
        
        Args:
            task_id: ID de la tarea padre.
            
        Returns:
            Lista de subtareas.
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM subtasks 
            WHERE task_id = ? 
            ORDER BY created_at ASC
        ''', (task_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [self._row_to_subtask(row) for row in rows]
    
    def create_subtask(self, subtask: SubTask) -> SubTask:
        """
        Crea una nueva subtarea.
        
        Args:
            subtask: Subtarea a crear.
            
        Returns:
            Subtarea creada con ID asignado.
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        now = datetime.now().isoformat()
        
        deadline_str = subtask.deadline.isoformat() if subtask.deadline else None
        
        cursor.execute('''
            INSERT INTO subtasks (task_id, title, description, deadline, completed, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            subtask.task_id,
            subtask.title,
            subtask.description or "",
            deadline_str,
            1 if subtask.completed else 0,
            now,
            now
        ))
        
        subtask.id = cursor.lastrowid
        subtask.created_at = datetime.now()
        subtask.updated_at = datetime.now()
        
        conn.commit()
        conn.close()
        
        return subtask
    
    def update_subtask(self, subtask: SubTask) -> SubTask:
        """
        Actualiza una subtarea existente.
        
        Args:
            subtask: Subtarea con los datos actualizados.
            
        Returns:
            Subtarea actualizada.
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        now = datetime.now().isoformat()
        
        deadline_str = subtask.deadline.isoformat() if subtask.deadline else None
        
        cursor.execute('''
            UPDATE subtasks 
            SET title = ?, description = ?, deadline = ?, completed = ?, updated_at = ?
            WHERE id = ?
        ''', (
            subtask.title,
            subtask.description or "",
            deadline_str,
            1 if subtask.completed else 0,
            now,
            subtask.id
        ))
        
        subtask.updated_at = datetime.now()
        
        conn.commit()
        conn.close()
        
        return subtask
    
    def delete_subtask(self, subtask_id: int) -> bool:
        """
        Elimina una subtarea por su ID.
        
        Args:
            subtask_id: ID de la subtarea a eliminar.
            
        Returns:
            True si se eliminó, False si no existía.
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM subtasks WHERE id = ?', (subtask_id,))
        deleted = cursor.rowcount > 0
        
        conn.commit()
        conn.close()
        
        return deleted
    
    def toggle_subtask_complete(self, subtask_id: int) -> Optional[SubTask]:
        """
        Cambia el estado de completado de una subtarea.
        
        Args:
            subtask_id: ID de la subtarea.
            
        Returns:
            Subtarea actualizada o None si no existe.
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM subtasks WHERE id = ?', (subtask_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            subtask = self._row_to_subtask(row)
            subtask.completed = not subtask.completed
            return self.update_subtask(subtask)
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
            priority=row['priority'],
            subtasks=[]  # Se cargarán después
        )
    
    def _row_to_subtask(self, row) -> SubTask:
        """
        Convierte una fila de la base de datos a un objeto SubTask.
        
        Args:
            row: Fila de SQLite.
            
        Returns:
            Objeto SubTask.
        """
        created_at = None
        updated_at = None
        deadline = None
        
        if row['created_at']:
            created_at = datetime.fromisoformat(row['created_at'])
        if row['updated_at']:
            updated_at = datetime.fromisoformat(row['updated_at'])
        
        # Acceder a deadline de forma segura (puede no existir en bases de datos antiguas)
        try:
            if 'deadline' in row.keys() and row['deadline']:
                deadline = datetime.fromisoformat(row['deadline'])
        except (KeyError, TypeError, ValueError):
            deadline = None
        
        # Acceder a description de forma segura
        description = ''
        try:
            if 'description' in row.keys():
                description = row['description'] or ''
        except (KeyError, TypeError):
            description = ''
        
        return SubTask(
            id=row['id'],
            task_id=row['task_id'],
            title=row['title'],
            description=description,
            deadline=deadline,
            completed=bool(row['completed']),
            created_at=created_at,
            updated_at=updated_at
        )

