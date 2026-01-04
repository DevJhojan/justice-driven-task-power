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
        self.user_id = "default_user"
        self.verify_integrity_callback = None  # Callback para verificar integridad
        print(f"[ResumeView] Vista de resumen inicializada con ProgressService")
    
    def set_verify_integrity_callback(self, callback):
        """Establece el callback para verificar integridad de puntos"""
        self.verify_integrity_callback = callback
        if self.rewards_view:
            self.rewards_view.on_verify_integrity = callback
            print(f"[ResumeView] Callback de integridad configurado")
    
    def build(self) -> ft.Container:
        """
        Construye y retorna el widget principal de la vista
        
        Returns:
            Container con el contenido de la vista de resumen
        """
        # Crear la vista de recompensas con el progress_service
        self.rewards_view = RewardsView(
            progress_service=self.progress_service,
            user_id=self.user_id,
            on_verify_integrity=self.verify_integrity_callback,
        )
        
        return self.rewards_view
    
    def get_progress_service(self):
        """Retorna el servicio de progreso para compartir con otras vistas"""
        return self.progress_service
