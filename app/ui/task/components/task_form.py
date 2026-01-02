"""Compat shim para `TaskForm`.

El formulario fue modularizado en `app.ui.task.components.form.task_form`.
Este módulo se mantiene para compatibilidad con imports antiguos.
"""

from __future__ import annotations

from app.ui.task.components.form.task_form import TaskForm

__all__ = ["TaskForm"]
