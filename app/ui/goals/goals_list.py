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
        self.filter_state = "in_progress"  # Opciones: in_progress, completed

        # Barra de filtro
        self.filter_bar = ft.Row([
            ft.Text("Filtrar:", size=13, color="#FF1744"),
            ft.RadioGroup(
                content=ft.Row([
                    ft.Radio(value="in_progress", label="Metas en progreso"),
                    ft.Radio(value="completed", label="Metas completadas"),
                ], spacing=10),
                value="in_progress",
                on_change=self._on_filter_change,
            ),
        ], alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.CENTER, spacing=20)

        self.controls.append(self.filter_bar)
        self.refresh()

    def _on_filter_change(self, e):
        self.filter_state = e.control.value
        self.refresh()

    def refresh(self):
        # Mantener la barra de filtro arriba
        self.controls = [self.filter_bar]
        filtered_goals = []
        for g in self.goals:
            goal_class = getattr(g, "goal_class", "incremental")
            if self.filter_state == "in_progress":
                if goal_class == "incremental":
                    # Incremental: meta NO cumplida si progreso < objetivo
                    if not (g.target > 0 and g.progress >= g.target):
                        filtered_goals.append(g)
                else:  # reductual
                    # Reductual: meta NO cumplida si progreso > objetivo
                    if not (g.target > 0 and g.progress <= g.target):
                        filtered_goals.append(g)
            else:  # completed
                if goal_class == "incremental":
                    # Incremental: meta cumplida si progreso >= objetivo
                    if g.target > 0 and g.progress >= g.target:
                        filtered_goals.append(g)
                else:  # reductual
                    # Reductual: meta cumplida si progreso <= objetivo
                    if g.target > 0 and g.progress <= g.target:
                        filtered_goals.append(g)
        for goal in filtered_goals:
            card = GoalsCard(
                goal,
                on_edit=self.on_edit,
                on_delete=self.on_delete,
                on_progress_update=self.on_progress_update,
            )
            self.controls.append(card)

    def set_goals(self, goals: List[Goal]):
        self.goals = goals
        self.refresh()
        if hasattr(self, 'page') and self.page:
            self.update()
