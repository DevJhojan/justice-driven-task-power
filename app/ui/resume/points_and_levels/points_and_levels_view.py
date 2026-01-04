"""
Vista de Puntos y Niveles (Points and Levels View)
Interfaz para mostrar nivel, puntos y progreso del usuario
"""

import flet as ft
from typing import Optional
from app.services.progress_service import ProgressService
from app.services.database_service import DatabaseService
from app.logic.system_points import LEVELS_ORDER, Level
from app.utils.task_helper import TASK_STATUS_COMPLETED


class PointsAndLevelsView(ft.Container):
    """Vista principal de puntos y niveles con paneles de información"""
    
    def __init__(self, progress_service: Optional[ProgressService] = None, user_id: str = "default_user", on_verify_integrity = None):
        super().__init__()
        
        self.progress_service = progress_service if progress_service else ProgressService()
        self.user_id = user_id
        self.on_verify_integrity = on_verify_integrity  # Callback para verificar integridad
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
        
        # Mapeo de niveles a iconos
        self.level_icons = {
            "Nadie": "👤",
            "Olvidado": "🕳️",
            "Novato": "🌱",
            "Aprendiz": "📘",
            "Conocido": "👀",
            "Respetado": "🛡️",
            "Influyente": "📣",
            "Maestro": "🧙",
            "Legendario": "🗡️",
            "Como Dios": "✨👑",
        }
        
        # Mapeo de niveles a descripciones
        self.level_descriptions = {
            "Nadie": "Inexistente, sin relevancia.",
            "Olvidado": "Apenas reconocido, casi invisible.",
            "Novato": "Empieza a dar sus primeros pasos.",
            "Aprendiz": "Adquiere habilidades y cierta notoriedad.",
            "Conocido": "Ya se habla de él en su entorno.",
            "Respetado": "Gana prestigio y autoridad.",
            "Influyente": "Sus acciones afectan a muchos.",
            "Maestro": "Domina su campo, inspira a otros.",
            "Legendario": "Trasciende generaciones, se convierte en mito.",
            "Como Dios": "Nivel supremo, omnipotente.",
        }
        
        # Header delgado con nivel y puntos
        self.level_icon = ft.Text("👤", size=32)
        self.level_text = ft.Text("Nadie", size=32, weight="bold", color="#FFD700")
        self.points_text = ft.Text("0.00", size=24, weight="bold", color="#4CAF50")
        self.tasks_completed_text = ft.Text("0 tareas completadas", size=14, color="#CCCCCC")
        self.habits_completed_text = ft.Text("0 hábitos completados", size=14, color="#CCCCCC")
        self.missions_completed_text = ft.Text("0 misiones completadas", size=14, color="#CCCCCC")
        
        # Botón de verificación de integridad
        self.verify_button = ft.IconButton(
            icon=ft.Icons.REFRESH,
            icon_size=20,
            tooltip="Verificar y corregir integridad de puntos",
            icon_color="#4CAF50",
            on_click=self._on_verify_integrity_click,
        )
        
        # Elementos de la barra de progreso
        self.progress_title = ft.Text("Progreso al siguiente nivel", size=18, weight="bold", color="#FFF", text_align=ft.TextAlign.CENTER)
        self.next_level_text = ft.Text("Siguiente nivel: --", size=14, color="#DDD", text_align=ft.TextAlign.CENTER)
        self.progress_detail_text = ft.Text("Faltan 0.00 pts", size=12, color="#AAA", text_align=ft.TextAlign.CENTER)
        self.levels_remaining_text = ft.Text(
            "Faltan 0 niveles para el máximo",
            size=13,
            color="#E0E0E0",
            weight="w600",
            text_align=ft.TextAlign.CENTER,
        )
        
        # Textos de puntos para la barra de progreso
        self.progress_current_points = ft.Text("0.00", size=11, color="#AAA")
        self.progress_total_points = ft.Text("0.00", size=11, color="#AAA")
        
        self.progress_bar = ft.ProgressBar(value=0.0, bgcolor="#222222", color="#F44336", height=16, bar_height=16, width=280, expand=True)
        
        # Row con solo la barra de progreso
        self.progress_bar_row = ft.Row(
            alignment=ft.MainAxisAlignment.CENTER,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=10,
            controls=[
                self.progress_bar,
            ],
        )
        
        # Row con los puntos debajo de la barra
        self.progress_points_row = ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                self.progress_current_points,
                self.progress_total_points,
            ],
        )
        
        self.header_stats = ft.Container(
            bgcolor="#2a2a2a",
            border_radius=10,
            padding=ft.padding.symmetric(horizontal=20, vertical=15),
            border=ft.border.all(1, "#3a3a3a"),
            expand=True,
            content=ft.Column(
                spacing=15,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    # Primera fila: Nivel | Barra de progreso | Botón actualizar
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            self.level_text,
                            ft.Column(
                                spacing=5,
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                expand=True,
                                controls=[
                                    self.next_level_text,
                                    self.progress_bar_row,
                                    self.progress_points_row,
                                ],
                            ),
                            self.verify_button,
                        ],
                    ),
                    ft.Divider(height=1, color="#3a3a3a"),
                    # Segunda fila: Puntos | Mensaje de puntos faltantes
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            self.points_text,
                            self.levels_remaining_text,
                        ],
                    ),
                    ft.Divider(height=1, color="#3a3a3a"),
                    # Tercera fila: Tareas | Hábitos | Misiones
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_AROUND,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            self.tasks_completed_text,
                            self.habits_completed_text,
                            self.missions_completed_text,
                        ],
                    ),
                ],
            ),
        )
        
        # Panel de verificación de integridad (inicialmente oculto)
        self.integrity_log_text = ft.Column(spacing=5, scroll=ft.ScrollMode.AUTO)
        self.integrity_panel = ft.Container(
            visible=False,
            bgcolor="#1f1f1f",
            border_radius=10,
            padding=15,
            border=ft.border.all(1, "#4CAF50"),
            content=ft.Column(
                spacing=10,
                controls=[
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Text("🔍 Verificación de Integridad", size=16, weight="bold", color="#4CAF50"),
                            ft.IconButton(
                                icon=ft.Icons.CLOSE,
                                icon_size=18,
                                tooltip="Cerrar",
                                on_click=self._close_integrity_panel,
                            ),
                        ],
                    ),
                    ft.Divider(height=1, color="#3a3a3a"),
                    self.integrity_log_text,
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
                # Header de nivel/puntos con barra de progreso
                self.header_stats,
                
                # Panel de verificación de integridad (debajo del header)
                self.integrity_panel,
                
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
        print(f"[PointsAndLevelsView] Actualizando puntos a: {self.points_text.value}")
        if self.page:
            try:
                self.update()
            except Exception as e:
                print(f"[PointsAndLevelsView] Error actualizando UI: {e}")
    
    def set_user_level(self, level: str):
        """Establece el nivel del usuario"""
        self.current_user_level = level
        self.level_text.value = level
        print(f"[PointsAndLevelsView] Actualizando nivel a: {level}")
        if self.page:
            try:
                self.update()
            except Exception as e:
                print(f"[PointsAndLevelsView] Error actualizando UI: {e}")

    def set_tasks_completed(self, count: int):
        """Actualiza el contador de tareas completadas"""
        self.tasks_completed_text.value = f"{int(count)} tareas completadas"
        if self.page:
            try:
                self.update()
            except Exception as e:
                print(f"[PointsAndLevelsView] Error actualizando tareas completadas: {e}")

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
        
        # Actualizar los textos de puntos en los extremos de la barra
        self.progress_current_points.value = f"{points_in_current:.2f}"
        self.progress_total_points.value = f"{total_for_next:.2f}"
        
        if total_for_next == 0:
            self.progress_detail_text.value = "Ya alcanzaste el nivel máximo"
        else:
            self.progress_detail_text.value = f"Progreso: {progress_percent:.1f}% • Faltan {points_remaining:.2f} pts"

        # Mostrar puntos faltantes hacia el siguiente nivel
        if total_for_next == 0:
            self.levels_remaining_text.value = "Estás en el nivel máximo"
        else:
            self.levels_remaining_text.value = f"Faltan {points_remaining:.2f} para el nivel {next_level}"

        if self.page:
            try:
                self.update()
            except Exception as e:
                print(f"[PointsAndLevelsView] Error actualizando progreso: {e}")
    
    async def refresh_from_progress_service(self):
        """Actualiza los puntos y nivel desde el ProgressService"""
        stats = await self.progress_service.load_stats()
        self.set_user_points(stats.get("points", 0.0))
        self.set_user_level(stats.get("level", "Nadie"))
        self.update_progress_from_stats(stats)
        await self._load_completed_tasks_count()
        print(f"[PointsAndLevelsView] Stats cargados desde ProgressService")
    
    def _on_verify_integrity_click(self, e):
        """Handler para el botón de verificar integridad"""
        print(f"[PointsAndLevelsView] 🔄 Botón de integridad presionado")
        
        # Limpiar logs anteriores y mostrar indicador de carga
        self.integrity_log_text.controls.clear()
        self.integrity_log_text.controls.append(
            ft.Row(
                controls=[
                    ft.ProgressRing(width=20, height=20, stroke_width=2),
                    ft.Text("Verificando integridad...", size=14, color="#CCCCCC"),
                ]
            )
        )
        self.integrity_log_text.controls.append(
            ft.Text("Panel actualizado exitosamente después de verificación y ya puedes cerrar el panel", size=12, color="#AAAAAA")
        )
        self.integrity_panel.visible = True
        
        if self.page:
            self.page.update()
        
        if self.on_verify_integrity:
            # Ejecutar el callback de verificación de integridad
            if self.page:
                self.page.run_task(self._run_verification_and_update_panel)
        else:
            self.integrity_log_text.controls.clear()
            self.integrity_log_text.controls.append(
                ft.Text("⚠️  No hay callback de verificación configurado", size=13, color="#FF9800")
            )
            if self.page:
                self.page.update()
    
    async def _run_verification_and_update_panel(self):
        """Ejecuta la verificación y actualiza el panel con los resultados"""
        import asyncio
        
        try:
            # Ejecutar la verificación con timeout de 5 segundos
            try:
                result = await asyncio.wait_for(self.on_verify_integrity(), timeout=5.0)
                print(f"[PointsAndLevelsView] Verificación completada. Resultado: {result}")
            except asyncio.TimeoutError:
                print(f"[PointsAndLevelsView] ⚠️ Timeout en verificación (5s), cerrando panel de carga")
                self.integrity_panel.visible = False
                if self.page:
                    self.page.update()
                return
            
            # Pequeño delay para asegurar que show_integrity_result se completó
            await asyncio.sleep(0.3)
            
            # Forzar actualización explícita del panel y del contenedor
            if self.page:
                # Actualizar todos los controles internos
                self.integrity_log_text.update()
                self.integrity_panel.update()
                self.update()
                self.page.update()
                print(f"[PointsAndLevelsView] Panel actualizado exitosamente después de verificación")
                
        except Exception as e:
            print(f"[PointsAndLevelsView] Error ejecutando verificación: {e}")
            import traceback
            traceback.print_exc()
            self.integrity_log_text.controls.clear()
            self.integrity_log_text.controls.append(
                ft.Text(f"❌ Error: {str(e)}", size=13, color="#F44336")
            )
            if self.page:
                self.integrity_log_text.update()
                self.integrity_panel.update()
                self.update()
                self.page.update()
    
    def _close_integrity_panel(self, e):
        """Cierra el panel de verificación de integridad"""
        self.integrity_panel.visible = False
        if self.page:
            self.page.update()
    
    def show_integrity_result(self, current_points, expected_points, completed_tasks, completed_subtasks, had_correction):
        """Muestra el resultado de la verificación en el panel"""
        print(f"[PointsAndLevelsView] Mostrando resultado de integridad en el panel")
        
        self.integrity_log_text.controls.clear()
        
        # Crear los controles visuales
        controls = [
            ft.Text(f"📊 Puntos actuales en BD: {current_points:.2f}", size=13, color="#EEEEEE"),
            ft.Text(f"📋 Tareas completadas: {completed_tasks} × 0.05 = {completed_tasks * 0.05:.2f} puntos", size=13, color="#CCCCCC"),
            ft.Text(f"✓ Subtareas completadas: {completed_subtasks} × 0.02 = {completed_subtasks * 0.02:.2f} puntos", size=13, color="#CCCCCC"),
            ft.Text(f"🎯 Total esperado: {expected_points:.2f} puntos", size=13, color="#4CAF50", weight="bold"),
        ]
        
        difference = abs(current_points - expected_points)
        
        if had_correction:
            controls.extend([
                ft.Divider(height=1, color="#555"),
                ft.Text(f"⚠️  INCONSISTENCIA DETECTADA", size=13, color="#FF9800", weight="bold"),
                ft.Text(f"📉 Diferencia: {difference:.2f} puntos", size=13, color="#FF9800"),
                ft.Text(f"🔧 Puntos corregidos automáticamente", size=13, color="#4CAF50"),
                ft.Text(f"✅ Nuevos puntos: {expected_points:.2f}", size=14, color="#4CAF50", weight="bold"),
            ])
        else:
            controls.extend([
                ft.Divider(height=1, color="#555"),
                ft.Text(f"✅ Integridad verificada correctamente", size=13, color="#4CAF50", weight="bold"),
                ft.Text(f"Los puntos coinciden con las tareas completadas", size=12, color="#AAAAAA"),
            ])
        
        self.integrity_log_text.controls.extend(controls)
        
        print(f"[PointsAndLevelsView] Panel actualizado con {len(controls)} elementos")
        
        # Asegurar que el panel sea visible
        self.integrity_panel.visible = True
        
        # Forzar actualización de la UI
        try:
            if self.page:
                self.update()
                self.page.update()
                print(f"[PointsAndLevelsView] UI actualizada exitosamente")
        except Exception as e:
            print(f"[PointsAndLevelsView] Error actualizando UI: {e}")
    
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
            print(f"[PointsAndLevelsView] Error cargando tareas completadas: {e}")
