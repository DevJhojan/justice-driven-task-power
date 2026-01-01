"""
Módulo de componentes de tarjetas de tareas (Task Card Components)
Importa componentes modulares y orquestadores para construcción de tarjetas de tareas
"""

# ============================================================================
# IMPORTACIONES DE HANDLERS
# ============================================================================
from .handlers import (
    create_subtask_toggle_handler,
    create_toggle_status_handler,
)

# ============================================================================
# IMPORTACIONES DE HEADER
# ============================================================================
from .header import (
    create_header,
    Header,
)

# ============================================================================
# IMPORTACIONES DE DESCRIPTION
# ============================================================================
from .description import (
    create_description,
    Description,
)

# ============================================================================
# IMPORTACIONES DE INFO_SECTION
# ============================================================================
from .info_section import (
    create_due_date_row,
    create_progress_controls,
    create_info_section,
    InfoSection,
)

# ============================================================================
# IMPORTACIONES DE TAGS
# ============================================================================
from .tags import (
    create_tag_chip,
    create_tags_row,
    Tags,
)

# ============================================================================
# IMPORTACIONES DE SUBTASKS
# ============================================================================
from .subtasks import (
    create_subtasks_list,
    create_subtasks_title_row,
    SubtasksSection,
)

# ============================================================================
# IMPORTACIONES DE ACTIONS
# ============================================================================
from .actions import (
    create_edit_button,
    create_delete_button,
    create_toggle_status_button,
    create_actions_row,
    Actions,
)

# ============================================================================
# IMPORTACIONES DE TASK_CARD (ORQUESTADOR FINAL)
# ============================================================================
from .task_card import (
    create_task_card,
    TaskCard,
)

# ============================================================================
# EXPORTACIONES PÚBLICAS (__all__)
# ============================================================================
__all__ = [
    # Handlers
    'create_subtask_toggle_handler',
    'create_toggle_status_handler',
    # Header
    'create_header',
    'Header',
    # Description
    'create_description',
    'Description',
    # Info Section
    'create_due_date_row',
    'create_progress_controls',
    'create_info_section',
    'InfoSection',
    # Tags
    'create_tag_chip',
    'create_tags_row',
    'Tags',
    # Subtasks
    'create_subtasks_list',
    'create_subtasks_title_row',
    'SubtasksSection',
    # Actions
    'create_edit_button',
    'create_delete_button',
    'create_toggle_status_button',
    'create_actions_row',
    'Actions',
    # Task Card (Orquestador Final)
    'create_task_card',
    'TaskCard',
]
