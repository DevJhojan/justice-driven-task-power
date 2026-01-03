"""
Tests para el componente Description (task card)
Incluye comprobaciones unitarias y una demo visual similar al estilo de otros tests.
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
from app.ui.task.cards.description import create_description, Description


def test_create_description_basic(mock_page):
    task = Task(id="d_task_1", title="Tarea Desc", description="Descripción corta", user_id="user_1")

    text = create_description(task, page=mock_page, compact=False)

    assert isinstance(text, ft.Text)
    assert text.value == "Descripción corta"
    assert text.overflow == ft.TextOverflow.ELLIPSIS
    assert text.max_lines == 5


def test_create_description_compact_mode(mock_page):
    long_desc = "Línea1\nLínea2\nLínea3\nLínea4"
    task = Task(id="d_task_2", title="Tarea Desc Compacta", description=long_desc, user_id="user_1")

    text = create_description(task, page=mock_page, compact=True)

    assert isinstance(text, ft.Text)
    assert text.max_lines == 3


def test_description_build_and_refresh_and_update(mock_page):
    task = Task(id="d_task_3", title="Tarea Desc Clase", description="Original", user_id="user_1")
    d = Description(task, page=mock_page, compact=False)

    first = d.build()
    assert isinstance(first, ft.Text)
    assert first.value == "Original"

    # Build debe cachear
    second = d.build()
    assert first is second

    # Refresh invalida cache
    d.refresh()
    third = d.build()
    assert third is not first

    # Update description
    d.update_description("Nueva descripción")
    updated = d.build()
    assert updated.value == "Nueva descripción"


def test_build_returns_none_when_description_empty():
    task = Task(id="d_task_4", title="Tarea Sin Desc", description="", user_id="user_1")
    d = Description(task)

    assert d.build() is None


# ============================================================================
# DEMO UI - Ejecutar con: python test/ui/task/components/cards/test_description.py
# ============================================================================

def main(page: ft.Page):
    page.title = "Description - Demo Visual"
    page.window.width = 600
    page.window.height = 320
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 20

    task = Task(id="demo_desc", title="Tarea Demo Desc", description="Descripción inicial larga que será truncada en la vista compacta.", user_id="demo_user")

    desc = Description(task, page=page)
    desc_control = desc.build()

    def toggle_desc(e):
        if task.description:
            task.description = ""
            desc.refresh()
        else:
            task.description = "Texto restaurado de la descripción"
            desc.refresh()
        # Reconstruir y actualizar la UI
        new = desc.build()
        # Reemplazar control en página (simplificado: limpiar y re-add)
        page.c()
        if new:
            page.add(new)
        page.add(ft.Divider(height=10, color=ft.Colors.TRANSPARENT))
        page.add(ft.ElevatedButton("Toggle Description", on_click=toggle_desc))
        page.update()

    # inicial
    controls = [desc_control, ft.Divider(height=10, color=ft.Colors.TRANSPARENT), ft.ElevatedButton("Toggle Description", on_click=toggle_desc)]
    page.add(ft.Column(controls=[c for c in controls if c is not None]))
    page.update()


if __name__ == "__main__":
    ft.run(main)
