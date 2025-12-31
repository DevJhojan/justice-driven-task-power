"""
Servicio de Tareas (Task Service)
Gestiona las operaciones CRUD de tareas y subtareas
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


class TaskService:
    """
    Servicio para gestionar tareas y subtareas
    """
    
    def __init__(self, database_service=None):
        """
        Inicializa el servicio de tareas
        
        Args:
            database_service: Servicio de base de datos (opcional)
        """
        self.database_service = database_service
        # Almacenamiento temporal en memoria (se reemplazará con base de datos)
        self._tasks: Dict[str, Task] = {}
        self._subtasks: Dict[str, Subtask] = {}
    
    # ============================================================================
    # OPERACIONES CRUD DE TAREAS
    # ============================================================================
    
    def create_task(self, task_data: Dict[str, Any]) -> Task:
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
        
        Returns:
            Instancia de Task creada
            
        Raises:
            ValueError: Si faltan datos requeridos
        """
        if not task_data.get("title"):
            raise ValueError("El título de la tarea es requerido")
        
        if not task_data.get("user_id"):
            raise ValueError("El user_id es requerido")
        
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
        
        # Guardar en almacenamiento
        self._tasks[task_id] = task
        
        # Si hay database_service, guardar en base de datos
        if self.database_service:
            # TODO: Implementar guardado en base de datos
            pass
        
        return task
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """
        Obtiene una tarea por su ID
        
        Args:
            task_id: ID de la tarea
        
        Returns:
            Instancia de Task o None si no existe
        """
        task = self._tasks.get(task_id)
        
        if not task and self.database_service:
            # TODO: Buscar en base de datos
            pass
        
        return task
    
    def get_all_tasks(self, user_id: Optional[str] = None, filters: Optional[Dict[str, Any]] = None) -> List[Task]:
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
        
        # Si hay database_service, buscar también en base de datos
        if self.database_service:
            # TODO: Buscar en base de datos
            pass
        
        return tasks
    
    def update_task(self, task_id: str, task_data: Dict[str, Any]) -> Optional[Task]:
        """
        Actualiza una tarea existente
        
        Args:
            task_id: ID de la tarea a actualizar
            task_data: Diccionario con los datos a actualizar
        
        Returns:
            Instancia de Task actualizada o None si no existe
        """
        task = self.get_task(task_id)
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
        
        # Actualizar timestamp
        task.updated_at = datetime.now()
        
        # Guardar cambios
        self._tasks[task_id] = task
        
        # Si hay database_service, actualizar en base de datos
        if self.database_service:
            # TODO: Actualizar en base de datos
            pass
        
        return task
    
    def delete_task(self, task_id: str) -> bool:
        """
        Elimina una tarea y todas sus subtareas
        
        Args:
            task_id: ID de la tarea a eliminar
        
        Returns:
            True si se eliminó correctamente, False si no existe
        """
        task = self.get_task(task_id)
        if not task:
            return False
        
        # Eliminar todas las subtareas asociadas
        for subtask in task.subtasks:
            self.delete_subtask(subtask.id)
        
        # Eliminar la tarea
        del self._tasks[task_id]
        
        # Si hay database_service, eliminar de base de datos
        if self.database_service:
            # TODO: Eliminar de base de datos
            pass
        
        return True
    
    # ============================================================================
    # OPERACIONES CRUD DE SUBTAREAS
    # ============================================================================
    
    def create_subtask(self, task_id: str, subtask_data: Dict[str, Any]) -> Optional[Subtask]:
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
        task = self.get_task(task_id)
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
        
        # Guardar en almacenamiento
        self._subtasks[subtask_id] = subtask
        
        # Si hay database_service, guardar en base de datos
        if self.database_service:
            # TODO: Implementar guardado en base de datos
            pass
        
        return subtask
    
    def get_subtask(self, subtask_id: str) -> Optional[Subtask]:
        """
        Obtiene una subtarea por su ID
        
        Args:
            subtask_id: ID de la subtarea
        
        Returns:
            Instancia de Subtask o None si no existe
        """
        return self._subtasks.get(subtask_id)
    
    def get_subtasks_by_task(self, task_id: str) -> List[Subtask]:
        """
        Obtiene todas las subtareas de una tarea
        
        Args:
            task_id: ID de la tarea
        
        Returns:
            Lista de subtareas
        """
        task = self.get_task(task_id)
        if not task:
            return []
        
        return task.subtasks
    
    def update_subtask(self, subtask_id: str, subtask_data: Dict[str, Any]) -> Optional[Subtask]:
        """
        Actualiza una subtarea existente
        
        Args:
            subtask_id: ID de la subtarea a actualizar
            subtask_data: Diccionario con los datos a actualizar
        
        Returns:
            Instancia de Subtask actualizada o None si no existe
        """
        subtask = self.get_subtask(subtask_id)
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
        
        # Guardar cambios
        self._subtasks[subtask_id] = subtask
        
        # Actualizar también en la tarea padre
        task = self.get_task(subtask.task_id)
        if task:
            task.updated_at = datetime.now()
        
        # Si hay database_service, actualizar en base de datos
        if self.database_service:
            # TODO: Actualizar en base de datos
            pass
        
        return subtask
    
    def delete_subtask(self, subtask_id: str) -> bool:
        """
        Elimina una subtarea
        
        Args:
            subtask_id: ID de la subtarea a eliminar
        
        Returns:
            True si se eliminó correctamente, False si no existe
        """
        subtask = self.get_subtask(subtask_id)
        if not subtask:
            return False
        
        # Eliminar de la tarea padre
        task = self.get_task(subtask.task_id)
        if task:
            task.remove_subtask(subtask_id)
        
        # Eliminar de almacenamiento
        del self._subtasks[subtask_id]
        
        # Si hay database_service, eliminar de base de datos
        if self.database_service:
            # TODO: Eliminar de base de datos
            pass
        
        return True
    
    # ============================================================================
    # MÉTODOS DE FILTRADO Y BÚSQUEDA
    # ============================================================================
    
    def get_tasks_by_status(self, status: str, user_id: Optional[str] = None) -> List[Task]:
        """
        Obtiene tareas filtradas por estado
        
        Args:
            status: Estado de la tarea
            user_id: ID del usuario (opcional)
        
        Returns:
            Lista de tareas con el estado especificado
        """
        return self.get_all_tasks(
            user_id=user_id,
            filters={"status": status}
        )
    
    def get_tasks_by_priority(self, urgent: bool, important: bool, user_id: Optional[str] = None) -> List[Task]:
        """
        Obtiene tareas filtradas por prioridad
        
        Args:
            urgent: Si es urgente
            important: Si es importante
            user_id: ID del usuario (opcional)
        
        Returns:
            Lista de tareas con la prioridad especificada
        """
        return self.get_all_tasks(
            user_id=user_id,
            filters={"urgent": urgent, "important": important}
        )
    
    def get_tasks_by_quadrant(self, quadrant: str, user_id: Optional[str] = None) -> List[Task]:
        """
        Obtiene tareas filtradas por cuadrante de Eisenhower
        
        Args:
            quadrant: Cuadrante (Q1, Q2, Q3, Q4)
            user_id: ID del usuario (opcional)
        
        Returns:
            Lista de tareas del cuadrante especificado
        """
        return self.get_all_tasks(
            user_id=user_id,
            filters={"quadrant": quadrant}
        )
    
    def get_overdue_tasks(self, user_id: Optional[str] = None) -> List[Task]:
        """
        Obtiene tareas vencidas
        
        Args:
            user_id: ID del usuario (opcional)
        
        Returns:
            Lista de tareas vencidas
        """
        return self.get_all_tasks(
            user_id=user_id,
            filters={"overdue": True}
        )
    
    def get_tasks_due_today(self, user_id: Optional[str] = None) -> List[Task]:
        """
        Obtiene tareas que vencen hoy
        
        Args:
            user_id: ID del usuario (opcional)
        
        Returns:
            Lista de tareas que vencen hoy
        """
        return self.get_all_tasks(
            user_id=user_id,
            filters={"due_today": True}
        )
    
    def search_tasks(self, query: str, user_id: Optional[str] = None) -> List[Task]:
        """
        Busca tareas por título o descripción
        
        Args:
            query: Texto a buscar
            user_id: ID del usuario (opcional)
        
        Returns:
            Lista de tareas que coinciden con la búsqueda
        """
        tasks = self.get_all_tasks(user_id=user_id)
        query_lower = query.lower()
        
        return [
            task for task in tasks
            if query_lower in task.title.lower() or query_lower in task.description.lower()
        ]
    
    # ============================================================================
    # MÉTODOS DE ESTADÍSTICAS
    # ============================================================================
    
    def get_task_statistics(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Obtiene estadísticas de tareas del usuario
        
        Args:
            user_id: ID del usuario (opcional)
        
        Returns:
            Diccionario con estadísticas
        """
        tasks = self.get_all_tasks(user_id=user_id)
        
        total = len(tasks)
        pending = len([t for t in tasks if t.status == TASK_STATUS_PENDING])
        in_progress = len([t for t in tasks if t.status == TASK_STATUS_IN_PROGRESS])
        completed = len([t for t in tasks if t.status == TASK_STATUS_COMPLETED])
        cancelled = len([t for t in tasks if t.status == TASK_STATUS_CANCELLED])
        
        # Estadísticas por cuadrante
        q1 = len(self.get_tasks_by_quadrant("Q1", user_id))
        q2 = len(self.get_tasks_by_quadrant("Q2", user_id))
        q3 = len(self.get_tasks_by_quadrant("Q3", user_id))
        q4 = len(self.get_tasks_by_quadrant("Q4", user_id))
        
        # Tareas vencidas
        overdue = len(self.get_overdue_tasks(user_id))
        
        return {
            "total": total,
            "pending": pending,
            "in_progress": in_progress,
            "completed": completed,
            "cancelled": cancelled,
            "quadrants": {
                "Q1": q1,
                "Q2": q2,
                "Q3": q3,
                "Q4": q4,
            },
            "overdue": overdue,
        }

