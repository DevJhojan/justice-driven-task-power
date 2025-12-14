"""
Modelos de datos para la aplicación de tareas.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List


@dataclass
class SubTask:
    """Modelo de una subtarea."""
    id: Optional[int]
    task_id: int  # ID de la tarea padre
    title: str
    description: str
    deadline: Optional[datetime]  # Límite de tiempo
    completed: bool
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    
    def __post_init__(self):
        """Inicializa valores por defecto."""
        if self.id is None:
            self.id = None
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()
        if self.description is None:
            self.description = ""
        if self.deadline is None:
            self.deadline = None
    
    def to_dict(self) -> dict:
        """Convierte la subtarea a un diccionario."""
        return {
            'id': self.id,
            'task_id': self.task_id,
            'title': self.title,
            'description': self.description,
            'deadline': self.deadline.isoformat() if self.deadline else None,
            'completed': self.completed,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'SubTask':
        """Crea una subtarea desde un diccionario."""
        created_at = None
        updated_at = None
        deadline = None
        
        if data.get('created_at'):
            created_at = datetime.fromisoformat(data['created_at'])
        if data.get('updated_at'):
            updated_at = datetime.fromisoformat(data['updated_at'])
        if data.get('deadline'):
            deadline = datetime.fromisoformat(data['deadline'])
        
        return cls(
            id=data.get('id'),
            task_id=data.get('task_id', 0),
            title=data.get('title', ''),
            description=data.get('description', ''),
            deadline=deadline,
            completed=bool(data.get('completed', False)),
            created_at=created_at,
            updated_at=updated_at
        )


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
    subtasks: List[SubTask] = field(default_factory=list)  # Lista de subtareas
    
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
        if self.subtasks is None:
            self.subtasks = []
    
    def to_dict(self) -> dict:
        """Convierte la tarea a un diccionario."""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'completed': self.completed,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'priority': self.priority,
            'subtasks': [st.to_dict() for st in self.subtasks]
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
        
        subtasks = []
        if data.get('subtasks'):
            subtasks = [SubTask.from_dict(st) for st in data['subtasks']]
        
        return cls(
            id=data.get('id'),
            title=data.get('title', ''),
            description=data.get('description', ''),
            completed=bool(data.get('completed', False)),
            created_at=created_at,
            updated_at=updated_at,
            priority=data.get('priority', 'medium'),
            subtasks=subtasks
        )

