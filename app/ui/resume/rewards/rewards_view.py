"""
Vista sencilla de recompensas para el resumen.
Muestra recompensas desbloqueadas y próximas según los puntos del usuario.
"""

import flet as ft
from typing import Optional, List
from app.services.rewards_service import RewardsService
from app.models.reward import Reward
from app.ui.resume.rewards.rewards_form import RewardsForm


class RewardsView(ft.Container):
	"""UI simple para listar recompensas desbloqueadas y próximas."""

	def __init__(self, rewards_service: Optional[RewardsService] = None, user_points: float = 0.0):
		super().__init__()

		self.rewards_service = rewards_service or RewardsService()
		self.user_points = float(user_points)
		self.current_filter = "desbloqueadas"  # próximas, desbloqueadas, reclamadas

		self.expand = True
		self.bgcolor = "#1a1a1a"
		self.padding = 20
		self.border_radius = 12

		self.unlocked_list = ft.Column(spacing=8)
		self.locked_list = ft.Column(spacing=8)
		self.claimed_list = ft.Column(spacing=8)
		self.showing_form = False

		self.form = RewardsForm(
			rewards_service=self.rewards_service,
			on_submit=self._on_form_submit,
			on_cancel=self._cancel_form,
		)

		# Botones de filtro
		self.filter_buttons = {
			"próximas": ft.TextButton(
				content=ft.Text("Próximas", size=12, weight="bold"),
				on_click=lambda _: self._set_filter("próximas"),
				style=ft.ButtonStyle(
					color={"": "#FF9800"},
				),
			),
			"desbloqueadas": ft.TextButton(
				content=ft.Text("Desbloqueadas", size=12, weight="bold"),
				on_click=lambda _: self._set_filter("desbloqueadas"),
				style=ft.ButtonStyle(
					color={"": "#4CAF50"},
				),
			),
			"reclamadas": ft.TextButton(
				content=ft.Text("Reclamadas", size=12, weight="bold"),
				on_click=lambda _: self._set_filter("reclamadas"),
				style=ft.ButtonStyle(
					color={"": "#2196F3"},
				),
			),
		}

		self.filter_bar = ft.Row(
			spacing=20,
			alignment=ft.MainAxisAlignment.CENTER,
			controls=list(self.filter_buttons.values()),
		)

		self.lists_column = ft.Column(spacing=16)

		self.dynamic_container = ft.Container(content=self.lists_column)

		self.add_button = ft.IconButton(
			icon=ft.Icons.ADD,
			icon_size=16,
			width=32,
			height=32,
			tooltip="Agregar recompensa",
			on_click=self._show_form,
			style=ft.ButtonStyle(
				shape=ft.RoundedRectangleBorder(radius=999),
				bgcolor={"": "#2d2d2d"},
			),
		)

		self.content = ft.Column(
			spacing=16,
			controls=[
				ft.Row(
					alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
					vertical_alignment=ft.CrossAxisAlignment.CENTER,
					controls=[
						ft.Text("Recompensas", size=24, weight="bold", color="#FFD700"),
						self.add_button,
					],
				),
				ft.Divider(color="#333", height=1),
				self.filter_bar,
				ft.Divider(color="#333", height=1),
				self.dynamic_container,
			],
		)

		self.refresh_lists()

	def did_mount(self):
		"""Se llama cuando el control se agrega a la página; refresca listas con page disponible."""
		self.refresh_lists()

	def set_user_points(self, points: float):
		"""Actualiza puntos del usuario y refresca las listas."""
		self.user_points = float(points)
		self.refresh_lists()

	def _set_filter(self, filter_name: str):
		"""Cambia el filtro actual y actualiza la vista."""
		self.current_filter = filter_name
		self._update_filter_bar_style()
		self._update_dynamic_content()
		if self.page:
			self.update()

	def _update_filter_bar_style(self):
		"""Actualiza el estilo de los botones de filtro según el seleccionado."""
		colors = {
			"próximas": "#FF9800",
			"desbloqueadas": "#4CAF50",
			"reclamadas": "#2196F3",
		}
		for filter_name, button in self.filter_buttons.items():
			if filter_name == self.current_filter:
				button.style.bgcolor = {"": "#333333"}
				button.content.color = colors[filter_name]
				button.content.weight = "bold"
			else:
				button.style.bgcolor = {"": "transparent"}
				button.content.color = "#CCCCCC"
				button.content.weight = "normal"

	def _update_dynamic_content(self):
		"""Actualiza el contenido mostrado según el filtro actual."""
		if self.current_filter == "próximas":
			self.lists_column.controls = [
				ft.Text("Próximas recompensas a desbloquear", size=12, color="#CCCCCC"),
				self.locked_list,
			]
		elif self.current_filter == "desbloqueadas":
			self.lists_column.controls = [
				ft.Text("Recompensas disponibles para reclamar", size=12, color="#CCCCCC"),
				self.unlocked_list,
			]
		elif self.current_filter == "reclamadas":
			self.lists_column.controls = [
				ft.Text("Recompensas que ya has reclamado", size=12, color="#CCCCCC"),
				self.claimed_list,
			]

	def refresh_lists(self):
		"""Reconstruye las listas de recompensas desbloqueadas, próximas y reclamadas."""
		unlocked = self.rewards_service.get_unlocked_rewards(self.user_points)
		locked = self.rewards_service.get_next_rewards(self.user_points, limit=5)
		
		# Obtener recompensas reclamadas
		all_rewards = self.rewards_service.get_all_rewards()
		claimed = [r for r in all_rewards if r.claimed]

		self.unlocked_list.controls = self._build_tiles(unlocked, unlocked=True)
		self.locked_list.controls = self._build_tiles(locked, unlocked=False)
		self.claimed_list.controls = self._build_tiles(claimed, unlocked=False, show_claim=False)

		self._update_dynamic_content()

		try:
			self.update()
		except RuntimeError:
			# Puede ocurrir si aún no está asignada la page; se ignorará hasta did_mount
			pass
		except Exception:
			pass

	def _build_tiles(self, rewards: List[Reward], unlocked: bool, show_claim: bool = True) -> List[ft.Control]:
		"""Crea tarjetas visuales para cada recompensa con icono, título, puntos y botón reclamar."""
		if not rewards:
			message = "Sin recompensas desbloqueadas" if unlocked else "Sin recompensas disponibles"
			return [ft.Text(message, size=12, color="#888888")]

		tiles: List[ft.Control] = []
		for reward in rewards:
			controls = [
				ft.Row(
					spacing=10,
					expand=True,
					controls=[
						ft.Text(reward.icon or "🎁", size=24),
						ft.Text(reward.title, size=14, weight="w600", color="#FFFFFF", expand=True),
						ft.Text(f"{reward.points_required:.2f} pts", size=12, color="#FFD700", weight="bold"),
					],
				),
			]
			
			# Agregar botón reclamar solo para recompensas desbloqueadas y si show_claim=True
			if unlocked and show_claim:
				controls.append(
					ft.IconButton(
						icon=ft.Icons.CARD_GIFTCARD,
						icon_size=18,
						icon_color="#4CAF50",
						tooltip="Reclamar recompensa",
						on_click=lambda e, reward_id=reward.id: self._claim_reward(reward_id),
					)
				)
			
			tile = ft.Container(
				bgcolor="#222",
				border_radius=10,
				padding=12,
				border=ft.border.all(1, "#333"),
				content=ft.Column(spacing=8, controls=controls),
			)
			tiles.append(tile)
		return tiles

	def _show_form(self, _):
		self.showing_form = True
		self.form.reset_form()
		self.dynamic_container.content = self.form
		if self.page:
			self.update()

	def _on_form_submit(self, reward: Reward):
		# Tras guardar, volver a la lista y refrescar contenido
		self.showing_form = False
		self.refresh_lists()
		self.dynamic_container.content = self.lists_column
		if self.page:
			self.update()

	def _cancel_form(self):
		self.showing_form = False
		self.dynamic_container.content = self.lists_column
		if self.page:
			self.update()

	def _claim_reward(self, reward_id: str):
		"""Marca una recompensa como reclamada."""
		reward = self.rewards_service.get_reward(reward_id)
		if reward:
			reward.claimed = True
			self.refresh_lists()
			if self.page:
				self.update()


