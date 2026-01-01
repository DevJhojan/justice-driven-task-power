"""Demo UI para visualizar `build_due_date_controls`.

Ejecutar manualmente (no es un test):

	/home/devjdtp/Proyectos/App_movil_real_live/.venv/bin/python \
		test/ui/task/components/form/test_ui_date_controls.py
"""

# Evita que pytest intente colectar tests de este módulo
__test__ = False

from pathlib import Path
import sys
from datetime import date, timedelta

import flet as ft


# Agregar el directorio raíz al path para imports si se ejecuta directamente
project_root = Path(__file__).resolve().parents[5]
if str(project_root) not in sys.path:
	sys.path.insert(0, str(project_root))


from app.ui.task.components.form.date_controls import build_due_date_controls
from app.utils.helpers.formats import format_date


def main(page: ft.Page):
	page.title = "Demo UI - Date Controls"
	page.window.width = 480
	page.window.height = 420
	page.theme_mode = ft.ThemeMode.DARK
	page.bgcolor = ft.Colors.GREY_900
	page.padding = 16

	state = {"selected_date": date.today() + timedelta(days=3)}

	selected_value_text = ft.Text("", size=12, color=ft.Colors.GREY_500)

	def on_selected_date_change(new_date):
		state["selected_date"] = new_date
		selected_value_text.value = (
			f"Valor interno: {format_date(new_date)}" if new_date else "Valor interno: None"
		)

	date_picker, date_text, open_date_picker, clear_date = build_due_date_controls(
		page=page,
		selected_date=state["selected_date"],
		on_selected_date_change=on_selected_date_change,
	)

	# Inicializa el texto del valor interno
	on_selected_date_change(state["selected_date"])

	content = ft.Column(
		controls=[
			ft.Text(
				"Demo UI - Date Controls",
				size=18,
				weight=ft.FontWeight.BOLD,
				color=ft.Colors.RED_400,
			),
			ft.Divider(height=1, color=ft.Colors.RED_900),
			ft.Text("Fecha de vencimiento:", size=12, weight=ft.FontWeight.BOLD),
			date_text,
			selected_value_text,
			ft.Row(
				controls=[
					ft.FilledButton(
						"Elegir fecha",
						icon=ft.Icons.CALENDAR_MONTH,
						on_click=open_date_picker,
						style=ft.ButtonStyle(bgcolor=ft.Colors.RED_900, color=ft.Colors.WHITE),
					),
					ft.TextButton(
						"Limpiar",
						on_click=clear_date,
						style=ft.ButtonStyle(color=ft.Colors.RED_700),
					),
				],
				spacing=10,
			),
			ft.Text(
				"Tip: el DatePicker vive en page.overlay",
				size=11,
				color=ft.Colors.GREY_600,
				italic=True,
			),
		],
		spacing=12,
	)

	page.add(content)


if __name__ == "__main__":
	ft.run(main)
