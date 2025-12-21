"""
Servicio de lógica de negocio para tareas.
"""
from typing import List, Optional
from datetime import datetime
from app.data.database import Database
from app.data.task_repository import TaskRepository
from app.data.models import Task, SubTask


class TaskService:
    """Servicio para gestionar la lógica de negocio de tareas."""
    
    def __init__(self):
        """Inicializa el servicio con la base de datos y repositorio."""
        self.db = Database()
        self.repository = TaskRepository(self.db)
    
    def create_task(self, title: str, description: str = "", priority: str = "not_urgent_important") -> Task:
        """
        Crea una nueva tarea.
        
        Args:
            title: Título de la tarea.
            description: Descripción de la tarea.
            priority: Prioridad según Matriz de Eisenhower:
                     'urgent_important' - Urgente e Importante
                     'not_urgent_important' - No Urgente e Importante
                     'urgent_not_important' - Urgente y No Importante
                     'not_urgent_not_important' - No Urgente y No Importante
            
        Returns:
            Tarea creada.
        """
        if not title or not title.strip():
            raise ValueError("El título de la tarea no puede estar vacío")
        
        valid_priorities = ['urgent_important', 'not_urgent_important', 'urgent_not_important', 'not_urgent_not_important']
        if priority not in valid_priorities:
            priority = 'not_urgent_important'
        
        task = Task(
            id=None,
            title=title.strip(),
            description=description.strip(),
            completed=False,
            created_at=None,
            updated_at=None,
            priority=priority
        )
        
        return self.repository.create(task)
    
    def get_all_tasks(self, filter_completed: Optional[bool] = None) -> List[Task]:
        """
        Obtiene todas las tareas, opcionalmente filtradas por estado.
        
        Args:
            filter_completed: Si se proporciona, filtra por estado de completado.
            
        Returns:
            Lista de tareas.
        """
        return self.repository.get_all(filter_completed)
    
    def get_task(self, task_id: int) -> Optional[Task]:
        """
        Obtiene una tarea por su ID.
        
        Args:
            task_id: ID de la tarea.
            
        Returns:
            Tarea encontrada o None.
        """
        return self.repository.get_by_id(task_id)
    
    def update_task(self, task: Task) -> Task:
        """
        Actualiza una tarea existente.
        
        Args:
            task: Tarea con los datos actualizados.
            
        Returns:
            Tarea actualizada.
        """
        if not task.title or not task.title.strip():
            raise ValueError("El título de la tarea no puede estar vacío")
        
        task.title = task.title.strip()
        task.description = task.description.strip()
        
        valid_priorities = ['urgent_important', 'not_urgent_important', 'urgent_not_important', 'not_urgent_not_important']
        if task.priority not in valid_priorities:
            task.priority = 'not_urgent_important'
        
        return self.repository.update(task)
    
    def delete_task(self, task_id: int) -> bool:
        """
        Elimina una tarea.
        
        Args:
            task_id: ID de la tarea a eliminar.
            
        Returns:
            True si se eliminó, False si no existía.
        """
        return self.repository.delete(task_id)
    
    def toggle_task_complete(self, task_id: int) -> Optional[Task]:
        """
        Cambia el estado de completado de una tarea.
        
        Args:
            task_id: ID de la tarea.
            
        Returns:
            Tarea actualizada o None si no existe.
        """
        return self.repository.toggle_complete(task_id)
    
    def get_statistics(self) -> dict:
        """
        Obtiene estadísticas de las tareas.
        
        Returns:
            Diccionario con estadísticas.
        """
        all_tasks = self.repository.get_all()
        total = len(all_tasks)
        completed = sum(1 for task in all_tasks if task.completed)
        pending = total - completed
        
        return {
            'total': total,
            'completed': completed,
            'pending': pending
        }
    
    def create_subtask(self, task_id: int, title: str, description: str = "", deadline: Optional[datetime] = None) -> SubTask:
        """
        Crea una nueva subtarea para una tarea.
        
        Args:
            task_id: ID de la tarea padre.
            title: Título de la subtarea.
            description: Descripción de la subtarea (opcional).
            deadline: Fecha límite de la subtarea (opcional).
            
        Returns:
            Subtarea creada.
        """
        if not title or not title.strip():
            raise ValueError("El título de la subtarea no puede estar vacío")
        
        subtask = SubTask(
            id=None,
            task_id=task_id,
            title=title.strip(),
            description=description.strip() if description else "",
            deadline=deadline,
            completed=False,
            created_at=None,
            updated_at=None
        )
        
        return self.repository.create_subtask(subtask)
    
    def update_subtask(self, subtask: SubTask) -> SubTask:
        """
        Actualiza una subtarea existente.
        
        Args:
            subtask: Subtarea con los datos actualizados.
            
        Returns:
            Subtarea actualizada.
        """
        if not subtask.title or not subtask.title.strip():
            raise ValueError("El título de la subtarea no puede estar vacío")
        
        subtask.title = subtask.title.strip()
        return self.repository.update_subtask(subtask)
    
    def delete_subtask(self, subtask_id: int) -> bool:
        """
        Elimina una subtarea.
        
        Args:
            subtask_id: ID de la subtarea a eliminar.
            
        Returns:
            True si se eliminó, False si no existía.
        """
        return self.repository.delete_subtask(subtask_id)
    
    def toggle_subtask_complete(self, subtask_id: int) -> Optional[SubTask]:
        """
        Cambia el estado de completado de una subtarea.
        
        Args:
            subtask_id: ID de la subtarea.
            
        Returns:
            Subtarea actualizada o None si no existe.
        """
        return self.repository.toggle_subtask_complete(subtask_id)

