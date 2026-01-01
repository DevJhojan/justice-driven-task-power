from unittest.mock import Mock
from typing import Callable, cast

import flet as ft

from app.models.subtask import Subtask
from app.ui.task.components.form.subtask import (
    build_add_subtask_row,
    create_subtask,
    delete_subtask,
    edit_subtask,
    render_subtasks,
    toggle_subtask,
)


def test_create_subtask_trims_title_and_sets_fields() -> None:
    subtask = create_subtask(title="  Hola  ", task_id="task_1", completed=True)

    assert isinstance(subtask, Subtask)
    assert subtask.title == "Hola"
    assert subtask.task_id == "task_1"
    assert subtask.completed is True
    assert subtask.id.startswith("subtask_")


def test_create_subtask_uses_given_id() -> None:
    subtask = create_subtask(title="X", task_id="t", completed=False, subtask_id="my_id")
    assert subtask.id == "my_id"


def test_delete_subtask_removes_valid_index() -> None:
    subtasks = [
        Subtask(id="1", task_id="t", title="A", completed=False),
        Subtask(id="2", task_id="t", title="B", completed=False),
    ]

    delete_subtask(subtasks, 0)
    assert [s.id for s in subtasks] == ["2"]


def test_delete_subtask_ignores_invalid_index() -> None:
    subtasks = [Subtask(id="1", task_id="t", title="A", completed=False)]
    delete_subtask(subtasks, -1)
    delete_subtask(subtasks, 99)
    assert [s.id for s in subtasks] == ["1"]


def test_toggle_subtask_updates_completed_value() -> None:
    subtasks = [Subtask(id="1", task_id="t", title="A", completed=False)]
    toggle_subtask(subtasks, 0, True)
    assert subtasks[0].completed is True


def test_toggle_subtask_ignores_invalid_index() -> None:
    subtasks = [Subtask(id="1", task_id="t", title="A", completed=False)]
    toggle_subtask(subtasks, -1, True)
    toggle_subtask(subtasks, 99, True)
    assert subtasks[0].completed is False


def test_edit_subtask_updates_title() -> None:
    subtasks = [Subtask(id="1", task_id="t", title="A", completed=False)]
    edit_subtask(subtasks, 0, "  Nuevo  ")
    assert subtasks[0].title == "Nuevo"


def test_render_subtasks_empty_shows_hint_text() -> None:
    col = render_subtasks([], on_delete=lambda i: None, on_toggle=lambda i, v: None)

    assert isinstance(col, ft.Column)
    assert len(col.controls) == 1
    assert isinstance(col.controls[0], ft.Text)
    assert "No hay subtareas" in col.controls[0].value


def test_render_subtasks_renders_rows_and_binds_handlers() -> None:
    subtasks = [
        Subtask(id="1", task_id="t", title="A", completed=False),
        Subtask(id="2", task_id="t", title="B", completed=True),
    ]
    on_delete = Mock()
    on_toggle = Mock()
    on_edit = Mock()

    col = render_subtasks(subtasks, on_delete=on_delete, on_toggle=on_toggle, on_edit=on_edit)

    assert isinstance(col, ft.Column)
    assert len(col.controls) == 2

    row0 = col.controls[0]
    assert isinstance(row0, ft.Row)
    cb0 = row0.controls[0]
    title0 = row0.controls[1]
    del0 = row0.controls[2]

    assert isinstance(cb0, ft.Checkbox)
    assert cb0.value is False
    assert isinstance(title0, ft.TextField)
    assert title0.value == "A"
    assert isinstance(del0, ft.IconButton)

    # Dispara handlers
    toggle_event = Mock()
    toggle_event.control = Mock()
    toggle_event.control.value = True
    on_change = cb0.on_change
    assert callable(on_change)
    cast(Callable, on_change)(toggle_event)
    on_toggle.assert_called_with(0, True)

    # Editar título (submit)
    title0.value = "  Editada  "
    submit_event = Mock()
    submit_event.control = title0
    on_submit = title0.on_submit
    assert callable(on_submit)
    cast(Callable, on_submit)(submit_event)
    on_edit.assert_called_with(0, "Editada")

    # También debe reflejarse en el modelo
    assert subtasks[0].title == "Editada"
    assert title0.value == "Editada"

    on_click_delete = del0.on_click
    assert callable(on_click_delete)
    cast(Callable, on_click_delete)(Mock())
    on_delete.assert_called_with(0)


def test_build_add_subtask_row_calls_callbacks() -> None:
    on_save = Mock()
    on_cancel = Mock()

    row = build_add_subtask_row(on_save=on_save, on_cancel=on_cancel)

    assert isinstance(row, ft.Row)
    assert len(row.controls) == 3
    assert isinstance(row.controls[0], ft.TextField)
    assert isinstance(row.controls[1], ft.IconButton)
    assert isinstance(row.controls[2], ft.IconButton)

    input_field: ft.TextField = row.controls[0]
    save_btn: ft.IconButton = row.controls[1]
    cancel_btn: ft.IconButton = row.controls[2]

    # Guardar con texto vacío: no llama
    input_field.value = "   "
    on_click_save = save_btn.on_click
    assert callable(on_click_save)
    cast(Callable, on_click_save)(Mock())
    on_save.assert_not_called()

    # Guardar con texto: llama con el título trimmed
    input_field.value = "  Nueva  "
    cast(Callable, on_click_save)(Mock())
    on_save.assert_called_with("Nueva")

    # Cancelar siempre llama
    on_click_cancel = cancel_btn.on_click
    assert callable(on_click_cancel)
    cast(Callable, on_click_cancel)(Mock())
    on_cancel.assert_called_once()
