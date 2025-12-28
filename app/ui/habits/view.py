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
        self._editing_habit_id = None  # ID del hábito que se está editando (None si no hay ninguno)
        self._expanded_habit_metrics = set()  # Set de IDs de hábitos con métricas expandidas
        self._global_metrics_visible = False  # Si las métricas globales están visibles
        self._global_metrics_container = None  # Contenedor de métricas globales
        self._sort_order = "recent"  # "recent" para más reciente primero, "oldest" para más antiguo primero
    
    def build_ui(self) -> ft.Container:
        """
        Construye la interfaz de usuario de hábitos.
        
        Returns:
            Container con la vista de hábitos.
        """
        # Contenedor para los hábitos
        self.habits_container = ft.Column(
            [],
            spacing=8
        )
        
        # Contenedor del formulario (oculto por defecto)
        self.form_container = self._build_form_container()
        
        # Contenedor de métricas globales (oculto por defecto)
        self._global_metrics_container = self._build_global_metrics_container()
        
        # Barra de título
        is_dark = self.page.theme_mode == ft.ThemeMode.DARK
        title_color = ft.Colors.RED_700 if not is_dark else ft.Colors.RED_500
        btn_color = ft.Colors.RED_700 if not is_dark else ft.Colors.RED_600
        
        # Botón de filtro de ordenamiento
        sort_icon = ft.Icons.ARROW_DOWNWARD if self._sort_order == "recent" else ft.Icons.ARROW_UPWARD
        sort_tooltip = "Más reciente primero" if self._sort_order == "recent" else "Más antiguo primero"
        sort_button = ft.IconButton(
            icon=sort_icon,
            on_click=self._toggle_sort_order,
            tooltip=sort_tooltip,
            icon_color=btn_color
        )
        
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
                            sort_button,
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
                    self._global_metrics_container,  # Métricas globales (se puede mostrar/ocultar)
                    ft.Container(
                        content=self.habits_container,
                        padding=16
                    )
                ],
                spacing=0,
                scroll=ft.ScrollMode.AUTO,
                expand=True
            ),
            expand=True
        )
    
    def _load_habits(self):
        """Carga los hábitos desde el servicio."""
        if self.habits_container is None:
            return
        
        habits = list(self.habit_service.get_all_habits())
        
        # Ordenar según el filtro seleccionado
        if self._sort_order == "recent":
            # Más reciente primero (created_at más reciente)
            habits.sort(key=lambda h: h.created_at if h.created_at else datetime.min, reverse=True)
        else:
            # Más antiguo primero (created_at más antiguo)
            habits.sort(key=lambda h: h.created_at if h.created_at else datetime.max)
        
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
                # Si este hábito se está editando, mostrar formulario inline en lugar de la tarjeta
                if self._editing_habit_id == habit.id:
                    self.habits_container.controls.append(
                        self._build_inline_form(habit)
                    )
                else:
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
        
        # Botón para expandir/contraer métricas
        is_expanded = habit.id in self._expanded_habit_metrics
        metrics_button = ft.IconButton(
            icon=ft.Icons.EXPAND_MORE if not is_expanded else ft.Icons.EXPAND_LESS,
            on_click=lambda e, h=habit: self._toggle_habit_metrics(h),
            tooltip="Ver métricas detalladas" if not is_expanded else "Ocultar métricas",
            icon_color=btn_color
        )
        
        # Sección de métricas detalladas (oculta por defecto)
        detailed_metrics = self._build_detailed_metrics(habit) if is_expanded else ft.Container()
        
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
                        metrics_button,
                        edit_button,
                        delete_button
                    ],
                    spacing=8,
                    vertical_alignment=ft.CrossAxisAlignment.START
                ),
                detailed_metrics
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
        if habit and habit.id:
            # Editar hábito específico - modo inline
            if self._editing_habit_id == habit.id:
                # Si ya está en edición, cancelar
                self._editing_habit_id = None
            else:
                # Iniciar edición inline
                self._editing_habit_id = habit.id
                self._edit_habit_in_form(habit)
            self._load_habits()  # Recargar para mostrar/ocultar formulario
            self.page.update()
        else:
            # Crear nuevo hábito - modo formulario superior
            if self.form_container.visible:
                # Si está visible, ocultarlo
                self.form_container.visible = False
                self._editing_habit_id = None
            else:
                # Si está oculto, mostrarlo y preparar para nuevo hábito
                self._new_habit_in_form()
                self.form_container.visible = True
            self.page.update()
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
            self._editing_habit_id = None
            self._load_habits()
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
    
    def _build_inline_form(self, habit: Habit) -> ft.Container:
        """Construye un formulario inline para editar un hábito en su posición."""
        is_dark = self.page.theme_mode == ft.ThemeMode.DARK
        bg_color = ft.Colors.WHITE if not is_dark else ft.Colors.SURFACE
        btn_color = ft.Colors.RED_700 if not is_dark else ft.Colors.RED_500
        
        # Campos del formulario inline
        inline_title_field = ft.TextField(
            label="Título",
            hint_text="Ingresa el título del hábito",
            value=habit.title,
            autofocus=True
        )
        
        inline_description_field = ft.TextField(
            label="Descripción",
            hint_text="Descripción del hábito (opcional)",
            multiline=True,
            min_lines=2,
            max_lines=4,
            value=habit.description or ""
        )
        
        def save_inline_habit(e):
            """Guarda el hábito desde el formulario inline."""
            title = inline_title_field.value.strip()
            if not title:
                return
            
            description = inline_description_field.value.strip() if inline_description_field.value else None
            
            try:
                # Actualizar hábito
                from app.data.models import Habit
                updated_habit = Habit(
                    id=habit.id,
                    title=title,
                    description=description,
                    created_at=habit.created_at
                )
                self.habit_service.update_habit(updated_habit)
                
                # Cancelar edición y recargar
                self._editing_habit_id = None
                self._load_habits()
                self.page.update()
            except Exception as ex:
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text(f"Error al guardar: {str(ex)}"),
                    bgcolor=ft.Colors.RED
                )
                self.page.snack_bar.open = True
                self.page.update()
        
        def cancel_inline_form(e):
            """Cancela la edición inline."""
            self._editing_habit_id = None
            self._load_habits()
            self.page.update()
        
        # Botones
        save_button = ft.ElevatedButton(
            "Guardar",
            icon=ft.Icons.SAVE,
            on_click=save_inline_habit,
            bgcolor=btn_color,
            color=ft.Colors.WHITE
        )
        
        cancel_button = ft.ElevatedButton(
            "Cancelar",
            icon=ft.Icons.CANCEL,
            on_click=cancel_inline_form,
            color=ft.Colors.GREY
        )
        
        # Contenido del formulario inline
        form_content = ft.Column(
            [
                ft.Container(
                    content=ft.Row(
                        [
                            ft.Text(
                                "Editar Hábito",
                                size=18,
                                weight=ft.FontWeight.BOLD,
                                color=btn_color
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
                            inline_title_field,
                            inline_description_field
                        ],
                        spacing=12
                    ),
                    padding=16,
                    bgcolor=bg_color
                )
            ],
            spacing=0
        )
        
        return ft.Container(
            content=form_content,
            padding=16,
            bgcolor=bg_color,
            border_radius=8,
            border=ft.border.all(2, btn_color),
            margin=ft.margin.only(bottom=8)
        )
    
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
            self._editing_habit_id = None
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
        """Muestra u oculta el panel de métricas globales."""
        self._global_metrics_visible = not self._global_metrics_visible
        if self._global_metrics_visible:
            # Reconstruir el contenedor de métricas globales para actualizar los datos
            self._global_metrics_container = self._build_global_metrics_container()
            self._global_metrics_container.visible = True
            # Actualizar la vista principal para incluir el nuevo contenedor
            self.page.update()
        else:
            if self._global_metrics_container:
                self._global_metrics_container.visible = False
            self.page.update()
    
    def _toggle_habit_metrics(self, habit: Habit):
        """Expande o contrae las métricas detalladas de un hábito."""
        if habit.id in self._expanded_habit_metrics:
            self._expanded_habit_metrics.remove(habit.id)
        else:
            self._expanded_habit_metrics.add(habit.id)
        self._load_habits()
        self.page.update()
    
    def _build_detailed_metrics(self, habit: Habit) -> ft.Container:
        """Construye el panel de métricas detalladas para un hábito."""
        from datetime import date, timedelta
        from collections import defaultdict
        
        is_dark = self.page.theme_mode == ft.ThemeMode.DARK
        btn_color = ft.Colors.RED_700 if not is_dark else ft.Colors.RED_500
        
        completions = self.habit_service.get_completions(habit.id)
        completion_count = len(completions)
        streak = self.habit_service.get_streak(habit.id)
        
        # Calcular racha máxima
        max_streak = 0
        if completions:
            sorted_dates = sorted(completions)
            current_streak = 1
            for i in range(1, len(sorted_dates)):
                if (sorted_dates[i] - sorted_dates[i-1]).days == 1:
                    current_streak += 1
                else:
                    max_streak = max(max_streak, current_streak)
                    current_streak = 1
            max_streak = max(max_streak, current_streak)
        
        # Calcular porcentaje de completación (últimos 30 días)
        today = date.today()
        last_30_days = [today - timedelta(days=i) for i in range(30)]
        completed_last_30 = sum(1 for d in last_30_days if d in completions)
        completion_rate_30 = (completed_last_30 / 30) * 100 if last_30_days else 0
        
        # Calcular porcentaje de completación (últimos 7 días)
        last_7_days = [today - timedelta(days=i) for i in range(7)]
        completed_last_7 = sum(1 for d in last_7_days if d in completions)
        completion_rate_7 = (completed_last_7 / 7) * 100 if last_7_days else 0
        
        bg_color = ft.Colors.GREY_100 if not is_dark else ft.Colors.GREY_900
        
        metrics_content = ft.Column(
            [
                ft.Divider(),
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Row(
                                [
                                    ft.Column(
                                        [
                                            ft.Text("Total completaciones", size=12, color=ft.Colors.GREY_700),
                                            ft.Text(str(completion_count), size=20, weight=ft.FontWeight.BOLD, color=btn_color)
                                        ],
                                        spacing=4
                                    ),
                                    ft.Column(
                                        [
                                            ft.Text("Racha actual", size=12, color=ft.Colors.GREY_700),
                                            ft.Text(f"{streak} días", size=20, weight=ft.FontWeight.BOLD, color=btn_color)
                                        ],
                                        spacing=4
                                    ),
                                    ft.Column(
                                        [
                                            ft.Text("Racha máxima", size=12, color=ft.Colors.GREY_700),
                                            ft.Text(f"{max_streak} días", size=20, weight=ft.FontWeight.BOLD, color=btn_color)
                                        ],
                                        spacing=4
                                    )
                                ],
                                spacing=16,
                                alignment=ft.MainAxisAlignment.SPACE_AROUND
                            ),
                            ft.Divider(),
                            ft.Row(
                                [
                                    ft.Column(
                                        [
                                            ft.Text("Últimos 7 días", size=12, color=ft.Colors.GREY_700),
                                            ft.Text(f"{completion_rate_7:.1f}%", size=18, weight=ft.FontWeight.BOLD, color=btn_color),
                                            ft.ProgressBar(value=completion_rate_7 / 100, color=btn_color, width=100)
                                        ],
                                        spacing=4,
                                        horizontal_alignment=ft.CrossAxisAlignment.CENTER
                                    ),
                                    ft.Column(
                                        [
                                            ft.Text("Últimos 30 días", size=12, color=ft.Colors.GREY_700),
                                            ft.Text(f"{completion_rate_30:.1f}%", size=18, weight=ft.FontWeight.BOLD, color=btn_color),
                                            ft.ProgressBar(value=completion_rate_30 / 100, color=btn_color, width=100)
                                        ],
                                        spacing=4,
                                        horizontal_alignment=ft.CrossAxisAlignment.CENTER
                                    )
                                ],
                                spacing=16,
                                alignment=ft.MainAxisAlignment.SPACE_AROUND
                            )
                        ],
                        spacing=12
                    ),
                    padding=16
                )
            ],
            spacing=0
        )
        
        return ft.Container(
            content=metrics_content,
            bgcolor=bg_color,
            border_radius=4,
            margin=ft.margin.only(top=8, left=32)
        )
    
    def _build_global_metrics_container(self) -> ft.Container:
        """Construye el contenedor de métricas globales."""
        is_dark = self.page.theme_mode == ft.ThemeMode.DARK
        bg_color = ft.Colors.WHITE if not is_dark else ft.Colors.SURFACE
        btn_color = ft.Colors.RED_700 if not is_dark else ft.Colors.RED_500
        title_color = ft.Colors.RED_700 if not is_dark else ft.Colors.RED_500
        
        # Calcular métricas globales
        habits = self.habit_service.get_all_habits()
        
        if not habits:
            metrics_content = ft.Container(
                content=ft.Text("No hay hábitos para mostrar métricas", text_align=ft.TextAlign.CENTER),
                padding=16
            )
        else:
            total_habits = len(habits)
            total_completions = 0
            total_streaks = 0
            habits_completed_today = 0
            completion_rates_30 = []
            completion_rates_7 = []
            
            from datetime import date, timedelta
            today = date.today()
            
            for habit in habits:
                completions = self.habit_service.get_completions(habit.id)
                total_completions += len(completions)
                streak = self.habit_service.get_streak(habit.id)
                total_streaks += streak
                
                if self.habit_service.is_completed_today(habit.id):
                    habits_completed_today += 1
                
                # Calcular porcentaje de completación (últimos 30 días)
                last_30_days = [today - timedelta(days=i) for i in range(30)]
                completed_last_30 = sum(1 for d in last_30_days if d in completions)
                completion_rate_30 = (completed_last_30 / 30) * 100 if last_30_days else 0
                completion_rates_30.append(completion_rate_30)
                
                # Calcular porcentaje de completación (últimos 7 días)
                last_7_days = [today - timedelta(days=i) for i in range(7)]
                completed_last_7 = sum(1 for d in last_7_days if d in completions)
                completion_rate_7 = (completed_last_7 / 7) * 100 if last_7_days else 0
                completion_rates_7.append(completion_rate_7)
            
            avg_completions = total_completions / total_habits if total_habits > 0 else 0
            avg_streak = total_streaks / total_habits if total_habits > 0 else 0
            avg_completion_rate_30 = sum(completion_rates_30) / len(completion_rates_30) if completion_rates_30 else 0
            avg_completion_rate_7 = sum(completion_rates_7) / len(completion_rates_7) if completion_rates_7 else 0
            
            metrics_content = ft.Container(
                content=ft.Column(
                    [
                        ft.Container(
                            content=ft.Row(
                                [
                                    ft.Text(
                                        "📊 Métricas Globales",
                                        size=20,
                                        weight=ft.FontWeight.BOLD,
                                        color=title_color,
                                        expand=True
                                    ),
                                    ft.IconButton(
                                        icon=ft.Icons.CLOSE,
                                        on_click=self._open_metrics,
                                        tooltip="Cerrar",
                                        icon_color=btn_color
                                    )
                                ],
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                            ),
                            padding=16,
                            bgcolor=ft.Colors.SURFACE if is_dark else ft.Colors.GREY_100
                        ),
                        ft.Container(
                            content=ft.Column(
                                [
                                    ft.Row(
                                        [
                                            ft.Column(
                                                [
                                                    ft.Text("Total hábitos", size=12, color=ft.Colors.GREY_700),
                                                    ft.Text(str(total_habits), size=24, weight=ft.FontWeight.BOLD, color=btn_color)
                                                ],
                                                spacing=4,
                                                horizontal_alignment=ft.CrossAxisAlignment.CENTER
                                            ),
                                            ft.Column(
                                                [
                                                    ft.Text("Hábitos completados hoy", size=12, color=ft.Colors.GREY_700),
                                                    ft.Text(str(habits_completed_today), size=24, weight=ft.FontWeight.BOLD, color=btn_color)
                                                ],
                                                spacing=4,
                                                horizontal_alignment=ft.CrossAxisAlignment.CENTER
                                            ),
                                            ft.Column(
                                                [
                                                    ft.Text("Promedio de completaciones", size=12, color=ft.Colors.GREY_700),
                                                    ft.Text(f"{avg_completions:.1f}", size=24, weight=ft.FontWeight.BOLD, color=btn_color)
                                                ],
                                                spacing=4,
                                                horizontal_alignment=ft.CrossAxisAlignment.CENTER
                                            ),
                                            ft.Column(
                                                [
                                                    ft.Text("Promedio de racha", size=12, color=ft.Colors.GREY_700),
                                                    ft.Text(f"{avg_streak:.1f} días", size=24, weight=ft.FontWeight.BOLD, color=btn_color)
                                                ],
                                                spacing=4,
                                                horizontal_alignment=ft.CrossAxisAlignment.CENTER
                                            )
                                        ],
                                        spacing=16,
                                        alignment=ft.MainAxisAlignment.SPACE_AROUND
                                    ),
                                    ft.Divider(),
                                    ft.Row(
                                        [
                                            ft.Column(
                                                [
                                                    ft.Text("Promedio últimos 7 días", size=12, color=ft.Colors.GREY_700),
                                                    ft.Text(f"{avg_completion_rate_7:.1f}%", size=20, weight=ft.FontWeight.BOLD, color=btn_color),
                                                    ft.ProgressBar(value=avg_completion_rate_7 / 100, color=btn_color, width=150)
                                                ],
                                                spacing=4,
                                                horizontal_alignment=ft.CrossAxisAlignment.CENTER
                                            ),
                                            ft.Column(
                                                [
                                                    ft.Text("Promedio últimos 30 días", size=12, color=ft.Colors.GREY_700),
                                                    ft.Text(f"{avg_completion_rate_30:.1f}%", size=20, weight=ft.FontWeight.BOLD, color=btn_color),
                                                    ft.ProgressBar(value=avg_completion_rate_30 / 100, color=btn_color, width=150)
                                                ],
                                                spacing=4,
                                                horizontal_alignment=ft.CrossAxisAlignment.CENTER
                                            )
                                        ],
                                        spacing=16,
                                        alignment=ft.MainAxisAlignment.SPACE_AROUND
                                    )
                                ],
                                spacing=16
                            ),
                            padding=16
                        )
                    ],
                    spacing=0
                ),
                bgcolor=bg_color,
                border=ft.border.all(2, btn_color),
                border_radius=8,
                margin=ft.margin.all(16)
            )
    
    def _toggle_sort_order(self, e):
        """Alterna entre ordenamiento más reciente primero y más antiguo primero."""
        self._sort_order = "oldest" if self._sort_order == "recent" else "recent"
        # Recargar hábitos con el nuevo orden
        self._load_habits()
        # Notificar a home_view para que reconstruya la UI y actualice el icono
        # Buscar la instancia de HomeView en la página
        if hasattr(self.page, '_home_view_ref'):
            home_view = self.page._home_view_ref
            home_view._build_ui()
        elif self.page:
            self.page.update()
        
        container = ft.Container(
            content=metrics_content,
            visible=False,  # Oculto por defecto
        )
        
        return container

