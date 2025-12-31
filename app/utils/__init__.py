"""
Módulo de utilidades
Importa componentes, helpers y funciones auxiliares para uso en toda la aplicación
"""

# ============================================================================
# IMPORTACIONES DE EISENHOWER MATRIX
# ============================================================================
from .eisenhower_matrix import (
    Quadrant,
    get_eisenhower_quadrant,
    get_quadrant_name,
    get_quadrant_description,
    get_quadrant_color,
    get_quadrant_ft_color,
    get_quadrant_icon,
    get_priority_label,
    get_priority_badge_text,
    sort_tasks_by_quadrant,
    get_quadrant_priority_order,
    is_high_priority,
    is_medium_priority,
    is_low_priority,
)

# ============================================================================
# IMPORTACIONES DE TASK HELPER
# ============================================================================
from .task_helper import (
    TASK_STATUS_PENDING,
    TASK_STATUS_IN_PROGRESS,
    TASK_STATUS_COMPLETED,
    TASK_STATUS_CANCELLED,
    VALID_TASK_STATUSES,
    format_task_status,
    get_task_status_color,
    get_task_status_ft_color,
    get_task_status_icon,
    calculate_completion_percentage,
    format_completion_percentage,
    is_task_overdue,
    is_task_due_today,
    is_task_due_soon,
    get_task_urgency_indicator,
    count_subtasks,
    count_completed_subtasks,
    has_subtasks,
    is_task_completed,
    is_task_pending,
    is_task_in_progress,
    filter_tasks_by_status,
    get_task_summary,
)

# ============================================================================
# IMPORTACIONES DE BOTTOM NAV
# ============================================================================
from .bottom_nav import (
    BottomNav,
    create_bottom_nav_with_views,
    wrap_view_with_bottom_nav,
)

# ============================================================================
# IMPORTACIONES DE LOADING SCREEN
# ============================================================================
from .screem_load import LoadingScreen

# ============================================================================
# EXPORTACIONES PÚBLICAS (__all__)
# ============================================================================
__all__ = [
    # Eisenhower Matrix
    'Quadrant',
    'get_eisenhower_quadrant',
    'get_quadrant_name',
    'get_quadrant_description',
    'get_quadrant_color',
    'get_quadrant_ft_color',
    'get_quadrant_icon',
    'get_priority_label',
    'get_priority_badge_text',
    'sort_tasks_by_quadrant',
    'get_quadrant_priority_order',
    'is_high_priority',
    'is_medium_priority',
    'is_low_priority',
    # Task Helper
    'TASK_STATUS_PENDING',
    'TASK_STATUS_IN_PROGRESS',
    'TASK_STATUS_COMPLETED',
    'TASK_STATUS_CANCELLED',
    'VALID_TASK_STATUSES',
    'format_task_status',
    'get_task_status_color',
    'get_task_status_ft_color',
    'get_task_status_icon',
    'calculate_completion_percentage',
    'format_completion_percentage',
    'is_task_overdue',
    'is_task_due_today',
    'is_task_due_soon',
    'get_task_urgency_indicator',
    'count_subtasks',
    'count_completed_subtasks',
    'has_subtasks',
    'is_task_completed',
    'is_task_pending',
    'is_task_in_progress',
    'filter_tasks_by_status',
    'get_task_summary',
    # Bottom Nav
    'BottomNav',
    'create_bottom_nav_with_views',
    'wrap_view_with_bottom_nav',
    # Loading Screen
    'LoadingScreen',
]

