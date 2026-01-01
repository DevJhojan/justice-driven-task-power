"""Demo UI para visualizar los controles del módulo app.ui.task.components.form.controls.

Ejecutar manualmente (no es un test):

    python test/ui/task/components/form/test_ui_controls.py

Nota: Este archivo existe como demo visual, no como suite de tests.
Los tests unitarios están en: test/ui/task/components/form/test_controls.py
"""

# Evita que pytest intente colectar tests de este módulo
__test__ = False

from pathlib import Path
import sys

# Agregar el directorio raíz al path para imports si se ejecuta directamente
project_root = Path(__file__).resolve().parents[5]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import flet as ft

from app.models.task import Task
from app.ui.task.components.form.controls import (
    create_description_field,
    create_error_text,
    create_notes_field,
    create_priority_checkboxes,
    create_status_dropdown,
    create_tags_field,
    create_title_field,
)


def main(page: ft.Page):
    page.title = "Demo UI - TaskForm Controls"
    page.window.width = 520
    page.window.height = 820
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = ft.Colors.GREY_900
    page.padding = 12

    sample_task = Task(
        id="demo_task",
        user_id="demo_user",
        title="Tarea demo",
        description="Descripción demo",
        tags=["python", "flet", "ui"],
        notes="Notas demo",
        urgent=True,
        important=False,
    )

    title_field = create_title_field(sample_task)
    description_field = create_description_field(sample_task)
    status_dropdown = create_status_dropdown(sample_task)
    urgent_checkbox, important_checkbox = create_priority_checkboxes(sample_task)
    tags_field = create_tags_field(sample_task)
    notes_field = create_notes_field(sample_task)
    error_text = create_error_text()

    def show_error(e):
        error_text.value = " • Ejemplo de mensaje de error\n • Segundo error"
        error_text.visible = True
        page.update()

    def clear_error(e):
        error_text.value = ""
        error_text.visible = False
        page.update()

    content = ft.Column(
        controls=[
            ft.Text(
                "Demo UI - Controls",
                size=20,
                weight=ft.FontWeight.BOLD,
                color=ft.Colors.RED_400,
            ),
            ft.Divider(height=1, color=ft.Colors.RED_900),
            title_field,
            description_field,
            # Estado y prioridad (vertical: evita que el dropdown rompa el layout)
            ft.Column(
                controls=[
                    status_dropdown,
                    ft.Column(
                        controls=[
                            ft.Text("Prioridad:", size=12, weight=ft.FontWeight.BOLD),
                            urgent_checkbox,
                            important_checkbox,
                        ],
                        spacing=4,
                    ),
                ],
                spacing=12,
            ),
            tags_field,
            notes_field,
            error_text,
            ft.Row(
                controls=[
                    ft.FilledButton(
                        "Mostrar error",
                        icon=ft.Icons.ERROR_OUTLINE,
                        on_click=show_error,
                        style=ft.ButtonStyle(bgcolor=ft.Colors.RED_900, color=ft.Colors.WHITE),
                    ),
                    ft.OutlinedButton(
                        "Limpiar",
                        icon=ft.Icons.CLEAR,
                        on_click=clear_error,
                        style=ft.ButtonStyle(side=ft.BorderSide(2, ft.Colors.RED_700), color=ft.Colors.RED_700),
                    ),
                ],
                spacing=12,
            ),
        ],
        spacing=16,
        scroll=ft.ScrollMode.AUTO,
        expand=True,
        horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
    )

    page.add(content)
    page.update()


if __name__ == "__main__":
    ft.run(main)

