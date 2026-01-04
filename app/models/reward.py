"""
Modelo de Recompensa (Reward)
Representa una recompensa que el usuario puede desbloquear
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import uuid


@dataclass
class Reward:
    """
    Modelo de Recompensa
    
    Attributes:
        id: Identificador único de la recompensa
        title: Título de la recompensa
        description: Descripción de la recompensa
        points_required: Puntos requeridos para desbloquear
        icon: Icono/emoji de la recompensa
        color: Color hexadecimal
        is_active: Si la recompensa está activa
        created_at: Fecha de creación
        updated_at: Fecha de última actualización
        category: Categoría de la recompensa (badge, achievement, etc)
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    description: str = ""
    points_required: float = 0.0
    icon: str = "🎁"
    color: str = "#FFD700"
    is_active: bool = True
    category: str = "badge"
    claimed: bool = False
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """Valida los datos"""
        if not self.title or not self.title.strip():
            raise ValueError("El título de la recompensa es requerido")
        if self.points_required < 0:
            raise ValueError("Los puntos requeridos no pueden ser negativos")
    
    def update(self, **kwargs):
        """
        Actualiza los datos de la recompensa
        
        Args:
            **kwargs: Campos a actualizar
        """
        for key, value in kwargs.items():
            if hasattr(self, key) and key != 'id' and key != 'created_at':
                setattr(self, key, value)
        self.updated_at = datetime.now()
    
    def to_dict(self) -> dict:
        """
        Convierte la recompensa a diccionario
        
        Returns:
            Diccionario con los datos de la recompensa
        """
        # Convertir timestamps a ISO format, manejando casos donde ya son strings
        created_at = self.created_at if isinstance(self.created_at, str) else self.created_at.isoformat()
        updated_at = self.updated_at if isinstance(self.updated_at, str) else self.updated_at.isoformat()
        
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "points_required": self.points_required,
            "icon": self.icon,
            "color": self.color,
            "is_active": self.is_active,
            "category": self.category,
            "claimed": self.claimed,
            "created_at": created_at,
            "updated_at": updated_at,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Reward':
        """
        Crea una instancia de Reward desde un diccionario
        
        Args:
            data: Diccionario con los datos de la recompensa
            
        Returns:
            Instancia de Reward
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
            id=data.get("id", str(uuid.uuid4())),
            title=data.get("title", ""),
            description=data.get("description", ""),
            points_required=data.get("points_required", 0.0),
            icon=data.get("icon", "🎁"),
            color=data.get("color", "#FFD700"),
            is_active=data.get("is_active", True),
            category=data.get("category", "badge"),
            claimed=data.get("claimed", False),
            created_at=created_at,
            updated_at=updated_at,
        )
