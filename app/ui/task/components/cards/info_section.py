"""
Info Section for Task Card
Provides helpers to build due date and progress controls and an InfoSection class
that caches and updates those controls. Implemented following the layout and styles
used in `task_card.py`.
"""

import flet as ft
from typing import Optional, Tuple
from app.models.task import Task
from app.utils.task_helper import (
    calculate_completion_percentage,
    format_completion_percentage,
    is_task_overdue,
    is_task_due_today,
    is_task_due_soon,
)
from app.utils.helpers.formats import format_date
from app.utils.helpers.responsives import get_responsive_size


def create_due_date_row(task: Task, page: Optional[ft.Page] = None, description_size: Optional[int] = None) -> Optional[ft.Row]:
    """Create a row showing due date info, or None if no due_date."""
    if not getattr(task, "due_date", None):
        return None

    # Allow caller to pass a specific text size, otherwise compute responsive
    if description_size is None:
        description_size = get_responsive_size(page=page, mobile=13, tablet=14, desktop=15)

    due_date_color = (
        ft.Colors.RED_400 if is_task_overdue(task) else
        (ft.Colors.ORANGE_400 if is_task_due_today(task) else
         (ft.Colors.YELLOW_400 if is_task_due_soon(task) else ft.Colors.WHITE_70))
    )

    due_date_icon = ft.Icons.CALENDAR_TODAY
    if is_task_overdue(task):
        due_date_icon = ft.Icons.WARNING
    elif is_task_due_today(task):
        due_date_icon = ft.Icons.TODAY

    due_date_row = ft.Row(
        controls=[
            ft.Icon(due_date_icon, size=16, color=due_date_color),
            ft.Text(
                format_date(task.due_date),
                size=description_size,
                color=due_date_color,
            ),
        ],
        spacing=6,
        tight=True,
    )
    return due_date_row


def create_progress_controls(task: Task, page: Optional[ft.Page] = None, compact: bool = False) -> Tuple[ft.Row, ft.ProgressBar, ft.Text]:
    """Create progress row, progress bar and progress text controls."""
    description_size = get_responsive_size(page=page, mobile=13, tablet=14, desktop=15) if not compact else get_responsive_size(page=page, mobile=12, tablet=13, desktop=14)

    completion_percentage = calculate_completion_percentage(task)

    progress_text = ft.Text(
        format_completion_percentage(task),
        size=description_size,
        color=ft.Colors.WHITE_70,
    )

    progress_bar = ft.ProgressBar(
        value=completion_percentage,
        width=100 if compact else 150,
        height=6,
        color=ft.Colors.BLUE_400,
        bgcolor=ft.Colors.GREY_800,
    )

    progress_row = ft.Row(
        controls=[
            ft.Icon(ft.Icons.CHECK_CIRCLE_OUTLINE, size=16, color=ft.Colors.BLUE_400),
            progress_text,
            progress_bar,
        ],
        spacing=8,
        alignment=ft.MainAxisAlignment.START,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )

    return progress_row, progress_bar, progress_text


def create_info_section(task: Task, page: Optional[ft.Page] = None, compact: bool = False, show_progress: bool = True) -> Tuple[Optional[ft.Row], Optional[ft.ProgressBar], Optional[ft.Text]]:
    """Create a composed info row (due date + progress) and return it with references to progress controls.

    Returns:
        (info_row_or_None, progress_bar_or_None, progress_text_or_None)
    """
    info_controls = []

    due_row = create_due_date_row(task, page=page, description_size=None)
    if due_row:
        info_controls.append(due_row)

    progress_bar = None
    progress_text = None
    if show_progress:
        progress_row, progress_bar, progress_text = create_progress_controls(task, page=page, compact=compact)
        info_controls.append(progress_row)

    if not info_controls:
        return None, None, None

    info_row = ft.Row(
        controls=info_controls,
        spacing=15,
        wrap=True,
    )

    return info_row, progress_bar, progress_text


class InfoSection:
    """Convenience class that builds and caches the info section controls."""

    def __init__(self, task: Task, page: Optional[ft.Page] = None, compact: bool = False, show_progress: bool = True):
        self.task = task
        self.page = page
        self.compact = compact
        self.show_progress = show_progress

        self._info_row: Optional[ft.Row] = None
        self.progress_bar: Optional[ft.ProgressBar] = None
        self.progress_text: Optional[ft.Text] = None
        self.due_date_row: Optional[ft.Row] = None

    def build(self) -> Optional[ft.Row]:
        """Build (or return cached) the info row."""
        if self._info_row is None:
            info_row, progress_bar, progress_text = create_info_section(
                self.task, page=self.page, compact=self.compact, show_progress=self.show_progress
            )
            self._info_row = info_row
            self.progress_bar = progress_bar
            self.progress_text = progress_text
            # find due_date row if present
            if info_row:
                # The due date row is the first control if exists and it's a Row with an Icon first child
                for ctrl in info_row.controls:
                    if isinstance(ctrl, ft.Row) and ctrl.controls and isinstance(ctrl.controls[0], ft.Icon):
                        self.due_date_row = ctrl
                        break
        return self._info_row

    def refresh(self):
        """Force rebuild on next call to build()."""
        self._info_row = None
        self.progress_bar = None
        self.progress_text = None
        self.due_date_row = None

    def update_progress(self):
        """Recalculate and update the progress controls values (does not call page.update)."""
        if self.progress_bar is not None and self.progress_text is not None:
            new_percentage = calculate_completion_percentage(self.task)
            self.progress_bar.value = new_percentage
            self.progress_text.value = format_completion_percentage(self.task)

    def update_due_date(self):
        """Recreate due_date row and replace it inside the info row if present."""
        if self._info_row is None:
            return

        new_due = create_due_date_row(self.task, page=self.page)
        if self.due_date_row is None and new_due is not None:
            # prepend
            self._info_row.controls.insert(0, new_due)
            self.due_date_row = new_due
        elif self.due_date_row is not None and new_due is None:
            # remove existing
            try:
                self._info_row.controls.remove(self.due_date_row)
            except ValueError:
                pass
            self.due_date_row = None
        elif self.due_date_row is not None and new_due is not None:
            # replace
            for i, ctrl in enumerate(self._info_row.controls):
                if ctrl is self.due_date_row:
                    self._info_row.controls[i] = new_due
                    self.due_date_row = new_due
                    break

