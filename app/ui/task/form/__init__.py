"""Componentes modulares del formulario de tareas.

Este paquete expone una API pública similar a otros paquetes de utilidades
del proyecto (ver app/utils y app/utils/helpers).
"""

# ============================================================================
# IMPORTACIONES DEL TASK FORM (MODULAR)
# ============================================================================
from .task_form import TaskForm, is_valid_tags_list, parse_csv_tags

# ============================================================================
# IMPORTACIONES DE CONTROLS (FACTORIES)
# ============================================================================
from .controls import (
	create_description_field,
	create_error_text,
	create_notes_field,
	create_priority_checkboxes,
	create_status_dropdown,
	create_tags_field,
	create_title_field,
)

# ============================================================================
# IMPORTACIONES DE DATE CONTROLS
# ============================================================================
from .date_controls import build_due_date_controls

# ============================================================================
# IMPORTACIONES DE SUBTASK
# ============================================================================
from .subtask import (
	build_add_subtask_row,
	create_subtask,
	delete_subtask,
	edit_subtask,
	render_subtasks,
	toggle_subtask,
)

# ============================================================================
# IMPORTACIONES DE LAYOUT
# ============================================================================
from .layout import build_form_layout

# ============================================================================
# EXPORTACIONES PÚBLICAS (__all__)
# ============================================================================
__all__ = [
	# TaskForm
	"TaskForm",
	"parse_csv_tags",
	"is_valid_tags_list",
	# Controls
	"create_title_field",
	"create_description_field",
	"create_status_dropdown",
	"create_priority_checkboxes",
	"create_tags_field",
	"create_notes_field",
	"create_error_text",
	# Date
	"build_due_date_controls",
	# Subtasks
	"create_subtask",
	"delete_subtask",
	"toggle_subtask",
	"edit_subtask",
	"render_subtasks",
	"build_add_subtask_row",
	# Layout
	"build_form_layout",
]

