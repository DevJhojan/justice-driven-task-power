"""
Modelo de Tarea (Task)
Representa una tarea con sus atributos, subtareas y prioridad según la matriz de Eisenhower
"""

from datetime import datetime, date
from typing import Optional, List, TYPE_CHECKING
from dataclasses import dataclass, field
from app.utils.task_helper import (
    TASK_STATUS_PENDING,
    TASK_STATUS_IN_PROGRESS,
    TASK_STATUS_COMPLETED,
    TASK_STATUS_CANCELLED,
    VALID_TASK_STATUSES,
)

if TYPE_CHECKING:
    from app.models.subtask import Subtask


@dataclass
class Task:
    """
    Modelo de Tarea
    
    Attributes:
        id: Identificador único de la tarea
        title: Título de la tarea
        description: Descripción detallada de la tarea
        status: Estado de la tarea (pendiente, en_progreso, completada, cancelada)
        urgent: Si la tarea es urgente (para matriz de Eisenhower)
        important: Si la tarea es importante (para matriz de Eisenhower)
        due_date: Fecha de vencimiento (opcional)
        created_at: Fecha de creación
        updated_at: Fecha de última actualización
        subtasks: Lista de subtareas
        user_id: ID del usuario propietario
        tags: Lista de etiquetas (opcional)
        notes: Notas adicionales (opcional)
    """
    id: str
    title: str
    description: str = ""
    status: str = TASK_STATUS_PENDING
    urgent: bool = False
    important: bool = False
    due_date: Optional[date] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    subtasks: List['Subtask'] = field(default_factory=list)  # type: ignore
    user_id: str = ""
    tags: List[str] = field(default_factory=list)
    notes: str = ""
    
    def __post_init__(self):
        """Valida los datos después de la inicialización"""
        self._validate_status()
        self._validate_title()
    
    def _validate_status(self):
        """Valida que el estado sea válido"""
        if self.status not in VALID_TASK_STATUSES:
            raise ValueError(f"Estado inválido: {self.status}. Debe ser uno de {VALID_TASK_STATUSES}")
    
    def _validate_title(self):
        """Valida que el título no esté vacío"""
        if not self.title or not self.title.strip():
            raise ValueError("El título de la tarea no puede estar vacío")
    
    def add_subtask(self, subtask: 'Subtask'):
        """
        Agrega una subtarea a la tarea
        
        Args:
            subtask: Subtarea a agregar
        """
        if subtask.task_id != self.id:
            subtask.task_id = self.id
        self.subtasks.append(subtask)
        self.updated_at = datetime.now()
    
    def remove_subtask(self, subtask_id: str):
        """
        Elimina una subtarea de la tarea
        
        Args:
            subtask_id: ID de la subtarea a eliminar
        """
        self.subtasks = [st for st in self.subtasks if st.id != subtask_id]
        self.updated_at = datetime.now()
    
    def update_status(self, new_status: str):
        """
        Actualiza el estado de la tarea
        
        Args:
            new_status: Nuevo estado
        """
        if new_status not in VALID_TASK_STATUSES:
            raise ValueError(f"Estado inválido: {new_status}")
        self.status = new_status
        self.updated_at = datetime.now()
    
    def set_priority(self, urgent: bool, important: bool):
        """
        Establece la prioridad de la tarea según la matriz de Eisenhower
        
        Args:
            urgent: Si la tarea es urgente
            important: Si la tarea es importante
        """
        self.urgent = urgent
        self.important = important
        self.updated_at = datetime.now()
    
    def mark_as_completed(self):
        """Marca la tarea como completada"""
        self.update_status(TASK_STATUS_COMPLETED)
    
    def mark_as_in_progress(self):
        """Marca la tarea como en progreso"""
        self.update_status(TASK_STATUS_IN_PROGRESS)
    
    def mark_as_pending(self):
        """Marca la tarea como pendiente"""
        self.update_status(TASK_STATUS_PENDING)
    
    def cancel(self):
        """Cancela la tarea"""
        self.update_status(TASK_STATUS_CANCELLED)
    
    def update_status_from_subtasks(self):
        """
        Actualiza automáticamente el estado de la tarea basado en sus subtareas.
        
        Lógica:
        - Sin subtareas: Se controla manualmente mediante checkbox
        - Con subtareas:
          * Ninguna completada → pendiente
          * Al menos 1 completada → en progreso
          * Todas completadas → completada
        """
        if not self.subtasks:
            # Sin subtareas, mantener estado actual (controlado por checkbox)
            return
        
        completed_count = sum(1 for st in self.subtasks if st.completed)
        total_count = len(self.subtasks)
        
        if completed_count == 0:
            # Ninguna subtarea completada
            self.status = TASK_STATUS_PENDING
        elif completed_count == total_count:
            # Todas las subtareas completadas
            self.status = TASK_STATUS_COMPLETED
        else:
            # Al menos una pero no todas
            self.status = TASK_STATUS_IN_PROGRESS
        
        self.updated_at = datetime.now()
    
    def to_dict(self) -> dict:
        """
        Convierte la tarea a diccionario
        
        Returns:
            Diccionario con los datos de la tarea
        """
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "status": self.status,
            "urgent": self.urgent,
            "important": self.important,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "subtasks": [subtask.to_dict() for subtask in self.subtasks],
            "user_id": self.user_id,
            "tags": self.tags,
            "notes": self.notes,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Task':
        """
        Crea una instancia de Task desde un diccionario
        
        Args:
            data: Diccionario con los datos de la tarea
            
        Returns:
            Instancia de Task
        """
        # Convertir fechas
        due_date = None
        if data.get("due_date"):
            if isinstance(data["due_date"], str):
                due_date = datetime.fromisoformat(data["due_date"]).date()
            elif isinstance(data["due_date"], date):
                due_date = data["due_date"]
        
        created_at = datetime.now()
        if data.get("created_at"):
            if isinstance(data["created_at"], str):
                created_at = datetime.fromisoformat(data["created_at"])
            elif isinstance(data["created_at"], datetime):
                created_at = data["created_at"]
        
        updated_at = datetime.now()
        if data.get("updated_at"):
            if isinstance(data["updated_at"], str):
                updated_at = datetime.fromisoformat(data["updated_at"])
            elif isinstance(data["updated_at"], datetime):
                updated_at = data["updated_at"]
        
        # Convertir subtareas
        subtasks = []
        if data.get("subtasks"):
            from app.models.subtask import Subtask
            subtasks = [Subtask.from_dict(st) for st in data["subtasks"]]
        
        return cls(
            id=data["id"],
            title=data["title"],
            description=data.get("description", ""),
            status=data.get("status", TASK_STATUS_PENDING),
            urgent=data.get("urgent", False),
            important=data.get("important", False),
            due_date=due_date,
            created_at=created_at,
            updated_at=updated_at,
            subtasks=subtasks,
            user_id=data.get("user_id", ""),
            tags=data.get("tags", []),
            notes=data.get("notes", ""),
        )
    
    def __repr__(self) -> str:
        """Representación string de la tarea"""
        return f"Task(id='{self.id}', title='{self.title}', status='{self.status}')"

