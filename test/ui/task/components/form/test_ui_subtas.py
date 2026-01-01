"""Demo UI para visualizar los helpers/UI de `app.ui.task.components.form.subtask`.

Ejecutar manualmente (no es un test):

	/home/devjdtp/Proyectos/App_movil_real_live/.venv/bin/python \
		test/ui/task/components/form/test_ui_subtas.py
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


from app.models.subtask import Subtask
from app.ui.task.components.form.subtask import (
	build_add_subtask_row,
	create_subtask,
	delete_subtask,
	edit_subtask,
	render_subtasks,
	toggle_subtask,
)


def main(page: ft.Page):
	page.title = "Demo UI - Subtasks"
	page.window.width = 520
	page.window.height = 720
	page.theme_mode = ft.ThemeMode.DARK
	page.bgcolor = ft.Colors.GREY_900
	page.padding = 16

	subtasks: list[Subtask] = [
		Subtask(id="1", task_id="demo", title="Comprar leche", completed=False),
		Subtask(id="2", task_id="demo", title="Hacer ejercicio", completed=True),
	]

	body = ft.Container()

	def rerender_list() -> None:
		def on_delete(index: int) -> None:
			delete_subtask(subtasks, index)
			rerender_list()
			page.update()

		def on_toggle(index: int, completed: bool) -> None:
			toggle_subtask(subtasks, index, completed)
			rerender_list()
			page.update()

		def on_edit(index: int, title: str) -> None:
			edit_subtask(subtasks, index, title)
			rerender_list()
			page.update()

		body.content = render_subtasks(
			subtasks,
			on_delete=on_delete,
			on_toggle=on_toggle,
			on_edit=on_edit,
		)

	def show_add_mode(e=None) -> None:
		def on_save(title: str) -> None:
			subtasks.append(create_subtask(title=title, task_id="demo"))
			rerender_list()
			page.update()

		def on_cancel() -> None:
			rerender_list()
			page.update()

		body.content = build_add_subtask_row(on_save=on_save, on_cancel=on_cancel)
		page.update()

	header = ft.Row(
		controls=[
			ft.Text("Subtareas", size=16, weight=ft.FontWeight.BOLD),
			ft.IconButton(
				icon=ft.Icons.ADD_CIRCLE,
				icon_color=ft.Colors.RED_700,
				tooltip="Agregar subtarea",
				on_click=show_add_mode,
			),
		],
		alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
	)

	rerender_list()

	page.add(
		ft.Column(
			controls=[
				ft.Text(
					"Demo UI - Subtasks",
					size=18,
					weight=ft.FontWeight.BOLD,
					color=ft.Colors.RED_400,
				),
				ft.Divider(height=1, color=ft.Colors.RED_900),
				header,
				body,
				ft.Text(
					"Tip: usa + para entrar al modo añadir",
					size=11,
					color=ft.Colors.GREY_600,
					italic=True,
				),
			],
			spacing=12,
		)
	)


if __name__ == "__main__":
	ft.run(main)
