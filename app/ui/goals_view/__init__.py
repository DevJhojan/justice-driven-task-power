"""
Módulo de vista de objetivos.

Este módulo proporciona una vista completa para gestionar objetivos,
dividida en múltiples archivos para facilitar el mantenimiento:

- goal_management.py: CRUD de objetivos
- forms.py: Navegación a formularios
- view.py: Clase principal GoalsView
"""
from .view import GoalsView

__all__ = ['GoalsView']

