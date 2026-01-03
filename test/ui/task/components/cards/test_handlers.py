"""
Tests para los handlers de Task Card
Incluye comprobaciones unitarias y una demo UI similar al estilo de `test_task_card.py`
"""

from pathlib import Path
import sys

# Agregar el directorio raíz al path para imports (necesario si se ejecuta directamente)
# Este archivo está en `test/ui/task/components/cards/` por lo que hay que subir 5 niveles
project_root = Path(__file__).resolve().parents[5]  # cards -> components -> task -> ui -> test -> raíz
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import pytest
import flet as ft
from unittest.mock import MagicMock

from app.models.task import Task
from app.models.subtask import Subtask
from app.ui.task.cards.handlers import (
    create_subtask_toggle_handler,
    create_toggle_status_handler,
    _update_task_status_by_progress,
)
from app.ui.task.status_badge import create_status_badge
from app.utils.task_helper import (
    calculate_completion_percentage,
    format_completion_percentage,
    TASK_STATUS_PENDING,
    TASK_STATUS_IN_PROGRESS,
    TASK_STATUS_COMPLETED,
)


class TestHandlers:
    def test_create_subtask_toggle_handler_updates_progress_and_calls_callback(self, mock_page):
        task = Task(id="task_1", title="Tarea con subtareas", user_id="user_1")
        s1 = Subtask(id="sub_1", task_id="task_1", title="Sub 1", completed=False)
        s2 = Subtask(id="sub_2", task_id="task_1", title="Sub 2", completed=False)
        task.add_subtask(s1)
        task.add_subtask(s2)

        progress_bar = ft.ProgressBar(value=0.0, width=200)
        progress_text = ft.Text(value="0%")
        badges_row = ft.Row(controls=[create_status_badge(task.status, page=None, size="small")])

        on_subtask_toggle = MagicMock()

        handler = create_subtask_toggle_handler(
            task=task,
            page=mock_page,
            progress_bar=progress_bar,
            progress_text=progress_text,
            badges_row=badges_row,
            show_progress=True,
            on_subtask_toggle=on_subtask_toggle,
        )

        # Ejecutar handler
        handler("sub_1")

        # La subtarea debe invertirse
        assert task.subtasks[0].completed is True

        # El progreso debe actualizarse
        expected_percentage = calculate_completion_percentage(task)
        assert progress_bar.value == expected_percentage
        assert progress_text.value == format_completion_percentage(task)

        # El estado de la tarea debe pasar a EN_PROGRESO (50%)
        assert task.status == TASK_STATUS_IN_PROGRESS

        # Badge debe haberse reconstruido (contenido no nulo)
        assert badges_row.controls[0] is not None

        # Debe haberse actualizado la página
        mock_page.update.assert_called()

        # Callback debe llamarse con task_id y subtask_id
        on_subtask_toggle.assert_called_once_with(task.id, "sub_1")

    def test_create_subtask_toggle_handler_with_missing_subtask_noop(self, mock_page):
        task = Task(id="task_2", title="Tarea vacía", user_id="user_1")
        s1 = Subtask(id="sub_1", task_id="task_2", title="Sub 1", completed=False)
        task.add_subtask(s1)

        progress_bar = ft.ProgressBar(value=0.0, width=200)
        progress_text = ft.Text(value="0%")
        badges_row = ft.Row(controls=[create_status_badge(task.status, page=None, size="small")])

        on_subtask_toggle = MagicMock()

        handler = create_subtask_toggle_handler(
            task=task,
            page=mock_page,
            progress_bar=progress_bar,
            progress_text=progress_text,
            badges_row=badges_row,
            show_progress=True,
            on_subtask_toggle=on_subtask_toggle,
        )

        # Llamar con un id que no existe
        handler("not_exists")

        # Nada debe cambiar
        assert task.subtasks[0].completed is False
        assert progress_bar.value == 0.0
        assert progress_text.value == "0%"
        on_subtask_toggle.assert_not_called()
        # No debe actualizar la página
        mock_page.update.assert_not_called()

    def test_create_toggle_status_handler_toggles_and_calls_callback(self, mock_page):
        # Tarea sin subtareas
        task = Task(id="task_3", title="Tarea simple", user_id="user_1")

        progress_bar = ft.ProgressBar(value=0.0, width=200)
        progress_text = ft.Text(value="0%")
        badges_row = ft.Row(controls=[create_status_badge(task.status, page=None, size="small")])
        toggle_button = ft.IconButton(icon=ft.Icons.CHECK_CIRCLE)

        on_toggle_status = MagicMock()

        handler = create_toggle_status_handler(
            task=task,
            page=mock_page,
            progress_bar=progress_bar,
            progress_text=progress_text,
            badges_row=badges_row,
            toggle_button=toggle_button,
            show_progress=True,
            on_toggle_status=on_toggle_status,
        )

        # Primera pulsación: pasar a completada
        handler(None)
        assert task.status == TASK_STATUS_COMPLETED
        assert progress_bar.value == 1.0
        assert progress_text.value == format_completion_percentage(task)
        # Icono debe reflejar el nuevo estado (según implementación)
        assert toggle_button.icon == ft.Icons.UNDO
        on_toggle_status.assert_called_once_with(task.id)
        mock_page.update.assert_called()

        # Resetear mocks
        mock_page.update.reset_mock()
        on_toggle_status.reset_mock()

        # Segunda pulsación: volver a pendiente
        handler(None)
        assert task.status == TASK_STATUS_PENDING
        assert progress_bar.value == 0.0
        assert progress_text.value == format_completion_percentage(task)
        assert toggle_button.icon == ft.Icons.CHECK_CIRCLE
        on_toggle_status.assert_called_once_with(task.id)
        mock_page.update.assert_called()

    def test_update_task_status_by_progress_transitions(self, mock_page):
        task = Task(id="task_4", title="Tarea estado", user_id="user_1")
        badges_row = ft.Row(controls=[create_status_badge(task.status, page=None, size="small")])

        # 100% -> COMPLETADA
        _update_task_status_by_progress(task=task, new_percentage=1.0, badges_row=badges_row, page=mock_page)
        assert task.status == TASK_STATUS_COMPLETED
        mock_page.update.assert_not_called()  # la función no llama a page.update directamente

        # 0% -> PENDIENTE
        task.update_status(TASK_STATUS_COMPLETED)  # asegurar starting point
        _update_task_status_by_progress(task=task, new_percentage=0.0, badges_row=badges_row, page=mock_page)
        assert task.status == TASK_STATUS_PENDING

        # Entre 0 y 1 -> EN_PROGRESO
        _update_task_status_by_progress(task=task, new_percentage=0.5, badges_row=badges_row, page=mock_page)
        assert task.status == TASK_STATUS_IN_PROGRESS


