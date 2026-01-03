"""
Actions component for Task Card
Provides helpers to create action buttons (toggle status, edit, delete) and an Actions
class that caches and updates those controls. Depends on handlers module for status toggle logic.
"""

import flet as ft
from typing import Optional, Callable, List
from app.models.task import Task
from app.ui.task.cards.handlers import create_toggle_status_handler
from app.utils.task_helper import TASK_STATUS_COMPLETED


def create_edit_button(
    task_id: str,
    page: Optional[ft.Page] = None,
    on_edit: Optional[Callable[[str], None]] = None,
) -> ft.IconButton:
    """Create an edit button for a task."""
    return ft.IconButton(
        icon=ft.Icons.EDIT,
        icon_size=20,
        icon_color=ft.Colors.BLUE_400,
        tooltip="Editar tarea",
        on_click=lambda e: on_edit(task_id) if on_edit else None,
    )


def create_delete_button(
    task_id: str,
    page: Optional[ft.Page] = None,
    on_delete: Optional[Callable[[str], None]] = None,
) -> ft.IconButton:
    """Create a delete button for a task."""
    return ft.IconButton(
        icon=ft.Icons.DELETE_OUTLINE,
        icon_size=20,
        icon_color=ft.Colors.RED_400,
        tooltip="Eliminar tarea",
        on_click=lambda e: on_delete(task_id) if on_delete else None,
    )


def create_toggle_status_button(
    task: Task,
    badges_row: ft.Row,
    page: Optional[ft.Page] = None,
    progress_bar: Optional[ft.ProgressBar] = None,
    progress_text: Optional[ft.Text] = None,
    show_progress: bool = True,
    on_toggle_status: Optional[Callable[[str], None]] = None,
) -> Optional[ft.IconButton]:
    """
    Create a toggle status button for a task without subtasks.
    Returns None if the task has subtasks (status is controlled via subtasks).
    """
    # Only show toggle button if no subtasks
    if task.subtasks and len(task.subtasks) > 0:
        return None

    status_icon = ft.Icons.CHECK_CIRCLE if task.status != TASK_STATUS_COMPLETED else ft.Icons.UNDO

    toggle_button = ft.IconButton(
        icon=status_icon,
        icon_size=20,
        icon_color=ft.Colors.GREEN_400,
        tooltip="Cambiar estado",
    )

    # Create handler using the handlers module (depends on handlers)
    handler = create_toggle_status_handler(
        task=task,
        page=page,
        progress_bar=progress_bar,
        progress_text=progress_text,
        badges_row=badges_row,
        toggle_button=toggle_button,
        show_progress=show_progress,
        on_toggle_status=on_toggle_status,
    )
    toggle_button.on_click = handler

    return toggle_button


def create_actions_row(
    task: Task,
    badges_row: ft.Row,
    page: Optional[ft.Page] = None,
    on_edit: Optional[Callable[[str], None]] = None,
    on_delete: Optional[Callable[[str], None]] = None,
    on_toggle_status: Optional[Callable[[str], None]] = None,
    progress_bar: Optional[ft.ProgressBar] = None,
    progress_text: Optional[ft.Text] = None,
    show_progress: bool = True,
) -> Optional[ft.Row]:
    """
    Create a Row with action buttons (toggle status, edit, delete).
    Returns None if there are no buttons to show.
    """
    action_buttons: list[ft.Control] = []

    # Toggle status button (only if no subtasks and a toggle handler was provided)
    toggle_btn = None
    if on_toggle_status:
        toggle_btn = create_toggle_status_button(
            task=task,
            page=page,
            progress_bar=progress_bar,
            progress_text=progress_text,
            badges_row=badges_row,
            show_progress=show_progress,
            on_toggle_status=on_toggle_status,
        )
        if toggle_btn is not None:
            action_buttons.append(toggle_btn)

    # Edit button
    if on_edit:
        edit_btn = create_edit_button(task.id, page=page, on_edit=on_edit)
        action_buttons.append(edit_btn)

    # Delete button
    if on_delete:
        delete_btn = create_delete_button(task.id, page=page, on_delete=on_delete)
        action_buttons.append(delete_btn)

    if not action_buttons:
        return None

    actions_row = ft.Row(
        controls=action_buttons,
        spacing=5,
        alignment=ft.MainAxisAlignment.END,
    )
    return actions_row


class Actions:
    """Convenience class to build and cache action buttons for a task."""

    def __init__(
        self,
        task: Task,
        badges_row: ft.Row,
        page: Optional[ft.Page] = None,
        on_edit: Optional[Callable[[str], None]] = None,
        on_delete: Optional[Callable[[str], None]] = None,
        on_toggle_status: Optional[Callable[[str], None]] = None,
        progress_bar: Optional[ft.ProgressBar] = None,
        progress_text: Optional[ft.Text] = None,
        show_progress: bool = True,
    ):
        self.task = task
        self.page = page
        self.on_edit = on_edit
        self.on_delete = on_delete
        self.on_toggle_status = on_toggle_status
        self.progress_bar = progress_bar
        self.progress_text = progress_text
        self.badges_row = badges_row
        self.show_progress = show_progress

        self._actions_row: Optional[ft.Row] = None
        self.toggle_button: Optional[ft.IconButton] = None
        self.edit_button: Optional[ft.IconButton] = None
        self.delete_button: Optional[ft.IconButton] = None

    def build(self) -> Optional[ft.Row]:
        """Builds (or returns cached) actions row."""
        if self._actions_row is None:
            self._actions_row = create_actions_row(
                task=self.task,
                page=self.page,
                on_edit=self.on_edit,
                on_delete=self.on_delete,
                on_toggle_status=self.on_toggle_status,
                progress_bar=self.progress_bar,
                progress_text=self.progress_text,
                badges_row=self.badges_row,
                show_progress=self.show_progress,
            )
            # Extract individual button references if row was built
            if self._actions_row:
                for ctrl in self._actions_row.controls:
                    if isinstance(ctrl, ft.IconButton):
                        # Try to identify button by icon
                        if ctrl.icon == ft.Icons.CHECK_CIRCLE or ctrl.icon == ft.Icons.UNDO:
                            self.toggle_button = ctrl
                        elif ctrl.icon == ft.Icons.EDIT:
                            self.edit_button = ctrl
                        elif ctrl.icon == ft.Icons.DELETE_OUTLINE:
                            self.delete_button = ctrl
        return self._actions_row

    def refresh(self):
        """Invalidate cache so next build rebuilds."""
        self._actions_row = None
        self.toggle_button = None
        self.edit_button = None
        self.delete_button = None
