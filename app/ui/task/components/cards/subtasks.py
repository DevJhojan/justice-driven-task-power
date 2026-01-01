"""
Subtasks section for Task Card
Provides helpers to build subtasks list, expand/collapse title row and a SubtasksSection
class that caches and updates those controls.
"""

import flet as ft
from typing import Optional, Callable, Tuple, List
from app.models.task import Task
from app.ui.task.components.subtask_item import create_subtask_item
from app.ui.task.components.status_badge import create_status_badge
from app.utils.task_helper import (
    calculate_completion_percentage,
    format_completion_percentage,
    TASK_STATUS_PENDING,
    TASK_STATUS_IN_PROGRESS,
    TASK_STATUS_COMPLETED,
)
from app.utils.helpers.responsives import get_responsive_size


def _create_subtask_toggle_handler(
    task: Task,
    page: Optional[ft.Page] = None,
    progress_bar: Optional[ft.ProgressBar] = None,
    progress_text: Optional[ft.Text] = None,
    badges_row: Optional[ft.Row] = None,
    on_subtask_toggle: Optional[Callable[[str, str], None]] = None,
) -> Callable[[str], None]:
    """
    Return a handler that toggles a subtask and updates progress/status.
    The returned handler receives the subtask id (str).
    """
    def handler(received_subtask_id: str):
        subtask = next((st for st in task.subtasks if st.id == received_subtask_id), None)
        if not subtask:
            return

        subtask.toggle_completed()

        new_percentage = calculate_completion_percentage(task)

        # Update task status accordingly
        if new_percentage >= 1.0:
            if task.status != TASK_STATUS_COMPLETED:
                task.update_status(TASK_STATUS_COMPLETED)
                if badges_row:
                    badges_row.controls[0] = create_status_badge(task.status, page=page, size="small")
        elif new_percentage == 0.0:
            if task.status != TASK_STATUS_PENDING:
                task.update_status(TASK_STATUS_PENDING)
                if badges_row:
                    badges_row.controls[0] = create_status_badge(task.status, page=page, size="small")
        else:
            if task.status in (TASK_STATUS_PENDING, TASK_STATUS_COMPLETED):
                task.update_status(TASK_STATUS_IN_PROGRESS)
                if badges_row:
                    badges_row.controls[0] = create_status_badge(task.status, page=page, size="small")

        # Update progress controls if provided
        if progress_bar is not None and progress_text is not None:
            progress_bar.value = new_percentage
            progress_text.value = format_completion_percentage(task)

        if page:
            page.update()

        if on_subtask_toggle:
            on_subtask_toggle(task.id, received_subtask_id)

    return handler


def create_subtasks_list(
    task: Task,
    page: Optional[ft.Page] = None,
    on_subtask_toggle: Optional[Callable[[str, str], None]] = None,
    on_subtask_edit: Optional[Callable[[str, str], None]] = None,
    on_subtask_delete: Optional[Callable[[str, str], None]] = None,
    show_priority: bool = True,
    show_actions: bool = True,
    compact: bool = False,
    expanded: bool = True,
    progress_bar: Optional[ft.ProgressBar] = None,
    progress_text: Optional[ft.Text] = None,
    badges_row: Optional[ft.Row] = None,
) -> ft.Column:
    """
    Create a Column with Subtask items for task.subtasks.

    The column is visible depending on `expanded`.
    """
    # Create handler factory to update progress & status
    handler_factory = _create_subtask_toggle_handler(
        task=task,
        page=page,
        progress_bar=progress_bar,
        progress_text=progress_text,
        badges_row=badges_row,
        on_subtask_toggle=on_subtask_toggle,
    )

    # helper factories with explicit types to satisfy type checkers
    def _make_on_edit(task_id: str) -> Optional[Callable[[str], None]]:
        if on_subtask_edit:
            def _fn(subtask_id: str) -> None:  # type: ignore[override]
                on_subtask_edit(task_id, subtask_id)
            return _fn
        return None

    def _make_on_delete(task_id: str) -> Optional[Callable[[str], None]]:
        if on_subtask_delete:
            def _fn(subtask_id: str) -> None:
                on_subtask_delete(task_id, subtask_id)
            return _fn
        return None

    on_edit_fn = _make_on_edit(task.id)
    on_delete_fn = _make_on_delete(task.id)

    controls: list[ft.Control] = [
        create_subtask_item(
            subtask=subtask,
            page=page,
            on_toggle_completed=handler_factory,
            on_edit=(on_edit_fn),
            on_delete=(on_delete_fn),
            show_priority=show_priority,
            show_actions=show_actions,
            compact=compact,
        )
        for subtask in task.subtasks
    ]

    subtasks_list = ft.Column(
        controls=controls,
        spacing=6,
        visible=expanded,
    )
    return subtasks_list


