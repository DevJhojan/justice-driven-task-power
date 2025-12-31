"""
Módulo de funciones auxiliares
Importa funciones organizadas por categoría para uso en toda la aplicación
"""

# ============================================================================
# IMPORTACIONES DE FILES
# ============================================================================
from .files import (
    get_project_root,
    get_asset_path,
    get_database_path,
    get_config_path,
    ensure_directory_exists,
    ensure_assets_directory,
    ensure_database_directory,
    file_exists,
    directory_exists,
    get_file_size,
    get_file_extension,
    get_file_name_without_extension,
    is_image_file,
    join_paths,
    get_relative_path,
    create_backup_path,
    list_files_in_directory,
    normalize_path,
)

# ============================================================================
# IMPORTACIONES DE FORMATS
# ============================================================================
from .formats import (
    format_date,
    format_time,
    format_datetime,
    format_duration,
    format_relative_time,
    format_number,
    format_percentage,
    format_currency,
    format_file_size,
    format_points,
    format_level,
    format_completion_percentage,
    format_task_count,
    format_habit_streak,
)

# ============================================================================
# IMPORTACIONES DE RESPONSIVES
# ============================================================================
from .responsives import (
    MOBILE_BREAKPOINT,
    TABLET_BREAKPOINT,
    DESKTOP_BREAKPOINT,
    get_responsive_padding,
    get_responsive_size,
    get_responsive_icon_size,
    get_responsive_width,
    get_responsive_columns,
    get_responsive_spacing,
    get_responsive_card_width,
    get_responsive_border_radius,
    get_responsive_elevation,
    get_responsive_max_width,
    is_mobile,
    is_tablet,
    is_desktop,
    get_device_type,
)

# ============================================================================
# IMPORTACIONES DE VALIDATIONS
# ============================================================================
from .validators import (
    is_valid_email,
    is_valid_username,
    is_valid_password,
    is_valid_date,
    is_valid_time,
    is_valid_number,
    is_valid_integer,
    is_valid_string,
    is_valid_url,
    is_valid_phone,
    is_valid_priority,
    is_valid_status,
    is_future_date,
    is_past_date,
)

# ============================================================================
# EXPORTACIONES PÚBLICAS (__all__)
# ============================================================================
__all__ = [
    # Files
    'get_project_root',
    'get_asset_path',
    'get_database_path',
    'get_config_path',
    'ensure_directory_exists',
    'ensure_assets_directory',
    'ensure_database_directory',
    'file_exists',
    'directory_exists',
    'get_file_size',
    'get_file_extension',
    'get_file_name_without_extension',
    'is_image_file',
    'join_paths',
    'get_relative_path',
    'create_backup_path',
    'list_files_in_directory',
    'normalize_path',
    # Formats
    'format_date',
    'format_time',
    'format_datetime',
    'format_duration',
    'format_relative_time',
    'format_number',
    'format_percentage',
    'format_currency',
    'format_file_size',
    'format_points',
    'format_level',
    'format_completion_percentage',
    'format_task_count',
    'format_habit_streak',
    # Responsives
    'MOBILE_BREAKPOINT',
    'TABLET_BREAKPOINT',
    'DESKTOP_BREAKPOINT',
    'get_responsive_padding',
    'get_responsive_size',
    'get_responsive_icon_size',
    'get_responsive_width',
    'get_responsive_columns',
    'get_responsive_spacing',
    'get_responsive_card_width',
    'get_responsive_border_radius',
    'get_responsive_elevation',
    'get_responsive_max_width',
    'is_mobile',
    'is_tablet',
    'is_desktop',
    'get_device_type',
    # Validations
    'is_valid_email',
    'is_valid_username',
    'is_valid_password',
    'is_valid_date',
    'is_valid_time',
    'is_valid_number',
    'is_valid_integer',
    'is_valid_string',
    'is_valid_url',
    'is_valid_phone',
    'is_valid_priority',
    'is_valid_status',
    'is_future_date',
    'is_past_date',
]
