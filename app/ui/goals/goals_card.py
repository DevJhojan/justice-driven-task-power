"""
Componente Card para mostrar una meta individual
"""
import flet as ft
from app.models.goal import Goal

class GoalsCard(ft.Card):
    def __init__(self, goal: Goal, on_edit, on_delete, on_progress_update=None):
        super().__init__()
        self.goal = goal
        self.on_edit = on_edit
        self.on_delete = on_delete
        self.on_progress_update = on_progress_update

        self.title = ft.Text(goal.title, size=18, weight=ft.FontWeight.BOLD)
        self.desc = ft.Text(goal.description, size=14, color=ft.Colors.GREY_700)
        self.type = ft.Text(f"Tipo: {goal.goal_type}", size=12, color=ft.Colors.GREY_600)
        self.unit = ft.Text(f"Unidad: {goal.unit_type if goal.unit_type != 'otro' else goal.custom_unit}", size=12, color=ft.Colors.GREY_600)
        self.target = ft.Text(f"Objetivo: {goal.target}", size=12, color=ft.Colors.GREY_600)
        self.progress = ft.Text(f"Progreso: {goal.progress}", size=12, color=ft.Colors.GREY_600)

        self.progress_bar = ft.ProgressBar(
            value=min(goal.progress / goal.target, 1.0) if goal.target > 0 else 0,
            width=200,
            color=ft.Colors.BLUE_400,
        )

        self.edit_btn = ft.IconButton(ft.Icons.EDIT.value, tooltip="Editar", on_click=lambda _: self.on_edit(goal))
        self.delete_btn = ft.IconButton(ft.Icons.DELETE.value, tooltip="Eliminar", on_click=lambda _: self.on_delete(goal))

        # Botón para actualizar progreso
        self.add_progress_btn = ft.IconButton(ft.Icons.ADD.value, tooltip="Sumar progreso", on_click=self._handle_add_progress)

        self.content = ft.Container(
            ft.Column([
                self.title,
                self.desc,
                ft.Row([self.type, self.unit]),
                ft.Row([self.target, self.progress]),
                self.progress_bar,
                ft.Row([self.edit_btn, self.delete_btn, self.add_progress_btn], alignment=ft.MainAxisAlignment.END),
            ], spacing=6),
            padding=16,
        )
        self.elevation = 2
        self.margin = 8

    def _handle_add_progress(self, _):
        if self.on_progress_update:
            self.on_progress_update(self.goal)
