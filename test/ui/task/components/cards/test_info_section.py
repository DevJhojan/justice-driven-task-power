"""
Tests para InfoSection (due date + progress) del Task Card
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
from datetime import date, timedelta

from app.models.task import Task
from app.models.subtask import Subtask
from app.ui.task.cards.info_section import (
    create_due_date_row,
    create_progress_controls,
    create_info_section,
    InfoSection,
)
from app.utils.task_helper import calculate_completion_percentage, format_completion_percentage
from app.utils.helpers.formats import format_date


def test_create_due_date_row_basic(mock_page):
    due = date.today() + timedelta(days=2)
    task = Task(id="i_task_1", title="Tarea Fecha", due_date=due, user_id="user_1")

    row = create_due_date_row(task, page=mock_page)
    assert isinstance(row, ft.Row)
    assert isinstance(row.controls[0], ft.Icon)
    assert isinstance(row.controls[1], ft.Text)
    assert row.controls[1].value == format_date(due)


def test_create_due_date_row_none_when_missing():
    task = Task(id="i_task_2", title="Sin fecha", user_id="user_1")
    assert create_due_date_row(task) is None


def test_create_progress_controls_basic(mock_page):
    task = Task(id="i_task_3", title="Tarea Progreso", user_id="user_1")
    s1 = Subtask(id="s1", task_id=task.id, title="s1", completed=True)
    s2 = Subtask(id="s2", task_id=task.id, title="s2", completed=False)
    task.add_subtask(s1)
    task.add_subtask(s2)

    progress_row, progress_bar, progress_text = create_progress_controls(task, page=mock_page, compact=False)
    assert isinstance(progress_row, ft.Row)
    assert isinstance(progress_bar, ft.ProgressBar)
    assert isinstance(progress_text, ft.Text)

    expected = calculate_completion_percentage(task)
    assert progress_bar.value == expected
    assert progress_text.value == format_completion_percentage(task)


def test_create_info_section_composed(mock_page):
    due = date.today() + timedelta(days=1)
    task = Task(id="i_task_4", title="Tarea Info", due_date=due, user_id="user_1")
    s1 = Subtask(id="s1", task_id=task.id, title="s1", completed=False)
    task.add_subtask(s1)

    info_row, pb, pt = create_info_section(task, page=mock_page, compact=False, show_progress=True)
    assert isinstance(info_row, ft.Row)
    # Debería contener al menos due_date row y progress row
    assert len(info_row.controls) >= 2
    assert isinstance(pb, ft.ProgressBar)
    assert isinstance(pt, ft.Text)


def test_info_section_build_refresh_and_update_progress(mock_page):
    task = Task(id="i_task_5", title="Tarea Actualiza", user_id="user_1")
    s1 = Subtask(id="s1", task_id=task.id, title="s1", completed=False)
    s2 = Subtask(id="s2", task_id=task.id, title="s2", completed=False)
    task.add_subtask(s1)
    task.add_subtask(s2)

    info = InfoSection(task, page=mock_page, compact=False, show_progress=True)
    row = info.build()
    assert isinstance(row, ft.Row)
    assert info.progress_bar is not None
    assert info.progress_text is not None

    # Completar una subtarea y actualizar progreso
    task.subtasks[0].toggle_completed()
    info.update_progress()

    expected = calculate_completion_percentage(task)
    assert info.progress_bar.value == expected
    assert info.progress_text.value == format_completion_percentage(task)

    # Refresh invalida cache
    info.refresh()
    assert info.build() is not None


def test_info_section_update_due_date_behaviour(mock_page):
    task = Task(id="i_task_6", title="Tarea Fecha Dinamica", user_id="user_1")
    info = InfoSection(task, page=mock_page, compact=False, show_progress=False)

    # Inicialmente no hay due_date
    assert info.build() is None

    # Añadir due_date y actualizar
    task.due_date = date.today() + timedelta(days=3)
    # Build para inicializar estructura
    info.refresh()
    row = info.build()
    assert isinstance(row, ft.Row)
    assert info.due_date_row is not None
    assert info.due_date_row.controls[1].value == format_date(task.due_date)

    # Eliminar due_date y update_due_date debe quitarlo
    task.due_date = None
    info.update_due_date()
    # Ahora la fila no debe contener due_date
    assert info.due_date_row is None


# ============================================================================
# DEMO UI - Ejecutar con: python test/ui/task/components/cards/test_info_section.py
# ============================================================================

def main(page: ft.Page):
    page.title = "Info Section - Demo"
    page.window.width = 700
    page.window.height = 240
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 20

    task = Task(id="demo_info", title="Tarea Demo Info", user_id="demo")
    task.add_subtask(Subtask(id="a", task_id=task.id, title="A", completed=False))
    task.add_subtask(Subtask(id="b", task_id=task.id, title="B", completed=False))

    info = InfoSection(task, page=page, compact=False, show_progress=True)
    row = info.build()

    def toggle_first(e):
        task.subtasks[0].toggle_completed()
        info.update_progress()
        page.update()

    def add_due(e):
        if task.due_date is None:
            task.due_date = date.today() + timedelta(days=2)
        else:
            task.due_date = None
        info.update_due_date()
        page.update()

    page.add(
        ft.Column(
            controls=[
                row if row is not None else ft.Text("No info"),
                ft.Row(controls=[ft.ElevatedButton("Toggle Sub A", on_click=toggle_first), ft.ElevatedButton("Toggle Due", on_click=add_due)]),
            ],
            spacing=12,
        )
    )
    page.update()


if __name__ == "__main__":
    ft.run(main)
