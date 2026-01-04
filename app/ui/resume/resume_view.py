"""
Vista de Resumen (Resume) de la aplicación
"""

import flet as ft
from app.ui.resume.points_and_levels.points_and_levels_view import PointsAndLevelsView
from app.ui.resume.rewards.rewards_view import RewardsView
from app.services.progress_service import ProgressService


class ResumeView:
    """Clase que representa la vista de resumen"""
    
    def __init__(self):
        """Inicializa la vista de resumen"""
        self.points_levels_view = None
        self.rewards_view = None
        self.progress_service = ProgressService()  # Sistema de progreso sin usuarios
        self.user_id = "default_user"
        self.verify_integrity_callback = None  # Callback para verificar integridad
        print(f"[ResumeView] Vista de resumen inicializada con ProgressService")
    
    def set_verify_integrity_callback(self, callback):
        """Establece el callback para verificar integridad de puntos"""
        self.verify_integrity_callback = callback
        if self.points_levels_view:
            self.points_levels_view.on_verify_integrity = callback
            print(f"[ResumeView] Callback de integridad configurado")
    
    def build(self) -> ft.Container:
        """
        Construye y retorna el widget principal de la vista
        
        Returns:
            Container con el contenido de la vista de resumen
        """
        # Vista de puntos y niveles
        self.points_levels_view = PointsAndLevelsView(
            progress_service=self.progress_service,
            user_id=self.user_id,
            on_verify_integrity=self.verify_integrity_callback,
        )
        # Evitar que ocupe todo el alto; deja espacio para recompensas debajo
        self.points_levels_view.expand = False

        # Obtener los puntos actuales del usuario desde progress_service
        user_points = self.progress_service.current_points
        
        # Panel de recompensas con altura fija equivalente a ~6 filas y scroll
        self.rewards_view = RewardsView(user_points=user_points)
        rewards_panel = ft.Container(
            height=6 * 64,  # aproximadamente 6 filas visibles
            bgcolor="#101010",
            border_radius=10,
            border=ft.border.all(1, "#2a2a2a"),
            padding=12,
            content=ft.Column(
                spacing=10,
                expand=True,
                scroll=ft.ScrollMode.AUTO,
                controls=[
                    ft.Text("Recompensas", size=18, weight="bold", color="#FFD700"),
                    self.rewards_view,
                ],
            ),
        )
        
        return ft.Column(
            spacing=16,
            expand=True,
            scroll=ft.ScrollMode.AUTO,
            controls=[
                self.points_levels_view,
                rewards_panel,
            ],
        )
    
    def get_progress_service(self):
        """Retorna el servicio de progreso para compartir con otras vistas"""
        return self.progress_service
