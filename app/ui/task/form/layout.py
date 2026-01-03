"""Layout del formulario de tareas.

Este módulo encapsula la composición visual del formulario (Column principal)
para mantener `TaskForm` más enfocado en estado/validación.
"""

from __future__ import annotations

from typing import Callable

import flet as ft


def build_form_layout(
	*,
	is_edit_mode: bool,
	title_field: ft.Control,
	description_field: ft.Control,
	status_dropdown: ft.Control,
	urgent_checkbox: ft.Control,
	important_checkbox: ft.Control,
	due_date_text: ft.Text,
	open_date_picker: Callable,
	clear_date: Callable,
	tags_field: ft.Control,
	notes_field: ft.Control,
	subtasks_section: ft.Control,
	error_text: ft.Control,
	save_button: ft.Control,
	cancel_button: ft.Control,
) -> ft.Column:
	"""Arma el Column completo del formulario con scroll correcto.

	Mantiene la composición visual actual del formulario:
	- Título + divider
	- Campos principales
	- Estado + prioridad (vertical)
	- Fecha de vencimiento (texto + botones)
	- Tags + notas
	- Sección de subtareas (control ya construido)
	- Error
	- Botones de acción
	"""

	return ft.Column(
		controls=[
			ft.Text(
				"Editar Tarea" if is_edit_mode else "Nueva Tarea",
				size=24,
				weight=ft.FontWeight.BOLD,
				color=ft.Colors.RED_400,
			),
			ft.Divider(height=1, color=ft.Colors.RED_900),
			# Campos principales
			title_field,
			description_field,
			# Estado y prioridad (layout vertical para evitar sobre-expansión del dropdown)
			ft.Column(
				controls=[
					status_dropdown,
					ft.Column(
						controls=[
							ft.Text("Prioridad:", size=12, weight=ft.FontWeight.BOLD),
							urgent_checkbox,
							important_checkbox,
						],
						spacing=4,
					),
				],
				spacing=12,
			),
			# Fecha de vencimiento
			ft.Column(
				controls=[
					ft.Text("Fecha de vencimiento:", size=12, weight=ft.FontWeight.BOLD),
					due_date_text,
					ft.Row(
						controls=[
							ft.FilledButton(
								"Elegir fecha",
								icon=ft.Icons.CALENDAR_MONTH,
								on_click=open_date_picker,
								style=ft.ButtonStyle(
									bgcolor=ft.Colors.RED_900,
									color=ft.Colors.WHITE,
								),
							),
							ft.TextButton(
								"Limpiar",
								on_click=clear_date,
								style=ft.ButtonStyle(color=ft.Colors.RED_700),
							),
						],
						spacing=8,
					),
				],
				spacing=8,
			),
			# Tags y notas
			tags_field,
			notes_field,
			# Subtareas (ya construido desde fuera)
			subtasks_section,
			# Error
			error_text,
			ft.Divider(height=1, color=ft.Colors.RED_900),
			# Botones
			ft.Row(
				controls=[save_button, cancel_button],
				alignment=ft.MainAxisAlignment.END,
				spacing=12,
			),
		],
		spacing=16,
		scroll=ft.ScrollMode.AUTO,
		expand=True,
	)
