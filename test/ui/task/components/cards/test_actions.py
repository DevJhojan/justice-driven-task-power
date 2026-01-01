"""
Tests para Actions (botones de acción) del Task Card
Incluye comprobaciones unitarias y una demo visual.
"""

from pathlib import Path
import sys

# Agregar el directorio raíz al path para imports (necesario si se ejecuta directamente)
# Este archivo está en `test/ui/task/components/cards/` por lo que hay que subir 5 niveles
project_root = Path(__file__).resolve().parents[5]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import pytest
import flet as ft
from app.models.task import Task
from app.models.subtask import Subtask
from app.ui.task.components.cards.actions import (
    create_edit_button,
    create_delete_button,
    create_toggle_status_button,
    create_actions_row,
    Actions,
)
from app.utils.task_helper import TASK_STATUS_COMPLETED, TASK_STATUS_PENDING


def test_create_edit_button_basic(mock_page):
    """Test que create_edit_button retorna un IconButton con ícono de edición."""
    edit_btn = create_edit_button(task_id="t1", page=mock_page, on_edit=lambda x: None)
    assert isinstance(edit_btn, ft.IconButton)
    assert edit_btn.icon == ft.Icons.EDIT
    assert edit_btn.icon_color == ft.Colors.BLUE_400


def test_create_delete_button_basic(mock_page):
    """Test que create_delete_button retorna un IconButton con ícono de eliminación."""
    delete_btn = create_delete_button(task_id="t1", page=mock_page, on_delete=lambda x: None)
    assert isinstance(delete_btn, ft.IconButton)
    assert delete_btn.icon == ft.Icons.DELETE_OUTLINE
    assert delete_btn.icon_color == ft.Colors.RED_400


def test_create_toggle_status_button_returns_none_with_subtasks(mock_page):
    """Test que create_toggle_status_button retorna None si la tarea tiene subtareas."""
    task = Task(id="t_sub", title="Con subtareas", user_id="u")
    subtask = Subtask(id="s1", title="Subtarea 1", task_id="t_sub")
    task.subtasks = [subtask]

    badges_row = ft.Row(controls=[ft.Container()])
    toggle_btn = create_toggle_status_button(
        task=task,
        badges_row=badges_row,
        page=mock_page,
        on_toggle_status=lambda x: None,
    )
    assert toggle_btn is None


def test_create_toggle_status_button_returns_button_without_subtasks(mock_page):
    """Test que create_toggle_status_button retorna un botón si NO tiene subtareas."""
    task = Task(id="t_no_sub", title="Sin subtareas", user_id="u")
    task.subtasks = []
    task.status = TASK_STATUS_PENDING

    badges_row = ft.Row(controls=[ft.Container()])
    toggle_btn = create_toggle_status_button(
        task=task,
        badges_row=badges_row,
        page=mock_page,
        on_toggle_status=lambda x: None,
    )
    assert isinstance(toggle_btn, ft.IconButton)
    assert toggle_btn.icon == ft.Icons.CHECK_CIRCLE
    assert toggle_btn.icon_color == ft.Colors.GREEN_400


def test_create_toggle_status_button_undo_icon_when_completed(mock_page):
    """Test que el botón muestra ícono de UNDO cuando la tarea está completada."""
    task = Task(id="t_completed", title="Completada", user_id="u")
    task.subtasks = []
    task.status = TASK_STATUS_COMPLETED

    badges_row = ft.Row(controls=[ft.Container()])
    toggle_btn = create_toggle_status_button(
        task=task,
        badges_row=badges_row,
        page=mock_page,
        on_toggle_status=lambda x: None,
    )
    assert toggle_btn.icon == ft.Icons.UNDO


def test_create_actions_row_with_all_buttons(mock_page):
    """Test que create_actions_row retorna una fila con los tres botones."""
    task = Task(id="t_all", title="Con botones", user_id="u")
    task.subtasks = []

    badges_row = ft.Row(controls=[ft.Container()])
    actions_row = create_actions_row(
        task=task,
        badges_row=badges_row,
        page=mock_page,
        on_edit=lambda x: None,
        on_delete=lambda x: None,
        on_toggle_status=lambda x: None,
    )
    assert isinstance(actions_row, ft.Row)
    assert len(actions_row.controls) == 3
    for btn in actions_row.controls:
        assert isinstance(btn, ft.IconButton)


def test_create_actions_row_only_edit_delete_with_subtasks(mock_page):
    """Test que create_actions_row omite toggle button si hay subtareas."""
    task = Task(id="t_sub2", title="Con subtareas", user_id="u")
    subtask = Subtask(id="s1", title="Subtarea", task_id="t_sub2")
    task.subtasks = [subtask]

    badges_row = ft.Row(controls=[ft.Container()])
    actions_row = create_actions_row(
        task=task,
        badges_row=badges_row,
        page=mock_page,
        on_edit=lambda x: None,
        on_delete=lambda x: None,
        on_toggle_status=lambda x: None,
    )
    assert isinstance(actions_row, ft.Row)
    assert len(actions_row.controls) == 2
    assert actions_row.controls[0].icon == ft.Icons.EDIT
    assert actions_row.controls[1].icon == ft.Icons.DELETE_OUTLINE


