"""Compat shim para `TaskForm`.

Se mantiene este módulo para compatibilidad con imports antiguos:
- `from app.ui.task.task_form import TaskForm`

La implementación real vive en `app.ui.task.task_form_view`.
"""

from __future__ import annotations

from app.ui.task.task_form_view import TaskForm

__all__ = ["TaskForm"]
