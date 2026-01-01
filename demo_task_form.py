"""Demo UI para TaskForm
Ejecutar: python demo_task_form.py
"""
import flet as ft
from app.ui.task.components.task_form import TaskForm


def main(page: ft.Page):
    page.title = "Task Form - Demo"
    page.window.width = 480
    page.window.height = 720
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = ft.Colors.GREY_900

    status = ft.Text("Interactúa con el formulario (Guardar/Cancelar)", color=ft.Colors.GREY_400)

    def on_save(task):
        status.value = f"Guardado: {task.title}"
        page.update()

    def on_cancel():
        status.value = "Cancelado"
        page.update()

    form = TaskForm(page=page, on_save=on_save, on_cancel=on_cancel)

    lv = ft.ListView(
        controls=[form.build(), ft.Divider(height=1), status],
        expand=True,
        spacing=0,
        padding=10,
        auto_scroll=False,
    )

    page.add(lv)
    page.update()


if __name__ == "__main__":
    ft.run(main)