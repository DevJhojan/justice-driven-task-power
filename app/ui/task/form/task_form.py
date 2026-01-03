"""TaskForm (versión modular).

Este archivo contiene el componente `TaskForm` delegando la creación de
controles a módulos especializados:
- `controls.py` (factories de campos)
- `date_controls.py` (DatePicker + handlers)
- `subtask.py` (UI + helpers de subtareas)
- `layout.py` (Column principal con scroll)
"""

from __future__ import annotations

import asyncio
from datetime import date, datetime
from typing import Awaitable, Callable, List, Optional, Union

import flet as ft

from app.models.subtask import Subtask
from app.models.task import Task
from app.ui.task.form.controls import (
	create_description_field,
	create_error_text,
	create_notes_field,
	create_priority_checkboxes,
	create_status_dropdown,
	create_tags_field,
	create_title_field,
)
from app.ui.task.form.date_controls import build_due_date_controls
from app.ui.task.form.layout import build_form_layout
from app.ui.task.form.subtask import (
	build_add_subtask_row,
	create_subtask,
	delete_subtask,
	edit_subtask,
	render_subtasks,
	toggle_subtask,
)
from app.utils.helpers.responsives import get_responsive_padding
from app.utils.helpers.validators import is_valid_string
from app.utils.task_helper import TASK_STATUS_PENDING


def parse_csv_tags(value: str) -> list[str]:
	"""Parsea tags separados por coma a una lista normalizada."""
	if not value:
		return []
	return [t.strip() for t in value.split(",") if t.strip()]


def is_valid_tags_list(tags: list[str], *, max_tags: int = 10) -> bool:
	"""Valida una lista de tags (reglas mínimas)."""
	if len(tags) > max_tags:
		return False
	return all(isinstance(t, str) and t.strip() for t in tags)


