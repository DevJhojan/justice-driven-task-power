"""
Servicio de Usuario
Gestiona la lógica de puntos y nivel del usuario
"""
from app.models.user import User
from app.logic.system_points import PointsSystem, POINTS_BY_ACTION

class UserService:
    def __init__(self, user: User):
        self.user = user

    def add_points_for_goal(self, goal_class: str):
        if goal_class == "reductual":
            action = "goal_decrement_completed"
        else:
            action = "goal_increment_completed"
        self.user.points = PointsSystem.add_points(self.user.points, action)
        self.user.level = PointsSystem.get_level_by_points(self.user.points).value
        self.user.updated_at = self.user.updated_at.now()
        # Aquí podrías persistir el usuario si tienes BD

    def get_points(self):
        return self.user.points

    def get_level(self):
        return self.user.level