def create_subtasks_title_row(task: Task, page: Optional[ft.Page] = None, expanded_state: Optional[List[bool]] = None) -> Tuple[ft.Row, ft.IconButton]:
    """
    Create a title row with an expand/collapse IconButton and the title text.
    expanded_state must be a list with one bool element to allow mutation from closures.
    Returns (title_row, expand_button).
    """
    if expanded_state is None:
        expanded_state = [True]

    description_size = get_responsive_size(page=page, mobile=13, tablet=14, desktop=15)

    expand_button = ft.IconButton(
        icon=ft.Icons.EXPAND_MORE if expanded_state[0] else ft.Icons.CHEVRON_RIGHT,
        icon_size=20,
        icon_color=ft.Colors.WHITE_70,
        tooltip="Expandir/Contraer subtareas",
    )

    title_text = ft.Text(
        f"Subtareas ({len(task.subtasks)})",
        size=description_size,
        weight=ft.FontWeight.W_500,
        color=ft.Colors.WHITE_70,
    )

    row = ft.Row(
        controls=[expand_button, title_text],
        spacing=8,
        tight=True,
        alignment=ft.MainAxisAlignment.START,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )

    def toggle(e):
        expanded_state[0] = not expanded_state[0]
        expand_button.icon = ft.Icons.EXPAND_MORE if expanded_state[0] else ft.Icons.CHEVRON_RIGHT
        if page:
            page.update()

    expand_button.on_click = toggle

    return row, expand_button


class SubtasksSection:
    """Convenience class that builds and caches subtasks title + list.
    Methods:
        - build() -> (title_row, subtasks_list)
        - refresh()
        - update_subtasks() -> rebuilds list (use when subtasks changed)
    """

    def __init__(
        self,
        task: Task,
        page: Optional[ft.Page] = None,
        on_subtask_toggle: Optional[Callable[[str, str], None]] = None,
        on_subtask_edit: Optional[Callable[[str, str], None]] = None,
        on_subtask_delete: Optional[Callable[[str, str], None]] = None,
        show_priority: bool = True,
        show_actions: bool = True,
        compact: bool = False,
        expanded: bool = True,
        progress_bar: Optional[ft.ProgressBar] = None,
        progress_text: Optional[ft.Text] = None,
        badges_row: Optional[ft.Row] = None,
    ):
        self.task = task
        self.page = page
        self.on_subtask_toggle = on_subtask_toggle
        self.on_subtask_edit = on_subtask_edit
        self.on_subtask_delete = on_subtask_delete
        self.show_priority = show_priority
        self.show_actions = show_actions
        self.compact = compact
        self.expanded_state = [expanded]
        self.progress_bar = progress_bar
        self.progress_text = progress_text
        self.badges_row = badges_row

        self._title_row: Optional[ft.Row] = None
        self._expand_button: Optional[ft.IconButton] = None
        self._subtasks_list: Optional[ft.Column] = None

    def build(self) -> Tuple[Optional[ft.Row], Optional[ft.Column]]:
        """Builds (or returns cached) title row and subtasks list."""
        if self._title_row is None or self._subtasks_list is None:
            self._title_row, self._expand_button = create_subtasks_title_row(
                task=self.task,
                page=self.page,
                expanded_state=self.expanded_state,
            )
            self._subtasks_list = create_subtasks_list(
                task=self.task,
                page=self.page,
                on_subtask_toggle=self.on_subtask_toggle,
                on_subtask_edit=self.on_subtask_edit,
                on_subtask_delete=self.on_subtask_delete,
                show_priority=self.show_priority,
                show_actions=self.show_actions,
                compact=self.compact,
                expanded=self.expanded_state[0],
                progress_bar=self.progress_bar,
                progress_text=self.progress_text,
                badges_row=self.badges_row,
            )

        # Always override the expand button handler to also control the visibility of the subtasks list
        def _toggle_and_set_list(e):
            self.expanded_state[0] = not self.expanded_state[0]
            if self._expand_button:
                self._expand_button.icon = ft.Icons.EXPAND_MORE if self.expanded_state[0] else ft.Icons.CHEVRON_RIGHT
            if self._subtasks_list is not None:
                self._subtasks_list.visible = self.expanded_state[0]
            if self.page:
                self.page.update()

        if self._expand_button:
            self._expand_button.on_click = _toggle_and_set_list
        return self._title_row, self._subtasks_list

    def refresh(self):
        """Invalidate cache so next build rebuilds."""
        self._title_row = None
        self._expand_button = None
        self._subtasks_list = None

    def update_subtasks(self):
        """Rebuild list when task.subtasks changed (keeps expansion state)."""
        self._subtasks_list = create_subtasks_list(
            task=self.task,
            page=self.page,
            on_subtask_toggle=self.on_subtask_toggle,
            on_subtask_edit=self.on_subtask_edit,
            on_subtask_delete=self.on_subtask_delete,
            show_priority=self.show_priority,
            show_actions=self.show_actions,
            compact=self.compact,
            expanded=self.expanded_state[0],
            progress_bar=self.progress_bar,
            progress_text=self.progress_text,
            badges_row=self.badges_row,
        )
        # Also update the title count text if we have it
        if self._title_row:
            # title row structure: [expand_button, title_text]
            if len(self._title_row.controls) >= 2 and isinstance(self._title_row.controls[1], ft.Text):
                self._title_row.controls[1].value = f"Subtareas ({len(self.task.subtasks)})"
        if self.page:
            self.page.update()
