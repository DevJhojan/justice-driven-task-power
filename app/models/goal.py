"""
Modelo de Meta (Goal)
"""
from dataclasses import dataclass, field
from datetime import datetime
import uuid

@dataclass
class Goal:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    description: str = ""
    goal_type: str = "Salud"
    unit_type: str = "kilos"
    custom_unit: str = ""
    target: float = 0.0
    progress: float = 0.0
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def update(self, **kwargs):
        for key, value in kwargs.items():
            if hasattr(self, key) and key != 'id' and key != 'created_at':
                setattr(self, key, value)
        self.updated_at = datetime.now()

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "goal_type": self.goal_type,
            "unit_type": self.unit_type,
            "custom_unit": self.custom_unit,
            "target": self.target,
            "progress": self.progress,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data):
        def parse_dt(val):
            if isinstance(val, datetime):
                return val
            if isinstance(val, str):
                try:
                    return datetime.fromisoformat(val)
                except Exception:
                    return datetime.now()
            return datetime.now()
        obj = cls(
            id=data.get("id", str(uuid.uuid4())),
            title=data.get("title", ""),
            description=data.get("description", ""),
            goal_type=data.get("goal_type", "Salud"),
            unit_type=data.get("unit_type", "kilos"),
            custom_unit=data.get("custom_unit", ""),
            target=float(data.get("target", 0.0)),
            progress=float(data.get("progress", 0.0)),
            created_at=parse_dt(data["created_at"]) if "created_at" in data else datetime.now(),
            updated_at=parse_dt(data["updated_at"]) if "updated_at" in data else datetime.now(),
        )
        # goal_class puede no estar en el dataclass, pero lo agregamos dinámicamente
        setattr(obj, "goal_class", data.get("goal_class", "incremental"))
        return obj
