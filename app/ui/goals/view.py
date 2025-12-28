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
    
    def __init__(self, page: ft.Page, goal_service: GoalService):
        """
        Inicializa la vista de metas.
        
        Args:
            page: Página de Flet.
            goal_service: Servicio de metas.
        """
        self.page = page
        self.goal_service = goal_service
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
        title_bar = ft.Container(
            content=ft.Row(
                [
                    ft.Text(
                        "🎯 Mis Metas",
                        size=24,
                        weight=ft.FontWeight.BOLD
                    ),
                    ft.IconButton(
                        icon=ft.Icons.ADD,
                        on_click=self._open_goal_form,
                        tooltip="Agregar meta"
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
        """Carga las metas desde el servicio."""
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
            for goal in goals:
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
        
        # Barra de progreso
        progress_bar = ft.ProgressBar(
            value=progress_percentage / 100 if goal.target_value else 0,
            color=ft.Colors.GREEN,
            bgcolor=ft.Colors.GREY_300
        )
        
        # Botones de acción
        edit_button = ft.IconButton(
            icon=ft.Icons.EDIT,
            on_click=lambda e, g=goal: self._open_goal_form(g),
            tooltip="Editar"
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
                                ft.Text(
                                    goal.title,
                                    size=16,
                                    weight=ft.FontWeight.BOLD,
                                    expand=True
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
        """Abre el formulario de meta."""
        GoalForm(self.page, self.goal_service, goal, self._load_goals, self.points_service)