# ==========================================================================
# DEMO UI - Ejecutar con: python test/ui/task/components/cards/test_handlers.py
# ==========================================================================

def main(page: ft.Page):
    page.title = "Handlers - Demo Visual"
    page.window.width = 600
    page.window.height = 400
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 20

    # Tarea de demo con subtareas
    task = Task(id="demo_task", title="Tarea Demo", user_id="demo_user")
    task.add_subtask(Subtask(id="sub_a", task_id=task.id, title="Sub A", completed=False))
    task.add_subtask(Subtask(id="sub_b", task_id=task.id, title="Sub B", completed=False))

    pb = ft.ProgressBar(value=calculate_completion_percentage(task), width=300)
    pt = ft.Text(value=format_completion_percentage(task))
    badges = ft.Row(controls=[create_status_badge(task.status, page=page, size="small")])

    def on_sub_toggle(tid, sid):
        print(f"subtoggle {tid} {sid}")

    sub_handler = create_subtask_toggle_handler(
        task=task,
        page=page,
        progress_bar=pb,
        progress_text=pt,
        badges_row=badges,
        show_progress=True,
        on_subtask_toggle=on_sub_toggle,
    )

    # Crear botones para simular toggle de subtareas
    btns = ft.Row(
        controls=[
            ft.ElevatedButton("Toggle Sub A", on_click=lambda e: sub_handler("sub_a")),
            ft.ElevatedButton("Toggle Sub B", on_click=lambda e: sub_handler("sub_b")),
        ],
        spacing=15,
    )

    # Toggle status para tarea sin subtareas
    single_task = Task(id="single", title="Toggle Status", user_id="demo_user")
    tb = ft.ProgressBar(value=calculate_completion_percentage(single_task), width=120)
    tt = ft.Text(value=format_completion_percentage(single_task))
    badges2 = ft.Row(controls=[create_status_badge(single_task.status, page=page, size="small")])
    toggle_btn = ft.IconButton(icon=ft.Icons.CHECK_CIRCLE)

    toggle_handler = create_toggle_status_handler(
        task=single_task,
        page=page,
        progress_bar=tb,
        progress_text=tt,
        badges_row=badges2,
        toggle_button=toggle_btn,
        show_progress=True,
    )
    toggle_btn.on_click = toggle_handler

    page.add(
        ft.Column(
            controls=[
                ft.Text("Handlers Demo", size=20, weight=ft.FontWeight.BOLD),
                ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                ft.Row(controls=[pb, pt, badges]),
                btns,
                ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
                ft.Row(controls=[tb, tt, badges2, toggle_btn]),
            ],
            spacing=12,
        )
    )
    page.update()


if __name__ == "__main__":
    ft.run(main)
