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

        self.title = ft.Text(goal.title, size=18, weight=ft.FontWeight.BOLD, color="#FF5252")
        self.desc = ft.Text(goal.description, size=14, color="#FF8A80")
        self.type = ft.Text(f"Tipo: {goal.goal_type}", size=12, color="#FF1744")
        self.unit = ft.Text(f"Unidad: {goal.unit_type if goal.unit_type != 'otro' else goal.custom_unit}", size=12, color="#FF1744")
        self.goal_class = getattr(goal, "goal_class", "incremental")
        self.target = ft.Text(f"Objetivo: {goal.target}", size=12, color="#FF5252")
        self.progress = ft.Text(f"Progreso: {goal.progress}", size=12, color="#FF5252")

        self.progress_bar = ft.ProgressBar(
            value=min(goal.progress / goal.target, 1.0) if goal.target > 0 else 0,
            width=200,
            color="#FF1744",
            bgcolor="#2a2a2a",
        )

        self.edit_btn = ft.IconButton(ft.Icons.EDIT.value, tooltip="Editar", on_click=lambda _: self.on_edit(goal), icon_color="#FF5252", bgcolor="#1a1a1a")
        self.delete_btn = ft.IconButton(ft.Icons.DELETE.value, tooltip="Eliminar", on_click=lambda _: self.on_delete(goal), icon_color="#FF1744", bgcolor="#1a1a1a")

        # Determinar si la meta está cumplida
        self.is_completed = goal.progress >= goal.target if goal.target > 0 else False

        # Botón para actualizar progreso (deshabilitado si está cumplida)
        if self.goal_class == "reductual":
            self.progress_btn = ft.IconButton(
                ft.Icons.REMOVE.value,
                tooltip="Reducir progreso",
                on_click=self._handle_reduce_progress,
                icon_color="#FF8A80",
                bgcolor="#1a1a1a",
                disabled=self.is_completed
            )
        else:
            self.progress_btn = ft.IconButton(
                ft.Icons.ADD.value,
                tooltip="Sumar progreso",
                on_click=self._handle_add_progress,
                icon_color="#FF8A80",
                bgcolor="#1a1a1a",
                disabled=self.is_completed
            )

        # Panel de meta cumplida
        self.completed_panel = None
        if self.is_completed:
            self.completed_panel = ft.Container(
                ft.Row([
                    ft.Icon(ft.Icons.CHECK_CIRCLE_OUTLINE, color="#4CAF50", size=20),
                    ft.Text("¡Meta cumplida!", color="#4CAF50", size=14, weight=ft.FontWeight.BOLD),
                ], alignment=ft.MainAxisAlignment.CENTER),
                padding=8,
                bgcolor="#232323",
                border_radius=8,
                margin=ft.margin.only(top=8),
            )

        # Construir el contenido de la card
        card_content = [
            self.title,
            self.desc,
            ft.Row([self.type, self.unit]),
            ft.Row([self.target, self.progress]),
            self.progress_bar,
            ft.Row([self.edit_btn, self.delete_btn, self.progress_btn], alignment=ft.MainAxisAlignment.END),
        ]
        if self.completed_panel:
            card_content.append(self.completed_panel)

        self.content = ft.Container(
            ft.Column(card_content, spacing=6),
            padding=16,
            bgcolor="#1a1a1a",
            border_radius=12,
            border=ft.border.all(1, "#FF1744"),
        )
        self.elevation = 4
        self.margin = 8

    def _handle_add_progress(self, _):
        if self.on_progress_update:
            self.on_progress_update(self.goal, action="incremental")

    def _handle_reduce_progress(self, _):
        if self.on_progress_update:
            self.on_progress_update(self.goal, action="reductual")
