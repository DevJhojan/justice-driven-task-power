"""
Modelo de Hábito (Habit Model)
Define la estructura de datos para un hábito con racha diaria
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from typing import Optional
import uuid


@dataclass
class Habit:
    """Modelo de datos para un hábito"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    description: str = ""
    frequency: str = "daily"  # daily o weekly
    streak: int = 0
    last_completed: Optional[str] = None  # ISO format datetime
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> dict:
        """Convierte el hábito a diccionario"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> "Habit":
        """Crea un hábito desde un diccionario"""
        return cls(**data)
    
    def complete_today(self) -> None:
        """Marca el hábito como completado hoy"""
        today = datetime.now().date().isoformat()
        
        if self.last_completed is None:
            # Primera vez completando
            self.streak = 1
        else:
            # Checar si fue completado hoy
            last_date = datetime.fromisoformat(self.last_completed).date().isoformat()
            if last_date != today:
                # Checar si fue completado ayer
                yesterday = (datetime.now().date() - timedelta(days=1)).isoformat()
                if last_date == yesterday:
                    # Continuar la racha
                    self.streak += 1
                else:
                    # Romper la racha
                    self.streak = 1
        
        self.last_completed = datetime.now().isoformat()
    
    def was_completed_today(self) -> bool:
        """Verifica si fue completado hoy"""
        if self.last_completed is None:
            return False
        today = datetime.now().date().isoformat()
        last_date = datetime.fromisoformat(self.last_completed).date().isoformat()
        return last_date == today
