"""
Modelo de Usuario
Representa la información del usuario en el sistema
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import uuid


@dataclass
class User:
    """
    Modelo de Usuario
    
    Attributes:
        id: Identificador único del usuario
        username: Nombre de usuario
        email: Correo electrónico
        points: Puntos acumulados
        level: Nivel actual
        created_at: Fecha de creación
        updated_at: Fecha de última actualización
        is_active: Si la cuenta está activa
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    username: str = ""
    email: str = ""
    points: float = 0.0
    level: str = "Nadie"
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    is_active: bool = True
    
    def __post_init__(self):
        """Valida los datos"""
        if not self.username or not self.username.strip():
            raise ValueError("El nombre de usuario es requerido")
    
    def add_points(self, amount: float):
        """
        Añade puntos al usuario
        
        Args:
            amount: Cantidad de puntos a añadir
        """
        if amount < 0:
            raise ValueError("Los puntos no pueden ser negativos")
        self.points += amount
        self.updated_at = datetime.now()
    
    def set_level(self, level: str):
        """
        Establece el nivel del usuario
        
        Args:
            level: Nivel a establecer
        """
        self.level = level
        self.updated_at = datetime.now()
    
    def to_dict(self) -> dict:
        """
        Convierte el usuario a diccionario
        
        Returns:
            Diccionario con los datos del usuario
        """
        # Convertir timestamps a ISO format, manejando casos donde ya son strings
        created_at = self.created_at if isinstance(self.created_at, str) else self.created_at.isoformat()
        updated_at = self.updated_at if isinstance(self.updated_at, str) else self.updated_at.isoformat()
        
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "points": self.points,
            "level": self.level,
            "created_at": created_at,
            "updated_at": updated_at,
            "is_active": self.is_active,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'User':
        """
        Crea una instancia de User desde un diccionario
        
        Args:
            data: Diccionario con los datos del usuario
            
        Returns:
            Instancia de User
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
            username=data.get("username", ""),
            email=data.get("email", ""),
            points=data.get("points", 0.0),
            level=data.get("level", "Nadie"),
            created_at=created_at,
            updated_at=updated_at,
            is_active=data.get("is_active", True),
        )
