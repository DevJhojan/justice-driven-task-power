"""
Vista principal de hábitos.
"""
import flet as ft
from datetime import date
from typing import Optional

from app.data.models import Habit
from app.services.habit_service import HabitService


class HabitsView:
    """Vista para gestión de hábitos."""
    
    def __init__(self, page: ft.Page, habit_service: HabitService, points_service=None):
        """
        Inicializa la vista de hábitos.
        
        Args:
            page: Página de Flet.
            habit_service: Servicio de hábitos.
            points_service: Servicio de puntos (opcional).
        """
        self.page = page
        self.habit_service = habit_service
        self.points_service = points_service
        self.habits_container = None
    
    def build_ui(self) -> ft.Container:
        """
        Construye la interfaz de usuario de hábitos.
        
        Returns:
            Container con la vista de hábitos.
        """
        # Contenedor para los hábitos
        self.habits_container = ft.Column(
            [],
            spacing=8,
            scroll=ft.ScrollMode.AUTO,
            expand=True
        )
        
        # Contenedor del formulario (oculto por defecto)
        self.form_container = self._build_form_container()
        
        # Barra de título
        is_dark = self.page.theme_mode == ft.ThemeMode.DARK
        title_color = ft.Colors.RED_700 if not is_dark else ft.Colors.RED_500
        btn_color = ft.Colors.RED_700 if not is_dark else ft.Colors.RED_600
        
        title_bar = ft.Container(
            content=ft.Row(
                [
                    ft.Text(
                        "🔁 Mis Hábitos",
                        size=24,
                        weight=ft.FontWeight.BOLD,
                        color=title_color
                    ),
                    ft.Row(
                        [
                            ft.IconButton(
                                icon=ft.Icons.BAR_CHART,
                                on_click=self._open_metrics,
                                tooltip="Ver métricas",
                                icon_color=btn_color
                            ),
                            ft.IconButton(
                                icon=ft.Icons.ADD,
                                on_click=self._toggle_form,
                                tooltip="Agregar hábito",
                                icon_color=btn_color
                            )
                        ],
                        spacing=4
                    )
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN
            ),
            padding=16,
            bgcolor=ft.Colors.SURFACE
        )
        
        # Cargar hábitos
        self._load_habits()
        
        # Vista principal
        return ft.Container(
            content=ft.Column(
                [
                    title_bar,
                    self.form_container,  # Formulario (aparece primero cuando está visible)
                    ft.Container(
                        content=self.habits_container,
                        padding=16,
                        expand=True
                    )
                ],
                spacing=0,
                expand=True
            ),
            expand=True
        )
    
    def _load_habits(self):
        """Carga los hábitos desde el servicio."""
        if self.habits_container is None:
            return
        
        habits = self.habit_service.get_all_habits()
        self.habits_container.controls.clear()
        
        if not habits:
            self.habits_container.controls.append(
                ft.Container(
                    content=ft.Text(
                        "No hay hábitos. ¡Crea uno nuevo!",
                        size=16,
                        text_align=ft.TextAlign.CENTER
                    ),
                    alignment=ft.alignment.center,
                    padding=32
                )
            )
        else:
            for habit in habits:
                self.habits_container.controls.append(
                    self._build_habit_card(habit)
                )
        
        if self.page:
            self.page.update()
    
    def _build_habit_card(self, habit: Habit) -> ft.Container:
        """
        Construye una tarjeta para un hábito.
        
        Args:
            habit: Hábito a mostrar.
        
        Returns:
            Container con la tarjeta del hábito.
        """
        # Obtener métricas
        completions = self.habit_service.get_completions(habit.id)
        completion_count = len(completions)
        streak = self.habit_service.get_streak(habit.id)
        is_completed_today = self.habit_service.is_completed_today(habit.id)
        
        # Checkbox para marcar completado hoy
        checkbox = ft.Checkbox(
            value=is_completed_today,
            on_change=lambda e, h=habit: self._toggle_today_completion(h)
        )
        
        # Botones de acción
        is_dark = self.page.theme_mode == ft.ThemeMode.DARK
        btn_color = ft.Colors.RED_700 if not is_dark else ft.Colors.RED_500
        
        edit_button = ft.IconButton(
            icon=ft.Icons.EDIT,
            on_click=lambda e, h=habit: self._toggle_form(e, h),
            tooltip="Editar",
            icon_color=btn_color
        )
        
        delete_button = ft.IconButton(
            icon=ft.Icons.DELETE,
            on_click=lambda e, h=habit: self._delete_habit(h),
            tooltip="Eliminar",
            icon_color=ft.Colors.RED
        )
        
        # Información del hábito
        metrics_text = f"Completado: {completion_count} veces | Racha: {streak} días"
        if is_completed_today:
            metrics_text = f"✅ Hoy completado | {metrics_text}"
        
        # Contenido de la tarjeta
        content = ft.Column(
            [
                ft.Row(
                    [
                        checkbox,
                        ft.Column(
                            [
                                ft.Text(
                                    habit.title,
                                    size=16,
                                    weight=ft.FontWeight.BOLD,
                                    expand=True,
                                    color=ft.Colors.RED_800 if self.page.theme_mode == ft.ThemeMode.LIGHT else ft.Colors.RED_400
                                ),
                                ft.Text(
                                    habit.description or "",
                                    size=12,
                                    color=ft.Colors.GREY,
                                    visible=bool(habit.description)
                                ),
                                ft.Text(
                                    metrics_text,
                                    size=11,
                                    color=ft.Colors.GREY_700
                                )
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
    
    def _toggle_today_completion(self, habit: Habit):
        """Alterna la completación de hoy para un hábito."""
        self.habit_service.toggle_completion(habit.id, date.today(), self.points_service)
        self._load_habits()
    
    def _delete_habit(self, habit: Habit):
        """Elimina un hábito."""
        def confirm_delete(e):
            self.habit_service.delete_habit(habit.id)
            self._load_habits()
            self.page.close_dialog()
        
        self.page.dialog = ft.AlertDialog(
            title=ft.Text("Confirmar eliminación"),
            content=ft.Text(f"¿Estás seguro de que quieres eliminar el hábito '{habit.title}'?"),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: self.page.close_dialog()),
                ft.TextButton("Eliminar", on_click=confirm_delete, style=ft.ButtonStyle(color=ft.Colors.RED))
            ]
        )
        self.page.dialog.open = True
        self.page.update()
    
    def _toggle_form(self, e, habit: Optional[Habit] = None):
        """Muestra u oculta el formulario de hábito."""
        if self.form_container.visible:
            # Si está visible, ocultarlo
            self.form_container.visible = False
        else:
            # Si está oculto, mostrarlo y preparar para nuevo hábito o editar
            if habit:
                self._edit_habit_in_form(habit)
            else:
                self._new_habit_in_form()
            self.form_container.visible = True
        self.page.update()
    
    def _new_habit_in_form(self):
        """Prepara el formulario para crear un nuevo hábito."""
        self.form_title_field.value = ""
        self.form_description_field.value = ""
        self._current_editing_habit = None
        if hasattr(self, '_form_title_text'):
            self._form_title_text.value = "Nuevo Hábito"
    
    def _edit_habit_in_form(self, habit: Habit):
        """Prepara el formulario para editar un hábito existente."""
        self.form_title_field.value = habit.title
        self.form_description_field.value = habit.description or ""
        self._current_editing_habit = habit
        if hasattr(self, '_form_title_text'):
            self._form_title_text.value = "Editar Hábito"
    
    def _build_form_container(self) -> ft.Container:
        """Construye el contenedor del formulario."""
        is_dark = self.page.theme_mode == ft.ThemeMode.DARK
        bg_color = ft.Colors.WHITE if not is_dark else ft.Colors.BLACK
        btn_color = ft.Colors.RED_700 if not is_dark else ft.Colors.RED_500
        
        # Campos del formulario
        self.form_title_field = ft.TextField(
            label="Título",
            hint_text="Ingresa el título del hábito",
            autofocus=True
        )
        
        self.form_description_field = ft.TextField(
            label="Descripción",
            hint_text="Descripción del hábito (opcional)",
            multiline=True,
            min_lines=3,
            max_lines=5
        )
        
        # Variable para rastrear el hábito que se está editando
        self._current_editing_habit = None
        
        def save_habit(e):
            self._save_habit_from_form()
        
        def cancel_form(e):
            self.form_container.visible = False
            self.page.update()
        
        # Botones
        save_button = ft.ElevatedButton(
            "Guardar",
            icon=ft.Icons.SAVE,
            on_click=save_habit,
            bgcolor=btn_color,
            color=ft.Colors.WHITE
        )
        
        cancel_button = ft.ElevatedButton(
            "Cancelar",
            icon=ft.Icons.CANCEL,
            on_click=cancel_form,
            color=ft.Colors.GREY
        )
        
        # Contenido del formulario
        form_content = ft.Column(
            [
                ft.Container(
                    content=ft.Row(
                        [
                            ft.Text(
                                "Nuevo Hábito",
                                size=20,
                                weight=ft.FontWeight.BOLD,
                                color=ft.Colors.RED_700 if not is_dark else ft.Colors.RED_500,
                                ref=lambda c: setattr(self, '_form_title_text', c) if c else None
                            ),
                            ft.Row(
                                [cancel_button, save_button],
                                spacing=8
                            )
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                    ),
                    padding=16,
                    bgcolor=ft.Colors.SURFACE
                ),
                ft.Container(
                    content=ft.Column(
                        [
                            self.form_title_field,
                            self.form_description_field
                        ],
                        spacing=16,
                        scroll=ft.ScrollMode.AUTO,
                        expand=True
                    ),
                    padding=16,
                    expand=True,
                    bgcolor=bg_color
                )
            ],
            spacing=0,
            expand=True
        )
        
        container = ft.Container(
            content=form_content,
            visible=False,  # Oculto por defecto
            border=ft.border.all(2, btn_color),
            border_radius=8,
            margin=ft.margin.symmetric(horizontal=16, vertical=8)
        )
        
        return container
    
    def _save_habit_from_form(self):
        """Guarda el hábito desde el formulario."""
        title = self.form_title_field.value.strip()
        if not title:
            return
        
        description = self.form_description_field.value.strip() if self.form_description_field.value else None
        
        try:
            if self._current_editing_habit:
                # Editar hábito existente
                from app.data.models import Habit
                updated_habit = Habit(
                    id=self._current_editing_habit.id,
                    title=title,
                    description=description,
                    created_at=self._current_editing_habit.created_at
                )
                self.habit_service.update_habit(updated_habit)
            else:
                # Crear nuevo hábito
                self.habit_service.create_habit(title, description)
            
            # Ocultar formulario y recargar hábitos
            self.form_container.visible = False
            self._load_habits()
            self.page.update()
        except Exception as ex:
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"Error al guardar: {str(ex)}"),
                bgcolor=ft.Colors.RED
            )
            self.page.snack_bar.open = True
            self.page.update()
    
    def _open_metrics(self, e):
        """Abre la vista de métricas de hábitos."""
        self.page.go("/habits-metrics")

