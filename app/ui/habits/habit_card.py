"""
Card de hábito reutilizable.
"""

import flet as ft
from datetime import datetime
from typing import Callable, Optional, Dict

from app.models.habit import Habit


def create_habit_card(
	habit: Habit,
	on_complete: Callable[[str], None],
	on_edit: Callable[[Habit], None],
	on_delete: Callable[[str], None],
	frequency_labels: Optional[Dict[str, str]] = None,
) -> ft.Container:
	"""Construye una card de hábito con acciones de completar/editar/eliminar."""
	labels = frequency_labels or {
		"daily": "Diario",
		"weekly": "Semanal",
		"monthly": "Mensual",
		"semiannual": "Semestral",
		"annual": "Anual",
	}

	completed_today = habit.was_completed_today()
	freq_text = labels.get(habit.frequency, habit.frequency.capitalize())
	if habit.frequency != "daily":
		freq_text = f"{freq_text}: {habit.frequency_times} veces"

	last_completed_text = (
		ft.Text(
			f"Última vez: {datetime.fromisoformat(habit.last_completed).strftime('%d/%m %H:%M')}",
			size=12,
			color=ft.Colors.WHITE_60,
		)
		if habit.last_completed
		else ft.Text(
			"No completado aún",
			size=12,
			color=ft.Colors.WHITE_60,
		)
	)

	metrics = ft.Row(
		[
			ft.IconButton(
				icon=ft.Icons.BAR_CHART,
				icon_color=ft.Colors.WHITE,
				on_click=lambda e: None,
				tooltip="Gráficos",
			),
			ft.Icon(ft.Icons.TRENDING_UP, size=16, color=ft.Colors.RED_400),
			ft.Text(f"Racha: {habit.streak}", size=12, color=ft.Colors.WHITE),
			ft.Icon(ft.Icons.SCHEDULE, size=16, color=ft.Colors.WHITE_70),
			ft.Text(freq_text, size=12, color=ft.Colors.WHITE_70),
		],
		spacing=6,
		vertical_alignment=ft.CrossAxisAlignment.CENTER,
	)

	return ft.Container(
		content=ft.Column(
			[
				ft.Row(
					[
						ft.Column(
							[
								ft.Text(
									habit.title,
									size=16,
									weight=ft.FontWeight.BOLD,
									color=ft.Colors.WHITE,
								),
								ft.Text(
									habit.description[:50] if habit.description else "",
									size=12,
									color=ft.Colors.WHITE_70,
								)
								if habit.description
								else ft.Container(),
								ft.Text(
									f"Frecuencia: {freq_text}",
									size=12,
									color=ft.Colors.WHITE_70,
								),
							],
							expand=True,
							spacing=4,
						),
						ft.Row(
							[
								ft.Icon(
									ft.Icons.WHATSHOT,
									size=20,
									color=ft.Colors.RED_400,
								),
								ft.Text(
									str(habit.streak),
									size=16,
									weight=ft.FontWeight.BOLD,
									color=ft.Colors.RED_400,
								),
							],
							spacing=4,
							vertical_alignment=ft.CrossAxisAlignment.CENTER,
						),
					],
					spacing=16,
					expand=True,
				),
				ft.Divider(height=1, color=ft.Colors.WHITE_10),
				ft.Row(
					[
						last_completed_text,
						ft.Row(
							[
								ft.IconButton(
									icon=ft.Icons.CHECK_CIRCLE if completed_today else ft.Icons.CIRCLE_OUTLINED,
									icon_color=ft.Colors.RED_500 if completed_today else ft.Colors.WHITE_60,
									on_click=lambda e, hid=habit.id: on_complete(hid),
								),
								ft.IconButton(
									icon=ft.Icons.EDIT,
									icon_color=ft.Colors.WHITE,
									on_click=lambda e, h=habit: on_edit(h),
								),
								ft.IconButton(
									icon=ft.Icons.DELETE_OUTLINE,
									icon_color=ft.Colors.RED_400,
									on_click=lambda e, hid=habit.id: on_delete(hid),
								),
							],
							spacing=8,
							vertical_alignment=ft.CrossAxisAlignment.CENTER,
						),
						metrics,
					],
					alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
					vertical_alignment=ft.CrossAxisAlignment.CENTER,
				),
			],
			spacing=8,
		),
		bgcolor=ft.Colors.WHITE_10,
		border_radius=8,
		padding=16,
		margin=ft.margin.only(bottom=12),
	)
