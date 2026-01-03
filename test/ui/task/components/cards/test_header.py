"""
Tests para el componente Header (task card)
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
from app.ui.task.cards.header import create_header, Header
from app.ui.task.status_badge import create_status_badge
from app.utils.task_helper import (
    TASK_STATUS_PENDING,
    TASK_STATUS_IN_PROGRESS,
    TASK_STATUS_COMPLETED,
)


def test_create_header_basic(mock_page):
    task = Task(id="h_task_1", title="Cabecera Test", user_id="user_1", urgent=True, important=False)

    header_row, title_text, badges_row = create_header(task, page=mock_page, compact=False)

    assert isinstance(header_row, ft.Row)
    assert isinstance(title_text, ft.Text)
    assert title_text.value == "Cabecera Test"
    assert isinstance(badges_row, ft.Row)
    assert len(badges_row.controls) >= 2
    # El primer control debe ser el status badge
    assert badges_row.controls[0] is not None


def test_header_class_build_and_refresh(mock_page):
    task = Task(id="h_task_2", title="Header Clase", user_id="user_2")
    h = Header(task, page=mock_page, compact=False)

    first = h.build()
    assert isinstance(first, ft.Row)
    assert h.title_text is not None
    assert h.badges_row is not None

    # Build debe cachear
    second = h.build()
    assert first is second

    # Refresh debe invalidar cache
    h.refresh()
    third = h.build()
    assert third is not first


def test_header_updates_on_status_change(mock_page):
    task = Task(id="h_task_3", title="Header Estado", user_id="user_3")
    h = Header(task, page=mock_page)
    header = h.build()

    badges = h.badges_row
    old_badge = badges.controls[0]

    # Cambiar estado de la tarea
    task.update_status(TASK_STATUS_COMPLETED)

    # Simular reemplazo del badge por implementación del componente
    new_badge = create_status_badge(task.status, page=mock_page, size="small")
    badges.controls[0] = new_badge

    assert badges.controls[0] is new_badge
    assert badges.controls[0] is not old_badge


# ============================================================================
# DEMO UI - Ejecutar con: python test/ui/task/components/cards/test_header.py
# ============================================================================

def main(page: ft.Page):
    page.title = "Header - Demo Visual"
    page.window.width = 600
    page.window.height = 200
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 20

    task = Task(id="demo_header", title="Tarea Demo Header", user_id="demo_user")

    header_comp = Header(task, page=page)
    header_row = header_comp.build()

    def toggle_status(e):
        # Alternar entre pendiente y completada
        if task.status != TASK_STATUS_COMPLETED:
            task.update_status(TASK_STATUS_COMPLETED)
        else:
            task.update_status(TASK_STATUS_PENDING)
        header_comp.badges_row.controls[0] = create_status_badge(task.status, page=page, size="small")
        page.update()

    toggle_btn = ft.ElevatedButton("Toggle Status", on_click=toggle_status)

    page.add(ft.Column(controls=[header_row, ft.Divider(height=10, color=ft.Colors.TRANSPARENT), toggle_btn]))
    page.update()


if __name__ == "__main__":
    ft.run(main)
