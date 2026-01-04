"""
Vista de Resumen (Resume) de la aplicación
"""

import flet as ft
from app.ui.resume.rewards.rewards_view import RewardsView


class ResumeView:
    """Clase que representa la vista de resumen"""
    
    def __init__(self):
        """Inicializa la vista de resumen"""
        self.rewards_view = None
    
    def build(self) -> ft.Container:
        """
        Construye y retorna el widget principal de la vista
        
        Returns:
            Container con el contenido de la vista de resumen
        """
        # Crear la vista de recompensas
        self.rewards_view = RewardsView()
        
        return self.rewards_view

