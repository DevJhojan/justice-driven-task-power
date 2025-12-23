"""
Módulo de vista de tareas - Organizado por funcionalidades.

Este módulo proporciona una vista completa para gestionar tareas con la Matriz de Eisenhower,
dividida en múltiples archivos para facilitar el mantenimiento:

- utils.py: Funciones auxiliares y constantes
- navigation.py: Barra de navegación de prioridades
- priority_sections.py: Construcción de secciones de prioridad
- task_management.py: CRUD de tareas
- subtask_management.py: Gestión de subtareas
- forms.py: Navegación a formularios
- view.py: Clase principal TasksView
"""
from .view import TasksView

__all__ = ['TasksView']

