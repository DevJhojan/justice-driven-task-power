"""
Módulo de vista de configuración - Organizado por funcionalidades.

Este módulo proporciona una vista completa para gestionar la configuración de la aplicación,
dividida en múltiples archivos para facilitar el mantenimiento:

- utils.py: Funciones auxiliares
- appearance.py: Gestión de apariencia (tema, colores)
- firebase_auth.py: Autenticación Firebase
- firebase_forms.py: Formularios de Firebase (login, registro)
- firebase_sync.py: Sincronización Firebase
- view.py: Clase principal SettingsView
"""
from .view import SettingsView

__all__ = ['SettingsView']

