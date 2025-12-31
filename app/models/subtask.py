"""
Modelo de Subtarea (Subtask)
Representa una subtarea asociada a una tarea principal
"""

from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Subtask:
    """
    Modelo de Subtarea
    
    Attributes:
        id: Identificador único de la subtarea
        task_id: ID de la tarea padre
        title: Título de la subtarea
        completed: Si la subtarea está completada
        urgent: Si la subtarea es urgente (para matriz de Eisenhower)
        important: Si la subtarea es importante (para matriz de Eisenhower)
        created_at: Fecha de creación
        updated_at: Fecha de última actualización
        notes: Notas adicionales (opcional)
    """
    id: str
    task_id: str
    title: str
    completed: bool = False
    urgent: bool = False
    important: bool = False
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    notes: str = ""
    
    def __post_init__(self):
        """Valida los datos después de la inicialización"""
        self._validate_title()
    
    def _validate_title(self):
        """Valida que el título no esté vacío"""
        if not self.title or not self.title.strip():
            raise ValueError("El título de la subtarea no puede estar vacío")
    
    def toggle_completed(self):
        """Alterna el estado de completitud de la subtarea"""
        self.completed = not self.completed
        self.updated_at = datetime.now()
    
    def mark_as_completed(self):
        """Marca la subtarea como completada"""
        self.completed = True
        self.updated_at = datetime.now()
    
    def mark_as_pending(self):
        """Marca la subtarea como pendiente"""
        self.completed = False
        self.updated_at = datetime.now()
    
    def set_priority(self, urgent: bool, important: bool):
        """
        Establece la prioridad de la subtarea según la matriz de Eisenhower
        
        Args:
            urgent: Si la subtarea es urgente
            important: Si la subtarea es importante
        """
        self.urgent = urgent
        self.important = important
        self.updated_at = datetime.now()
    
    def to_dict(self) -> dict:
        """
        Convierte la subtarea a diccionario
        
        Returns:
            Diccionario con los datos de la subtarea
        """
        return {
            "id": self.id,
            "task_id": self.task_id,
            "title": self.title,
            "completed": self.completed,
            "urgent": self.urgent,
            "important": self.important,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "notes": self.notes,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Subtask':
        """
        Crea una instancia de Subtask desde un diccionario
        
        Args:
            data: Diccionario con los datos de la subtarea
            
        Returns:
            Instancia de Subtask
        """
        # Convertir fechas
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
        
        return cls(
            id=data["id"],
            task_id=data["task_id"],
            title=data["title"],
            completed=data.get("completed", False),
            urgent=data.get("urgent", False),
            important=data.get("important", False),
            created_at=created_at,
            updated_at=updated_at,
            notes=data.get("notes", ""),
        )
    
    def __repr__(self) -> str:
        """Representación string de la subtarea"""
        status = "✓" if self.completed else "○"
        return f"Subtask(id='{self.id}', title='{self.title}', {status})"

