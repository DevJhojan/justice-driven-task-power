"""
Vista principal de objetivos.
"""
import flet as ft
from typing import Optional
from app.data.models import Goal
from app.services.goal_service import GoalService
from .goal_management import (
    load_goals_into_container,
    toggle_goal,
    delete_goal as delete_goal_func,
    save_goal
)
from .forms import navigate_to_goal_form


class GoalsView:
    """Vista dedicada para gestionar objetivos."""
    
    def __init__(self, page: ft.Page, goal_service: GoalService, on_go_back: callable):
        """
        Inicializa la vista de objetivos.
        
        Args:
            page: Página de Flet.
            goal_service: Servicio para gestionar objetivos.
            on_go_back: Callback para volver a la vista anterior.
        """
        self.page = page
        self.goal_service = goal_service
        self.on_go_back = on_go_back
        
        self.current_frequency_filter: Optional[str] = None  # None=all, o una frecuencia específica
        self.editing_goal: Optional[Goal] = None
        self.goals_container = ft.Column([], spacing=0, scroll=ft.ScrollMode.AUTO, expand=True)
        self.filter_buttons: dict = {}  # Referencias a los botones de filtro
    
    def build_ui(self, title_bar=None, bottom_bar=None, home_view=None) -> ft.Container:
        """
        Construye la interfaz de usuario de objetivos.
        
        Args:
            title_bar: Barra de título de la vista principal (no se usa actualmente).
            bottom_bar: Barra inferior de navegación (no se usa actualmente).
            home_view: Vista principal para actualizar (no se usa actualmente).
        
        Returns:
            Container con la vista completa de objetivos.
        """
        is_dark = self.page.theme_mode == ft.ThemeMode.DARK
        bgcolor = ft.Colors.BLACK if is_dark else ft.Colors.GREY_50
        
        scheme = self.page.theme.color_scheme if self.page.theme else None
        primary = scheme.primary if scheme and scheme.primary else ft.Colors.RED_700
        
        # Botón "+" para agregar objetivo
        new_goal_button = ft.IconButton(
            icon=ft.Icons.ADD,
            on_click=self._show_new_goal_form,
            bgcolor=primary,
            icon_color=ft.Colors.WHITE,
            tooltip="Nuevo Objetivo",
            width=40,
            height=40
        )
        
        # Filtros de frecuencia
        active_bg = primary
        inactive_bg = ft.Colors.GREY_800 if is_dark else ft.Colors.GREY_100
        text_color = ft.Colors.WHITE
        
        frequency_labels = {
            None: "Todos",
            'daily': 'Diario',
            'weekly': 'Semanal',
            'monthly': 'Mensual',
            'quarterly': 'Trimestral',
            'semiannual': 'Semestral',
            'annual': 'Anual'
        }
        
        # Botones de filtro
        filter_buttons_list = []
        self.filter_buttons = {}  # Resetear referencias
        for freq, label in frequency_labels.items():
            button = ft.ElevatedButton(
                text=label,
                on_click=lambda e, f=freq: self._filter_goals(f),
                bgcolor=active_bg if self.current_frequency_filter == freq else inactive_bg,
                color=text_color,
                height=36,
                style=ft.ButtonStyle(
                    shape=ft.RoundedRectangleBorder(radius=8)
                )
            )
            filter_buttons_list.append(button)
            self.filter_buttons[freq] = button  # Guardar referencia
        
        filter_row = ft.Row(
            filter_buttons_list,
            spacing=8,
            scroll=ft.ScrollMode.AUTO,
            wrap=True
        )
        
        # Vista principal
        main_content = ft.Container(
            content=ft.Column(
                [
                    ft.Container(
                        content=ft.Row(
                            [
                                ft.Text(
                                    "Filtros",
                                    size=16,
                                    weight=ft.FontWeight.BOLD,
                                    color=primary
                                ),
                                new_goal_button
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                        ),
                        padding=16
                    ),
                    ft.Container(
                        content=filter_row,
                        padding=ft.padding.symmetric(horizontal=16, vertical=8)
                    ),
                    ft.Container(
                        content=self.goals_container,
                        padding=16,
                        expand=True
                    )
                ],
                spacing=0,
                expand=True
            ),
            expand=True,
            bgcolor=bgcolor
        )
        
        return main_content
    
    def load_goals(self):
        """Carga los objetivos desde la base de datos."""
        load_goals_into_container(
            self.page,
            self.goal_service,
            self.goals_container,
            self.current_frequency_filter,
            self._toggle_goal,
            self._edit_goal,
            self._delete_goal
        )
    
    def _filter_goals(self, frequency: Optional[str]):
        """Filtra los objetivos por frecuencia."""
        self.current_frequency_filter = frequency
        self._update_filter_button_colors()
        self.load_goals()
    
    def _update_filter_button_colors(self):
        """Actualiza los colores de los botones de filtro según el filtro activo."""
        is_dark = self.page.theme_mode == ft.ThemeMode.DARK
        scheme = self.page.theme.color_scheme if self.page.theme else None
        primary = scheme.primary if scheme and scheme.primary else ft.Colors.RED_700
        active_bg = primary
        inactive_bg = ft.Colors.GREY_800 if is_dark else ft.Colors.GREY_100
        
        # Actualizar colores de todos los botones
        for freq, button in self.filter_buttons.items():
            if button:
                button.bgcolor = active_bg if self.current_frequency_filter == freq else inactive_bg
        
        # Actualizar la página para reflejar los cambios
        self.page.update()
    
    def _show_new_goal_form(self, e):
        """Navega a la vista del formulario para crear un nuevo objetivo."""
        self.editing_goal = None
        self._navigate_to_goal_form_view()
    
    def _edit_goal(self, goal: Goal):
        """Navega a la vista del formulario para editar un objetivo."""
        self.editing_goal = goal
        self._navigate_to_goal_form_view()
    
    def _navigate_to_goal_form_view(self):
        """Navega a la vista del formulario."""
        navigate_to_goal_form(
            self.page,
            self.editing_goal,
            self._save_goal,
            self._go_back_from_form
        )
    
    def _go_back_from_form(self, e=None):
        """Vuelve a la vista principal desde un formulario."""
        self.editing_goal = None
        if self.on_go_back:
            self.on_go_back(e)
        else:
            if len(self.page.views) > 1:
                self.page.views.pop()
            if self.page.views:
                self.page.go(self.page.views[-1].route)
            else:
                self.page.go("/")
            self.page.update()
    
    def _save_goal(self, *args):
        """Guarda un objetivo (crear o actualizar)."""
        save_goal(self.goal_service, *args)
        
        # Volver a la vista principal
        self._go_back_from_form()
        
        # Forzar actualización de la página antes de recargar objetivos
        self.page.update()
        
        # Recargar los objetivos después de volver
        self.load_goals()
    
    def _toggle_goal(self, goal_id: int):
        """Cambia el estado de completado de un objetivo."""
        toggle_goal(self.goal_service, goal_id)
        self.load_goals()
    
    def _delete_goal(self, goal_id: int):
        """Elimina un objetivo."""
        deleted = delete_goal_func(self.page, self.goal_service, goal_id)
        if deleted:
            self.load_goals()

