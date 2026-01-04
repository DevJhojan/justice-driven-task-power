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
from app.ui.task.List.task_list import TaskList
from app.models.task import Task
from app.models.subtask import Subtask
from app.utils.task_helper import TASK_STATUS_PENDING
from app.services.database_service import DatabaseService
from app.services.task_service import TaskService

# Permite ejecución directa añadiendo la raíz del proyecto al path
ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
	sys.path.insert(0, str(ROOT_DIR))


class TaskView:
	def __init__(self, page: Optional[ft.Page] = None):
		self.page = page

		self.tasks: List[Task] = []
		self.editing: Optional[Task] = None
		self.user_id: str = "default_user"  # ID del usuario actual

		# Servicios
		self.database_service: Optional[DatabaseService] = None
		self.task_service: Optional[TaskService] = None

		# UI refs
		self.form: TaskForm = TaskForm(self._handle_save, self._handle_cancel, self._on_subtask_changed)
		self.form_card: Optional[ft.Card] = None
		self.form_container: Optional[ft.Container] = None
		self.task_list: TaskList = TaskList(self._edit_task, self._delete_task, self._on_task_updated)

	def build(self) -> ft.Container:
		self.form_card = self.form.build()
		self.form.set_page(self.page)
		self.form_container = ft.Container(content=self.form_card, visible=False)
		list_column = self.task_list.build()

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
				list_column,
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

		# Inicializar servicios y cargar tareas
		if self.page:
			self.page.run_task(self._initialize_services)
		
		return host

	# ------------------------------------------------------------------
	# Actions
	# ------------------------------------------------------------------
	def _handle_save(self, _):
		title = (self.form.title_field.value or "").strip()
		description = (self.form.desc_field.value or "").strip()
		if not title:
			self.form.show_error("El título es obligatorio")
			return

		# Obtener subtareas del formulario
		subtasks = self.form.subtask_manager.get_subtasks() if self.form.subtask_manager else []

		# Validar que si hay subtareas, deben ser mínimo 2
		if subtasks and len(subtasks) < 2:
			self.form.show_error("Debe agregar mínimo 2 subtareas para la tarea")
			return

		# Limpiar errores si todo es válido
		self.form.clear_error()

		# Ejecutar operación asincrónica
		if self.page:
			self.page.run_task(self._async_save_task, title, description, subtasks)

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
		# Ejecutar operación asincrónica
		if self.page:
			self.page.run_task(self._async_delete_task, task.id)
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
		self.task_list.hide()
		if self.page:
			self.page.update()

	def _show_list(self):
		self.task_list.show()
		if self.page:
			self.page.update()

	def _refresh_list(self):
		self.task_list.render(self.tasks)
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
		# Ejecutar operación asincrónica
		if self.page:
			self.page.run_task(self._async_update_task, task)
		self._refresh_list()


	# ------------------------------------------------------------------
	# Operaciones Asincrónicas
	# ------------------------------------------------------------------
	async def _initialize_services(self):
		"""Inicializa los servicios de base de datos y tareas."""
		try:
			self.database_service = DatabaseService()
			await self.database_service.initialize()
			
			self.task_service = TaskService(self.database_service)
			await self.task_service.initialize()
			
			# Cargar tareas existentes
			await self._async_load_tasks()
		except Exception as e:
			self.form.show_error(f"Error inicializando servicios: {str(e)}")
	
	async def _async_load_tasks(self):
		"""Carga las tareas de la base de datos."""
		try:
			all_tasks = await self.task_service.get_all_tasks(user_id=self.user_id)
			self.tasks = all_tasks
			self._refresh_list()
		except Exception as e:
			self.form.show_error(f"Error cargando tareas: {str(e)}")
	
	async def _async_save_task(self, title: str, description: str, subtasks: List[Subtask]):
		"""Guarda una tarea en la base de datos."""
		try:
			if self.editing:
				# Actualizar tarea existente
				self.editing.title = title
				self.editing.description = description
				# Asignar task_id a las subtareas
				for subtask in subtasks:
					subtask.task_id = self.editing.id
				self.editing.subtasks = subtasks
				self.editing.updated_at = datetime.now()
				self.editing.update_status_from_subtasks()
				
				await self.task_service.update_task(
					self.editing.id,
					self.editing.to_dict()
				)
			else:
				# Crear nueva tarea
				task = Task(
					id=str(uuid.uuid4()),
					title=title,
					description=description,
					status=TASK_STATUS_PENDING,
					subtasks=[],  # Iniciar vacío
					user_id=self.user_id,
				)
				
				# Asignar task_id a las subtareas
				for subtask in subtasks:
					subtask.task_id = task.id
				task.subtasks = subtasks
				task.update_status_from_subtasks()
				
				await self.task_service.create_task(task.to_dict())
				self.tasks.insert(0, task)
			
			self.editing = None
			self._reset_form()
			self._hide_form()
			self._show_list()
			self._refresh_list()
		except Exception as e:
			self.form.show_error(f"Error guardando tarea: {str(e)}")
	
	async def _async_delete_task(self, task_id: str):
		"""Elimina una tarea de la base de datos."""
		try:
			await self.task_service.delete_task(task_id)
		except Exception as e:
			self.form.show_error(f"Error eliminando tarea: {str(e)}")
	
	async def _async_update_task(self, task: Task):
		"""Actualiza una tarea en la base de datos."""
		try:
			await self.task_service.update_task(task.id, task.to_dict())
		except Exception as e:
			self.form.show_error(f"Error actualizando tarea: {str(e)}")


# Permite vista rápida ejecutando directamente este archivo
def main(page: ft.Page):
	page.title = "Tareas"
	view = TaskView(page)
	page.add(view.build())


if __name__ == "__main__":
	ft.app(target=main)


