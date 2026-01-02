"""Tests para el TaskForm modular (components/form/task_form.py)."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from unittest.mock import Mock

import flet as ft
import pytest

from app.models.subtask import Subtask
from app.models.task import Task
from app.ui.task.components.form.task_form import TaskForm
from app.utils.task_helper import TASK_STATUS_COMPLETED, TASK_STATUS_PENDING


@pytest.fixture
def page():
    test_page = Mock(spec=ft.Page)
    test_page.theme_mode = ft.ThemeMode.DARK
    test_page.overlay = []
    test_page.controls = []
    test_page.update = Mock(name="page.update")

    # Necesario para get_responsive_padding(...)
    test_page.window = Mock()
    test_page.window.width = 800
    test_page.window.height = 600

    return test_page


@pytest.fixture
def sample_task():
    return Task(
        id="task_1",
        title="Tarea de ejemplo",
        description="Descripción de ejemplo",
        status=TASK_STATUS_PENDING,
        urgent=True,
        important=False,
        due_date=date.today() + timedelta(days=3),
        tags=["python", "testing"],
        notes="Notas de ejemplo",
        subtasks=[
            Subtask(id="sub_1", task_id="task_1", title="Subtarea 1", completed=False),
            Subtask(id="sub_2", task_id="task_1", title="Subtarea 2", completed=True),
        ],
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )


def test_form_initialization_create_mode(page: ft.Page):
    form = TaskForm(page=page)

    assert form.page == page
    assert form.task is None
    assert form.is_edit_mode is False
    assert form.selected_date is None
    assert form.subtasks == []


def test_form_initialization_edit_mode(page: ft.Page, sample_task: Task):
    form = TaskForm(page=page, task=sample_task)

    assert form.is_edit_mode is True
    assert form.selected_date == sample_task.due_date
    assert len(form.subtasks) == len(sample_task.subtasks)


def test_build_creates_container_and_controls(page: ft.Page):
    form = TaskForm(page=page)
    container = form.build()

    assert isinstance(container, ft.Container)
    assert container.expand is True

    # El contenido es el layout scrollable
    assert isinstance(container.content, ft.Column)
    assert container.content.scroll == ft.ScrollMode.AUTO
    assert container.content.expand is True

    # Controles base creados
    assert form.title_field is not None
    assert form.description_field is not None
    assert form.status_dropdown is not None
    assert form.urgent_checkbox is not None
    assert form.important_checkbox is not None
    assert form.due_date_picker is not None
    assert form.due_date_text is not None
    assert form.tags_field is not None
    assert form.notes_field is not None
    assert form.error_text is not None

    # DatePicker se agrega al overlay
    assert form.due_date_picker in page.overlay


def test_textfields_do_not_expand(page: ft.Page):
    form = TaskForm(page=page)
    form.build()

    assert form.title_field is not None
    assert form.description_field is not None

    assert getattr(form.title_field, "expand", None) is not True
    assert getattr(form.description_field, "expand", None) is not True


def test_validate_empty_title_shows_error(page: ft.Page):
    form = TaskForm(page=page)
    form.build()

    assert form.title_field is not None
    assert form.error_text is not None

    form.title_field.value = ""
    ok = form._validate_and_save()

    assert ok is False
    assert form.error_text.visible is True
    assert "título" in (form.error_text.value or "").lower()


def test_validate_too_many_tags_shows_error(page: ft.Page):
    form = TaskForm(page=page)
    form.build()

    assert form.title_field is not None
    assert form.tags_field is not None
    assert form.error_text is not None

    form.title_field.value = "Tarea válida"
    form.tags_field.value = ", ".join([f"tag{i}" for i in range(11)])

    ok = form._validate_and_save()

    assert ok is False
    assert form.error_text.visible is True
    assert "10" in (form.error_text.value or "")


def test_build_task_creates_new_task_and_parses_tags(page: ft.Page):
    form = TaskForm(page=page)
    form.build()

    assert form.title_field is not None
    assert form.description_field is not None
    assert form.status_dropdown is not None
    assert form.urgent_checkbox is not None
    assert form.important_checkbox is not None
    assert form.tags_field is not None
    assert form.notes_field is not None

    form.title_field.value = "Nueva Tarea"
    form.description_field.value = "Descripción"
    form.status_dropdown.value = TASK_STATUS_PENDING
    form.urgent_checkbox.value = True
    form.important_checkbox.value = False
    form.tags_field.value = " python, , testing ,"
    form.notes_field.value = "Notas"

    task = form._build_task()

    assert isinstance(task, Task)
    assert task.title == "Nueva Tarea"
    assert task.tags == ["python", "testing"]


def test_build_task_updates_existing_task(page: ft.Page, sample_task: Task):
    original_created_at = sample_task.created_at

    form = TaskForm(page=page, task=sample_task)
    form.build()

    assert form.title_field is not None
    assert form.description_field is not None
    assert form.status_dropdown is not None
    assert form.urgent_checkbox is not None
    assert form.important_checkbox is not None

    form.title_field.value = "Título actualizado"
    form.description_field.value = "Descripción actualizada"
    form.status_dropdown.value = TASK_STATUS_COMPLETED
    form.urgent_checkbox.value = False
    form.important_checkbox.value = True

    task = form._build_task()

    assert task is sample_task
    assert task.title == "Título actualizado"
    assert task.status == TASK_STATUS_COMPLETED
    assert task.created_at == original_created_at
    assert task.updated_at >= original_created_at
