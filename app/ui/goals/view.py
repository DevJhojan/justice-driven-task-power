"""
Vista principal de metas.
"""
import flet as ft
from typing import Optional

from app.data.models import Goal
from app.services.goal_service import GoalService
from app.ui.goals.form import GoalForm


class GoalsView:
    """Vista para gestión de metas."""
    
    def __init__(self, page: ft.Page, goal_service: GoalService, points_service=None):
        """
        Inicializa la vista de metas.
        
        Args:
            page: Página de Flet.
            goal_service: Servicio de metas.
            points_service: Servicio de puntos (opcional).
        """
        self.page = page
        self.goal_service = goal_service
        self.points_service = points_service
        self.goals_container = None
    
    def build_ui(self) -> ft.Container:
        """
        Construye la interfaz de usuario de metas.
        
        Returns:
            Container con la vista de metas.
        """
        # Contenedor para las metas
        self.goals_container = ft.Column(
            [],
            spacing=8,
            scroll=ft.ScrollMode.AUTO,
            expand=True
        )
        
        # Barra de título
        is_dark = self.page.theme_mode == ft.ThemeMode.DARK
        title_color = ft.Colors.RED_700 if not is_dark else ft.Colors.RED_500
        btn_color = ft.Colors.RED_700 if not is_dark else ft.Colors.RED_600
        
        title_bar = ft.Container(
            content=ft.Row(
                [
                    ft.Text(
                        "🎯 Mis Metas",
                        size=24,
                        weight=ft.FontWeight.BOLD,
                        color=title_color
                    ),
                    ft.IconButton(
                        icon=ft.Icons.ADD,
                        on_click=self._open_goal_form,
                        tooltip="Agregar meta",
                        icon_color=btn_color
                    )
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN
            ),
            padding=16,
            bgcolor=ft.Colors.SURFACE
        )
        
        # Cargar metas
        self._load_goals()
        
        # Vista principal
        return ft.Container(
            content=ft.Column(
                [
                    title_bar,
                    ft.Container(
                        content=self.goals_container,
                        padding=16,
                        expand=True
                    )
                ],
                spacing=0,
                expand=True
            ),
            expand=True
        )
    
    def _load_goals(self):
        """Carga las metas desde el servicio agrupadas por período."""
        if self.goals_container is None:
            return
        
        goals = self.goal_service.get_all_goals()
        self.goals_container.controls.clear()
        
        if not goals:
            self.goals_container.controls.append(
                ft.Container(
                    content=ft.Text(
                        "No hay metas. ¡Crea una nueva!",
                        size=16,
                        text_align=ft.TextAlign.CENTER
                    ),
                    alignment=ft.alignment.center,
                    padding=32
                )
            )
        else:
            # Agrupar metas por período
            period_order = ["semana", "mes", "trimestre", "semestre", "anual"]
            period_names = {
                "semana": "📅 Semanales",
                "mes": "📆 Mensuales",
                "trimestre": "📊 Trimestrales",
                "semestre": "📈 Semestrales",
                "anual": "🎯 Anuales"
            }
            
            goals_by_period = {}
            for goal in goals:
                period = goal.period or "mes"
                if period not in goals_by_period:
                    goals_by_period[period] = []
                goals_by_period[period].append(goal)
            
            # Mostrar metas agrupadas por período
            is_dark = self.page.theme_mode == ft.ThemeMode.DARK
            title_color = ft.Colors.RED_700 if not is_dark else ft.Colors.RED_500
            
            for period in period_order:
                if period in goals_by_period:
                    # Título del período
                    self.goals_container.controls.append(
                        ft.Container(
                            content=ft.Text(
                                period_names[period],
                                size=18,
                                weight=ft.FontWeight.BOLD,
                                color=title_color
                            ),
                            padding=ft.padding.only(top=16, bottom=8, left=16, right=16)
                        )
                    )
                    
                    # Metas de este período
                    for goal in goals_by_period[period]:
                        self.goals_container.controls.append(
                            self._build_goal_card(goal)
                        )
        
        if self.page:
            self.page.update()
    
    def _build_goal_card(self, goal: Goal) -> ft.Container:
        """
        Construye una tarjeta para una meta.
        
        Args:
            goal: Meta a mostrar.
        
        Returns:
            Container con la tarjeta de la meta.
        """
        # Calcular progreso
        progress_percentage = self.goal_service.get_progress_percentage(goal.id)
        
        # Información de progreso
        if goal.target_value:
            progress_text = f"{goal.current_value:.1f} / {goal.target_value:.1f}"
            if goal.unit:
                progress_text += f" {goal.unit}"
            progress_text += f" ({progress_percentage:.1f}%)"
        else:
            progress_text = f"{goal.current_value:.1f}"
            if goal.unit:
                progress_text += f" {goal.unit}"
        
        # Mostrar período en la tarjeta
        period_names = {
            "semana": "Semanal",
            "mes": "Mensual",
            "trimestre": "Trimestral",
            "semestre": "Semestral",
            "anual": "Anual"
        }
        period_display = period_names.get(goal.period or "mes", "Mensual")
        
        # Barra de progreso
        progress_bar = ft.ProgressBar(
            value=progress_percentage / 100 if goal.target_value else 0,
            color=ft.Colors.GREEN,
            bgcolor=ft.Colors.GREY_300
        )
        
        # Botones de acción
        is_dark = self.page.theme_mode == ft.ThemeMode.DARK
        btn_color = ft.Colors.RED_700 if not is_dark else ft.Colors.RED_500
        
        edit_button = ft.IconButton(
            icon=ft.Icons.EDIT,
            on_click=lambda e, g=goal: self._open_goal_form(g),
            tooltip="Editar",
            icon_color=btn_color
        )
        
        delete_button = ft.IconButton(
            icon=ft.Icons.DELETE,
            on_click=lambda e, g=goal: self._delete_goal(g),
            tooltip="Eliminar",
            icon_color=ft.Colors.RED
        )
        
        # Contenido de la tarjeta
        content = ft.Column(
            [
                ft.Row(
                    [
                        ft.Column(
                            [
                                ft.Row(
                                    [
                                        ft.Text(
                                            goal.title,
                                            size=16,
                                            weight=ft.FontWeight.BOLD,
                                            color=ft.Colors.RED_800 if self.page.theme_mode == ft.ThemeMode.LIGHT else ft.Colors.RED_400,
                                            expand=True
                                        ),
                                        ft.Container(
                                            content=ft.Text(
                                                period_display,
                                                size=11,
                                                color=ft.Colors.RED_700 if self.page.theme_mode == ft.ThemeMode.LIGHT else ft.Colors.RED_400,
                                                weight=ft.FontWeight.W_500
                                            ),
                                            padding=ft.padding.symmetric(horizontal=8, vertical=4),
                                            bgcolor=ft.Colors.SURFACE if self.page.theme_mode == ft.ThemeMode.DARK else ft.Colors.GREY_100,
                                            border_radius=12
                                        )
                                    ],
                                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                                ),
                                ft.Text(
                                    goal.description or "",
                                    size=12,
                                    color=ft.Colors.GREY,
                                    visible=bool(goal.description)
                                ),
                                ft.Text(
                                    progress_text,
                                    size=12,
                                    color=ft.Colors.GREY_700
                                ),
                                progress_bar if goal.target_value else ft.Container(height=0)
                            ],
                            spacing=4,
                            expand=True
                        ),
                        edit_button,
                        delete_button
                    ],
                    spacing=8,
                    vertical_alignment=ft.CrossAxisAlignment.START
                )
            ],
            spacing=4
        )
        
        is_dark = self.page.theme_mode == ft.ThemeMode.DARK
        bg_color = ft.Colors.SURFACE if is_dark else ft.Colors.WHITE
        
        return ft.Container(
            content=content,
            padding=16,
            bgcolor=bg_color,
            border_radius=8,
            border=ft.border.all(1, ft.Colors.OUTLINE)
        )
    
    def _delete_goal(self, goal: Goal):
        """Elimina una meta."""
        def confirm_delete(e):
            self.goal_service.delete_goal(goal.id)
            self._load_goals()
            self.page.close_dialog()
        
        self.page.dialog = ft.AlertDialog(
            title=ft.Text("Confirmar eliminación"),
            content=ft.Text(f"¿Estás seguro de que quieres eliminar la meta '{goal.title}'?"),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: self.page.close_dialog()),
                ft.TextButton("Eliminar", on_click=confirm_delete, style=ft.ButtonStyle(color=ft.Colors.RED))
            ]
        )
        self.page.dialog.open = True
        self.page.update()
    
    def _open_goal_form(self, e=None, goal: Optional[Goal] = None):
        """Abre el formulario de meta en una nueva vista."""
        route = f"/goal-form?id={goal.id}" if goal and goal.id else "/goal-form"
        self.page.go(route)

