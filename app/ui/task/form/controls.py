"""Factories de controles para el TaskForm.

Este módulo concentra la creación/configuración de widgets de Flet para el
formulario de tareas, manteniendo estilos y propiedades consistentes.
"""

from __future__ import annotations

from typing import Optional

import flet as ft

from app.models.task import Task
from app.utils.task_helper import (
	TASK_STATUS_PENDING,
	TASK_STATUS_IN_PROGRESS,
	TASK_STATUS_COMPLETED,
	TASK_STATUS_CANCELLED,
)


def create_title_field(task: Optional[Task]) -> ft.TextField:
	return ft.TextField(
		label="Título *",
		hint_text="Ingrese el título de la tarea",
		value=task.title if task else "",
		max_length=100,
		border_color=ft.Colors.RED_700,
		focused_border_color=ft.Colors.RED_400,
		cursor_color=ft.Colors.RED_400,
		# No usar expand en campos de texto para evitar que crezcan verticalmente y rompan el scroll
	)


def create_description_field(task: Optional[Task]) -> ft.TextField:
	return ft.TextField(
		label="Descripción",
		hint_text="Descripción detallada de la tarea",
		value=task.description if task else "",
		multiline=True,
		min_lines=3,
		max_lines=5,
		max_length=500,
		border_color=ft.Colors.RED_700,
		focused_border_color=ft.Colors.RED_400,
		cursor_color=ft.Colors.RED_400,
		# No usar expand en campos multiline para evitar que ocupen todo el alto y bloqueen scroll
	)


def create_status_dropdown(task: Optional[Task]) -> ft.Dropdown:
	return ft.Dropdown(
		label="Estado",
		value=task.status if task else TASK_STATUS_PENDING,
		options=[
			ft.dropdown.Option(TASK_STATUS_PENDING, "Pendiente"),
			ft.dropdown.Option(TASK_STATUS_IN_PROGRESS, "En Progreso"),
			ft.dropdown.Option(TASK_STATUS_COMPLETED, "Completada"),
			ft.dropdown.Option(TASK_STATUS_CANCELLED, "Cancelada"),
		],
		border_color=ft.Colors.RED_700,
		focused_border_color=ft.Colors.RED_400,
		# El ancho responsive se controla desde el layout contenedor.
	)


def create_priority_checkboxes(task: Optional[Task]) -> tuple[ft.Checkbox, ft.Checkbox]:
	urgent_checkbox = ft.Checkbox(
		label="Urgente",
		value=task.urgent if task else False,
		fill_color=ft.Colors.RED_700,
	)

	important_checkbox = ft.Checkbox(
		label="Importante",
		value=task.important if task else False,
		fill_color=ft.Colors.RED_700,
	)

	return urgent_checkbox, important_checkbox


def create_tags_field(task: Optional[Task]) -> ft.TextField:
	tags_value = ""
	if task and task.tags:
		tags_value = ", ".join(task.tags)

	return ft.TextField(
		label="Etiquetas",
		hint_text="Separadas por comas (ej: python, backend, api)",
		value=tags_value,
		border_color=ft.Colors.RED_700,
		focused_border_color=ft.Colors.RED_400,
		cursor_color=ft.Colors.RED_400,
	)


def create_notes_field(task: Optional[Task]) -> ft.TextField:
	return ft.TextField(
		label="Notas adicionales",
		hint_text="Notas, comentarios o recordatorios",
		value=task.notes if task else "",
		multiline=True,
		min_lines=2,
		max_lines=4,
		max_length=300,
		border_color=ft.Colors.RED_700,
		focused_border_color=ft.Colors.RED_400,
		cursor_color=ft.Colors.RED_400,
	)


def create_error_text() -> ft.Text:
	return ft.Text(
		"",
		color=ft.Colors.RED_400,
		size=12,
		visible=False,
	)

