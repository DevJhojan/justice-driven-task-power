"""
Lista de metas, muestra GoalsCard por cada meta
"""
import flet as ft
from typing import List, Callable
from app.models.goal import Goal
from app.ui.goals.goals_card import GoalsCard

class GoalsList(ft.Column):
    def __init__(self, goals: List[Goal], on_edit: Callable, on_delete: Callable, on_progress_update: Callable = None):
        super().__init__()
        self.goals = goals
        self.on_edit = on_edit
        self.on_delete = on_delete
        self.on_progress_update = on_progress_update
        self.spacing = 10
        self.controls = []
        self.refresh()

    def refresh(self):
        self.controls.clear()
        for goal in self.goals:
            card = GoalsCard(
                goal,
                on_edit=self.on_edit,
                on_delete=self.on_delete,
                on_progress_update=self.on_progress_update,
            )
            self.controls.append(card)
        # self.update() eliminado para evitar error antes de estar en la página

    def set_goals(self, goals: List[Goal]):
        self.goals = goals
        self.refresh()
        if hasattr(self, 'page') and self.page:
            self.update()
