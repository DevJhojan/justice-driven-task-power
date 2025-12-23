"""
Vista principal de hábitos - Orquesta todos los módulos.
"""
import flet as ft
from typing import Optional
from app.data.models import Habit
from app.services.habit_service import HabitService
from app.ui.widgets import create_habit_statistics_card

from .utils import get_screen_width, is_desktop_platform
from .habit_management import (
    load_habits_into_container,
    toggle_habit_completion,
    delete_habit as delete_habit_func,
    save_habit
)
from .forms import navigate_to_habit_form, navigate_to_habit_details


class HabitsView:
    """Vista dedicada para gestionar hábitos."""
    
    def __init__(self, page: ft.Page, habit_service: HabitService, on_go_back: callable):
        """
        Inicializa la vista de hábitos.
        
        Args:
            page: Página de Flet.
            habit_service: Servicio para gestionar hábitos.
            on_go_back: Callback para volver a la vista anterior.
        """
        self.page = page
        self.habit_service = habit_service
        self.on_go_back = on_go_back
        
        self.current_habit_filter: Optional[bool] = None  # None=all, True=active, False=inactive
        self.editing_habit: Optional[Habit] = None
        self.habits_container = ft.Column([], spacing=0, scroll=ft.ScrollMode.AUTO, expand=True)
        self.habit_stats_container = None
        self.new_habit_button = None
    
    def build_ui(self, title_bar, bottom_bar, home_view) -> ft.Container:
        """
        Construye la interfaz de usuario de hábitos.
        
        Args:
            title_bar: Barra de título de la vista principal.
            bottom_bar: Barra inferior de navegación.
            home_view: Vista principal para actualizar.
        
        Returns:
            Container con la vista completa de hábitos.
        """
        is_dark = self.page.theme_mode == ft.ThemeMode.DARK
        bgcolor = ft.Colors.BLACK if is_dark else ft.Colors.GREY_50

        scheme = self.page.theme.color_scheme if self.page.theme else None
        primary = scheme.primary if scheme and scheme.primary else ft.Colors.RED_700
        secondary = scheme.secondary if scheme and scheme.secondary else ft.Colors.RED_600
        
        # Botón para agregar nuevo hábito - color adaptativo
        new_habit_button_bg = primary
        
        # Botón "+" para agregar hábito
        self.new_habit_button = ft.IconButton(
            icon=ft.Icons.ADD,
            on_click=self._show_new_habit_form,
            bgcolor=new_habit_button_bg,
            icon_color=ft.Colors.WHITE,
            tooltip="Nuevo Hábito",
            width=40,
            height=40
        )
        
        # Filtros para hábitos (Activos/Inactivos/Todos)
        active_bg = primary
        inactive_bg = ft.Colors.GREY_800 if is_dark else ft.Colors.GREY_100
        text_color = ft.Colors.WHITE
        
        # Contenedor de estadísticas de hábitos
        habit_stats_container = ft.Container(
            content=create_habit_statistics_card(self.habit_service.get_statistics(), self.page),
            visible=True
        )
        self.habit_stats_container = habit_stats_container
        
        # Filtros de hábitos
        habit_filter_row = ft.Row(
            [
                ft.ElevatedButton(
                    text="Todos",
                    on_click=lambda e: self._filter_habits(None),
                    bgcolor=active_bg if self.current_habit_filter is None else inactive_bg,
                    color=text_color,
                    height=40
                ),
                ft.ElevatedButton(
                    text="Activos",
                    on_click=lambda e: self._filter_habits(True),
                    bgcolor=active_bg if self.current_habit_filter is True else inactive_bg,
                    color=text_color,
                    height=40
                ),
                ft.ElevatedButton(
                    text="Inactivos",
                    on_click=lambda e: self._filter_habits(False),
                    bgcolor=active_bg if self.current_habit_filter is False else inactive_bg,
                    color=text_color,
                    height=40
                ),
                self.new_habit_button
            ],
            spacing=8,
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER
        )
        
        # Vista principal (lista de hábitos)
        return ft.Container(
            content=ft.Column(
                [
                    habit_stats_container,
                    habit_filter_row,
                    self.habits_container
                ],
                spacing=8,
                expand=True
            ),
            padding=16,
            expand=True
        )
    
    def load_habits(self):
        """Carga los hábitos desde la base de datos."""
        load_habits_into_container(
            self.page,
            self.habit_service,
            self.habits_container,
            self.habit_stats_container,
            self.current_habit_filter,
            self._toggle_habit_completion,
            self._edit_habit,
            self._delete_habit,
            self._view_habit_details
        )
    
    def _filter_habits(self, filter_active: Optional[bool]):
        """Filtra los hábitos por estado activo/inactivo."""
        self.current_habit_filter = filter_active
        self.load_habits()
        # Actualizar colores de los botones de filtro
        self._update_habit_filters()
    
    def _update_habit_filters(self):
        """Actualiza los colores de los botones de filtro de hábitos."""
        is_dark = self.page.theme_mode == ft.ThemeMode.DARK
        scheme = self.page.theme.color_scheme if self.page.theme else None
        primary = scheme.primary if scheme and scheme.primary else ft.Colors.RED_700
        active_bg = primary
        inactive_bg = ft.Colors.GREY_800 if is_dark else ft.Colors.GREY_100
        text_color = ft.Colors.WHITE
        
        # Los botones se actualizan automáticamente cuando se reconstruye la UI
        # Esta función se mantiene para compatibilidad pero la actualización real
        # se hace en build_ui cuando se reconstruye la vista
        pass
    
    def _show_new_habit_form(self, e):
        """Navega a la vista del formulario para crear un nuevo hábito."""
        self.editing_habit = None
        self._navigate_to_habit_form_view()
    
    def _edit_habit(self, habit: Habit):
        """Navega a la vista del formulario para editar un hábito."""
        self.editing_habit = habit
        self._navigate_to_habit_form_view()
    
    def _navigate_to_habit_form_view(self):
        """Navega a la vista del formulario de hábito."""
        navigate_to_habit_form(
            self.page,
            self.editing_habit,
            self._save_habit,
            self._go_back_from_form
        )
    
    def _go_back_from_form(self, e=None):
        """Vuelve a la vista principal desde un formulario."""
        self.editing_habit = None
        # Usar el callback proporcionado
        if self.on_go_back:
            self.on_go_back(e)
        else:
            # Fallback si no hay callback
            if len(self.page.views) > 1:
                self.page.views.pop()
            if self.page.views:
                self.page.go(self.page.views[-1].route)
            else:
                self.page.go("/")
            self.page.update()
    
    def _save_habit(self, *args):
        """Guarda un hábito (crear o actualizar)."""
        save_habit(self.habit_service, *args)
        
        # Volver a la vista principal
        self._go_back_from_form()
        
        # Forzar actualización de la página antes de recargar hábitos
        self.page.update()
        
        # Recargar los hábitos después de volver
        self.load_habits()
    
    def _toggle_habit_completion(self, habit_id: int):
        """Alterna el cumplimiento de un hábito para hoy."""
        toggle_habit_completion(self.page, self.habit_service, habit_id)
        self.load_habits()
    
    def _delete_habit(self, habit_id: int):
        """Elimina un hábito."""
        deleted = delete_habit_func(self.page, self.habit_service, habit_id)
        if deleted:
            self.load_habits()
    
    def _view_habit_details(self, habit: Habit):
        """Muestra la vista de detalles de un hábito con historial y métricas."""
        navigate_to_habit_details(
            self.page,
            self.habit_service,
            habit,
            self._go_back
        )
    
    def _go_back(self, e=None):
        """Vuelve a la vista anterior."""
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

