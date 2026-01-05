"""
Formulario para crear recompensas de manera sencilla.
"""

import flet as ft
from typing import Optional, Callable
from app.services.rewards_service import RewardsService
from app.models.reward import Reward


class RewardsForm(ft.Container):
	"""Formulario inline para agregar recompensas."""

	def __init__(self, rewards_service: Optional[RewardsService] = None, on_submit: Optional[Callable[[Reward], None]] = None, on_cancel: Optional[Callable[[], None]] = None):
		super().__init__()

		self.rewards_service = rewards_service or RewardsService()
		self.on_submit = on_submit
		self.on_cancel = on_cancel
		self.editing_reward_id: Optional[str] = None

		self.expand = True
		self.padding = 16
		self.border_radius = 10
		self.bgcolor = "#1a1a1a"
		self.border = ft.border.all(1, "#2a2a2a")

		self.title_input = ft.TextField(label="Título", hint_text="Ej. Insignia Ninja", autofocus=True)
		self.desc_input = ft.TextField(label="Descripción", hint_text="¿Qué desbloquea?", multiline=True, max_lines=3)
		self.points_input = ft.TextField(label="Puntos requeridos", value="1.0", keyboard_type=ft.KeyboardType.NUMBER)
		self.icon_value = "🎁"
		self.icon_button = ft.ElevatedButton(
			content=ft.Row(
				spacing=6,
				vertical_alignment=ft.CrossAxisAlignment.CENTER,
				controls=[ft.Text("Elegir icono", weight="bold"), ft.Text(self.icon_value, size=20)],
			),
			on_click=self._toggle_icon_panel,
		)
		self._icon_panel = self._build_icon_panel()
		self._icon_panel.visible = False
		self.color_input = ft.TextField(label="Color (hex)", hint_text="#FFD700", value="#FFD700")
		self.category_dropdown = ft.Dropdown(
			label="Categoría de recompensa",
			value="Recompensas pequeñas",
			options=[
				ft.dropdown.Option("Recompensas pequeñas"),
				ft.dropdown.Option("Recompensas medianas"),
				ft.dropdown.Option("Recompensas grandes"),
				ft.dropdown.Option("Recompensas épicas"),
			],
			helper_text="Selecciona el tipo: 🎁 pequeñas, 🏅 medianas, 🏆 grandes, 💎 épicas",
		)
		self.active_switch = ft.Switch(label="Activa", value=True)

		self.error_text = ft.Text("", color="#ef5350", size=12)

		self.save_button = ft.ElevatedButton(
			content=ft.Row(
				spacing=6,
				vertical_alignment=ft.CrossAxisAlignment.CENTER,
				controls=[ft.Icon(ft.Icons.CHECK, size=16), ft.Text("Guardar")],
			),
			on_click=self._handle_submit,
		)
		self.reset_button = ft.OutlinedButton(
			content=ft.Row(
				spacing=6,
				vertical_alignment=ft.CrossAxisAlignment.CENTER,
				controls=[ft.Icon(ft.Icons.REFRESH, size=16), ft.Text("Limpiar")],
			),
			on_click=lambda _: self.reset_form(),
		)
		self.cancel_button = ft.TextButton(
			content=ft.Row(
				spacing=6,
				vertical_alignment=ft.CrossAxisAlignment.CENTER,
				controls=[ft.Icon(ft.Icons.CLOSE, size=16), ft.Text("Cancelar")],
			),
			on_click=self._handle_cancel,
		)

		self.content = ft.Column(
			spacing=12,
			controls=[
				ft.Text("Nueva recompensa", size=18, weight="bold", color="#FFD700"),
				self.title_input,
				self.desc_input,
				self.points_input,
				ft.Column([
					self.icon_button,
					self._icon_panel,
				], spacing=6),
				self.color_input,
				ft.Row([self.category_dropdown, self.active_switch], spacing=12, vertical_alignment=ft.CrossAxisAlignment.CENTER),
				self.error_text,
				ft.Row([self.save_button, self.reset_button, self.cancel_button], spacing=12),
			],
		)

	def reset_form(self):
		self.title_input.value = ""
		self.desc_input.value = ""
		self.points_input.value = "1.0"
		self.icon_value = "🎁"
		self.icon_button.content.controls[-1].value = self.icon_value
		self._icon_panel.visible = False
		self.color_input.value = "#FFD700"
		self.editing_reward_id = None
		self.category_dropdown.value = "Recompensas pequeñas"
		self.active_switch.value = True
		self.error_text.value = ""
		try:
			self.update()
		except RuntimeError:
			# Puede ocurrir si aún no está montado; ignorar silenciosamente
			pass
		except Exception:
			pass

	def _handle_submit(self, _):
		self.error_text.value = ""
		title = (self.title_input.value or "").strip()
		desc = (self.desc_input.value or "").strip()
		icon = self.icon_value
		color = (self.color_input.value or "#FFD700").strip() or "#FFD700"
		category = self.category_dropdown.value or "Recompensas pequeñas"
		is_active = bool(self.active_switch.value)

		try:
			points_required = float(self.points_input.value or 0)
		except ValueError:
			points_required = -1

		if not title:
			self.error_text.value = "El título es requerido"
		elif points_required < 0:
			self.error_text.value = "Los puntos deben ser un número positivo"

		if self.error_text.value:
			if self.page:
				self.update()
			return

		payload = {
			"title": title,
			"description": desc,
			"points_required": points_required,
			"icon": icon,
			"color": color,
			"is_active": is_active,
			"category": category,
		}

		if self.editing_reward_id:
			try:
				self.rewards_service.update_reward(self.editing_reward_id, payload)
			except Exception:
				pass
			reward = self.rewards_service.get_reward(self.editing_reward_id) or Reward(**payload)
		else:
			reward = self.rewards_service.create_reward(payload)

		if self.on_submit:
			try:
				self.on_submit(reward)
			except Exception:
				pass

		self.reset_form()
		try:
			self.update()
		except RuntimeError:
			pass
		except Exception:
			pass

	def _handle_cancel(self, _):
		if self.on_cancel:
			try:
				self.on_cancel()
			except Exception:
				pass
		try:
			self.update()
		except RuntimeError:
			pass
		except Exception:
			pass

	def _toggle_icon_panel(self, _):
		self._icon_panel.visible = not self._icon_panel.visible
		try:
			self.update()
		except RuntimeError:
			pass
		except Exception:
			pass

	def _build_icon_panel(self) -> ft.Container:
		icons = ["🎁", "🎖️", "🔥", "⭐", "💎", "🏆", "🚀", "⏱️", "🧠"]
		buttons = []
		for ico in icons:
			btn = ft.TextButton(
				content=ft.Text(ico, size=28),
				on_click=lambda e, icon_val=ico: self._select_icon(icon_val),
			)
			buttons.append(btn)

		rows = []
		for i in range(0, len(buttons), 5):
			chunk = buttons[i:i+5]
			rows.append(ft.Row(controls=chunk, spacing=10))
		grid = ft.Column(controls=rows, spacing=10)
		panel = ft.Container(
			bgcolor="#222",
			padding=10,
			border_radius=8,
			border=ft.border.all(1, "#333"),
			content=grid,
		)
		return panel

	def _select_icon(self, icon_val: str):
		self.icon_value = icon_val
		self.icon_button.content.controls[-1].value = icon_val
		self._icon_panel.visible = False
		try:
			self.update()
		except RuntimeError:
			pass
		except Exception:
			pass

	def load_reward(self, reward: Reward):
		"""Carga una recompensa existente para edición."""
		self.editing_reward_id = getattr(reward, "id", None)
		self.title_input.value = reward.title or ""
		self.desc_input.value = reward.description or ""
		self.points_input.value = f"{getattr(reward, 'points_required', 0):.2f}"
		self.icon_value = reward.icon or "🎁"
		self.icon_button.content.controls[-1].value = self.icon_value
		self.color_input.value = reward.color or "#FFD700"
		self.category_dropdown.value = reward.category or "Recompensas pequeñas"
		self.active_switch.value = bool(getattr(reward, "is_active", True))
		self._icon_panel.visible = False
		self.error_text.value = ""
		try:
			self.update()
		except Exception:
			pass
