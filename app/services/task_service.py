"""
Servicio de Tareas (Task Service)
Gestiona las operaciones CRUD de tareas y subtareas
Integrado con DatabaseService para persistencia
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, date
from app.models.task import Task
from app.models.subtask import Subtask
from app.utils.task_helper import (
    TASK_STATUS_PENDING,
    TASK_STATUS_IN_PROGRESS,
    TASK_STATUS_COMPLETED,
    TASK_STATUS_CANCELLED,
    VALID_TASK_STATUSES,
)
from app.utils.eisenhower_matrix import get_eisenhower_quadrant
from app.services.database_service import DatabaseService, TableSchema


class TaskService:
    """
    Servicio para gestionar tareas y subtareas
    """
    
    def __init__(self, database_service: Optional[DatabaseService] = None):
        """
        Inicializa el servicio de tareas
        
        Args:
            database_service: Servicio de base de datos (opcional)
        """
        self.database_service = database_service
        # Almacenamiento temporal en memoria (fallback si no hay database_service)
        self._tasks: Dict[str, Task] = {}
        self._subtasks: Dict[str, Subtask] = {}
    
    async def initialize(self):
        """
        Inicializa el servicio y la base de datos si está disponible
        Registra los esquemas de tablas para tasks y subtasks
        """
        if self.database_service:
            # Registrar esquema de tabla de tasks
            tasks_schema = TableSchema(
                table_name="tasks",
                columns={
                    "id": "TEXT PRIMARY KEY",
                    "title": "TEXT NOT NULL",
                    "description": "TEXT",
                    "status": "TEXT NOT NULL DEFAULT 'pendiente'",
                    "urgent": "INTEGER NOT NULL DEFAULT 0",
                    "important": "INTEGER NOT NULL DEFAULT 0",
                    "due_date": "TEXT",
                    "created_at": "TEXT NOT NULL",
                    "updated_at": "TEXT NOT NULL",
                    "user_id": "TEXT NOT NULL",
                    "tags": "TEXT",
                    "notes": "TEXT"
                },
                indexes=["user_id", "status"]
            )
            
            # Registrar esquema de tabla de subtasks
            subtasks_schema = TableSchema(
                table_name="subtasks",
                columns={
                    "id": "TEXT PRIMARY KEY",
                    "task_id": "TEXT NOT NULL",
                    "title": "TEXT NOT NULL",
                    "completed": "INTEGER NOT NULL DEFAULT 0",
                    "urgent": "INTEGER NOT NULL DEFAULT 0",
                    "important": "INTEGER NOT NULL DEFAULT 0",
                    "created_at": "TEXT NOT NULL",
                    "updated_at": "TEXT NOT NULL",
                    "notes": "TEXT"
                },
                foreign_keys=[{"column": "task_id", "references": "tasks(id)"}],
                indexes=["task_id"]
            )
            
            self.database_service.register_table_schema(tasks_schema)
            self.database_service.register_table_schema(subtasks_schema)
            await self.database_service.initialize()
    
    # ============================================================================
    # OPERACIONES CRUD DE TAREAS
    # ============================================================================
    
    async def create_task(self, task_data: Dict[str, Any]) -> Task:
        """
        Crea una nueva tarea
        
        Args:
            task_data: Diccionario con los datos de la tarea
                - title: Título (requerido)
                - description: Descripción (opcional)
                - status: Estado (opcional, default: pendiente)
                - urgent: Si es urgente (opcional, default: False)
                - important: Si es importante (opcional, default: False)
                - due_date: Fecha de vencimiento (opcional)
                - user_id: ID del usuario (requerido)
                - tags: Lista de etiquetas (opcional)
                - notes: Notas (opcional)
                - subtasks: Lista de subtareas (opcional)
        
        Returns:
            Instancia de Task creada
            
        Raises:
            ValueError: Si faltan datos requeridos
        """
        if not task_data.get("title"):
            raise ValueError("El título de la tarea es requerido")
        
        if not task_data.get("user_id"):
            raise ValueError("El user_id es requerido")
        
        # Extraer subtareas antes de crear la tarea
        subtasks_data = task_data.get('subtasks', [])
        
        # Generar ID único
        task_id = f"task_{datetime.now().timestamp()}_{len(self._tasks)}"
        
        # Crear la tarea
        task = Task(
            id=task_id,
            title=task_data["title"],
            description=task_data.get("description", ""),
            status=task_data.get("status", TASK_STATUS_PENDING),
            urgent=task_data.get("urgent", False),
            important=task_data.get("important", False),
            due_date=task_data.get("due_date"),
            user_id=task_data["user_id"],
            tags=task_data.get("tags", []),
            notes=task_data.get("notes", ""),
        )
        
        # Guardar en almacenamiento (fallback)
        self._tasks[task_id] = task
        
        # Si hay database_service, guardar en base de datos
        if self.database_service:
            try:
                task_dict = task.to_dict()
                # Remover subtasks del dict principal (se guardan por separado)
                task_dict.pop('subtasks', [])
                await self.database_service.create('tasks', task_dict)
                
                # Guardar subtareas
                print(f"DEBUG: Creando {len(subtasks_data)} subtareas para task_id: {task_id}")
                for idx, subtask_data in enumerate(subtasks_data):
                    try:
                        # Asegurar que task_id esté establecido
                        if isinstance(subtask_data, dict):
                            subtask_dict = subtask_data.copy()
                        else:
                            subtask_dict = subtask_data.to_dict() if hasattr(subtask_data, 'to_dict') else subtask_data
                        
                        subtask_dict['task_id'] = task_id
                        print(f"DEBUG: Subtarea {idx+1}: id={subtask_dict.get('id')}, title={subtask_dict.get('title')}, task_id={subtask_dict.get('task_id')}")
                        
                        await self.database_service.create('subtasks', subtask_dict)
                        print(f"DEBUG: Subtarea {idx+1} guardada exitosamente")
                    except Exception as e:
                        print(f"Error guardando subtarea {idx+1}: {e}")
                
                print(f"DEBUG: Tarea {task_id} creada exitosamente con {len(subtasks_data)} subtareas")
                
            except Exception as e:
                # Si falla la BD, mantener en memoria
                print(f"Error guardando tarea en BD: {e}")
        
        return task
    
    async def get_task(self, task_id: str) -> Optional[Task]:
        """
        Obtiene una tarea por su ID
        
        Args:
            task_id: ID de la tarea
        
        Returns:
            Instancia de Task o None si no existe
        """
        # Buscar primero en memoria
        task = self._tasks.get(task_id)
        
        # Si no está en memoria y hay database_service, buscar en BD
        if not task and self.database_service:
            try:
                task_dict = await self.database_service.get('tasks', task_id)
                if task_dict:
                    # Obtener subtareas relacionadas
                    subtasks_dict = await self.database_service.get_all(
                        'subtasks',
                        filters={'task_id': task_id},
                        order_by='created_at ASC'
                    )
                    task_dict['subtasks'] = subtasks_dict
                    task = Task.from_dict(task_dict)
                    # Guardar en memoria para acceso rápido
                    self._tasks[task_id] = task
            except Exception as e:
                print(f"Error obteniendo tarea de BD: {e}")
        
        return task
    
    async def get_all_tasks(self, user_id: Optional[str] = None, filters: Optional[Dict[str, Any]] = None) -> List[Task]:
        """
        Obtiene todas las tareas, opcionalmente filtradas
        
        Args:
            user_id: ID del usuario (opcional, filtra por usuario)
            filters: Diccionario con filtros (opcional)
                - status: Filtrar por estado
                - urgent: Filtrar por urgente
                - important: Filtrar por importante
                - quadrant: Filtrar por cuadrante (Q1, Q2, Q3, Q4)
                - overdue: Solo tareas vencidas (True/False)
                - due_today: Solo tareas que vencen hoy (True/False)
        
        Returns:
            Lista de tareas
        """
        # Si hay database_service, obtener de BD (fuente principal)
        if self.database_service:
            try:
                # Preparar filtros para BD (excluir filtros que se aplican en memoria)
                db_filters = {}
                if user_id:
                    db_filters['user_id'] = user_id
                
                if filters:
                    if filters.get("status"):
                        db_filters['status'] = filters["status"]
                    if "urgent" in filters:
                        db_filters['urgent'] = filters["urgent"]
                    if "important" in filters:
                        db_filters['important'] = filters["important"]
                
                tasks_dict = await self.database_service.get_all(
                    'tasks',
                    filters=db_filters if db_filters else None,
                    order_by='created_at DESC'
                )
                
                # Obtener subtareas para cada tarea
                for task_dict in tasks_dict:
                    task_id = task_dict['id']
                    subtasks_dict = await self.database_service.get_all(
                        'subtasks',
                        filters={'task_id': task_id},
                        order_by='created_at ASC'
                    )
                    task_dict['subtasks'] = subtasks_dict
                
                tasks = [Task.from_dict(t) for t in tasks_dict]
                
                # Actualizar cache en memoria
                for task in tasks:
                    self._tasks[task.id] = task
                
                # Aplicar filtros adicionales que no están en BD
                if filters:
                    if filters.get("quadrant"):
                        quadrant = filters["quadrant"]
                        tasks = [
                            t for t in tasks
                            if get_eisenhower_quadrant(t.urgent, t.important) == quadrant
                        ]
                    
                    if filters.get("overdue"):
                        from app.utils.task_helper import is_task_overdue
                        tasks = [t for t in tasks if is_task_overdue(t)]
                    
                    if filters.get("due_today"):
                        from app.utils.task_helper import is_task_due_today
                        tasks = [t for t in tasks if is_task_due_today(t)]
                
                return tasks
            except Exception as e:
                print(f"Error obteniendo tareas de BD: {e}")
                # Fallback a memoria
        
        # Fallback: usar almacenamiento en memoria
        tasks = list(self._tasks.values())
        
        # Filtrar por usuario si se proporciona
        if user_id:
            tasks = [t for t in tasks if t.user_id == user_id]
        
        # Aplicar filtros adicionales
        if filters:
            if filters.get("status"):
                tasks = [t for t in tasks if t.status == filters["status"]]
            
            if "urgent" in filters:
                tasks = [t for t in tasks if t.urgent == filters["urgent"]]
            
            if "important" in filters:
                tasks = [t for t in tasks if t.important == filters["important"]]
            
            if filters.get("quadrant"):
                quadrant = filters["quadrant"]
                tasks = [
                    t for t in tasks
                    if get_eisenhower_quadrant(t.urgent, t.important) == quadrant
                ]
            
            if filters.get("overdue"):
                from app.utils.task_helper import is_task_overdue
                tasks = [t for t in tasks if is_task_overdue(t)]
            
            if filters.get("due_today"):
                from app.utils.task_helper import is_task_due_today
                tasks = [t for t in tasks if is_task_due_today(t)]
        
        return tasks
    
    async def update_task(self, task_id: str, task_data: Dict[str, Any]) -> Optional[Task]:
        """
        Actualiza una tarea existente
        
        Args:
            task_id: ID de la tarea a actualizar
            task_data: Diccionario con los datos a actualizar
        
        Returns:
            Instancia de Task actualizada o None si no existe
        """
        task = await self.get_task(task_id)
        if not task:
            return None
        
        # Actualizar campos
        if "title" in task_data:
            task.title = task_data["title"]
        
        if "description" in task_data:
            task.description = task_data["description"]
        
        if "status" in task_data:
            task.update_status(task_data["status"])
        
        if "urgent" in task_data or "important" in task_data:
            urgent = task_data.get("urgent", task.urgent)
            important = task_data.get("important", task.important)
            task.set_priority(urgent, important)
        
        if "due_date" in task_data:
            task.due_date = task_data["due_date"]
        
        if "tags" in task_data:
            task.tags = task_data["tags"]
        
        if "notes" in task_data:
            task.notes = task_data["notes"]
        
        # Actualizar subtareas si se proporcionan
        if "subtasks" in task_data:
            subtasks_data = task_data["subtasks"]
            # Eliminar subtareas antiguas
            for subtask in task.subtasks:
                if self.database_service:
                    try:
                        await self.database_service.delete('subtasks', subtask.id)
                    except Exception as e:
                        print(f"Error eliminando subtarea en BD: {e}")
            
            # Agregar nuevas subtareas
            task.subtasks = []
            for subtask_data in subtasks_data:
                if isinstance(subtask_data, dict):
                    subtask = Subtask(**subtask_data)
                else:
                    subtask = subtask_data
                subtask.task_id = task_id
                task.subtasks.append(subtask)
                
                if self.database_service:
                    try:
                        await self.database_service.create('subtasks', subtask.to_dict())
                    except Exception as e:
                        print(f"Error guardando subtarea en BD: {e}")
        
        # Actualizar timestamp
        task.updated_at = datetime.now()
        
        # Guardar cambios en memoria
        self._tasks[task_id] = task
        
        # Si hay database_service, actualizar en base de datos
        if self.database_service:
            try:
                # Preparar datos para actualización
                update_data = {}
                if "title" in task_data:
                    update_data["title"] = task.title
                if "description" in task_data:
                    update_data["description"] = task.description
                if "status" in task_data:
                    update_data["status"] = task.status
                if "urgent" in task_data or "important" in task_data:
                    update_data["urgent"] = task.urgent
                    update_data["important"] = task.important
                if "due_date" in task_data:
                    update_data["due_date"] = task.due_date
                if "tags" in task_data:
                    update_data["tags"] = task.tags
                if "notes" in task_data:
                    update_data["notes"] = task.notes
                
                update_data["updated_at"] = task.updated_at.isoformat()
                
                await self.database_service.update('tasks', task_id, update_data)
            except Exception as e:
                print(f"Error actualizando tarea en BD: {e}")
        
        return task
    
    async def delete_task(self, task_id: str) -> bool:
        """
        Elimina una tarea y todas sus subtareas
        
        Args:
            task_id: ID de la tarea a eliminar
        
        Returns:
            True si se eliminó correctamente, False si no existe
        """
        task = await self.get_task(task_id)
        if not task:
            return False
        
        # Eliminar todas las subtareas asociadas
        for subtask in task.subtasks:
            await self.delete_subtask(subtask.id)
        
        # Eliminar de memoria
        if task_id in self._tasks:
            del self._tasks[task_id]
        
        # Si hay database_service, eliminar de base de datos
        # Las subtareas se eliminan automáticamente por CASCADE
        if self.database_service:
            try:
                await self.database_service.delete('tasks', task_id)
            except Exception as e:
                print(f"Error eliminando tarea de BD: {e}")
        
        return True
    
    # ============================================================================
    # OPERACIONES CRUD DE SUBTAREAS
    # ============================================================================
    
    async def create_subtask(self, task_id: str, subtask_data: Dict[str, Any]) -> Optional[Subtask]:
        """
        Crea una nueva subtarea para una tarea
        
        Args:
            task_id: ID de la tarea padre
            subtask_data: Diccionario con los datos de la subtarea
                - title: Título (requerido)
                - completed: Si está completada (opcional, default: False)
                - urgent: Si es urgente (opcional, default: False)
                - important: Si es importante (opcional, default: False)
                - notes: Notas (opcional)
        
        Returns:
            Instancia de Subtask creada o None si la tarea no existe
        """
        task = await self.get_task(task_id)
        if not task:
            return None
        
        if not subtask_data.get("title"):
            raise ValueError("El título de la subtarea es requerido")
        
        # Generar ID único
        subtask_id = f"subtask_{datetime.now().timestamp()}_{len(self._subtasks)}"
        
        # Crear la subtarea
        subtask = Subtask(
            id=subtask_id,
            task_id=task_id,
            title=subtask_data["title"],
            completed=subtask_data.get("completed", False),
            urgent=subtask_data.get("urgent", False),
            important=subtask_data.get("important", False),
            notes=subtask_data.get("notes", ""),
        )
        
        # Agregar a la tarea
        task.add_subtask(subtask)
        
        # Guardar en almacenamiento (fallback)
        self._subtasks[subtask_id] = subtask
        
        # Si hay database_service, guardar en base de datos
        if self.database_service:
            try:
                subtask_dict = subtask.to_dict()
                await self.database_service.create('subtasks', subtask_dict)
            except Exception as e:
                print(f"Error guardando subtarea en BD: {e}")
        
        return subtask
    
    async def get_subtask(self, subtask_id: str) -> Optional[Subtask]:
        """
        Obtiene una subtarea por su ID
        
        Args:
            subtask_id: ID de la subtarea
        
        Returns:
            Instancia de Subtask o None si no existe
        """
        # Buscar primero en memoria
        subtask = self._subtasks.get(subtask_id)
        
        # Si no está en memoria y hay database_service, buscar en BD
        if not subtask and self.database_service:
            try:
                subtask_dict = await self.database_service.get('subtasks', subtask_id)
                if subtask_dict:
                    subtask = Subtask.from_dict(subtask_dict)
                    # Guardar en memoria para acceso rápido
                    self._subtasks[subtask_id] = subtask
            except Exception as e:
                print(f"Error obteniendo subtarea de BD: {e}")
        
        return subtask
    
    async def get_subtasks_by_task(self, task_id: str) -> List[Subtask]:
        """
        Obtiene todas las subtareas de una tarea
        
        Args:
            task_id: ID de la tarea
        
        Returns:
            Lista de subtareas
        """
        task = await self.get_task(task_id)
        if not task:
            return []
        
        return task.subtasks
    
    async def update_subtask(self, subtask_id: str, subtask_data: Dict[str, Any]) -> Optional[Subtask]:
        """
        Actualiza una subtarea existente
        
        Args:
            subtask_id: ID de la subtarea a actualizar
            subtask_data: Diccionario con los datos a actualizar
        
        Returns:
            Instancia de Subtask actualizada o None si no existe
        """
        subtask = await self.get_subtask(subtask_id)
        if not subtask:
            return None
        
        # Actualizar campos
        if "title" in subtask_data:
            subtask.title = subtask_data["title"]
        
        if "completed" in subtask_data:
            if subtask_data["completed"]:
                subtask.mark_as_completed()
            else:
                subtask.mark_as_pending()
        
        if "urgent" in subtask_data or "important" in subtask_data:
            urgent = subtask_data.get("urgent", subtask.urgent)
            important = subtask_data.get("important", subtask.important)
            subtask.set_priority(urgent, important)
        
        if "notes" in subtask_data:
            subtask.notes = subtask_data["notes"]
        
        # Actualizar timestamp
        subtask.updated_at = datetime.now()
        
        # Guardar cambios en memoria
        self._subtasks[subtask_id] = subtask
        
        # Actualizar también en la tarea padre
        task = await self.get_task(subtask.task_id)
        if task:
            task.updated_at = datetime.now()
            # Actualizar tarea en BD también
            if self.database_service:
                try:
                    await self.database_service.update(
                        'tasks',
                        task.id,
                        {"updated_at": task.updated_at}
                    )
                except Exception as e:
                    print(f"Error actualizando timestamp de tarea en BD: {e}")
        
        # Si hay database_service, actualizar en base de datos
        if self.database_service:
            try:
                # Preparar datos para actualización
                update_data = {}
                if "title" in subtask_data:
                    update_data["title"] = subtask.title
                if "completed" in subtask_data:
                    update_data["completed"] = subtask.completed
                if "urgent" in subtask_data or "important" in subtask_data:
                    update_data["urgent"] = subtask.urgent
                    update_data["important"] = subtask.important
                if "notes" in subtask_data:
                    update_data["notes"] = subtask.notes
                
                await self.database_service.update('subtasks', subtask_id, update_data)
            except Exception as e:
                print(f"Error actualizando subtarea en BD: {e}")
        
        return subtask
    
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
        
        # Eliminar de la tarea padre
        task = await self.get_task(subtask.task_id)
        if task:
            task.remove_subtask(subtask_id)
        
        # Eliminar de memoria
        if subtask_id in self._subtasks:
            del self._subtasks[subtask_id]
        
        # Si hay database_service, eliminar de base de datos
        if self.database_service:
            try:
                await self.database_service.delete('subtasks', subtask_id)
            except Exception as e:
                print(f"Error eliminando subtarea de BD: {e}")
        
        return True
    
    # ============================================================================
    # MÉTODOS DE FILTRADO Y BÚSQUEDA
    # ============================================================================
    
    async def get_tasks_by_status(self, status: str, user_id: Optional[str] = None) -> List[Task]:
        """
        Obtiene tareas filtradas por estado
        
        Args:
            status: Estado de la tarea
            user_id: ID del usuario (opcional)
        
        Returns:
            Lista de tareas con el estado especificado
        """
        return await self.get_all_tasks(
            user_id=user_id,
            filters={"status": status}
        )
    
    async def get_tasks_by_priority(self, urgent: bool, important: bool, user_id: Optional[str] = None) -> List[Task]:
        """
        Obtiene tareas filtradas por prioridad
        
        Args:
            urgent: Si es urgente
            important: Si es importante
            user_id: ID del usuario (opcional)
        
        Returns:
            Lista de tareas con la prioridad especificada
        """
        return await self.get_all_tasks(
            user_id=user_id,
            filters={"urgent": urgent, "important": important}
        )
    
    async def get_tasks_by_quadrant(self, quadrant: str, user_id: Optional[str] = None) -> List[Task]:
        """
        Obtiene tareas filtradas por cuadrante de Eisenhower
        
        Args:
            quadrant: Cuadrante (Q1, Q2, Q3, Q4)
            user_id: ID del usuario (opcional)
        
        Returns:
            Lista de tareas del cuadrante especificado
        """
        return await self.get_all_tasks(
            user_id=user_id,
            filters={"quadrant": quadrant}
        )
    
    async def get_overdue_tasks(self, user_id: Optional[str] = None) -> List[Task]:
        """
        Obtiene tareas vencidas
        
        Args:
            user_id: ID del usuario (opcional)
        
        Returns:
            Lista de tareas vencidas
        """
        return await self.get_all_tasks(
            user_id=user_id,
            filters={"overdue": True}
        )
    
    async def get_tasks_due_today(self, user_id: Optional[str] = None) -> List[Task]:
        """
        Obtiene tareas que vencen hoy
        
        Args:
            user_id: ID del usuario (opcional)
        
        Returns:
            Lista de tareas que vencen hoy
        """
        return await self.get_all_tasks(
            user_id=user_id,
            filters={"due_today": True}
        )
    
    async def search_tasks(self, query: str, user_id: Optional[str] = None) -> List[Task]:
        """
        Busca tareas por título o descripción
        
        Args:
            query: Texto a buscar
            user_id: ID del usuario (opcional)
        
        Returns:
            Lista de tareas que coinciden con la búsqueda
        """
        tasks = await self.get_all_tasks(user_id=user_id)
        query_lower = query.lower()
        
        return [
            task for task in tasks
            if query_lower in task.title.lower() or query_lower in task.description.lower()
        ]
    
    # ============================================================================
    # MÉTODOS DE ESTADÍSTICAS
    # ============================================================================
    
    async def get_task_statistics(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Obtiene estadísticas de tareas del usuario
        
        Args:
            user_id: ID del usuario (opcional)
        
        Returns:
            Diccionario con estadísticas
        """
        tasks = await self.get_all_tasks(user_id=user_id)
        
        total = len(tasks)
        pending = len([t for t in tasks if t.status == TASK_STATUS_PENDING])
        in_progress = len([t for t in tasks if t.status == TASK_STATUS_IN_PROGRESS])
        completed = len([t for t in tasks if t.status == TASK_STATUS_COMPLETED])
        cancelled = len([t for t in tasks if t.status == TASK_STATUS_CANCELLED])
        
        # Estadísticas por cuadrante
        q1_tasks = await self.get_tasks_by_quadrant("Q1", user_id)
        q2_tasks = await self.get_tasks_by_quadrant("Q2", user_id)
        q3_tasks = await self.get_tasks_by_quadrant("Q3", user_id)
        q4_tasks = await self.get_tasks_by_quadrant("Q4", user_id)
        
        # Tareas vencidas
        overdue_tasks = await self.get_overdue_tasks(user_id)
        
        return {
            "total": total,
            "pending": pending,
            "in_progress": in_progress,
            "completed": completed,
            "cancelled": cancelled,
            "quadrants": {
                "Q1": len(q1_tasks),
                "Q2": len(q2_tasks),
                "Q3": len(q3_tasks),
                "Q4": len(q4_tasks),
            },
            "overdue": len(overdue_tasks),
        }

