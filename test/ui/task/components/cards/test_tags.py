"""
Tests para Tags (chips de tags) del Task Card
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
from app.models.task import Task
from app.ui.task.cards.tags import create_tag_chip, create_tags_row, Tags


def test_create_tag_chip_basic(mock_page):
    chip = create_tag_chip("mi-tag", page=mock_page)
    assert isinstance(chip, ft.Container)
    assert hasattr(chip, "content") and isinstance(chip.content, ft.Text)
    assert chip.content.value == "mi-tag"


def test_create_tags_row_none_when_empty():
    task = Task(id="t_none", title="Sin tags", user_id="u")
    assert create_tags_row(task) is None


def test_create_tags_row_with_tags(mock_page):
    task = Task(id="t_tags", title="Con tags", user_id="u")
    task.tags = ["alpha", "beta", "gamma"]
    row = create_tags_row(task, page=mock_page, max_tags=2)
    assert isinstance(row, ft.Row)
    assert len(row.controls) == 2
    for container in row.controls:
        assert isinstance(container, ft.Container)
        assert isinstance(container.content, ft.Text)


def test_tags_class_build_refresh_and_update(mock_page):
    task = Task(id="t_class", title="Tags class", user_id="u")
    task.tags = ["one", "two"]

    tags_comp = Tags(task, page=mock_page, max_tags=5)
    row = tags_comp.build()
    assert isinstance(row, ft.Row)
    assert len(row.controls) == 2
    assert row.controls[0].content.value == "one"

    # Add a tag and refresh (add_tag already refreshes but for clarity)
    tags_comp.add_tag("three")
    tags_comp.refresh()
    row2 = tags_comp.build()
    assert any(c.content.value == "three" for c in (row2.controls or []))

    # Remove a tag and refresh
    tags_comp.remove_tag("one")
    tags_comp.refresh()
    row3 = tags_comp.build()
    assert all(c.content.value != "one" for c in (row3.controls or []))

    # Replace tags list
    tags_comp.update_tags(["x"])
    row4 = tags_comp.build()
    assert row4 is not None and len(row4.controls) == 1
    assert row4.controls[0].content.value == "x"

    # Clear tags -> build should return None after refresh
    tags_comp.update_tags([])
    assert tags_comp.build() is None


# ============================================================================
# DEMO UI - Ejecutar con: python test/ui/task/components/cards/test_tags.py
# ============================================================================

def main(page: ft.Page):
    page.title = "Tags - Demo"
    page.window.width = 500
    page.window.height = 200
    page.padding = 20
    page.theme_mode = ft.ThemeMode.DARK

    task = Task(id="demo_tags", title="Demo Tags", user_id="demo")
    task.tags = ["alpha", "beta"]

    tags_comp = Tags(task, page=page, max_tags=5)
    row = tags_comp.build()

    def add_tag(e):
        task.tags.append(f"t{len(task.tags)+1}")
        tags_comp.refresh()
        page.controls.clear()
        page.add(ft.Column(controls=[tags_comp.build()] + controls_row()))
        page.update()

    def remove_tag(e):
        if task.tags:
            task.tags.pop(0)
            tags_comp.refresh()
            page.controls.clear()
            page.add(ft.Column(controls=[tags_comp.build()] + controls_row()))
            page.update()

    def controls_row():
        return [
            ft.Row(controls=[ft.ElevatedButton("Add Tag", on_click=add_tag), ft.ElevatedButton("Remove Tag", on_click=remove_tag)], spacing=8)
        ]

    page.add(
        ft.Column(
            controls=[
                row if row is not None else ft.Text("No tags"),
                *controls_row(),
            ],
            spacing=12,
        )
    )
    page.update()


if __name__ == "__main__":
    ft.run(main)
