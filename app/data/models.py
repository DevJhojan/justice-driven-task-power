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
    priority: str  # 'urgent_important', 'not_urgent_important', 'urgent_not_important', 'not_urgent_not_important'
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
            self.priority = 'not_urgent_important'  # Por defecto: No Urgente e Importante
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
            priority=data.get('priority', 'not_urgent_important'),
            subtasks=subtasks
        )


@dataclass
class HabitCompletion:
    """Modelo de un registro de cumplimiento de hábito."""
    id: Optional[int]
    habit_id: int  # ID del hábito
    completion_date: datetime  # Fecha de cumplimiento (solo fecha, sin hora)
    created_at: Optional[datetime]
    
    def __post_init__(self):
        """Inicializa valores por defecto."""
        if self.id is None:
            self.id = None
        if self.created_at is None:
            self.created_at = datetime.now()
        # Normalizar la fecha de cumplimiento a medianoche (solo fecha)
        if isinstance(self.completion_date, datetime):
            self.completion_date = self.completion_date.replace(hour=0, minute=0, second=0, microsecond=0)
    
    def to_dict(self) -> dict:
        """Convierte el cumplimiento a un diccionario."""
        return {
            'id': self.id,
            'habit_id': self.habit_id,
            'completion_date': self.completion_date.isoformat() if self.completion_date else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'HabitCompletion':
        """Crea un cumplimiento desde un diccionario."""
        created_at = None
        completion_date = None
        
        if data.get('created_at'):
            created_at = datetime.fromisoformat(data['created_at'])
        if data.get('completion_date'):
            completion_date = datetime.fromisoformat(data['completion_date'])
            # Normalizar a medianoche
            completion_date = completion_date.replace(hour=0, minute=0, second=0, microsecond=0)
        
        return cls(
            id=data.get('id'),
            habit_id=data.get('habit_id', 0),
            completion_date=completion_date,
            created_at=created_at
        )


@dataclass
class Habit:
    """Modelo de un hábito."""
    id: Optional[int]
    title: str
    description: str
    frequency: str  # 'daily', 'weekly', 'custom'
    target_days: int  # Número de días objetivo por semana (para weekly) o días personalizados
    active: bool  # Si el hábito está activo o inactivo
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    completions: List[HabitCompletion] = field(default_factory=list)  # Historial de cumplimientos
    
    def __post_init__(self):
        """Inicializa valores por defecto."""
        if self.id is None:
            self.id = None
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()
        if not self.frequency:
            self.frequency = 'daily'
        if self.target_days is None or self.target_days < 1:
            self.target_days = 7 if self.frequency == 'weekly' else 1
        if self.completions is None:
            self.completions = []
    
    def to_dict(self) -> dict:
        """Convierte el hábito a un diccionario."""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'frequency': self.frequency,
            'target_days': self.target_days,
            'active': self.active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'completions': [c.to_dict() for c in self.completions]
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Habit':
        """Crea un hábito desde un diccionario."""
        created_at = None
        updated_at = None
        
        if data.get('created_at'):
            created_at = datetime.fromisoformat(data['created_at'])
        if data.get('updated_at'):
            updated_at = datetime.fromisoformat(data['updated_at'])
        
        completions = []
        if data.get('completions'):
            completions = [HabitCompletion.from_dict(c) for c in data['completions']]
        
        return cls(
            id=data.get('id'),
            title=data.get('title', ''),
            description=data.get('description', ''),
            frequency=data.get('frequency', 'daily'),
            target_days=data.get('target_days', 7),
            active=bool(data.get('active', True)),
            created_at=created_at,
            updated_at=updated_at,
            completions=completions
        )