def test_create_actions_row_returns_none_without_callbacks(mock_page):
    """Test que create_actions_row retorna None si no hay callbacks."""
    task = Task(id="t_none", title="Sin callbacks", user_id="u")
    task.subtasks = []

    badges_row = ft.Row(controls=[ft.Container()])
    actions_row = create_actions_row(
        task=task,
        badges_row=badges_row,
        page=mock_page,
    )
    assert actions_row is None


def test_actions_class_build_and_refresh(mock_page):
    """Test que Actions class construye y cachea la fila de acciones."""
    task = Task(id="t_class", title="Actions class", user_id="u")
    task.subtasks = []

    badges_row = ft.Row(controls=[ft.Container()])
    actions_comp = Actions(
        task=task,
        badges_row=badges_row,
        page=mock_page,
        on_edit=lambda x: None,
        on_delete=lambda x: None,
        on_toggle_status=lambda x: None,
    )

    row1 = actions_comp.build()
    assert isinstance(row1, ft.Row)
    assert len(row1.controls) == 3

    # Comprobar que está en caché (la siguiente llamada retorna el mismo objeto)
    row2 = actions_comp.build()
    assert row1 is row2

    # refresh() invalida el caché
    actions_comp.refresh()
    row3 = actions_comp.build()
    assert row3 is not row1
    assert isinstance(row3, ft.Row)
    assert len(row3.controls) == 3


def test_actions_class_button_references(mock_page):
    """Test que Actions class almacena referencias a los botones."""
    task = Task(id="t_refs", title="Button refs", user_id="u")
    task.subtasks = []

    badges_row = ft.Row(controls=[ft.Container()])
    actions_comp = Actions(
        task=task,
        badges_row=badges_row,
        page=mock_page,
        on_edit=lambda x: None,
        on_delete=lambda x: None,
        on_toggle_status=lambda x: None,
    )

    actions_comp.build()
    assert actions_comp.toggle_button is not None
    assert actions_comp.edit_button is not None
    assert actions_comp.delete_button is not None


# ============================================================================
# DEMO UI - Ejecutar con: python test/ui/task/components/cards/test_actions.py
# ============================================================================

def main(page: ft.Page):
    page.title = "Actions - Demo"
    page.window.width = 600
    page.window.height = 400
    page.padding = 20
    page.theme_mode = ft.ThemeMode.DARK

    # Tarea sin subtareas
    task_no_sub = Task(id="t_demo1", title="Tarea sin subtareas", user_id="demo")
    task_no_sub.subtasks = []

    # Tarea con subtareas
    task_with_sub = Task(id="t_demo2", title="Tarea con subtareas", user_id="demo")
    subtask = Subtask(id="s1", title="Subtarea demo", task_id="t_demo2")
    task_with_sub.subtasks = [subtask]

    badges_row = ft.Row(controls=[ft.Container()])

    edit_count = 0
    delete_count = 0
    toggle_count = 0

    def on_edit(task_id):
        nonlocal edit_count
        edit_count += 1
        status_text.value = f"Edit clicked! (Count: {edit_count})"
        page.update()

    def on_delete(task_id):
        nonlocal delete_count
        delete_count += 1
        status_text.value = f"Delete clicked! (Count: {delete_count})"
        page.update()

    def on_toggle(task_id):
        nonlocal toggle_count
        toggle_count += 1
        status_text.value = f"Toggle clicked! (Count: {toggle_count})"
        page.update()

    actions_no_sub = Actions(
        task=task_no_sub,
        badges_row=badges_row,
        page=page,
        on_edit=on_edit,
        on_delete=on_delete,
        on_toggle_status=on_toggle,
    )

    actions_with_sub = Actions(
        task=task_with_sub,
        badges_row=badges_row,
        page=page,
        on_edit=on_edit,
        on_delete=on_delete,
        on_toggle_status=on_toggle,
    )

    status_text = ft.Text("Click any button...", size=14, color=ft.Colors.BLUE_400)

    controls_list = [
        ft.Text("Actions - Demo UI", size=20, weight=ft.FontWeight.BOLD),
        ft.Divider(),
        ft.Text("Sin subtareas (3 botones):", weight=ft.FontWeight.BOLD),
    ]
    actions_row_no_sub = actions_no_sub.build()
    if actions_row_no_sub:
        controls_list.append(actions_row_no_sub)

    controls_list.extend([
        ft.Divider(),
        ft.Text("Con subtareas (2 botones):", weight=ft.FontWeight.BOLD),
    ])
    actions_row_with_sub = actions_with_sub.build()
    if actions_row_with_sub:
        controls_list.append(actions_row_with_sub)

    controls_list.extend([
        ft.Divider(),
        status_text,
    ])

    page.add(
        ft.Column(
            controls=controls_list,
            spacing=12,
        )
    )
    page.update()


if __name__ == "__main__":
    ft.run(main)
