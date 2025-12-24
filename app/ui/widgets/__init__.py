"""
Módulo de widgets - Organizado por funcionalidades.

Este módulo proporciona widgets reutilizables para la interfaz de usuario,
dividido en múltiples archivos para facilitar el mantenimiento:

- utils.py: Funciones auxiliares comunes (colores, temas, tamaños)
- task_widgets.py: Widgets relacionados con tareas
- habit_widgets.py: Widgets relacionados con hábitos
"""

# Importar widgets de tareas
from .task_widgets import (
    create_task_card,
    create_empty_state,
    create_statistics_card
)

# Importar widgets de hábitos
from .habit_widgets import (
    create_habit_card,
    create_habit_empty_state,
    create_habit_statistics_card
)

# Exportar todas las funciones para mantener compatibilidad
__all__ = [
    # Widgets de tareas
    'create_task_card',
    'create_empty_state',
    'create_statistics_card',
    # Widgets de hábitos
    'create_habit_card',
    'create_habit_empty_state',
    'create_habit_statistics_card',
]

