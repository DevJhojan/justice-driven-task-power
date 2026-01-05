"""
Servicio de Metas (GoalsService)
Gestiona operaciones CRUD y persistencia en memoria (puedes adaptar a BD)
"""
from typing import List, Optional, Dict
from app.models.goal import Goal

class GoalsService:
    def __init__(self):
        self.goals: Dict[str, Goal] = {}

    def create_goal(self, **kwargs) -> Goal:
        goal = Goal.from_dict(kwargs)
        self.goals[goal.id] = goal
        return goal

    def get_goal(self, goal_id: str) -> Optional[Goal]:
        return self.goals.get(goal_id)

    def list_goals(self) -> List[Goal]:
        return list(self.goals.values())

    def update_goal(self, goal_id: str, **kwargs) -> Optional[Goal]:
        goal = self.get_goal(goal_id)
        if not goal:
            return None
        goal.update(**kwargs)
        self.goals[goal.id] = goal
        return goal

    def delete_goal(self, goal_id: str) -> bool:
        if goal_id in self.goals:
            del self.goals[goal_id]
            return True
        return False
