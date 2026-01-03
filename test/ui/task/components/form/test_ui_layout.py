"""Demo UI para visualizar `build_form_layout`.

Ejecutar manualmente (no es un test):

	/home/devjdtp/Proyectos/App_movil_real_live/.venv/bin/python \
		test/ui/task/components/form/test_ui_layout.py
"""

# Evita que pytest intente colectar tests de este módulo
__test__ = False

from pathlib import Path
import sys

import flet as ft


# Agregar el directorio raíz al path para imports si se ejecuta directamente
project_root = Path(__file__).resolve().parents[5]
if str(project_root) not in sys.path:
	sys.path.insert(0, str(project_root))


from app.ui.task.form.layout import build_form_layout
from app.ui.task.form.date_controls import build_due_date_controls
from app.models.subtask import Subtask
from app.ui.task.form.subtask import (
	build_add_subtask_row,
	create_subtask,
	delete_subtask,
	edit_subtask,
	render_subtasks,
	toggle_subtask,
)


def main(page: ft.Page):
	page.title = "Demo UI - Form Layout"
	page.window.width = 520
	page.window.height = 820
	page.theme_mode = ft.ThemeMode.DARK
	page.bgcolor = ft.Colors.GREY_900
	page.padding = 12

	# Controles de ejemplo (mínimos)
	title_field = ft.TextField(label="Título", value="Tarea demo")
	description_field = ft.TextField(
		label="Descripción",
		value="Descripción larga\n" * 20,
		multiline=True,
		min_lines=3,
		max_lines=8,
	)
	status_dropdown = ft.Dropdown(
		label="Estado",
		value="pending",
		options=[
			ft.dropdown.Option("pending", "Pendiente"),
			ft.dropdown.Option("in_progress", "En progreso"),
			ft.dropdown.Option("completed", "Completada"),
			ft.dropdown.Option("cancelled", "Cancelada"),
		],
	)
	urgent_checkbox = ft.Checkbox(label="Urgente", value=False)
	important_checkbox = ft.Checkbox(label="Importante", value=True)

	state = {"selected_date": None}

	def on_selected_date_change(new_date):
		state["selected_date"] = new_date

	date_picker, due_date_text, open_date_picker, clear_date = build_due_date_controls(
		page=page,
		selected_date=state["selected_date"],
		on_selected_date_change=on_selected_date_change,
	)

	tags_field = ft.TextField(label="Etiquetas", value="python, flet")
	notes_field = ft.TextField(label="Notas", value="Notas...")

	subtasks: list[Subtask] = [
		Subtask(id="1", task_id="demo", title="Subtarea 1", completed=False),
		Subtask(id="2", task_id="demo", title="Subtarea 2", completed=True),
	]

	subtasks_body = ft.Container()

	def rerender_subtasks() -> None:
		def on_delete(index: int) -> None:
			delete_subtask(subtasks, index)
			rerender_subtasks()
			page.update()

		def on_toggle(index: int, completed: bool) -> None:
			toggle_subtask(subtasks, index, completed)
			rerender_subtasks()
			page.update()

		def on_edit(index: int, title: str) -> None:
			edit_subtask(subtasks, index, title)
			rerender_subtasks()
			page.update()

		subtasks_body.content = render_subtasks(
			subtasks,
			on_delete=on_delete,
			on_toggle=on_toggle,
			on_edit=on_edit,
		)

	def show_add_subtask(e=None) -> None:
		def on_save(title: str) -> None:
			subtasks.append(create_subtask(title=title, task_id="demo"))
			rerender_subtasks()
			page.update()

		def on_cancel() -> None:
			rerender_subtasks()
			page.update()

		subtasks_body.content = build_add_subtask_row(on_save=on_save, on_cancel=on_cancel)
		page.update()

	subtasks_header = ft.Row(
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
	)

	subtasks_section = ft.Column(
		controls=[subtasks_header, subtasks_body],
		spacing=8,
	)
	rerender_subtasks()
	error_text = ft.Text("", visible=False)

	def save(e):
		error_text.value = "Guardar (demo) ejecutado"
		error_text.color = ft.Colors.GREEN_400
		error_text.visible = True
		page.snack_bar = ft.SnackBar(ft.Text("Guardar (demo)"))
		page.snack_bar.open = True
		page.update()

	def cancel(e):
		error_text.value = "Cancelar (demo) ejecutado"
		error_text.color = ft.Colors.RED_400
		error_text.visible = True
		page.snack_bar = ft.SnackBar(ft.Text("Cancelar (demo)"))
		page.snack_bar.open = True
		page.update()

	save_button = ft.FilledButton(
		"Guardar",
		icon=ft.Icons.SAVE,
		on_click=save,
		style=ft.ButtonStyle(bgcolor=ft.Colors.RED_700, color=ft.Colors.WHITE),
	)
	cancel_button = ft.OutlinedButton(
		"Cancelar",
		icon=ft.Icons.CANCEL,
		on_click=cancel,
		style=ft.ButtonStyle(side=ft.BorderSide(2, ft.Colors.RED_700), color=ft.Colors.RED_700),
	)

	layout = build_form_layout(
		is_edit_mode=False,
		title_field=title_field,
		description_field=description_field,
		status_dropdown=status_dropdown,
		urgent_checkbox=urgent_checkbox,
		important_checkbox=important_checkbox,
		due_date_text=due_date_text,
		open_date_picker=open_date_picker,
		clear_date=clear_date,
		tags_field=tags_field,
		notes_field=notes_field,
		subtasks_section=subtasks_section,
		error_text=error_text,
		save_button=save_button,
		cancel_button=cancel_button,
	)

	page.add(layout)


if __name__ == "__main__":
	ft.run(main)
