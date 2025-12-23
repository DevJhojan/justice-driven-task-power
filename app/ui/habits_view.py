"""
Vista de hábitos - Módulo separado para gestionar todas las funcionalidades de hábitos.
"""
import flet as ft
from typing import Optional
from datetime import date
from app.data.models import Habit
from app.services.habit_service import HabitService
from app.ui.widgets import create_habit_card, create_habit_empty_state, create_habit_statistics_card
from app.ui.habit_form import HabitForm


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
                    bgcolor=active_bg,
                    color=text_color,
                    height=40
                ),
                ft.ElevatedButton(
                    text="Activos",
                    on_click=lambda e: self._filter_habits(True),
                    bgcolor=inactive_bg,
                    color=text_color,
                    height=40
                ),
                ft.ElevatedButton(
                    text="Inactivos",
                    on_click=lambda e: self._filter_habits(False),
                    bgcolor=inactive_bg,
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
        habits = self.habit_service.get_all_habits(self.current_habit_filter)
        
        # Asegurarse de que el contenedor existe
        if not hasattr(self, 'habits_container') or self.habits_container is None:
            return
        
        self.habits_container.controls.clear()
        
        if not habits:
            self.habits_container.controls.append(create_habit_empty_state(self.page))
        else:
            for habit in habits:
                # Obtener métricas del hábito
                metrics = self.habit_service.get_habit_metrics(habit.id)
                
                card = create_habit_card(
                    habit,
                    metrics,
                    on_toggle_completion=self._toggle_habit_completion,
                    on_edit=self._edit_habit,
                    on_delete=self._delete_habit,
                    on_view_details=self._view_habit_details,
                    page=self.page
                )
                self.habits_container.controls.append(card)
        
        # Actualizar estadísticas
        if hasattr(self, 'habit_stats_container') and self.habit_stats_container:
            stats = self.habit_service.get_statistics()
            self.habit_stats_container.content = create_habit_statistics_card(stats, self.page)
            try:
                self.habit_stats_container.update()
            except:
                pass
        
        try:
            self.habits_container.update()
        except:
            pass
        self.page.update()
    
    def _filter_habits(self, filter_active: Optional[bool]):
        """Filtra los hábitos por estado activo/inactivo."""
        self.current_habit_filter = filter_active
        self.load_habits()
        # Actualizar colores de los botones de filtro
        self._update_habit_filters()
    
    def _update_habit_filters(self):
        """Actualiza los colores de los botones de filtro de hábitos."""
        is_dark = self.page.theme_mode == ft.ThemeMode.DARK
        active_bg = ft.Colors.RED_700 if is_dark else ft.Colors.RED_600
        inactive_bg = ft.Colors.GREY_800 if is_dark else ft.Colors.RED_100
        text_color = ft.Colors.WHITE
        
        if hasattr(self, 'habit_filter_all_btn'):
            self.habit_filter_all_btn.bgcolor = active_bg if self.current_habit_filter is None else inactive_bg
            self.habit_filter_all_btn.update()
        if hasattr(self, 'habit_filter_active_btn'):
            self.habit_filter_active_btn.bgcolor = active_bg if self.current_habit_filter is True else inactive_bg
            self.habit_filter_active_btn.update()
        if hasattr(self, 'habit_filter_inactive_btn'):
            self.habit_filter_inactive_btn.bgcolor = active_bg if self.current_habit_filter is False else inactive_bg
            self.habit_filter_inactive_btn.update()
    
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
        title = "Editar Hábito" if self.editing_habit else "Nuevo Hábito"
        
        # Crear el formulario
        form = HabitForm(
            on_save=self._save_habit,
            on_cancel=self._go_back_from_form,
            habit=self.editing_habit
        )
        
        # Detectar el tema actual
        is_dark = self.page.theme_mode == ft.ThemeMode.DARK
        bgcolor = ft.Colors.BLACK if is_dark else ft.Colors.GREY_50
        
        # Crear la barra de título con botón de volver
        back_button = ft.IconButton(
            icon=ft.Icons.ARROW_BACK,
            on_click=lambda e: self._go_back_from_form(),
            icon_color=ft.Colors.RED_400,
            tooltip="Volver"
        )
        
        title_bar = ft.Container(
            content=ft.Row(
                [
                    back_button,
                    ft.Text(
                        title,
                        size=24,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.RED_400,
                        expand=True
                    )
                ],
                alignment=ft.MainAxisAlignment.START,
                vertical_alignment=ft.CrossAxisAlignment.CENTER
            ),
            padding=ft.padding.symmetric(vertical=16, horizontal=20),
            bgcolor=ft.Colors.BLACK87 if is_dark else ft.Colors.RED_50
        )
        
        # Construir la vista del formulario
        form_view = ft.View(
            route="/habit-form",
            controls=[
                title_bar,
                ft.Container(
                    content=form.build(),
                    expand=True,
                    padding=20
                )
            ],
            bgcolor=bgcolor
        )
        
        # Agregar la vista y navegar a ella
        self.page.views.append(form_view)
        self.page.go("/habit-form")
    
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
        # Si el primer argumento es un objeto Habit, es una actualización
        if args and isinstance(args[0], Habit):
            # Actualizar hábito existente
            habit = args[0]
            self.habit_service.update_habit(habit)
        else:
            # Crear nuevo hábito
            title, description, frequency, target_days = args
            self.habit_service.create_habit(title, description, frequency, target_days)
        
        # Volver a la vista principal
        self._go_back_from_form()
        
        # Forzar actualización de la página antes de recargar hábitos
        self.page.update()
        
        # Recargar los hábitos después de volver
        self.load_habits()
    
    def _toggle_habit_completion(self, habit_id: int):
        """Alterna el cumplimiento de un hábito para hoy."""
        completion = self.habit_service.toggle_completion(habit_id, date.today())
        self.load_habits()
        
        # Mostrar mensaje
        if completion:
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text("¡Hábito completado!"),
                bgcolor=ft.Colors.RED_700
            )
        else:
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text("Cumplimiento eliminado"),
                bgcolor=ft.Colors.GREY_700
            )
        self.page.snack_bar.open = True
        self.page.update()
    
    def _delete_habit(self, habit_id: int):
        """Elimina un hábito."""
        if habit_id is None:
            return
        
        try:
            deleted = self.habit_service.delete_habit(int(habit_id))
            if deleted:
                self.load_habits()
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text("Hábito eliminado correctamente"),
                    bgcolor=ft.Colors.RED_700
                )
                self.page.snack_bar.open = True
            else:
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text("No se pudo eliminar el hábito"),
                    bgcolor=ft.Colors.RED
                )
                self.page.snack_bar.open = True
        except Exception as ex:
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"Error: {str(ex)}"),
                bgcolor=ft.Colors.RED
            )
            self.page.snack_bar.open = True
        
        self.page.update()
    
    def _view_habit_details(self, habit: Habit):
        """Muestra la vista de detalles de un hábito con historial y métricas."""
        # Obtener métricas completas
        metrics = self.habit_service.get_habit_metrics(habit.id)
        weekly_progress = self.habit_service.get_weekly_progress(habit.id)
        monthly_progress = self.habit_service.get_monthly_progress(habit.id)
        
        # Detectar el tema actual
        is_dark = self.page.theme_mode == ft.ThemeMode.DARK
        bgcolor = ft.Colors.BLACK if is_dark else ft.Colors.GREY_50
        
        # Crear la barra de título con botón de volver
        back_button = ft.IconButton(
            icon=ft.Icons.ARROW_BACK,
            on_click=lambda e: self._go_back(),
            icon_color=ft.Colors.RED_400,
            tooltip="Volver"
        )
        
        title_bar = ft.Container(
            content=ft.Row(
                [
                    back_button,
                    ft.Text(
                        habit.title,
                        size=24,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.RED_400,
                        expand=True
                    )
                ],
                alignment=ft.MainAxisAlignment.START,
                vertical_alignment=ft.CrossAxisAlignment.CENTER
            ),
            padding=ft.padding.symmetric(vertical=16, horizontal=20),
            bgcolor=ft.Colors.BLACK87 if is_dark else ft.Colors.RED_50
        )
        
        # Construir contenido de detalles
        details_content = ft.Container(
            content=ft.Column(
                [
                    # Descripción
                    ft.Text(
                        habit.description if habit.description else "Sin descripción",
                        size=14,
                        color=ft.Colors.GREY_500 if is_dark else ft.Colors.GREY_600
                    ),
                    ft.Divider(),
                    # Métricas principales
                    ft.Text(
                        "Métricas",
                        size=20,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.RED_400
                    ),
                    ft.Row(
                        [
                            ft.Container(
                                content=ft.Column(
                                    [
                                        ft.Text(
                                            str(metrics['streak']),
                                            size=32,
                                            weight=ft.FontWeight.BOLD,
                                            color=ft.Colors.RED_400
                                        ),
                                        ft.Text("Días seguidos", size=12)
                                    ],
                                    horizontal_alignment=ft.CrossAxisAlignment.CENTER
                                ),
                                expand=True
                            ),
                            ft.VerticalDivider(),
                            ft.Container(
                                content=ft.Column(
                                    [
                                        ft.Text(
                                            f"{metrics['completion_percentage']:.1f}%",
                                            size=32,
                                            weight=ft.FontWeight.BOLD,
                                            color=ft.Colors.RED_500
                                        ),
                                        ft.Text("Cumplimiento", size=12)
                                    ],
                                    horizontal_alignment=ft.CrossAxisAlignment.CENTER
                                ),
                                expand=True
                            ),
                            ft.VerticalDivider(),
                            ft.Container(
                                content=ft.Column(
                                    [
                                        ft.Text(
                                            str(metrics['total_completions']),
                                            size=32,
                                            weight=ft.FontWeight.BOLD,
                                            color=ft.Colors.RED_600
                                        ),
                                        ft.Text("Total", size=12)
                                    ],
                                    horizontal_alignment=ft.CrossAxisAlignment.CENTER
                                ),
                                expand=True
                            )
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_EVENLY
                    ),
                    ft.Divider(),
                    # Información adicional
                    ft.Text(
                        f"Frecuencia: {habit.frequency.capitalize()}",
                        size=14
                    ),
                    ft.Text(
                        f"Último cumplimiento: {metrics['last_completion_date'].strftime('%d/%m/%Y') if metrics['last_completion_date'] else 'Nunca'}",
                        size=14
                    )
                ],
                spacing=16,
                scroll=ft.ScrollMode.AUTO
            ),
            padding=20,
            expand=True
        )
        
        # Construir la vista de detalles
        details_view = ft.View(
            route="/habit-details",
            controls=[
                title_bar,
                details_content
            ],
            bgcolor=bgcolor
        )
        
        # Agregar la vista y navegar a ella
        self.page.views.append(details_view)
        self.page.go("/habit-details")
    
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

