import pytest
import flet as ft
from datetime import date, datetime
from unittest.mock import Mock

from app.ui.task.form.date_controls import build_due_date_controls
from app.utils.helpers.formats import format_date


@pytest.fixture
def page():
    test_page = Mock(spec=ft.Page)
    test_page.overlay = []
    return test_page


def test_build_due_date_controls_initial_none(page):
    cb = Mock()
    date_picker, date_text, open_date_picker, clear_date = build_due_date_controls(
        page=page,
        selected_date=None,
        on_selected_date_change=cb,
    )

    assert isinstance(date_picker, ft.DatePicker)
    assert isinstance(date_text, ft.Text)
    assert date_text.value == "📅 Sin fecha"
    assert date_picker in page.overlay


def test_build_due_date_controls_initial_date(page):
    cb = Mock()
    initial = date(2024, 12, 25)
    _, date_text, _, _ = build_due_date_controls(
        page=page,
        selected_date=initial,
        on_selected_date_change=cb,
    )

    assert date_text.value == f"📅 {format_date(initial)}"


def test_clear_date_resets_value_and_calls_callback(page):
    cb = Mock()
    initial = date(2024, 1, 15)
    _, date_text, _, clear_date = build_due_date_controls(
        page=page,
        selected_date=initial,
        on_selected_date_change=cb,
    )

    clear_date(None)
    cb.assert_called_with(None)
    assert date_text.value == "📅 Sin fecha"


def test_open_date_picker_sets_open_true(page):
    cb = Mock()
    date_picker, _, open_date_picker, _ = build_due_date_controls(
        page=page,
        selected_date=None,
        on_selected_date_change=cb,
    )

    assert getattr(date_picker, "open", False) in (False, None)
    open_date_picker(None)
    assert date_picker.open is True


def test_date_change_updates_text_and_callback_with_datetime(page):
    cb = Mock()
    date_picker, date_text, _, _ = build_due_date_controls(
        page=page,
        selected_date=None,
        on_selected_date_change=cb,
    )

    new_dt = datetime(2024, 2, 1, 10, 0, 0)
    event = Mock()
    event.control = Mock()
    event.control.value = new_dt

    date_picker.on_change(event)

    cb.assert_called_with(new_dt.date())
    assert date_text.value == f"📅 {format_date(new_dt.date())}"