class TaskForm:
	"""Formulario para crear y editar tareas."""

	def __init__(
		self,
		page: ft.Page,
		task: Optional[Task] = None,
		on_save: Optional[Union[Callable[[Task], None], Callable[[Task], Awaitable[None]]]] = None,
		on_cancel: Optional[Callable] = None,
	):
		self.page = page
		self.task = task
		self.on_save = on_save
		self.on_cancel = on_cancel
		self.is_edit_mode = task is not None

		# Controles del formulario
		self.title_field: Optional[ft.TextField] = None
		self.description_field: Optional[ft.TextField] = None
		self.status_dropdown: Optional[ft.Dropdown] = None
		self.urgent_checkbox: Optional[ft.Checkbox] = None
		self.important_checkbox: Optional[ft.Checkbox] = None
		self.due_date_picker: Optional[ft.DatePicker] = None
		self.due_date_text: Optional[ft.Text] = None
		self.tags_field: Optional[ft.TextField] = None
		self.notes_field: Optional[ft.TextField] = None
		self.error_text: Optional[ft.Text] = None

		# Estado de subtareas
		self.subtasks: List[Subtask] = []
		if self.task and self.task.subtasks:
			self.subtasks = list(self.task.subtasks)

		# Fecha seleccionada
		self.selected_date: Optional[date] = None
		if self.task and self.task.due_date:
			self.selected_date = self.task.due_date

	def build(self) -> ft.Container:
		"""Construye el formulario completo."""
		# 1) Controles principales (delegados a factories)
		self.title_field = create_title_field(self.task)
		self.description_field = create_description_field(self.task)
		self.status_dropdown = create_status_dropdown(self.task)
		self.urgent_checkbox, self.important_checkbox = create_priority_checkboxes(self.task)
		self.tags_field = create_tags_field(self.task)
		self.notes_field = create_notes_field(self.task)
		self.error_text = create_error_text()

		# 2) Fecha (delegada a date_controls.py)
		def on_selected_date_change(new_date: Optional[date]) -> None:
			self.selected_date = new_date

		(
			self.due_date_picker,
			self.due_date_text,
			open_date_picker,
			clear_date,
		) = build_due_date_controls(
			page=self.page,
			selected_date=self.selected_date,
			on_selected_date_change=on_selected_date_change,
		)

		# 3) Subtareas (estado en TaskForm, UI en subtask.py)
		subtasks_body = ft.Container()

		def rerender_subtasks() -> None:
			def on_delete(index: int) -> None:
				delete_subtask(self.subtasks, index)
				rerender_subtasks()
				self.page.update()

			def on_toggle(index: int, completed: bool) -> None:
				toggle_subtask(self.subtasks, index, completed)
				rerender_subtasks()
				self.page.update()

			def on_edit(index: int, title: str) -> None:
				edit_subtask(self.subtasks, index, title)
				rerender_subtasks()
				self.page.update()

			subtasks_body.content = render_subtasks(
				self.subtasks,
				on_delete=on_delete,
				on_toggle=on_toggle,
				on_edit=on_edit,
			)

		def show_add_subtask(e=None) -> None:
			def on_save_subtask(title: str) -> None:
				task_id = self.task.id if self.task else ""
				self.subtasks.append(create_subtask(title=title, task_id=task_id))
				rerender_subtasks()
				self.page.update()

			def on_cancel_subtask() -> None:
				rerender_subtasks()
				self.page.update()

			subtasks_body.content = build_add_subtask_row(
				on_save=on_save_subtask,
				on_cancel=on_cancel_subtask,
			)
			self.page.update()

		subtasks_section = ft.Column(
			controls=[
				ft.Row(
					controls=[
						ft.Text("Subtareas:", size=14, weight=ft.FontWeight.BOLD),
						ft.IconButton(
							icon=ft.Icons.ADD_CIRCLE,
							icon_color=ft.Colors.RED_700,
							tooltip="Agregar subtarea",
							on_click=show_add_subtask,
						),
					],
					alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
				),
				subtasks_body,
			],
			spacing=8,
		)
		rerender_subtasks()

		# 4) Botones
		def handle_save(e) -> None:
			if not self._validate_and_save():
				return
			if not self.on_save:
				return
			result = self.on_save(self._build_task())
			if asyncio.iscoroutine(result):
				asyncio.create_task(result)

		def handle_cancel(e) -> None:
			if self.on_cancel:
				self.on_cancel()

		save_button = ft.FilledButton(
			"Guardar" if self.is_edit_mode else "Crear Tarea",
			icon=ft.Icons.SAVE,
			on_click=handle_save,
			style=ft.ButtonStyle(bgcolor=ft.Colors.RED_700, color=ft.Colors.WHITE),
		)
		cancel_button = ft.OutlinedButton(
			"Cancelar",
			icon=ft.Icons.CANCEL,
			on_click=handle_cancel,
			style=ft.ButtonStyle(
				side=ft.BorderSide(2, ft.Colors.RED_700),
				color=ft.Colors.RED_700,
			),
		)

		# 5) Layout principal (delegado a layout.py)
		form_content = build_form_layout(
			is_edit_mode=self.is_edit_mode,
			title_field=self.title_field,
			description_field=self.description_field,
			status_dropdown=self.status_dropdown,
			urgent_checkbox=self.urgent_checkbox,
			important_checkbox=self.important_checkbox,
			due_date_text=self.due_date_text,
			open_date_picker=open_date_picker,
			clear_date=clear_date,
			tags_field=self.tags_field,
			notes_field=self.notes_field,
			subtasks_section=subtasks_section,
			error_text=self.error_text,
			save_button=save_button,
			cancel_button=cancel_button,
		)

		# 6) Container final con expand=True (scroll funciona por expand + Column.scroll)
		return ft.Container(
			content=form_content,
			padding=get_responsive_padding(page=self.page),
			bgcolor=ft.Colors.GREY_900,
			border_radius=12,
			border=ft.Border.all(1, ft.Colors.RED_900),
			# expand se deja en False para que el ListView padre maneje el scroll
		)

	def _validate_and_save(self) -> bool:
		"""Valida los campos del formulario y muestra errores si aplica."""
		if not self.title_field or not self.description_field or not self.tags_field or not self.error_text:
			return False

		errors: list[str] = []

		title = (self.title_field.value or "").strip()
		if not title:
			errors.append("El título es obligatorio")
		elif len(title) > 100:
			errors.append("El título no puede exceder 100 caracteres")
		elif not is_valid_string(title, min_length=1, max_length=100, allow_empty=False):
			# Fallback por si el validador aplica reglas adicionales
			errors.append("El título no es válido")

		description = self.description_field.value or ""
		if description and not is_valid_string(description, min_length=0, max_length=500, allow_empty=True):
			errors.append("La descripción no puede exceder 500 caracteres")

		tags = parse_csv_tags(self.tags_field.value or "")
		if not is_valid_tags_list(tags, max_tags=10):
			errors.append("Máximo 10 etiquetas permitidas")

		if errors:
			self.error_text.value = " • " + "\n • ".join(errors)
			self.error_text.visible = True
			self.page.update()
			return False

		self.error_text.visible = False
		return True

	def _build_task(self) -> Task:
		"""Construye el objeto `Task` con los datos del formulario."""
		if (
			not self.title_field
			or not self.description_field
			or not self.status_dropdown
			or not self.urgent_checkbox
			or not self.important_checkbox
			or not self.notes_field
			or not self.tags_field
		):
			raise ValueError("Los controles del formulario no están inicializados")

		tags = parse_csv_tags(self.tags_field.value or "")

		if self.is_edit_mode and self.task:
			self.task.title = (self.title_field.value or "").strip()
			self.task.description = (self.description_field.value or "").strip()
			self.task.status = self.status_dropdown.value or TASK_STATUS_PENDING
			self.task.urgent = bool(self.urgent_checkbox.value)
			self.task.important = bool(self.important_checkbox.value)
			self.task.due_date = self.selected_date
			self.task.tags = tags
			self.task.notes = (self.notes_field.value or "").strip()
			self.task.subtasks = self.subtasks
			self.task.updated_at = datetime.now()
			return self.task

		from uuid import uuid4

		return Task(
			id=str(uuid4()),
			title=(self.title_field.value or "").strip(),
			description=(self.description_field.value or "").strip(),
			status=self.status_dropdown.value or TASK_STATUS_PENDING,
			urgent=bool(self.urgent_checkbox.value),
			important=bool(self.important_checkbox.value),
			due_date=self.selected_date,
			tags=tags,
			notes=(self.notes_field.value or "").strip(),
			subtasks=self.subtasks,
			created_at=datetime.now(),
			updated_at=datetime.now(),
		)
