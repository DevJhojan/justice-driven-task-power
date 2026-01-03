"""Tests para factories de controles del formulario de tareas."""

import flet as ft

from app.models.task import Task
from app.ui.task.form.controls import (
    create_description_field,
    create_error_text,
    create_notes_field,
    create_priority_checkboxes,
    create_status_dropdown,
    create_tags_field,
    create_title_field,
)
from app.utils.task_helper import (
    TASK_STATUS_CANCELLED,
    TASK_STATUS_COMPLETED,
    TASK_STATUS_IN_PROGRESS,
    TASK_STATUS_PENDING,
)


def test_create_title_field_without_task():
    field = create_title_field(None)
    assert isinstance(field, ft.TextField)
    assert field.label == "Título *"
    assert field.value == ""
    assert field.max_length == 100
    assert field.border_color == ft.Colors.RED_700
    assert field.focused_border_color == ft.Colors.RED_400
    assert field.cursor_color == ft.Colors.RED_400
    assert getattr(field, "expand", None) is not True


def test_create_title_field_with_task():
    task = Task(id="t1", title="Mi tarea", user_id="u")
    field = create_title_field(task)
    assert field.value == "Mi tarea"


def test_create_description_field_properties():
    task = Task(id="t1", title="T", description="Desc", user_id="u")
    field = create_description_field(task)

    assert isinstance(field, ft.TextField)
    assert field.label == "Descripción"
    assert field.multiline is True
    assert field.min_lines == 3
    assert field.max_lines == 5
    assert field.max_length == 500
    assert field.value == "Desc"
    assert field.border_color == ft.Colors.RED_700
    assert field.focused_border_color == ft.Colors.RED_400
    assert field.cursor_color == ft.Colors.RED_400
    assert getattr(field, "expand", None) is not True


def test_create_status_dropdown_defaults_and_options():
    dropdown = create_status_dropdown(None)

    assert isinstance(dropdown, ft.Dropdown)
    assert dropdown.label == "Estado"
    assert dropdown.value == TASK_STATUS_PENDING
    assert getattr(dropdown, "expand", None) is not True

    keys = {getattr(opt, "key", None) for opt in dropdown.options}
    assert keys == {
        TASK_STATUS_PENDING,
        TASK_STATUS_IN_PROGRESS,
        TASK_STATUS_COMPLETED,
        TASK_STATUS_CANCELLED,
    }


def test_create_priority_checkboxes_values_and_style():
    task = Task(id="t1", title="T", user_id="u", urgent=True, important=False)
    urgent, important = create_priority_checkboxes(task)

    assert isinstance(urgent, ft.Checkbox)
    assert isinstance(important, ft.Checkbox)

    assert urgent.label == "Urgente"
    assert urgent.value is True
    assert urgent.fill_color == ft.Colors.RED_700

    assert important.label == "Importante"
    assert important.value is False
    assert important.fill_color == ft.Colors.RED_700


def test_create_tags_field_joins_tags():
    task = Task(id="t1", title="T", user_id="u", tags=["python", "api"])
    field = create_tags_field(task)

    assert isinstance(field, ft.TextField)
    assert field.label == "Etiquetas"
    assert field.value == "python, api"
    assert field.border_color == ft.Colors.RED_700
    assert field.focused_border_color == ft.Colors.RED_400
    assert field.cursor_color == ft.Colors.RED_400


def test_create_notes_field_properties():
    task = Task(id="t1", title="T", user_id="u", notes="Nota")
    field = create_notes_field(task)

    assert isinstance(field, ft.TextField)
    assert field.label == "Notas adicionales"
    assert field.multiline is True
    assert field.min_lines == 2
    assert field.max_lines == 4
    assert field.max_length == 300
    assert field.value == "Nota"
    assert field.border_color == ft.Colors.RED_700
    assert field.focused_border_color == ft.Colors.RED_400
    assert field.cursor_color == ft.Colors.RED_400


def test_create_error_text_defaults():
    txt = create_error_text()
    assert isinstance(txt, ft.Text)
    assert txt.value == ""
    assert txt.color == ft.Colors.RED_400
    assert txt.size == 12
    assert txt.visible is False
