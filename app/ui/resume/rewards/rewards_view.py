"""
Vista de Recompensas (Rewards View)
Interfaz para mostrar nivel, puntos y recompensas
"""

import flet as ft
from typing import Optional
from app.services.progress_service import ProgressService
from app.services.database_service import DatabaseService
from app.logic.system_points import LEVELS_ORDER, Level
from app.utils.task_helper import TASK_STATUS_COMPLETED


class RewardsView(ft.Container):
    """Vista principal de recompensas con paneles de información"""
    
    def __init__(self, progress_service: Optional[ProgressService] = None, user_id: str = "default_user"):
        super().__init__()
        
        self.progress_service = progress_service if progress_service else ProgressService()
        self.user_id = user_id
        self.database_service: Optional[DatabaseService] = None
        self.current_user_points = 0.0
        self.current_user_level = "Nadie"
        self.progress_percent = 0.0
        self.next_level_name = ""
        self.points_remaining = 0.0
        
        # Estilos generales
        self.expand = True
        self.bgcolor = "#1a1a1a"
        self.padding = 20
        
        # Header delgado con nivel y puntos
        self.level_text = ft.Text("Nadie", size=32, weight="bold", color="#FFD700")
        self.points_text = ft.Text("0.00", size=24, weight="bold", color="#4CAF50")
        self.tasks_completed_text = ft.Text("0 tareas completadas", size=14, color="#CCCCCC")
        
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
                    self.tasks_completed_text,
                ],
            ),
        )

        # Panel de progreso hacia el siguiente nivel
        self.progress_title = ft.Text("Progreso al siguiente nivel", size=18, weight="bold", color="#FFF", text_align=ft.TextAlign.CENTER)
        self.next_level_text = ft.Text("Siguiente nivel: --", size=14, color="#DDD", text_align=ft.TextAlign.CENTER)
        self.progress_detail_text = ft.Text("Faltan 0.00 pts", size=12, color="#AAA", text_align=ft.TextAlign.CENTER)
        self.levels_remaining_text = ft.Text("Faltan 0 niveles para el máximo", size=12, color="#AAA", text_align=ft.TextAlign.CENTER)
        self.progress_bar = ft.ProgressBar(value=0.0, bgcolor="#333", color="#4CAF50", height=10, width=280)

        self.progress_panel = ft.Container(
            bgcolor="#242424",
            border_radius=12,
            padding=ft.padding.all(16),
            border=ft.border.all(1, "#3a3a3a"),
            expand=True,
            content=ft.Column(
                spacing=8,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    self.progress_title,
                    self.next_level_text,
                    self.progress_bar,
                    self.progress_detail_text,
                    self.levels_remaining_text,
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
                    alignment=ft.MainAxisAlignment.START,
                    vertical_alignment=ft.CrossAxisAlignment.START,
                    controls=[
                        self.progress_panel,
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
        if self.page:
            self.page.run_task(self.refresh_from_progress_service)
    
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

    def set_tasks_completed(self, count: int):
        """Actualiza el contador de tareas completadas"""
        self.tasks_completed_text.value = f"{int(count)} tareas completadas"
        if self.page:
            try:
                self.update()
            except Exception as e:
                print(f"[RewardsView] Error actualizando tareas completadas: {e}")

    def update_progress_from_stats(self, stats: dict):
        """Actualiza barra y textos de progreso usando stats completas"""
        progress_percent = float(stats.get("progress_percent", 0.0))
        next_level = stats.get("next_level") or "Nivel máximo"
        points_in_current = float(stats.get("points_in_current_level", 0.0))
        total_for_next = float(stats.get("total_for_next_level", 0.0))
        points_remaining = max(0.0, total_for_next - points_in_current) if total_for_next else 0.0

        # Calcular cuántos niveles faltan para el máximo
        current_level_str = stats.get("level", "Nadie")
        remaining_levels = 0
        try:
            idx_current = [lvl.value for lvl in LEVELS_ORDER].index(current_level_str)
            remaining_levels = max(0, len(LEVELS_ORDER) - idx_current - 1)
        except ValueError:
            remaining_levels = 0

        self.progress_percent = progress_percent
        self.next_level_name = next_level
        self.points_remaining = points_remaining

        self.progress_bar.value = min(1.0, progress_percent / 100.0)
        self.next_level_text.value = f"Siguiente nivel: {next_level}"
        if total_for_next == 0:
            self.progress_detail_text.value = "Ya alcanzaste el nivel máximo"
        else:
            self.progress_detail_text.value = f"Progreso: {progress_percent:.1f}% • Faltan {points_remaining:.2f} pts"

        if remaining_levels == 0:
            self.levels_remaining_text.value = "Estás en el nivel máximo"
        elif remaining_levels == 1:
            self.levels_remaining_text.value = "Falta 1 nivel para el máximo"
        else:
            self.levels_remaining_text.value = f"Faltan {remaining_levels} niveles para el máximo"

        if self.page:
            try:
                self.update()
            except Exception as e:
                print(f"[RewardsView] Error actualizando progreso: {e}")
    
    async def refresh_from_progress_service(self):
        """Actualiza los puntos y nivel desde el ProgressService"""
        stats = await self.progress_service.load_stats()
        self.set_user_points(stats.get("points", 0.0))
        self.set_user_level(stats.get("level", "Nadie"))
        self.update_progress_from_stats(stats)
        await self._load_completed_tasks_count()
        print(f"[RewardsView] Stats cargados desde ProgressService")
    
    def update_points_display(self, points: float):
        """Actualiza la visualización de puntos"""
        self.set_user_points(points)

    async def _load_completed_tasks_count(self):
        """Carga desde BD cuántas tareas se completaron y actualiza el header"""
        try:
            if self.database_service is None:
                self.database_service = DatabaseService()
                await self.database_service.initialize()

            count = await self.database_service.count(
                table_name="tasks",
                filters={"status": TASK_STATUS_COMPLETED, "user_id": self.user_id},
            )
            self.set_tasks_completed(count)
        except Exception as e:
            print(f"[RewardsView] Error cargando tareas completadas: {e}")
