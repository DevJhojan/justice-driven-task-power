"""
Tests para TaskView
"""
import sys
from pathlib import Path

# Agregar el directorio raíz al PYTHONPATH
root_dir = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(root_dir))

import flet as ft
import pytest
from app.ui.task.task_view import TaskView
from app.models.task import Task
from datetime import date


@pytest.fixture
def page():
    from unittest.mock import Mock
    test_page = Mock(spec=ft.Page)
    test_page.theme_mode = ft.ThemeMode.DARK
    test_page.overlay = []
    test_page.controls = []
    test_page.update = lambda: None
    return test_page


@pytest.fixture
def sample_task():
    return Task(id="t1", title="Tarea ejemplo", description="Desc", due_date=date.today())


def test_show_create_form_sets_listview_and_scroll(page: ft.Page):
    view = TaskView(page=page)
    container = view.build()

    # Estado inicial
    assert view.form_container is not None
    assert view.form_container.visible is False
    assert view.main_content is not None and view.main_content.visible is True
    assert view.fab is not None and view.fab.visible is True

    # Mostrar formulario de creación
    view._show_create_form(None)

    assert view.form_container.visible is True
    assert isinstance(view.form_container.content, ft.ListView)
    assert getattr(view.form_container.content, "expand", False) is True
    # El primer control dentro del ListView debe ser el container del formulario
    inner = view.form_container.content.controls[0]
    assert isinstance(inner, ft.Container)
    # El contenido del formulario debe ser una Column desplazable y expandible
    inner_content = inner.content
    assert isinstance(inner_content, ft.Column)
    assert getattr(inner_content, "scroll", None) == ft.ScrollMode.AUTO
    assert getattr(inner_content, "expand", False) is True

    # Verificar visibilidades
    assert view.main_content.visible is False
    assert view.fab.visible is False


def test_show_edit_form_populates_title_and_header(page: ft.Page, sample_task: Task):
    view = TaskView(page=page)
    view.build()

    view._show_edit_form(sample_task)

    assert view.form_container.visible is True
    lv = view.form_container.content
    assert isinstance(lv, ft.ListView)
    inner = lv.controls[0]
    assert isinstance(inner, ft.Container)
    inner_content = inner.content
    # Header del formulario: "Editar Tarea"
    assert isinstance(inner_content.controls[0], ft.Text)
    assert "Editar Tarea" in inner_content.controls[0].value


def test_hide_form_restores_visibility(page: ft.Page):
    view = TaskView(page=page)
    view.build()
    view._show_create_form(None)
    assert view.form_container.visible is True

    view._hide_form()
    assert view.form_container.visible is False
    assert view.main_content.visible is True
    assert view.fab.visible is True
