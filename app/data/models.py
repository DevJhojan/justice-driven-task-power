"""
Modelos de datos para la aplicación.
Define las estructuras de datos para Tareas, Hábitos y Metas.
"""
from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional


@dataclass
class Subtask:
    """Modelo de una subtarea."""
    id: Optional[int]
    task_id: int
    title: str
    completed: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class Task:
    """Modelo de una tarea."""
    id: Optional[int]
    title: str
    description: Optional[str] = None
    due_date: Optional[date] = None
    status: str = "pendiente"  # pendiente, completada
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Validar datos después de la inicialización."""
        if self.status not in ["pendiente", "completada"]:
            raise ValueError(f"Estado inválido: {self.status}. Debe ser 'pendiente' o 'completada'")


@dataclass
class Habit:
    """Modelo de un hábito."""
    id: Optional[int]
    title: str
    description: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class HabitCompletion:
    """Modelo de un registro de completación de hábito."""
    id: Optional[int]
    habit_id: int
    completion_date: date
    created_at: Optional[datetime] = None


@dataclass
class Goal:
    """Modelo de una meta."""
    id: Optional[int]
    title: str
    description: Optional[str] = None
    target_value: Optional[float] = None
    current_value: float = 0.0
    unit: Optional[str] = None  # ej: "tareas", "días", "horas"
    period: str = "mes"  # semana, mes, trimestre, semestre, anual
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Validar período después de la inicialización."""
        valid_periods = ["semana", "mes", "trimestre", "semestre", "anual"]
        if self.period not in valid_periods:
            raise ValueError(f"Período inválido: {self.period}. Debe ser uno de {valid_periods}")

