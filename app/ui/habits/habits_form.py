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
				ft.dropdown.Option("monthly", "Mensual"),
				ft.dropdown.Option("semiannual", "Semestral"),
				ft.dropdown.Option("annual", "Anual"),
			],
			value="daily",
		)
		self.frequency_dropdown.on_change = self._on_frequency_change
		self.frequency_times_input = ft.TextField(
			label="Veces por periodo",
			value="1",
			visible=False,
			keyboard_type=ft.KeyboardType.NUMBER,
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
					self.frequency_times_input,
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
			"frequency_times": self._get_frequency_times(),
		}

	def reset(self):
		self.title_input.value = ""
		self.description_input.value = ""
		self.frequency_dropdown.value = "daily"
		self.frequency_times_input.value = "1"
		self.frequency_times_input.visible = False
		self._safe_update_controls()

	def set_values(self, title: str = "", description: str = "", frequency: str = "daily", frequency_times: int = 1):
		self.title_input.value = title or ""
		self.description_input.value = description or ""
		self.frequency_dropdown.value = frequency or "daily"
		self.frequency_times_input.value = str(frequency_times or 1)
		self._on_frequency_change(None)

	def _on_frequency_change(self, e):
		frequency = (getattr(e, "control", None).value if e else None) or self.frequency_dropdown.value or "daily"
		label = self._get_frequency_times_label(frequency)
		show_input = frequency != "daily"
		self.frequency_times_input.label = label
		self.frequency_times_input.visible = show_input
		if not show_input:
			self.frequency_times_input.value = "1"
		elif not (self.frequency_times_input.value or "").strip():
			self.frequency_times_input.value = "1"
		self._safe_update_controls()

	def _safe_update_controls(self):
		try:
			if self.frequency_dropdown.page:
				self.frequency_dropdown.update()
			if self.frequency_times_input.page:
				self.frequency_times_input.update()
		except Exception:
			# Si no hay página todavía, se actualizará al renderizar
			pass

	def _get_frequency_times_label(self, frequency: str) -> str:
		labels = {
			"weekly": "Veces por semana",
			"monthly": "Veces por mes",
			"semiannual": "Veces por semestre",
			"annual": "Veces por año",
		}
		return labels.get(frequency, "Veces por periodo")

	def _get_frequency_times(self) -> int:
		try:
			value = int(self.frequency_times_input.value or 1)
			return value if value > 0 else 1
		except ValueError:
			return 1

