"""
Servicio de Base de Datos (Database Service)
Gestiona las operaciones de base de datos SQLite de forma asíncrona
"""

import aiosqlite
import json
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from pathlib import Path
from app.utils.helpers import get_database_path, ensure_database_directory


class DatabaseService:
    """
    Servicio para gestionar la base de datos SQLite
    """
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Inicializa el servicio de base de datos
        
        Args:
            db_path: Ruta al archivo de base de datos (opcional)
        """
        if db_path is None:
            # Asegurar que el directorio existe
            ensure_database_directory()
            db_path = str(get_database_path("app.db"))
        
        self.db_path = db_path
        self._connection: Optional[aiosqlite.Connection] = None
    
    async def connect(self):
        """
        Establece conexión con la base de datos
        """
        if self._connection is None:
            self._connection = await aiosqlite.connect(self.db_path)
            # Habilitar foreign keys
            await self._connection.execute("PRAGMA foreign_keys = ON")
            await self._connection.commit()
    
    async def disconnect(self):
        """
        Cierra la conexión con la base de datos
        """
        if self._connection:
            await self._connection.close()
            self._connection = None
    
    async def initialize(self):
        """
        Inicializa la base de datos creando las tablas necesarias
        """
        await self.connect()
        await self._create_tables()
        await self._connection.commit()
    
    async def _create_tables(self):
        """
        Crea las tablas necesarias en la base de datos
        """
        # Tabla de tareas
        await self._connection.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT,
                status TEXT NOT NULL DEFAULT 'pendiente',
                urgent INTEGER NOT NULL DEFAULT 0,
                important INTEGER NOT NULL DEFAULT 0,
                due_date TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                user_id TEXT NOT NULL,
                tags TEXT,
                notes TEXT
            )
        """)
        
        # Tabla de subtareas
        await self._connection.execute("""
            CREATE TABLE IF NOT EXISTS subtasks (
                id TEXT PRIMARY KEY,
                task_id TEXT NOT NULL,
                title TEXT NOT NULL,
                completed INTEGER NOT NULL DEFAULT 0,
                urgent INTEGER NOT NULL DEFAULT 0,
                important INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                notes TEXT,
                FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE
            )
        """)
        
        # Índices para mejorar rendimiento
        await self._connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_tasks_user_id ON tasks(user_id)
        """)
        await self._connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)
        """)
        await self._connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_subtasks_task_id ON subtasks(task_id)
        """)
    
    # ============================================================================
    # MÉTODOS GENÉRICOS DE BASE DE DATOS
    # ============================================================================
    
    async def execute(self, query: str, parameters: tuple = ()) -> aiosqlite.Cursor:
        """
        Ejecuta una consulta SQL
        
        Args:
            query: Consulta SQL
            parameters: Parámetros para la consulta
        
        Returns:
            Cursor con el resultado
        """
        if self._connection is None:
            await self.connect()
        
        return await self._connection.execute(query, parameters)
    
    async def executemany(self, query: str, parameters: List[tuple]) -> aiosqlite.Cursor:
        """
        Ejecuta una consulta SQL múltiples veces
        
        Args:
            query: Consulta SQL
            parameters: Lista de tuplas con parámetros
        
        Returns:
            Cursor con el resultado
        """
        if self._connection is None:
            await self.connect()
        
        return await self._connection.executemany(query, parameters)
    
    async def commit(self):
        """
        Confirma los cambios en la base de datos
        """
        if self._connection:
            await self._connection.commit()
    
    async def rollback(self):
        """
        Revierte los cambios en la base de datos
        """
        if self._connection:
            await self._connection.rollback()
    
    # ============================================================================
    # OPERACIONES CRUD DE TAREAS
    # ============================================================================
    
    async def create_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crea una nueva tarea en la base de datos
        
        Args:
            task_data: Diccionario con los datos de la tarea
        
        Returns:
            Diccionario con los datos de la tarea creada
        """
        # Convertir datos a formato de base de datos
        db_data = {
            "id": task_data["id"],
            "title": task_data["title"],
            "description": task_data.get("description", ""),
            "status": task_data.get("status", "pendiente"),
            "urgent": 1 if task_data.get("urgent", False) else 0,
            "important": 1 if task_data.get("important", False) else 0,
            "due_date": task_data.get("due_date").isoformat() if task_data.get("due_date") else None,
            "created_at": task_data.get("created_at", datetime.now()).isoformat() if isinstance(task_data.get("created_at"), datetime) else task_data.get("created_at", datetime.now().isoformat()),
            "updated_at": task_data.get("updated_at", datetime.now()).isoformat() if isinstance(task_data.get("updated_at"), datetime) else task_data.get("updated_at", datetime.now().isoformat()),
            "user_id": task_data["user_id"],
            "tags": json.dumps(task_data.get("tags", [])),
            "notes": task_data.get("notes", ""),
        }
        
        await self.execute("""
            INSERT INTO tasks (id, title, description, status, urgent, important, 
                             due_date, created_at, updated_at, user_id, tags, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            db_data["id"],
            db_data["title"],
            db_data["description"],
            db_data["status"],
            db_data["urgent"],
            db_data["important"],
            db_data["due_date"],
            db_data["created_at"],
            db_data["updated_at"],
            db_data["user_id"],
            db_data["tags"],
            db_data["notes"],
        ))
        
        await self.commit()
        return await self.get_task(db_data["id"])
    
    async def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene una tarea por su ID
        
        Args:
            task_id: ID de la tarea
        
        Returns:
            Diccionario con los datos de la tarea o None si no existe
        """
        cursor = await self.execute("""
            SELECT * FROM tasks WHERE id = ?
        """, (task_id,))
        
        row = await cursor.fetchone()
        if not row:
            return None
        
        # Convertir a diccionario
        columns = [description[0] for description in cursor.description]
        task_dict = dict(zip(columns, row))
        
        # Convertir tipos
        task_dict["urgent"] = bool(task_dict["urgent"])
        task_dict["important"] = bool(task_dict["important"])
        task_dict["tags"] = json.loads(task_dict["tags"]) if task_dict["tags"] else []
        
        if task_dict["due_date"]:
            task_dict["due_date"] = datetime.fromisoformat(task_dict["due_date"]).date()
        
        task_dict["created_at"] = datetime.fromisoformat(task_dict["created_at"])
        task_dict["updated_at"] = datetime.fromisoformat(task_dict["updated_at"])
        
        # Obtener subtareas
        task_dict["subtasks"] = await self.get_subtasks_by_task(task_id)
        
        return task_dict
    
    async def get_all_tasks(self, user_id: Optional[str] = None, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Obtiene todas las tareas, opcionalmente filtradas
        
        Args:
            user_id: ID del usuario (opcional)
            filters: Diccionario con filtros (opcional)
        
        Returns:
            Lista de diccionarios con los datos de las tareas
        """
        query = "SELECT * FROM tasks WHERE 1=1"
        parameters = []
        
        if user_id:
            query += " AND user_id = ?"
            parameters.append(user_id)
        
        if filters:
            if filters.get("status"):
                query += " AND status = ?"
                parameters.append(filters["status"])
            
            if "urgent" in filters:
                query += " AND urgent = ?"
                parameters.append(1 if filters["urgent"] else 0)
            
            if "important" in filters:
                query += " AND important = ?"
                parameters.append(1 if filters["important"] else 0)
        
        query += " ORDER BY created_at DESC"
        
        cursor = await self.execute(query, tuple(parameters))
        rows = await cursor.fetchall()
        
        # Convertir a diccionarios
        columns = [description[0] for description in cursor.description]
        tasks = []
        
        for row in rows:
            task_dict = dict(zip(columns, row))
            
            # Convertir tipos
            task_dict["urgent"] = bool(task_dict["urgent"])
            task_dict["important"] = bool(task_dict["important"])
            task_dict["tags"] = json.loads(task_dict["tags"]) if task_dict["tags"] else []
            
            if task_dict["due_date"]:
                task_dict["due_date"] = datetime.fromisoformat(task_dict["due_date"]).date()
            
            task_dict["created_at"] = datetime.fromisoformat(task_dict["created_at"])
            task_dict["updated_at"] = datetime.fromisoformat(task_dict["updated_at"])
            
            # Obtener subtareas
            task_dict["subtasks"] = await self.get_subtasks_by_task(task_dict["id"])
            
            tasks.append(task_dict)
        
        return tasks
    
    async def update_task(self, task_id: str, task_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Actualiza una tarea existente
        
        Args:
            task_id: ID de la tarea a actualizar
            task_data: Diccionario con los datos a actualizar
        
        Returns:
            Diccionario con los datos actualizados o None si no existe
        """
        # Obtener tarea actual
        current_task = await self.get_task(task_id)
        if not current_task:
            return None
        
        # Actualizar solo los campos proporcionados
        update_fields = []
        parameters = []
        
        if "title" in task_data:
            update_fields.append("title = ?")
            parameters.append(task_data["title"])
        
        if "description" in task_data:
            update_fields.append("description = ?")
            parameters.append(task_data["description"])
        
        if "status" in task_data:
            update_fields.append("status = ?")
            parameters.append(task_data["status"])
        
        if "urgent" in task_data:
            update_fields.append("urgent = ?")
            parameters.append(1 if task_data["urgent"] else 0)
        
        if "important" in task_data:
            update_fields.append("important = ?")
            parameters.append(1 if task_data["important"] else 0)
        
        if "due_date" in task_data:
            update_fields.append("due_date = ?")
            due_date = task_data["due_date"]
            if due_date:
                if isinstance(due_date, date):
                    parameters.append(due_date.isoformat())
                else:
                    parameters.append(due_date)
            else:
                parameters.append(None)
        
        if "tags" in task_data:
            update_fields.append("tags = ?")
            parameters.append(json.dumps(task_data["tags"]))
        
        if "notes" in task_data:
            update_fields.append("notes = ?")
            parameters.append(task_data["notes"])
        
        # Siempre actualizar updated_at
        update_fields.append("updated_at = ?")
        parameters.append(datetime.now().isoformat())
        
        # Agregar task_id a los parámetros
        parameters.append(task_id)
        
        if update_fields:
            query = f"UPDATE tasks SET {', '.join(update_fields)} WHERE id = ?"
            await self.execute(query, tuple(parameters))
            await self.commit()
        
        return await self.get_task(task_id)
    
    async def delete_task(self, task_id: str) -> bool:
        """
        Elimina una tarea y todas sus subtareas (CASCADE)
        
        Args:
            task_id: ID de la tarea a eliminar
        
        Returns:
            True si se eliminó correctamente, False si no existe
        """
        # Verificar que existe
        task = await self.get_task(task_id)
        if not task:
            return False
        
        await self.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        await self.commit()
        
        return True
    
    # ============================================================================
    # OPERACIONES CRUD DE SUBTAREAS
    # ============================================================================
    
    async def create_subtask(self, subtask_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crea una nueva subtarea en la base de datos
        
        Args:
            subtask_data: Diccionario con los datos de la subtarea
        
        Returns:
            Diccionario con los datos de la subtarea creada
        """
        db_data = {
            "id": subtask_data["id"],
            "task_id": subtask_data["task_id"],
            "title": subtask_data["title"],
            "completed": 1 if subtask_data.get("completed", False) else 0,
            "urgent": 1 if subtask_data.get("urgent", False) else 0,
            "important": 1 if subtask_data.get("important", False) else 0,
            "created_at": subtask_data.get("created_at", datetime.now()).isoformat() if isinstance(subtask_data.get("created_at"), datetime) else subtask_data.get("created_at", datetime.now().isoformat()),
            "updated_at": subtask_data.get("updated_at", datetime.now()).isoformat() if isinstance(subtask_data.get("updated_at"), datetime) else subtask_data.get("updated_at", datetime.now().isoformat()),
            "notes": subtask_data.get("notes", ""),
        }
        
        await self.execute("""
            INSERT INTO subtasks (id, task_id, title, completed, urgent, important, 
                                 created_at, updated_at, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            db_data["id"],
            db_data["task_id"],
            db_data["title"],
            db_data["completed"],
            db_data["urgent"],
            db_data["important"],
            db_data["created_at"],
            db_data["updated_at"],
            db_data["notes"],
        ))
        
        await self.commit()
        return await self.get_subtask(db_data["id"])
    
    async def get_subtask(self, subtask_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene una subtarea por su ID
        
        Args:
            subtask_id: ID de la subtarea
        
        Returns:
            Diccionario con los datos de la subtarea o None si no existe
        """
        cursor = await self.execute("""
            SELECT * FROM subtasks WHERE id = ?
        """, (subtask_id,))
        
        row = await cursor.fetchone()
        if not row:
            return None
        
        columns = [description[0] for description in cursor.description]
        subtask_dict = dict(zip(columns, row))
        
        # Convertir tipos
        subtask_dict["completed"] = bool(subtask_dict["completed"])
        subtask_dict["urgent"] = bool(subtask_dict["urgent"])
        subtask_dict["important"] = bool(subtask_dict["important"])
        subtask_dict["created_at"] = datetime.fromisoformat(subtask_dict["created_at"])
        subtask_dict["updated_at"] = datetime.fromisoformat(subtask_dict["updated_at"])
        
        return subtask_dict
    
    async def get_subtasks_by_task(self, task_id: str) -> List[Dict[str, Any]]:
        """
        Obtiene todas las subtareas de una tarea
        
        Args:
            task_id: ID de la tarea
        
        Returns:
            Lista de diccionarios con los datos de las subtareas
        """
        cursor = await self.execute("""
            SELECT * FROM subtasks WHERE task_id = ? ORDER BY created_at ASC
        """, (task_id,))
        
        rows = await cursor.fetchall()
        columns = [description[0] for description in cursor.description]
        
        subtasks = []
        for row in rows:
            subtask_dict = dict(zip(columns, row))
            
            # Convertir tipos
            subtask_dict["completed"] = bool(subtask_dict["completed"])
            subtask_dict["urgent"] = bool(subtask_dict["urgent"])
            subtask_dict["important"] = bool(subtask_dict["important"])
            subtask_dict["created_at"] = datetime.fromisoformat(subtask_dict["created_at"])
            subtask_dict["updated_at"] = datetime.fromisoformat(subtask_dict["updated_at"])
            
            subtasks.append(subtask_dict)
        
        return subtasks
    
    async def update_subtask(self, subtask_id: str, subtask_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Actualiza una subtarea existente
        
        Args:
            subtask_id: ID de la subtarea a actualizar
            subtask_data: Diccionario con los datos a actualizar
        
        Returns:
            Diccionario con los datos actualizados o None si no existe
        """
        current_subtask = await self.get_subtask(subtask_id)
        if not current_subtask:
            return None
        
        update_fields = []
        parameters = []
        
        if "title" in subtask_data:
            update_fields.append("title = ?")
            parameters.append(subtask_data["title"])
        
        if "completed" in subtask_data:
            update_fields.append("completed = ?")
            parameters.append(1 if subtask_data["completed"] else 0)
        
        if "urgent" in subtask_data:
            update_fields.append("urgent = ?")
            parameters.append(1 if subtask_data["urgent"] else 0)
        
        if "important" in subtask_data:
            update_fields.append("important = ?")
            parameters.append(1 if subtask_data["important"] else 0)
        
        if "notes" in subtask_data:
            update_fields.append("notes = ?")
            parameters.append(subtask_data["notes"])
        
        # Siempre actualizar updated_at
        update_fields.append("updated_at = ?")
        parameters.append(datetime.now().isoformat())
        
        parameters.append(subtask_id)
        
        if update_fields:
            query = f"UPDATE subtasks SET {', '.join(update_fields)} WHERE id = ?"
            await self.execute(query, tuple(parameters))
            await self.commit()
        
        return await self.get_subtask(subtask_id)
    
    async def delete_subtask(self, subtask_id: str) -> bool:
        """
        Elimina una subtarea
        
        Args:
            subtask_id: ID de la subtarea a eliminar
        
        Returns:
            True si se eliminó correctamente, False si no existe
        """
        subtask = await self.get_subtask(subtask_id)
        if not subtask:
            return False
        
        await self.execute("DELETE FROM subtasks WHERE id = ?", (subtask_id,))
        await self.commit()
        
        return True
    
    # ============================================================================
    # MÉTODOS DE UTILIDAD
    # ============================================================================
    
    async def clear_all_data(self):
        """
        Elimina todos los datos de la base de datos (CUIDADO: Destructivo)
        """
        await self.execute("DELETE FROM subtasks")
        await self.execute("DELETE FROM tasks")
        await self.commit()
    
    async def get_table_count(self, table_name: str) -> int:
        """
        Obtiene el número de registros en una tabla
        
        Args:
            table_name: Nombre de la tabla
        
        Returns:
            Número de registros
        """
        cursor = await self.execute(f"SELECT COUNT(*) FROM {table_name}")
        row = await cursor.fetchone()
        return row[0] if row else 0

