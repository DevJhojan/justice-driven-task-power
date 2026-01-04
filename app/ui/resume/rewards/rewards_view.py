"""
Vista de Recompensas (Rewards View)
Interfaz para mostrar nivel, puntos y recompensas
"""

import flet as ft
from typing import Optional
from app.services.user_service import UserService


class RewardsView(ft.Container):
    """Vista principal de recompensas con paneles de información"""
    
    def __init__(self, user_service: Optional[UserService] = None, user_id: str = "default_user"):
        super().__init__()
        
        self.user_service = user_service
        self.user_id = user_id
        self.current_user_points = 0.0
        self.current_user_level = "Nadie"
        
        # Estilos generales
        self.expand = True
        self.bgcolor = "#1a1a1a"
        self.padding = 20
        
        # Header delgado con nivel y puntos
        self.level_text = ft.Text("Nadie", size=32, weight="bold", color="#FFD700")
        self.points_text = ft.Text("0.00", size=24, weight="bold", color="#4CAF50")
        
        self.header_stats = ft.Container(
            bgcolor="#2a2a2a",
            border_radius=10,
            padding=ft.padding.symmetric(horizontal=20, vertical=15),
            border=ft.border.all(1, "#3a3a3a"),
            content=ft.Column(
                spacing=8,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    self.level_text,
                    self.points_text,
                ],
            ),
        )
        
        # Panel vacío
        self.panel_empty = ft.Container(
            bgcolor="#2a2a2a",
            border_radius=15,
            padding=30,
            border=ft.border.all(2, "#3a3a3a"),
            expand=True,
        )
        
        # Contenido principal
        self.content = ft.Column(
            spacing=20,
            expand=True,
            controls=[
                # Título y header de nivel/puntos en un Row
                ft.Row(
                    spacing=20,
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Text("Recompensas", size=28, weight="bold", color="#FFF"),
                        self.header_stats,
                    ],
                ),
                
                # Panel principal vacío
                ft.Container(
                    expand=True,
                    content=self.panel_empty,
                ),
            ],
        )
    
    def did_mount(self):
        """Se llama cuando el control es añadido a la página"""
        if self.user_service:
            self.refresh_from_user_service()
    
    def set_user_points(self, points: float):
        """Establece los puntos del usuario"""
        self.current_user_points = float(points)
        # Asegurar siempre 2 decimales
        self.points_text.value = f"{float(points):.2f}"
        print(f"[RewardsView] Actualizando puntos a: {self.points_text.value}")
        if self.page:
            try:
                self.update()
            except Exception as e:
                print(f"[RewardsView] Error actualizando UI: {e}")
    
    def set_user_level(self, level: str):
        """Establece el nivel del usuario"""
        self.current_user_level = level
        self.level_text.value = level
        print(f"[RewardsView] Actualizando nivel a: {level}")
        if self.page:
            try:
                self.update()
            except Exception as e:
                print(f"[RewardsView] Error actualizando UI: {e}")
    
    def refresh_from_user_service(self):
        """Actualiza los puntos y nivel desde el UserService"""
        if self.user_service:
            stats = self.user_service.get_user_stats(self.user_id)
            if stats:
                self.set_user_points(stats.get("points", 0.0))
                self.set_user_level(stats.get("level", "Nadie"))
    
    def update_points_display(self, points: float):
        """Actualiza la visualización de puntos"""
        self.set_user_points(points)
