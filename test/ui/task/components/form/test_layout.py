from unittest.mock import Mock

import flet as ft

from app.ui.task.form.layout import build_form_layout


def _build_common_controls():
    title_field = ft.TextField(value="T")
    description_field = ft.TextField(value="D")
    status_dropdown = ft.Dropdown(value="pending")
    urgent_checkbox = ft.Checkbox(label="Urgente", value=False)
    important_checkbox = ft.Checkbox(label="Importante", value=True)
    due_date_text = ft.Text("📅 Sin fecha")
    open_date_picker = Mock(name="open_date_picker")
    clear_date = Mock(name="clear_date")
    tags_field = ft.TextField(value="a,b")
    notes_field = ft.TextField(value="n")
    subtasks_section = ft.Column([ft.Text("Subtareas section")])
    error_text = ft.Text("", visible=False)
    save_button = ft.FilledButton("Guardar")
    cancel_button = ft.OutlinedButton("Cancelar")

    return dict(
        title_field=title_field,
        description_field=description_field,
        status_dropdown=status_dropdown,
        urgent_checkbox=urgent_checkbox,
        important_checkbox=important_checkbox,
        due_date_text=due_date_text,
        open_date_picker=open_date_picker,
        clear_date=clear_date,
        tags_field=tags_field,
        notes_field=notes_field,
        subtasks_section=subtasks_section,
        error_text=error_text,
        save_button=save_button,
        cancel_button=cancel_button,
    )


def test_build_form_layout_create_mode_structure() -> None:
    c = _build_common_controls()
    col = build_form_layout(is_edit_mode=False, **c)

    assert isinstance(col, ft.Column)
    assert col.scroll == ft.ScrollMode.AUTO
    assert col.expand is True
    assert col.spacing == 16

    # Encabezado
    assert isinstance(col.controls[0], ft.Text)
    assert col.controls[0].value == "Nueva Tarea"

    assert isinstance(col.controls[1], ft.Divider)

    # Campos principales
    assert col.controls[2] is c["title_field"]
    assert col.controls[3] is c["description_field"]

    # Estado + prioridad
    status_priority = col.controls[4]
    assert isinstance(status_priority, ft.Column)
    assert status_priority.controls[0] is c["status_dropdown"]

    priority_col = status_priority.controls[1]
    assert isinstance(priority_col, ft.Column)
    assert isinstance(priority_col.controls[0], ft.Text)
    assert priority_col.controls[0].value == "Prioridad:"
    assert priority_col.controls[1] is c["urgent_checkbox"]
    assert priority_col.controls[2] is c["important_checkbox"]

    # Fecha de vencimiento
    due_date_section = col.controls[5]
    assert isinstance(due_date_section, ft.Column)
    assert isinstance(due_date_section.controls[0], ft.Text)
    assert due_date_section.controls[0].value == "Fecha de vencimiento:"
    assert due_date_section.controls[1] is c["due_date_text"]

    due_buttons_row = due_date_section.controls[2]
    assert isinstance(due_buttons_row, ft.Row)
    assert len(due_buttons_row.controls) == 2
    assert isinstance(due_buttons_row.controls[0], ft.FilledButton)
    assert isinstance(due_buttons_row.controls[1], ft.TextButton)
    assert due_buttons_row.controls[0].on_click is c["open_date_picker"]
    assert due_buttons_row.controls[1].on_click is c["clear_date"]

    # Tags y notas
    assert col.controls[6] is c["tags_field"]
    assert col.controls[7] is c["notes_field"]

    # Subtareas + error
    assert col.controls[8] is c["subtasks_section"]
    assert col.controls[9] is c["error_text"]

    # Divider + botones
    assert isinstance(col.controls[10], ft.Divider)
    buttons_row = col.controls[11]
    assert isinstance(buttons_row, ft.Row)
    assert buttons_row.controls[0] is c["save_button"]
    assert buttons_row.controls[1] is c["cancel_button"]


def test_build_form_layout_edit_mode_title() -> None:
    c = _build_common_controls()
    col = build_form_layout(is_edit_mode=True, **c)

    assert isinstance(col.controls[0], ft.Text)
    assert col.controls[0].value == "Editar Tarea"
