"""
Módulo de vista de hábitos - Organizado por funcionalidades.

Este módulo proporciona una vista completa para gestionar hábitos,
dividida en múltiples archivos para facilitar el mantenimiento:

- utils.py: Funciones auxiliares
- habit_management.py: CRUD de hábitos
- forms.py: Navegación a formularios
- view.py: Clase principal HabitsView
"""
from .view import HabitsView

__all__ = ['HabitsView']

