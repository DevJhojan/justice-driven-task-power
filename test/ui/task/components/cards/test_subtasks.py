"""
Tests para SubtasksSection (lista de subtareas) del Task Card
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
from unittest.mock import MagicMock
from app.models.task import Task
from app.models.subtask import Subtask
from app.ui.task.cards.subtasks import (
    create_subtasks_list,
    create_subtasks_title_row,
    _create_subtask_toggle_handler,
    SubtasksSection,
)
from app.utils.task_helper import calculate_completion_percentage, format_completion_percentage


def test_subtasks_list_basic(mock_page):
    task = Task(id="s_task_1", title="Tarea Sub", user_id="u")
    s1 = Subtask(id="sub1", task_id=task.id, title="A", completed=False)
    s2 = Subtask(id="sub2", task_id=task.id, title="B", completed=True)
    task.add_subtask(s1)
    task.add_subtask(s2)

    col = create_subtasks_list(task, page=mock_page, show_priority=True, show_actions=True, compact=False, expanded=True)
    assert isinstance(col, ft.Column)
    assert len(col.controls) == 2


def test_subtasks_title_row_and_toggle(mock_page):
    task = Task(id="s_task_2", title="Tarea Sub T", user_id="u")
    task.add_subtask(Subtask(id="a", task_id=task.id, title="A"))

    expanded_state = [True]
    row, btn = create_subtasks_title_row(task, page=mock_page, expanded_state=expanded_state)
    assert isinstance(row, ft.Row)
    # toggle programmatically
    btn.on_click(None)
    assert expanded_state[0] is False
    btn.on_click(None)
    assert expanded_state[0] is True


def test_subtask_toggle_handler_updates_progress_and_calls_callback(mock_page):
    task = Task(id="s_task_3", title="Tarea Toggle", user_id="u")
    s1 = Subtask(id="sub1", task_id=task.id, title="Sub 1", completed=False)
    s2 = Subtask(id="sub2", task_id=task.id, title="Sub 2", completed=False)
    task.add_subtask(s1)
    task.add_subtask(s2)

    pb = ft.ProgressBar(value=0.0, width=120)
    pt = ft.Text(value="0%")
    badges = ft.Row(controls=[ft.Text("badge")])

    on_toggle = MagicMock()
    handler = _create_subtask_toggle_handler(task, page=mock_page, progress_bar=pb, progress_text=pt, badges_row=badges, on_subtask_toggle=on_toggle)

    handler("sub1")
    assert task.subtasks[0].completed is True
    expected = calculate_completion_percentage(task)
    assert pb.value == expected
    assert pt.value == format_completion_percentage(task)
    on_toggle.assert_called_once_with(task.id, "sub1")


def test_subtasks_section_build_refresh_and_update(mock_page):
    task = Task(id="s_task_4", title="Tarea Sec", user_id="u")
    task.add_subtask(Subtask(id="x", task_id=task.id, title="X"))

    info = SubtasksSection(task, page=mock_page, show_priority=True, show_actions=True, compact=False, expanded=True)
    title_row, list_col = info.build()
    assert isinstance(title_row, ft.Row)
    assert isinstance(list_col, ft.Column)

    # Add a subtask and update_subtasks
    task.add_subtask(Subtask(id="y", task_id=task.id, title="Y"))
    info.update_subtasks()
    assert len(info._subtasks_list.controls) == 2


# ============================================================================
# DEMO UI - Ejecutar con: python test/ui/task/components/cards/test_subtasks.py
# ============================================================================

def main(page: ft.Page):
    page.title = "Subtasks - Demo"
    page.window.width = 700
    page.window.height = 400
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 20

    task = Task(id="demo_subs", title="Demo Subtasks", user_id="demo")
    task.add_subtask(Subtask(id="sa", task_id=task.id, title="A", completed=False))
    task.add_subtask(Subtask(id="sb", task_id=task.id, title="B", completed=False))

    subs = SubtasksSection(task, page=page, show_priority=True, show_actions=True, compact=False, expanded=True)
    title_row, list_col = subs.build()

    def toggle_first(e):
        handler = _create_subtask_toggle_handler(task, page=page, progress_bar=None, progress_text=None, badges_row=None)
        handler("sa")

    controls: list[ft.Control] = [c for c in (title_row, list_col, ft.ElevatedButton("Toggle A", on_click=toggle_first)) if c is not None]
    page.add(ft.Column(controls=controls))
    page.update()


if __name__ == "__main__":
    ft.run(main)
