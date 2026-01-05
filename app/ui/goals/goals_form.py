"""
Formulario para crear/editar metas medibles
"""
import flet as ft
from typing import Optional, Callable
from app.models.goal import Goal

GOAL_TYPES = [
    "Salud",
    "Finanzas",
    "Estudio",
    "Trabajo",
    "Personal",
    "Otro",
]

UNIT_TYPES = [
    "kilos",
    "libras",
    "horas",
    "páginas",
    "pasos",
    "veces",
    "unidades",
    "otro",
]

class GoalsForm(ft.Container):
    def __init__(self, on_save: Callable, on_cancel: Callable, editing_goal: Optional[Goal] = None):
        super().__init__()
        self.on_save = on_save
        self.on_cancel = on_cancel
        self.editing_goal = editing_goal

        self.title_input = ft.TextField(label="Título de la meta", expand=True)
        self.desc_input = ft.TextField(label="Descripción", expand=True, multiline=True, min_lines=2)
        self.goal_type_input = ft.Dropdown(
            label="Tipo de objetivo",
            options=[ft.dropdown.Option(t) for t in GOAL_TYPES],
            value=GOAL_TYPES[0],
        )
        self.unit_type_input = ft.Dropdown(
            label="Tipo de unidad",
            options=[ft.dropdown.Option(u) for u in UNIT_TYPES],
            value=UNIT_TYPES[0],
        )
        self.custom_unit_input = ft.TextField(label="¿Cuál es la unidad?", hint_text="Ej. kilómetros", visible=False)
        self.target_input = ft.TextField(label="Objetivo a alcanzar", hint_text="Ej. 70", keyboard_type=ft.KeyboardType.NUMBER)
        self.progress_input = ft.TextField(label="Progreso actual", hint_text="Ej. 0", keyboard_type=ft.KeyboardType.NUMBER, value="0")

        self.unit_type_input.on_change = self._on_unit_type_change

        self.save_btn = ft.FilledButton("Guardar", on_click=self._handle_save)
        self.cancel_btn = ft.TextButton("Cancelar", on_click=self._handle_cancel)

        self.content = ft.Column([
            ft.Text("Nueva Meta", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_400),
            self.title_input,
            self.desc_input,
            self.goal_type_input,
            self.unit_type_input,
            self.custom_unit_input,
            self.target_input,
            self.progress_input,
            ft.Row([self.save_btn, self.cancel_btn], spacing=10),
        ], spacing=12)
        self.padding = 20
        self.expand = True
        self.bgcolor = None

        if editing_goal:
            self.set_values(editing_goal)

    def set_values(self, goal: Goal):
        self.title_input.value = goal.title
        self.desc_input.value = goal.description
        self.goal_type_input.value = goal.goal_type
        self.unit_type_input.value = goal.unit_type
        self.custom_unit_input.value = goal.custom_unit
        self.custom_unit_input.visible = goal.unit_type == "otro"
        self.target_input.value = str(goal.target)
        self.progress_input.value = str(goal.progress)
        # self.update() eliminado para evitar error antes de estar en la página

    def get_values(self) -> dict:
        return {
            "title": (self.title_input.value or "").strip(),
            "description": self.desc_input.value or "",
            "goal_type": self.goal_type_input.value or GOAL_TYPES[0],
            "unit_type": self.custom_unit_input.value.strip() if self.unit_type_input.value == "otro" else self.unit_type_input.value or UNIT_TYPES[0],
            "custom_unit": self.custom_unit_input.value.strip() if self.unit_type_input.value == "otro" else "",
            "target": float(self.target_input.value or 0),
            "progress": float(self.progress_input.value or 0),
        }

    def _on_unit_type_change(self, e):
        if self.unit_type_input.value == "otro":
            self.custom_unit_input.visible = True
        else:
            self.custom_unit_input.visible = False
            self.custom_unit_input.value = ""
        self.update()

    def _handle_save(self, _):
        values = self.get_values()
        if not values["title"]:
            self.title_input.error_text = "El título es obligatorio"
            self.update()
            return
        if not values["target"]:
            self.target_input.error_text = "El objetivo es obligatorio"
            self.update()
            return
        self.title_input.error_text = None
        self.target_input.error_text = None
        self.on_save(values)

    def _handle_cancel(self, _):
        self.on_cancel()
