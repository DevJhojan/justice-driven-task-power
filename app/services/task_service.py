"""
Servicio de lógica de negocio para tareas.
"""
from typing import List, Optional

from app.data.models import Task, Subtask
from app.data.task_repository import TaskRepository
from app.data.subtask_repository import SubtaskRepository


class TaskService:
    """Servicio para gestión de tareas."""
    
    def __init__(self, task_repository: TaskRepository, subtask_repository: Optional[SubtaskRepository] = None):
        """
        Inicializa el servicio.
        
        Args:
            task_repository: Repositorio de tareas.
            subtask_repository: Repositorio de subtareas (opcional).
        """
        self.repository = task_repository
        self.subtask_repository = subtask_repository
    
    def create_task(self, title: str, description: Optional[str] = None, 
                   due_date: Optional[str] = None) -> Task:
        """
        Crea una nueva tarea.
        
        Args:
            title: Título de la tarea.
            description: Descripción de la tarea.
            due_date: Fecha de vencimiento en formato ISO (YYYY-MM-DD).
            
        Returns:
            Tarea creada.
        """
        from datetime import date
        
        task = Task(
            id=None,
            title=title,
            description=description,
            due_date=date.fromisoformat(due_date) if due_date else None,
            status="pendiente"
        )
        
        return self.repository.create(task)
    
    def get_task(self, task_id: int) -> Optional[Task]:
        """
        Obtiene una tarea por su ID.
        
        Args:
            task_id: ID de la tarea.
            
        Returns:
            Tarea si existe, None en caso contrario.
        """
        return self.repository.get_by_id(task_id)
    
    def get_all_tasks(self) -> List[Task]:
        """
        Obtiene todas las tareas.
        
        Returns:
            Lista de todas las tareas.
        """
        return self.repository.get_all()
    
    def get_pending_tasks(self) -> List[Task]:
        """
        Obtiene todas las tareas pendientes.
        
        Returns:
            Lista de tareas pendientes.
        """
        return self.repository.get_by_status("pendiente")
    
    def get_completed_tasks(self) -> List[Task]:
        """
        Obtiene todas las tareas completadas.
        
        Returns:
            Lista de tareas completadas.
        """
        return self.repository.get_by_status("completada")
    
    def update_task(self, task: Task) -> Task:
        """
        Actualiza una tarea.
        
        Args:
            task: Tarea a actualizar.
            
        Returns:
            Tarea actualizada.
        """
        return self.repository.update(task)
    
    def mark_as_completed(self, task_id: int, points_service=None) -> bool:
        """
        Marca una tarea como completada.
        
        Args:
            task_id: ID de la tarea.
            points_service: Servicio de puntos para agregar puntos al completar.
        
        Returns:
            True si se actualizó correctamente, False si no existe.
        """
        task = self.repository.get_by_id(task_id)
        if task is None:
            return False
        
        # Solo agregar puntos si la tarea no estaba ya completada
        was_completed = task.status == "completada"
        
        task.status = "completada"
        self.repository.update(task)
        
        # Agregar puntos si se completó (no si ya estaba completada)
        if not was_completed and points_service:
            points_service.add_points(0.05)  # 0.05 puntos por completar una tarea
        
        return True
    
    def mark_as_pending(self, task_id: int, points_service=None) -> bool:
        """
        Marca una tarea como pendiente.
        
        Args:
            task_id: ID de la tarea.
            points_service: Servicio de puntos para restar puntos al desmarcar.
        
        Returns:
            True si se actualizó correctamente, False si no existe.
        """
        task = self.repository.get_by_id(task_id)
        if task is None:
            return False
        
        # Solo restar puntos si la tarea estaba completada
        was_completed = task.status == "completada"
        
        task.status = "pendiente"
        self.repository.update(task)
        
        # Restar puntos si se desmarcó (estaba completada)
        if was_completed and points_service:
            points_service.add_points(-0.05)  # Restar 0.05 puntos al desmarcar una tarea
        
        return True
    
    def delete_task(self, task_id: int) -> bool:
        """
        Elimina una tarea.
        
        Args:
            task_id: ID de la tarea a eliminar.
            
        Returns:
            True si se eliminó, False si no existía.
        """
        return self.repository.delete(task_id)
    
    # Métodos de subtareas
    def get_subtasks(self, task_id: int) -> List[Subtask]:
        """
        Obtiene todas las subtareas de una tarea.
        
        Args:
            task_id: ID de la tarea.
        
        Returns:
            Lista de subtareas.
        """
        if not self.subtask_repository:
            return []
        return self.subtask_repository.get_by_task_id(task_id)
    
    def create_subtask(self, task_id: int, title: str) -> Optional[Subtask]:
        """
        Crea una nueva subtarea.
        
        Args:
            task_id: ID de la tarea padre.
            title: Título de la subtarea.
        
        Returns:
            Subtarea creada, None si el repositorio no está disponible.
        """
        if not self.subtask_repository:
            return None
        
        subtask = Subtask(
            id=None,
            task_id=task_id,
            title=title,
            completed=False
        )
        return self.subtask_repository.create(subtask)
    
    def toggle_subtask(self, subtask_id: int) -> bool:
        """
        Alterna el estado de completado de una subtarea.
        
        Args:
            subtask_id: ID de la subtarea.
        
        Returns:
            True si ahora está completada, False si se desmarcó.
        """
        if not self.subtask_repository:
            return False
        
        subtask = self.subtask_repository.get_by_id(subtask_id)
        if subtask is None:
            return False
        
        subtask.completed = not subtask.completed
        self.subtask_repository.update(subtask)
        return subtask.completed
    
    def delete_subtask(self, subtask_id: int) -> bool:
        """
        Elimina una subtarea.
        
        Args:
            subtask_id: ID de la subtarea a eliminar.
        
        Returns:
            True si se eliminó, False si no existía.
        """
        if not self.subtask_repository:
            return False
        return self.subtask_repository.delete(subtask_id)
    
    def update_subtask(self, subtask: Subtask) -> Optional[Subtask]:
        """
        Actualiza una subtarea.
        
        Args:
            subtask: Subtarea a actualizar.
        
        Returns:
            Subtarea actualizada, None si el repositorio no está disponible.
        """
        if not self.subtask_repository:
            return None
        return self.subtask_repository.update(subtask)

