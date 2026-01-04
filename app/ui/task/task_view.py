"""
Vista simple de tareas: listado, formulario para crear/editar y botón de eliminar.
"""

from __future__ import annotations

from typing import List, Optional
import uuid
from datetime import datetime

import flet as ft
import sys
from pathlib import Path
from app.ui.task.form.task_form import TaskForm
from app.ui.task.card.task_card_view import TaskCardView
from app.models.task import Task
from app.models.subtask import Subtask
from app.utils.task_helper import TASK_STATUS_PENDING

# Permite ejecución directa añadiendo la raíz del proyecto al path
ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
	sys.path.insert(0, str(ROOT_DIR))


class TaskView:
	def __init__(self, page: Optional[ft.Page] = None):
		self.page = page

		self.tasks: List[Task] = []
		self.editing: Optional[Task] = None
		self.next_id: int = 1

		# UI refs
		self.list_column: Optional[ft.Column] = None
		self.form: TaskForm = TaskForm(self._handle_save, self._handle_cancel, self._on_subtask_changed)
		self.form_card: Optional[ft.Card] = None
		self.form_container: Optional[ft.Container] = None
		self.task_card_view: TaskCardView = TaskCardView(self._edit_task, self._delete_task, self._on_task_updated)

	def build(self) -> ft.Container:
		self.form_card = self.form.build()
		self.form_container = ft.Container(content=self.form_card, visible=False)
		self.list_column = ft.Column(spacing=8, expand=True)

		add_button = ft.FloatingActionButton(
			icon=ft.Icons.ADD,
			tooltip="Agregar tarea",
			bgcolor=ft.Colors.RED,
			on_click=self._start_new,
		)

		scrollable_content = ft.Column(
			controls=[
				ft.Row(
					[
						ft.Text("Listado de tareas", size=24, weight=ft.FontWeight.BOLD),
						add_button,
					],
					alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
				),
				self.form_container,
				ft.Divider(height=16, color=ft.Colors.TRANSPARENT),
				self.list_column,
			],
			spacing=12,
			scroll=ft.ScrollMode.AUTO,
			expand=True,
		)

		host = ft.Container(
			content=scrollable_content,
			padding=16,
			expand=True,
		)

		self._refresh_list()
		return host

	# ------------------------------------------------------------------
	# Actions
	# ------------------------------------------------------------------
	def _handle_save(self, _):
		title = (self.form.title_field.value or "").strip()
		description = (self.form.desc_field.value or "").strip()
		if not title:
			self._show_message("El título es obligatorio")
			return

		# Obtener subtareas del formulario
		subtasks = self.form.subtask_manager.get_subtasks() if self.form.subtask_manager else []

		if self.editing:
			self.editing.title = title
			self.editing.description = description
			self.editing.subtasks = subtasks
			self.editing.updated_at = datetime.now()
			# Actualizar estado basado en subtareas
			self.editing.update_status_from_subtasks()
		else:
			task = Task(
				id=str(uuid.uuid4()),
				title=title,
				description=description,
				status=TASK_STATUS_PENDING,
				subtasks=subtasks,
			)
			# Actualizar estado basado en subtareas (si las hay)
			task.update_status_from_subtasks()
			self.tasks.insert(0, task)

		self.editing = None
		self._reset_form()
		self._hide_form()
		self._show_list()
		self._refresh_list()

	def _handle_cancel(self, _):
		self.editing = None
		self._reset_form()
		self._hide_form()
		self._show_list()
		self._refresh_list()

	def _start_new(self, _):
		self.editing = None
		self._reset_form()
		self._show_form()
		self._refresh_list()

	def _edit_task(self, task: Task):
		self.editing = task
		self.form.set_values(task.title, task.description, task.subtasks)
		self._hide_list()
		self._show_form()
		if self.page:
			self.page.update()

	def _delete_task(self, task: Task):
		self.tasks = [t for t in self.tasks if t.id != task.id]
		if self.editing and self.editing.id == task.id:
			self.editing = None
			self._reset_form()
		self._refresh_list()

	# ------------------------------------------------------------------
	# Helpers
	# ------------------------------------------------------------------
	def _reset_form(self):
		self.form.reset()
		if self.page:
			self.page.update()

	def _show_form(self):
		if self.form_container:
			self.form_container.visible = True
			if self.page:
				self.page.update()

	def _hide_form(self):
		if self.form_container:
			self.form_container.visible = False
			if self.page:
				self.page.update()

	def _hide_list(self):
		if self.list_column:
			self.list_column.visible = False
			if self.page:
				self.page.update()

	def _show_list(self):
		if self.list_column:
			self.list_column.visible = True
			if self.page:
				self.page.update()

	def _refresh_list(self):
		if not self.list_column:
			return
		self.list_column.controls.clear()

		if not self.tasks:
			self.list_column.controls.append(
				ft.Text("No hay tareas", color=ft.Colors.GREY_600)
			)
		else:
			for task in self.tasks:
				self.list_column.controls.append(self.task_card_view.build(task))

		if self.page:
			self.page.update()

	def _show_message(self, text: str):
		if not self.page:
			return
		self.page.snack_bar = ft.SnackBar(content=ft.Text(text))
		self.page.snack_bar.open = True
		self.page.update()

	def _on_subtask_changed(self, subtask):
		"""Callback cuando cambia una subtarea en el formulario."""
		if self.editing:
			# Actualizar estado de la tarea basado en sus subtareas
			self.editing.update_status_from_subtasks()

	def _on_task_updated(self, task: Task):
		"""Callback cuando se actualiza una tarea (ej: checkbox toggle)."""
		# Refrescar la lista para mostrar cambios de estado
		self._refresh_list()


# Permite vista rápida ejecutando directamente este archivo
def main(page: ft.Page):
	page.title = "Tareas"
	view = TaskView(page)
	page.add(view.build())


if __name__ == "__main__":
	ft.app(target=main)


