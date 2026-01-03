"""
Vista de Resumen (Resume) de la aplicación
"""

import flet as ft
from app.ui.resume.rewards.rewards_view import RewardsView
from app.services.progress_service import ProgressService


class ResumeView:
    """Clase que representa la vista de resumen"""
    
    def __init__(self):
        """Inicializa la vista de resumen"""
        self.rewards_view = None
        self.progress_service = ProgressService()  # Sistema de progreso sin usuarios
        print(f"[ResumeView] Vista de resumen inicializada con ProgressService")
    
    def build(self) -> ft.Container:
        """
        Construye y retorna el widget principal de la vista
        
        Returns:
            Container con el contenido de la vista de resumen
        """
        # Crear la vista de recompensas con el progress_service
        self.rewards_view = RewardsView(
            progress_service=self.progress_service
        )
        
        return self.rewards_view
    
    def get_progress_service(self):
        """Retorna el servicio de progreso para compartir con otras vistas"""
        return self.progress_service
