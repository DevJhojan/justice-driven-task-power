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

		self.expand = True
		self.bgcolor = "#1a1a1a"
		self.padding = 20
		self.border_radius = 12

		self.unlocked_list = ft.Column(spacing=8)
		self.locked_list = ft.Column(spacing=8)
		self.showing_form = False

		self.form = RewardsForm(
			rewards_service=self.rewards_service,
			on_submit=self._on_form_submit,
			on_cancel=self._cancel_form,
		)

		self.lists_column = ft.Column(
			spacing=16,
			controls=[
				ft.Text("Según tus puntos actuales", size=12, color="#CCCCCC"),
				ft.Divider(color="#333", height=1),
				ft.Text("Desbloqueadas", size=16, weight="bold", color="#4CAF50"),
				self.unlocked_list,
				ft.Divider(color="#333", height=1),
				ft.Text("Próximas", size=16, weight="bold", color="#FF9800"),
				self.locked_list,
			],
		)

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
				self.dynamic_container,
			],
		)

		self._ensure_seed_data()
		self.refresh_lists()

	def did_mount(self):
		"""Se llama cuando el control se agrega a la página; refresca listas con page disponible."""
		self.refresh_lists()

	def set_user_points(self, points: float):
		"""Actualiza puntos del usuario y refresca las listas."""
		self.user_points = float(points)
		self.refresh_lists()

	def _ensure_seed_data(self):
		"""Carga algunas recompensas de ejemplo si no hay ninguna."""
		if self.rewards_service.get_all_rewards():
			return
		defaults = [
			{
				"title": "Insignia Novato",
				"description": "Completa tu primera tarea",
				"points_required": 1.0,
				"icon": "🎖️",
				"color": "#4CAF50",
				"is_active": True,
			},
			{
				"title": "Racha de Productividad",
				"description": "Completa 5 tareas",
				"points_required": 5.0,
				"icon": "🔥",
				"color": "#FF9800",
				"is_active": True,
			},
			{
				"title": "Maestro del Tiempo",
				"description": "Completa 10 tareas a tiempo",
				"points_required": 10.0,
				"icon": "⏱️",
				"color": "#2196F3",
				"is_active": True,
			},
		]
		for data in defaults:
			self.rewards_service.create_reward(data)

	def refresh_lists(self):
		"""Reconstruye las listas de recompensas desbloqueadas y próximas."""
		unlocked = self.rewards_service.get_unlocked_rewards(self.user_points)
		locked = self.rewards_service.get_next_rewards(self.user_points, limit=5)

		self.unlocked_list.controls = self._build_tiles(unlocked, unlocked=True)
		self.locked_list.controls = self._build_tiles(locked, unlocked=False)

		try:
			self.update()
		except RuntimeError:
			# Puede ocurrir si aún no está asignada la page; se ignorará hasta did_mount
			pass
		except Exception:
			pass

	def _build_tiles(self, rewards: List[Reward], unlocked: bool) -> List[ft.Control]:
		"""Crea tarjetas visuales para cada recompensa."""
		if not rewards:
			message = "Sin recompensas desbloqueadas" if unlocked else "Sin próximas recompensas"
			return [ft.Text(message, size=12, color="#888888")]

		tiles: List[ft.Control] = []
		for reward in rewards:
			status_text = "Desbloqueada" if unlocked else f"Faltan {max(0.0, reward.points_required - self.user_points):.2f} pts"
			status_color = "#4CAF50" if unlocked else "#FFC107"
			tile = ft.Container(
				bgcolor="#222",
				border_radius=10,
				padding=12,
				border=ft.border.all(1, "#333"),
				content=ft.Row(
					alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
					vertical_alignment=ft.CrossAxisAlignment.CENTER,
					controls=[
						ft.Row(
							spacing=12,
							controls=[
								ft.Text(reward.icon or "🎁", size=22),
								ft.Column(
									spacing=2,
									controls=[
										ft.Text(reward.title, size=15, weight="w600", color="#EEE"),
										ft.Text(reward.description, size=12, color="#AAA"),
									],
								),
							],
						),
						ft.Column(
							spacing=2,
							horizontal_alignment=ft.CrossAxisAlignment.END,
							controls=[
								ft.Text(status_text, size=12, color=status_color),
								ft.Text(f"{reward.points_required:.2f} pts", size=11, color="#999"),
							],
						),
					],
				),
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

