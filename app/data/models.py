"""
Modelos de datos para la aplicación de tareas.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Task:
    """Modelo de una tarea."""
    id: Optional[int]
    title: str
    description: str
    completed: bool
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    priority: str  # 'low', 'medium', 'high'
    
    def __post_init__(self):
        """Inicializa valores por defecto."""
        if self.id is None:
            self.id = None
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()
        if not self.priority:
            self.priority = 'medium'
    
    def to_dict(self) -> dict:
        """Convierte la tarea a un diccionario."""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'completed': self.completed,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'priority': self.priority
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Task':
        """Crea una tarea desde un diccionario."""
        created_at = None
        updated_at = None
        
        if data.get('created_at'):
            created_at = datetime.fromisoformat(data['created_at'])
        if data.get('updated_at'):
            updated_at = datetime.fromisoformat(data['updated_at'])
        
        return cls(
            id=data.get('id'),
            title=data.get('title', ''),
            description=data.get('description', ''),
            completed=bool(data.get('completed', False)),
            created_at=created_at,
            updated_at=updated_at,
            priority=data.get('priority', 'medium')
        )

