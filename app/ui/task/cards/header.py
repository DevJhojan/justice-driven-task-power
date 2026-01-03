"""
Header component for Task Card
Provides helper functions and a Header class to build the title + badges row
based on the implementation in `task_card.py`.
"""

import flet as ft
from typing import Optional, Tuple
from app.models.task import Task
from app.ui.task.components.status_badge import create_status_badge
from app.ui.task.components.priority_badge import create_priority_badge
from app.utils.helpers.responsives import get_responsive_size


def create_header(
    task: Task,
    page: Optional[ft.Page] = None,
    compact: bool = False,
) -> Tuple[ft.Row, ft.Text, ft.Row]:
    """
    Create a header row for a task card containing the title and badges.

    Returns a tuple: (header_row, title_text, badges_row). The badges_row has the
    status badge as its first control so callers can replace it when the status
    changes.
    """

    # Calculate responsive sizes
    if compact:
        title_size = get_responsive_size(page=page, mobile=16, tablet=18, desktop=20)
    else:
        title_size = get_responsive_size(page=page, mobile=18, tablet=20, desktop=22)

    # Title
    title_text = ft.Text(
        task.title,
        size=title_size,
        weight=ft.FontWeight.BOLD,
        color=ft.Colors.WHITE,
        expand=True,
    )

    # Badges
    status_badge = create_status_badge(task.status, page=page, size="small")
    priority_badge = create_priority_badge(
        urgent=task.urgent,
        important=task.important,
        page=page,
        size="small",
        show_quadrant=False,
    )

    badges_row = ft.Row(
        controls=[status_badge, priority_badge],
        spacing=6,
        tight=True,
    )

    header_row = ft.Row(
        controls=[title_text, badges_row],
        spacing=10,
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )

    return header_row, title_text, badges_row


class Header:
    """Convenience class wrapping header creation and caching."""

    def __init__(self, task: Task, page: Optional[ft.Page] = None, compact: bool = False):
        self.task = task
        self.page = page
        self.compact = compact
        self._header: Optional[ft.Row] = None
        self.title_text: Optional[ft.Text] = None
        self.badges_row: Optional[ft.Row] = None

    def build(self) -> ft.Row:
        """Builds (or returns cached) header row."""
        if self._header is None:
            header_row, title_text, badges_row = create_header(self.task, page=self.page, compact=self.compact)
            self._header = header_row
            self.title_text = title_text
            self.badges_row = badges_row
        return self._header

    def refresh(self):
        """Force rebuild on next call to build()."""
        self._header = None
        self.title_text = None
        self.badges_row = None
