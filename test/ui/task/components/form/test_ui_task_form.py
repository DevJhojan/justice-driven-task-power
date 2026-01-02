"""Demo UI para el TaskForm modular.

Ejecución manual:
	./.venv/bin/python test/ui/task/components/form/test_ui_task_form.py

Nota: este archivo NO es un test de pytest.
"""

from __future__ import annotations

import sys
from pathlib import Path
from datetime import date, datetime, timedelta

import flet as ft


# Permite ejecutar este archivo directamente sin depender del cwd.
_this_file = Path(__file__).resolve()
for _parent in _this_file.parents:
	if (_parent / "app").is_dir():
		sys.path.insert(0, str(_parent))
		break

from app.models.subtask import Subtask
from app.models.task import Task
from app.ui.task.components.form.task_form import TaskForm
from app.utils.task_helper import TASK_STATUS_IN_PROGRESS


__test__ = False


def main(page: ft.Page) -> None:
	page.title = "TaskForm (modular) Demo"
	page.theme_mode = ft.ThemeMode.DARK
	page.theme = ft.Theme(color_scheme_seed=ft.Colors.RED_900)
	page.bgcolor = ft.Colors.GREY_900
	page.padding = 20

	status_text = ft.Text("", color=ft.Colors.WHITE)

	def show_snackbar(message: str, color: str = ft.Colors.GREEN_400) -> None:
		snackbar = ft.SnackBar(content=ft.Text(message, color=ft.Colors.WHITE), bgcolor=color)
		page.overlay.append(snackbar)
		snackbar.open = True
		page.update()

	def handle_save(task: Task) -> None:
		status_text.value = f"Guardado: {task.title}"
		show_snackbar(f"✅ Tarea '{task.title}' guardada", ft.Colors.GREEN_400)
		page.update()

	def handle_cancel() -> None:
		status_text.value = "Cancelado"
		show_snackbar("❌ Formulario cancelado", ft.Colors.ORANGE_400)
		page.update()

	# Cambia a None si quieres ver modo crear
	sample_task = Task(
		id="task_demo",
		title="Implementar autenticación",
		description="Agregar sistema de login con JWT",
		status=TASK_STATUS_IN_PROGRESS,
		urgent=True,
		important=True,
		due_date=date.today() + timedelta(days=5),
		tags=["backend", "security", "api"],
		notes="Revisar documentación de JWT",
		subtasks=[
			Subtask(id="s1", task_id="task_demo", title="Diseñar endpoints", completed=True),
			Subtask(id="s2", task_id="task_demo", title="Implementar middleware", completed=False),
		],
		created_at=datetime.now(),
		updated_at=datetime.now(),
	)

	form = TaskForm(page=page, task=sample_task, on_save=handle_save, on_cancel=handle_cancel)

	page.add(
		ft.Column(
			controls=[
				form.build(),
				ft.Divider(height=24, color=ft.Colors.TRANSPARENT),
				status_text,
			],
			spacing=12,
			expand=True,
		)
	)


if __name__ == "__main__":
	ft.app(target=main)

