"""
Vista de gráficos para un hábito.
"""

import flet as ft
from app.models.habit import Habit


class HabitGraphics:
	"""Construye una vista simple de gráficos para un hábito."""

	def __init__(self, habit: Habit):
		self.habit = habit

	def build(self) -> ft.Column:
		habit = self.habit
		target = max(1, habit.frequency_times)
		progress_value = min(habit.streak, target) / target

		return ft.Column(
			[
				ft.Text(habit.title, size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
				ft.Text(habit.description or "", size=12, color=ft.Colors.WHITE_70),
				ft.Text(
					f"Frecuencia: {habit.frequency} | Veces por periodo: {habit.frequency_times}",
					size=12,
					color=ft.Colors.WHITE_70,
				),
				ft.Divider(color=ft.Colors.WHITE_10),
				ft.Text("Progreso del periodo", weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
				ft.ProgressBar(value=progress_value, color=ft.Colors.RED_400, bgcolor=ft.Colors.WHITE24),
				ft.Text(
					f"{min(habit.streak, target)}/{target} completado(s) del periodo",
					size=12,
					color=ft.Colors.WHITE,
				),
				ft.Divider(color=ft.Colors.WHITE_10),
				ft.Text("Racha", weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
				ft.Row(
					[
						ft.Icon(ft.Icons.WHATSHOT, color=ft.Colors.RED_400),
						ft.Text(f"Racha actual: {habit.streak}", color=ft.Colors.WHITE),
					]
				),
			],
			spacing=10,
			width=350,
		)
