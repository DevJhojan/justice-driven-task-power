"""
Vista de Resumen (Resume) de la aplicación
"""

import flet as ft
from app.ui.resume.rewards.rewards_view import RewardsView
from app.services.user_service import UserService


class ResumeView:
    """Clase que representa la vista de resumen"""
    
    def __init__(self):
        """Inicializa la vista de resumen"""
        self.rewards_view = None
        self.user_service = UserService()  # Servicio de usuario compartido
        self.user_id = "default_user"
    
    def build(self) -> ft.Container:
        """
        Construye y retorna el widget principal de la vista
        
        Returns:
            Container con el contenido de la vista de resumen
        """
        # Crear la vista de recompensas con el user_service
        self.rewards_view = RewardsView(
            user_service=self.user_service,
            user_id=self.user_id
        )
        
        return self.rewards_view
    
    def get_user_service(self):
        """Retorna el servicio de usuario para compartir con otras vistas"""
        return self.user_service
