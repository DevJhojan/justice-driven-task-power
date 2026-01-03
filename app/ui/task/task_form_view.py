"""TaskForm legacy (wrapper compatible).

El formulario real fue modularizado en `app.ui.task.form.task_form`.
Este wrapper existe para mantener compatibilidad con la API anterior usada en
tests y algunos imports históricos.
"""

from __future__ import annotations

from typing import Awaitable, Callable, Optional, Union

import flet as ft

from app.models.task import Task
from app.ui.task.form.subtask import delete_subtask, toggle_subtask
from app.ui.task.form.task_form import TaskForm as _ModularTaskForm


class TaskFormView(_ModularTaskForm):
	"""Wrapper compatible del TaskForm modular."""

	def __init__(
		self,
		page: ft.Page,
		task: Optional[Task] = None,
		on_save: Optional[Union[Callable[[Task], None], Callable[[Task], Awaitable[None]]]] = None,
		on_cancel: Optional[Callable[[], None]] = None,
	):
		super().__init__(page=page, task=task, on_save=on_save, on_cancel=on_cancel)
		self.subtasks_column: Optional[ft.Column] = None

	def build(self) -> ft.Container:
		container = super().build()
		# Atributo esperado por tests antiguos
		self.subtasks_column = ft.Column(spacing=8)
		self._render_subtasks()
		return container

	def _render_subtasks(self) -> None:
		if self.subtasks_column is None:
			self.subtasks_column = ft.Column(spacing=8)

		if not self.subtasks:
			self.subtasks_column.controls = [ft.Text("No hay subtareas")]
			return

		# Para compatibilidad con tests, solo importa el conteo
		self.subtasks_column.controls = [ft.Text(s.title) for s in self.subtasks]

	def _delete_subtask(self, index: int) -> None:
		delete_subtask(self.subtasks, index)
		self._render_subtasks()

	def _toggle_subtask(self, index: int, completed: bool) -> None:
		toggle_subtask(self.subtasks, index, completed)
		self._render_subtasks()


# Alias legacy: muchos imports esperan `TaskForm`
TaskForm = TaskFormView


__all__ = ["TaskFormView", "TaskForm"]
