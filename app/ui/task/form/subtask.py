"""UI + helpers de subtareas para el formulario de tareas.

Objetivo: concentrar aquí la lógica de subtareas (creación, toggle, borrado y
render de la sección) para que `TaskForm` mantenga únicamente el estado
principal (lista de subtareas) y delegue la UI a este módulo.
"""

from __future__ import annotations

from datetime import datetime
from typing import Callable, Optional

import flet as ft

from app.models.subtask import Subtask


def create_subtask(
	*,
	title: str,
	task_id: str = "",
	completed: bool = False,
	subtask_id: Optional[str] = None,
) -> Subtask:
	"""Crea una instancia `Subtask` con un id único por defecto."""
	safe_title = (title or "").strip()
	generated_id = subtask_id or f"subtask_{datetime.now().timestamp()}"
	return Subtask(
		id=generated_id,
		task_id=task_id,
		title=safe_title,
		completed=completed,
	)


def delete_subtask(subtasks: list[Subtask], index: int) -> None:
	"""Elimina una subtarea por índice (in-place)."""
	if 0 <= index < len(subtasks):
		subtasks.pop(index)


def toggle_subtask(subtasks: list[Subtask], index: int, completed: bool) -> None:
	"""Marca/desmarca una subtarea por índice (in-place)."""
	if 0 <= index < len(subtasks):
		subtasks[index].completed = bool(completed)


def edit_subtask(subtasks: list[Subtask], index: int, title: str) -> None:
	"""Edita el título de una subtarea por índice (in-place)."""
	if 0 <= index < len(subtasks):
		subtasks[index].title = (title or "").strip()


def build_add_subtask_row(
	*,
	on_save: Callable[[str], None],
	on_cancel: Callable[[], None],
	autofocus: bool = True,
) -> ft.Row:
	"""Construye la fila UI para el modo "añadir subtarea".

	Nota: el estado real (lista) debe mantenerse fuera (por ejemplo en TaskForm).
	Este control solo emite eventos de UI.
	"""

	subtask_input = ft.TextField(
		hint_text="Título de la subtarea",
		border_color=ft.Colors.RED_700,
		focused_border_color=ft.Colors.RED_400,
		cursor_color=ft.Colors.RED_400,
		autofocus=autofocus,
	)

	def _save(e):
		title = (subtask_input.value or "").strip()
		if title:
			on_save(title)

	def _cancel(e):
		on_cancel()

	return ft.Row(
		controls=[
			subtask_input,
			ft.IconButton(
				icon=ft.Icons.CHECK,
				icon_color=ft.Colors.GREEN_400,
				tooltip="Guardar",
				on_click=_save,
			),
			ft.IconButton(
				icon=ft.Icons.CLOSE,
				icon_color=ft.Colors.RED_400,
				tooltip="Cancelar",
				on_click=_cancel,
			),
		],
		spacing=8,
	)


def render_subtasks(
	subtasks: list[Subtask],
	on_delete: Callable[[int], None],
	on_toggle: Callable[[int, bool], None],
	on_edit: Optional[Callable[[int, str], None]] = None,
) -> ft.Column:
	"""Renderiza la lista de subtareas.

	Args:
		subtasks: Lista de subtareas (fuente de verdad fuera de este módulo)
		on_delete: Callback on_delete(index)
		on_toggle: Callback on_toggle(index, completed)

	Returns:
		Un `ft.Column` listo para insertarse en el formulario.
	"""

	column = ft.Column(spacing=8)

	if not subtasks:
		column.controls.append(
			ft.Text(
				"No hay subtareas. Haz clic en + para agregar.",
				size=12,
				color=ft.Colors.GREY_600,
				italic=True,
			)
		)
		return column

	for idx, subtask in enumerate(subtasks):
		def _delete_handler(e, index: int = idx):
			on_delete(index)

		def _toggle_handler(e, index: int = idx):
			on_toggle(index, bool(getattr(e.control, "value", False)))

		def _commit_title(control: ft.TextField, index: int, previous_title: str) -> None:
			new_title = (control.value or "").strip()
			if not new_title:
				control.value = previous_title
				return
			# Siempre muta el modelo local (fuente de datos del render)
			subtasks[index].title = new_title
			# Normaliza el control para que se vea el trim
			control.value = new_title
			# Notifica al caller (para re-render / persistencia si aplica)
			if on_edit is not None:
				on_edit(index, new_title)

		def _title_submit(e, index: int = idx, previous_title: str = subtask.title):
			_commit_title(e.control, index, previous_title)

		def _title_blur(e, index: int = idx, previous_title: str = subtask.title):
			_commit_title(e.control, index, previous_title)

		subtask_row = ft.Row(
			controls=[
				ft.Checkbox(
					value=subtask.completed,
					on_change=_toggle_handler,
					fill_color=ft.Colors.RED_700,
				),
				ft.TextField(
					value=subtask.title,
					hint_text="Título de subtarea",
					expand=True,
					text_size=13,
					color=ft.Colors.GREY_400 if subtask.completed else ft.Colors.WHITE,
					cursor_color=ft.Colors.RED_400,
					border_color=ft.Colors.TRANSPARENT,
					focused_border_color=ft.Colors.RED_400,
					on_submit=_title_submit,
					on_blur=_title_blur,
				),
				ft.IconButton(
					icon=ft.Icons.DELETE_OUTLINE,
					icon_color=ft.Colors.RED_400,
					icon_size=20,
					tooltip="Eliminar",
					on_click=_delete_handler,
				),
			],
			spacing=8,
		)
		column.controls.append(subtask_row)

	return column
