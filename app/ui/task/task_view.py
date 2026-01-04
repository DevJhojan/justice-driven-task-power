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
from app.utils.task_helper import TASK_STATUS_PENDING, TASK_STATUS_COMPLETED
from app.services.database_service import DatabaseService
from app.services.task_service import TaskService
from app.services.progress_service import ProgressService

# Permite ejecución directa añadiendo la raíz del proyecto al path
ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
	sys.path.insert(0, str(ROOT_DIR))


class TaskView:
	def __init__(self, page: Optional[ft.Page] = None, rewards_view=None):
		self.page = page
		self.rewards_view = rewards_view  # Referencia a PointsAndLevelsView para actualizar puntos

		self.tasks: List[Task] = []
		self.editing: Optional[Task] = None
		self.user_id: str = "default_user"  # ID del usuario actual

		# Servicios
		self.database_service: Optional[DatabaseService] = None
		self.task_service: Optional[TaskService] = None
		self.progress_service = ProgressService()  # Sistema de progreso sin usuarios

		# UI refs
		self.form: TaskForm = TaskForm(self._handle_save, self._handle_cancel, self._on_subtask_changed)
		self.form_card: Optional[ft.Card] = None
		self.form_container: Optional[ft.Container] = None
		self.task_list: TaskList = TaskList(self._edit_task, self._delete_task, self._on_task_updated, self.progress_service, self.rewards_view, self.page)

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
		# Si la tarea está completada, añadir puntos
		if task.status == TASK_STATUS_COMPLETED:
			self.page.run_task(self._async_add_points_for_task, task)
		
		# Ejecutar operación asincrónica para actualizar
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
			
			# Usar la misma conexión para el progreso si aún no tiene una
			if self.progress_service.database_service is None:
				self.progress_service.database_service = self.database_service
			await self.progress_service.ensure_persistence()
			
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
			await self._async_update_completed_tasks_count()
			# Calcular y sumar puntos por subtareas completadas
			await self._async_sync_subtask_points()
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
	
	async def _async_add_points_for_task(self, task: Task):
		"""Añade puntos al usuario por completar una tarea."""
		try:
			print(f"[TaskView] Añadiendo puntos por completar tarea: {task.title}")
			
			# Añadir puntos usando ProgressService con persistencia
			stats = await self.progress_service.add_points("task_completed")
			print(f"[TaskView] Stats actualizados: Puntos={stats['points']:.2f}, Nivel={stats['level']}")
			
			# Actualizar PointsAndLevelsView si está disponible
			if self.rewards_view:
				current_points = stats.get("points", 0.0)
				current_level = stats.get("level", "Nadie")
				
				print(f"[TaskView] Actualizando PointsAndLevelsView - Puntos: {current_points:.2f}, Nivel: {current_level}")
				self.rewards_view.set_user_points(current_points)
				self.rewards_view.set_user_level(current_level)
				self.rewards_view.update_progress_from_stats(stats)
				
				# Mostrar notificación si hubo subida de nivel
				if stats.get("level_up", False):
					old_level = stats.get("old_level", "")
					print(f"[TaskView] 🎉 ¡NIVEL SUBIDO! {old_level} → {current_level}")
				
				# Forzar actualización de la página
				if self.page:
					self.page.update()
					print(f"[TaskView] Página actualizada")
			
			print(f"✓ Puntos añadidos por completar tarea: {task.title}")
			# Actualizar contador de tareas completadas
			await self._async_update_completed_tasks_count()
		except Exception as e:
			print(f"[TaskView] Error añadiendo puntos: {str(e)}")
			import traceback
			traceback.print_exc()

	async def _async_update_completed_tasks_count(self):
		"""Calcula tareas completadas y actualiza la vista de recompensas"""
		try:
			count = 0
			if self.database_service:
				count = await self.database_service.count(
					table_name="tasks",
					filters={"status": TASK_STATUS_COMPLETED, "user_id": self.user_id},
				)
			else:
				count = sum(1 for t in self.tasks if t.status == TASK_STATUS_COMPLETED)

			if self.rewards_view:
				self.rewards_view.set_tasks_completed(count)
		except Exception as e:
			print(f"[TaskView] Error actualizando tareas completadas: {e}")

	async def _async_verify_points_integrity(self):
		"""Verifica la integridad de los puntos y corrige si hay inconsistencias"""
		try:
			print(f"\n{'='*70}")
			print(f"[TaskView] 🔍 VERIFICACIÓN DE INTEGRIDAD DE PUNTOS")
			print(f"{'='*70}")
			
			# Obtener puntos actuales de la BD
			stats = await self.progress_service.load_stats()
			current_points = stats.get("points", 0.0)
			print(f"  📊 Puntos actuales en BD: {current_points:.2f}")
			
			# Calcular puntos esperados basados en tareas y subtareas completadas
			expected_points = 0.0
			completed_tasks = 0
			completed_subtasks = 0
			
			for task in self.tasks:
				if task.status == TASK_STATUS_COMPLETED:
					completed_tasks += 1
					expected_points += 0.05  # POINTS_BY_ACTION["task_completed"]
				
				if task.subtasks:
					for subtask in task.subtasks:
						if subtask.completed:
							completed_subtasks += 1
							expected_points += 0.02  # POINTS_BY_ACTION["subtask_completed"]
			
			print(f"  📋 Tareas completadas: {completed_tasks} x 0.05 = {completed_tasks * 0.05:.2f} puntos")
			print(f"  ✓ Subtareas completadas: {completed_subtasks} x 0.02 = {completed_subtasks * 0.02:.2f} puntos")
			print(f"  🎯 Total esperado: {expected_points:.2f} puntos")
			
			# Verificar si hay diferencia
			difference = abs(current_points - expected_points)
			had_correction = False
			
			if difference > 0.001:  # Tolerancia de precisión flotante
				print(f"  ⚠️  INCONSISTENCIA DETECTADA")
				print(f"  📉 Diferencia: {difference:.2f} puntos")
				print(f"  🔧 Corrigiendo puntos...")
				
				# Corregir los puntos usando set_points
				await self.progress_service.set_points(expected_points)
				
				# Recargar stats corregidos
				stats = await self.progress_service.load_stats()
				print(f"  ✅ Puntos corregidos: {stats['points']:.2f}")
				print(f"  📊 Nivel actualizado: {stats['level']}")
				
				# Actualizar PointsAndLevelsView
				if self.rewards_view:
					self.rewards_view.set_user_points(stats.get("points", 0.0))
					self.rewards_view.set_user_level(stats.get("level", "Nadie"))
					self.rewards_view.update_progress_from_stats(stats)
				
				had_correction = True
			else:
				print(f"  ✅ Integridad verificada - Los puntos son correctos")
			
			print(f"{'='*70}\n")
			
			# Mostrar resultado en el panel de PointsAndLevelsView
			if self.rewards_view:
				self.rewards_view.show_integrity_result(
					current_points=current_points,
					expected_points=expected_points,
					completed_tasks=completed_tasks,
					completed_subtasks=completed_subtasks,
					had_correction=had_correction
				)
			
			return had_correction
			
		except Exception as e:
			print(f"[TaskView] ❌ Error verificando integridad de puntos: {e}")
			import traceback
			traceback.print_exc()
			return False
	
	async def _async_sync_subtask_points(self):
		"""Sincroniza los puntos de subtareas completadas (suma solo si BD está en 0.00)"""
		try:
			print(f"\n[TaskView] 🔄 SINCRONIZACIÓN DE PUNTOS AL INICIAR")
			
			# Obtener puntos actuales de la BD
			stats = await self.progress_service.load_stats()
			current_points = stats.get("points", 0.0)
			
			print(f"[TaskView] 📊 Puntos actuales en BD: {current_points:.2f}")
			
			# Contar subtareas completadas
			total_completed_subtasks = 0
			for task in self.tasks:
				if task.subtasks:
					total_completed_subtasks += sum(1 for st in task.subtasks if st.completed)
			
			print(f"[TaskView] ✓ Subtareas completadas detectadas: {total_completed_subtasks}")
			
			# Si la BD está en 0.00 y hay subtareas completadas, sumarlas
			if current_points == 0.0 and total_completed_subtasks > 0:
				print(f"[TaskView] 🆕 BD en 0.00 - Sumando puntos por primera vez...")
				
				# Sumar 0.02 puntos por cada subtarea completada
				for _ in range(total_completed_subtasks):
					stats = await self.progress_service.add_points("subtask_completed")
				
				print(f"[TaskView] ✅ {total_completed_subtasks} subtareas sumadas - Nuevos puntos: {stats['points']:.2f}")
			else:
				if current_points > 0.0:
					print(f"[TaskView] 📝 BD tiene puntos ({current_points:.2f}) - NO sumando duplicados")
					print(f"[TaskView] 🔍 Verificando integridad de puntos...")
					# Verificar integridad de los puntos
					await self._async_verify_points_integrity()
				else:
					print(f"[TaskView] ℹ️  No hay subtareas completadas para sumar")
			
			# Actualizar PointsAndLevelsView con los stats finales
			if self.rewards_view:
				stats = await self.progress_service.load_stats()
				self.rewards_view.set_user_points(stats.get("points", 0.0))
				self.rewards_view.set_user_level(stats.get("level", "Nadie"))
				self.rewards_view.update_progress_from_stats(stats)
				print(f"[TaskView] 🔄 PointsAndLevelsView actualizado - Puntos totales: {stats['points']:.2f}\n")
			
		except Exception as e:
			print(f"[TaskView] ❌ Error sincronizando puntos de subtareas: {e}")
			import traceback
			traceback.print_exc()

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


