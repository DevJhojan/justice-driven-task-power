"""
Vista simple de tareas: listado, formulario para crear/editar y botón de eliminar.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

import flet as ft
import sys
from pathlib import Path
from app.ui.task.form.task_form import TaskForm
from app.ui.task.card.task_card_view import TaskCardView

# Permite ejecución directa añadiendo la raíz del proyecto al path
ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
	sys.path.insert(0, str(ROOT_DIR))


@dataclass
class SimpleSubtask:
	id: int
	title: str
	completed: bool = False


@dataclass
class SimpleTask:
	id: int
	title: str
	description: str = ""
	completed: bool = False
	subtasks: List[SimpleSubtask] = None

	def __post_init__(self):
		if self.subtasks is None:
			self.subtasks = []


class TaskView:
	def __init__(self, page: Optional[ft.Page] = None):
		self.page = page

		self.tasks: List[SimpleTask] = []
		self.editing: Optional[SimpleTask] = None
		self.next_id: int = 1

		# UI refs
		self.list_column: Optional[ft.Column] = None
		self.form: TaskForm = TaskForm(self._handle_save, self._handle_cancel)
		self.form_card: Optional[ft.Card] = None
		self.form_container: Optional[ft.Container] = None
		self.task_card_view: TaskCardView = TaskCardView(self._edit_task, self._delete_task)

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
		else:
			task = SimpleTask(
				id=self.next_id,
				title=title,
				description=description,
				subtasks=subtasks,
			)
			self.next_id += 1
			self.tasks.insert(0, task)

		self.editing = None
		self._reset_form()
		self._hide_form()
		self._refresh_list()

	def _handle_cancel(self, _):
		self.editing = None
		self._reset_form()
		self._hide_form()
		self._refresh_list()

	def _start_new(self, _):
		self.editing = None
		self._reset_form()
		self._show_form()
		self._refresh_list()

	def _edit_task(self, task: SimpleTask):
		self.editing = task
		self.form.set_values(task.title, task.description, task.subtasks)
		self._show_form()
		if self.page:
			self.page.update()

	def _delete_task(self, task: SimpleTask):
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


# Permite vista rápida ejecutando directamente este archivo
def main(page: ft.Page):
	page.title = "Tareas"
	view = TaskView(page)
	page.add(view.build())


if __name__ == "__main__":
	ft.app(target=main)


