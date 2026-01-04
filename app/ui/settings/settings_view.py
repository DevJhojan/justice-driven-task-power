"""
Vista de Configuración (Settings) de la aplicación
"""

import flet as ft


class SettingsView:
    """Clase que representa la vista de configuración"""
    
    def __init__(self):
        """Inicializa la vista de configuración"""
        pass
    
    def build(self) -> ft.Container:
        """
        Construye y retorna el widget principal de la vista
        
        Returns:
            Container con el contenido de la vista de configuración
        """
        # Datos de los niveles
        levels_data = [
            ("👤 Nadie", "0.00", "Inexistente, sin relevancia."),
            ("🕳️ Olvidado", "50.00", "Apenas reconocido, casi invisible."),
            ("🌱 Novato", "100.00", "Empieza a dar sus primeros pasos."),
            ("📘 Aprendiz", "500.00", "Adquiere habilidades y cierta notoriedad."),
            ("👀 Conocido", "1000.00", "Ya se habla de él en su entorno."),
            ("🛡️ Respetado", "5000.00", "Gana prestigio y autoridad."),
            ("📣 Influyente", "10000.00", "Sus acciones afectan a muchos."),
            ("🧙 Maestro", "50000.00", "Domina su campo, inspira a otros."),
            ("🗡️ Legendario", "100000.00", "Trasciende generaciones, se convierte en mito."),
            ("✨👑 Como Dios", "500000.00", "Nivel supremo, omnipotente."),
        ]
        
        # Crear controles para cada nivel
        level_controls = []
        for level_name, points, description in levels_data:
            level_card = ft.Container(
                bgcolor="#2a2a2a",
                border_radius=8,
                padding=15,
                border=ft.border.all(1, "#3a3a3a"),
                content=ft.Row(
                    spacing=15,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        # Puntos requeridos (columna izquierda)
                        ft.Container(
                            width=100,
                            content=ft.Column(
                                spacing=2,
                                controls=[
                                    ft.Text(f"{points}", size=16, weight="bold", color="#4CAF50"),
                                    ft.Text("puntos", size=11, color="#AAA"),
                                ],
                            ),
                        ),
                        # Separador
                        ft.VerticalDivider(width=1, color="#3a3a3a"),
                        # Nombre y descripción (columna central/derecha)
                        ft.Column(
                            spacing=5,
                            expand=True,
                            controls=[
                                ft.Text(level_name, size=14, weight="bold", color="#FFD700"),
                                ft.Text(description, size=12, color="#CCCCCC"),
                            ],
                        ),
                    ],
                ),
            )
            level_controls.append(level_card)
        
        # Panel principal de niveles
        levels_panel = ft.Container(
            bgcolor="#1a1a1a",
            border_radius=12,
            padding=20,
            border=ft.border.all(1, "#3a3a3a"),
            content=ft.Column(
                spacing=15,
                controls=[
                    ft.Column(
                        spacing=5,
                        controls=[
                            ft.Text("🌟 Sistema de Niveles", size=24, weight="bold", color="#FFD700"),
                            ft.Text("De \"Nadie\" a \"Como Dios\"", size=14, color="#AAAAAA"),
                        ],
                    ),
                    ft.Divider(height=1, color="#3a3a3a"),
                    ft.Column(
                        spacing=10,
                        controls=level_controls,
                    ),
                    ft.Divider(height=1, color="#3a3a3a"),
                    ft.Container(
                        padding=10,
                        bgcolor="#1f1f1f",
                        border_radius=8,
                        content=ft.Column(
                            spacing=8,
                            controls=[
                                ft.Text("📝 Información del Sistema", size=13, weight="bold", color="#4CAF50"),
                                ft.Text(
                                    "Completa tareas y subtareas para ganar puntos. "
                                    "Cada tarea completada te otorga 0.05 puntos y cada subtarea 0.02 puntos. "
                                    "Acumula puntos para avanzar de nivel y desbloquear logros.",
                                    size=12,
                                    color="#CCCCCC",
                                ),
                            ],
                        ),
                    ),
                ],
            ),
        )
        
        return ft.Container(
            content=ft.Column(
                controls=[
                    levels_panel,
                ],
                spacing=20,
                scroll=ft.ScrollMode.AUTO,
            ),
            padding=20,
            expand=True,
            bgcolor="#0d0d0d",
        )

