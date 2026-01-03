"""
Tags component for Task Card
Provides helpers to create tag chips/row and a Tags class to cache/update
controls following patterns used in `task_card.py`.
"""

import flet as ft
from typing import Optional, List
from app.models.task import Task
from app.utils.helpers.responsives import get_responsive_size


def create_tag_chip(tag: str, page: Optional[ft.Page] = None) -> ft.Container:
    """Create a styled tag chip for a given tag string."""
    text_size = get_responsive_size(page=page, mobile=10, tablet=11, desktop=12)

    return ft.Container(
        content=ft.Text(tag, size=text_size, color=ft.Colors.BLUE_300),
        padding=ft.Padding.symmetric(horizontal=6, vertical=2),
        border_radius=4,
        bgcolor=ft.Colors.BLUE_900,
    )


def create_tags_row(task: Task, page: Optional[ft.Page] = None, max_tags: int = 5) -> Optional[ft.Row]:
    """Create a Row with up to `max_tags` tag chips for the provided task.

    Returns None if there are no tags.
    """
    tags = [t for t in (getattr(task, "tags", []) or []) if t is not None]
    if not tags:
        return None

    chips: list[ft.Control] = [create_tag_chip(str(tag), page=page) for tag in tags[:max_tags]]

    tags_row = ft.Row(controls=chips, spacing=6, wrap=True)
    return tags_row


class Tags:
    """Convenience class to build and cache tags row for a task."""

    def __init__(self, task: Task, page: Optional[ft.Page] = None, max_tags: int = 5):
        self.task = task
        self.page = page
        self.max_tags = max_tags
        self._tags_row: Optional[ft.Row] = None

    def build(self) -> Optional[ft.Row]:
        """Builds (or returns cached) tags row."""
        if self._tags_row is None:
            self._tags_row = create_tags_row(self.task, page=self.page, max_tags=self.max_tags)
        return self._tags_row

    def refresh(self):
        """Invalidate cached row so next build rebuilds it."""
        self._tags_row = None

    def update_tags(self, new_tags: List[str]):
        """Update the task tags and refresh the cached controls."""
        self.task.tags = new_tags
        self.refresh()

    def add_tag(self, tag: str):
        """Add a tag if not present and refresh."""
        if tag not in self.task.tags:
            self.task.tags.append(tag)
            self.refresh()

    def remove_tag(self, tag: str):
        """Remove a tag if present and refresh."""
        if tag in self.task.tags:
            self.task.tags.remove(tag)
            self.refresh()
