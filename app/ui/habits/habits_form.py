"""
Componente de formulario para crear hábitos
"""

import flet as ft


class HabitsForm:
	"""Formulario reutilizable para crear hábitos"""

	def __init__(self, on_save, on_cancel):
		self.on_save = on_save
		self.on_cancel = on_cancel

		self.title_input = ft.TextField(label="Título del hábito", expand=True)
		self.description_input = ft.TextField(
			label="Descripción",
			expand=True,
			multiline=True,
			min_lines=2,
		)
		self.frequency_dropdown = ft.Dropdown(
			label="Frecuencia",
			options=[
				ft.dropdown.Option("daily", "Diario"),
				ft.dropdown.Option("weekly", "Semanal"),
			],
			value="daily",
		)

	def build(self) -> ft.Container:
		return ft.Container(
			content=ft.Column(
				[
					ft.Text(
						"Nuevo Hábito",
						size=24,
						weight=ft.FontWeight.BOLD,
						color=ft.Colors.WHITE,
					),
					self.title_input,
					self.description_input,
					self.frequency_dropdown,
					ft.Row(
						[
							ft.TextButton(
								"Cancelar",
								on_click=self.on_cancel,
								style=ft.ButtonStyle(color=ft.Colors.WHITE_70),
							),
							ft.FilledButton(
								"Guardar",
								on_click=self.on_save,
								style=ft.ButtonStyle(
									bgcolor=ft.Colors.RED_400,
									color=ft.Colors.WHITE,
								),
							),
						],
						spacing=8,
					),
				],
				spacing=16,
				scroll=ft.ScrollMode.AUTO,
			),
			padding=20,
			expand=True,
		)

	def get_values(self) -> dict:
		return {
			"title": (self.title_input.value or "").strip(),
			"description": self.description_input.value or "",
			"frequency": self.frequency_dropdown.value or "daily",
		}

	def reset(self):
		self.title_input.value = ""
		self.description_input.value = ""
		self.frequency_dropdown.value = "daily"

