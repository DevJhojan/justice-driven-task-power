"""
Servicio de Metas (GoalsService)
Gestiona operaciones CRUD y persistencia en memoria (puedes adaptar a BD)
"""
import asyncio
from typing import List, Optional
from app.models.goal import Goal
from app.services.database_service import DatabaseService, TableSchema

GOALS_TABLE = "goals"

GOALS_SCHEMA = TableSchema(
    table_name=GOALS_TABLE,
    columns={
        "id": "TEXT PRIMARY KEY",
        "title": "TEXT NOT NULL",
        "description": "TEXT",
        "goal_type": "TEXT",
        "unit_type": "TEXT",
        "custom_unit": "TEXT",
        "target": "REAL",
        "progress": "REAL",
        "created_at": "TEXT",
        "updated_at": "TEXT",
    },
    primary_key="id",
    indexes=["goal_type", "unit_type"]
)

class GoalsService:
    def __init__(self, db_service: DatabaseService = None):
        self.db = db_service or DatabaseService()
        self.db.register_table_schema(GOALS_SCHEMA)
        # La inicialización debe hacerse de forma asíncrona fuera del constructor

    async def create_goal(self, **kwargs) -> Goal:
        goal = Goal.from_dict(kwargs)
        await self.db.create(GOALS_TABLE, goal.to_dict())
        return goal

    async def get_goal(self, goal_id: str) -> Optional[Goal]:
        data = await self.db.get(GOALS_TABLE, goal_id)
        return Goal.from_dict(data) if data else None

    async def list_goals(self) -> List[Goal]:
        rows = await self.db.get_all(GOALS_TABLE, order_by="created_at DESC")
        return [Goal.from_dict(row) for row in rows]

    async def update_goal(self, goal_id: str, **kwargs) -> Optional[Goal]:
        updated = await self.db.update(GOALS_TABLE, goal_id, kwargs)
        return Goal.from_dict(updated) if updated else None

    async def delete_goal(self, goal_id: str) -> bool:
        return await self.db.delete(GOALS_TABLE, goal_id)
