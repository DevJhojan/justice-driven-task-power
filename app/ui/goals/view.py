"""
Vista principal de metas.
"""
import flet as ft
from typing import Optional

from app.data.models import Goal
from app.services.goal_service import GoalService


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
        self._editing_goal_id = None  # ID de la meta que se está editando (None si no hay ninguna)
    
    def build_ui(self) -> ft.Container:
        """
        Construye la interfaz de usuario de metas.
        
        Returns:
            Container con la vista de metas.
        """
        # Contenedor para las metas
        self.goals_container = ft.Column(
            [],
            spacing=8
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
                        "🎯 Mis Metas",
                        size=24,
                        weight=ft.FontWeight.BOLD,
                        color=title_color
                    ),
                    ft.IconButton(
                        icon=ft.Icons.ADD,
                        on_click=self._toggle_form,
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
                    self.form_container,  # Formulario (aparece primero cuando está visible)
                    ft.Container(
                        content=self.goals_container,
                        padding=16
                    )
                ],
                spacing=0,
                scroll=ft.ScrollMode.AUTO,
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
            on_click=lambda e, g=goal: self._toggle_form(e, g),
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
    
    def _toggle_form(self, e, goal: Optional[Goal] = None):
        """Muestra u oculta el formulario de meta."""
        if self.form_container.visible:
            # Si está visible, ocultarlo
            self.form_container.visible = False
        else:
            # Si está oculto, mostrarlo y preparar para nueva meta o editar
            if goal:
                self._edit_goal_in_form(goal)
            else:
                self._new_goal_in_form()
            self.form_container.visible = True
        self.page.update()
    
    def _new_goal_in_form(self):
        """Prepara el formulario para crear una nueva meta."""
        self.form_title_field.value = ""
        self.form_description_field.value = ""
        self.form_target_value_field.value = ""
        self.form_current_value_field.value = "0.0"
        self.form_unit_field.value = ""
        self.form_period_field.value = "mes"
        self._current_editing_goal = None
        if hasattr(self, '_form_title_text'):
            self._form_title_text.value = "Nueva Meta"
    
    def _edit_goal_in_form(self, goal: Goal):
        """Prepara el formulario para editar una meta existente."""
        self.form_title_field.value = goal.title
        self.form_description_field.value = goal.description or ""
        self.form_target_value_field.value = str(goal.target_value) if goal.target_value else ""
        self.form_current_value_field.value = str(goal.current_value) if goal.current_value else "0.0"
        self.form_unit_field.value = goal.unit or ""
        self.form_period_field.value = goal.period if goal.period else "mes"
        self._current_editing_goal = goal
        if hasattr(self, '_form_title_text'):
            self._form_title_text.value = "Editar Meta"
    
    def _build_form_container(self) -> ft.Container:
        """Construye el contenedor del formulario."""
        is_dark = self.page.theme_mode == ft.ThemeMode.DARK
        bg_color = ft.Colors.WHITE if not is_dark else ft.Colors.BLACK
        btn_color = ft.Colors.RED_700 if not is_dark else ft.Colors.RED_500
        
        # Campos del formulario
        self.form_title_field = ft.TextField(
            label="Título",
            hint_text="Ingresa el título de la meta",
            autofocus=True
        )
        
        self.form_description_field = ft.TextField(
            label="Descripción",
            hint_text="Descripción de la meta (opcional)",
            multiline=True,
            min_lines=3,
            max_lines=5
        )
        
        self.form_target_value_field = ft.TextField(
            label="Valor objetivo",
            hint_text="Valor objetivo (opcional)"
        )
        
        self.form_current_value_field = ft.TextField(
            label="Valor actual",
            hint_text="Valor actual",
            value="0.0"
        )
        
        self.form_unit_field = ft.TextField(
            label="Unidad",
            hint_text="Unidad de medida (ej: días, tareas, horas) - opcional"
        )
        
        # Selector de período
        period_options = [
            ft.dropdown.Option("semana", "Semana"),
            ft.dropdown.Option("mes", "Mes"),
            ft.dropdown.Option("trimestre", "Trimestre"),
            ft.dropdown.Option("semestre", "Semestre"),
            ft.dropdown.Option("anual", "Anual")
        ]
        
        self.form_period_field = ft.Dropdown(
            label="Período",
            hint_text="Selecciona el período de la meta",
            options=period_options,
            value="mes"
        )
        
        # Variable para rastrear la meta que se está editando
        self._current_editing_goal = None
        
        def save_goal(e):
            self._save_goal_from_form()
        
        def cancel_form(e):
            self.form_container.visible = False
            self.page.update()
        
        # Botones
        save_button = ft.ElevatedButton(
            "Guardar",
            icon=ft.Icons.SAVE,
            on_click=save_goal,
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
                                "Nueva Meta",
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
                            self.form_description_field,
                            self.form_period_field,
                            self.form_target_value_field,
                            self.form_current_value_field,
                            self.form_unit_field
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
    
    def _save_goal_from_form(self):
        """Guarda la meta desde el formulario."""
        title = self.form_title_field.value.strip()
        if not title:
            return
        
        description = self.form_description_field.value.strip() if self.form_description_field.value else None
        
        # Validar valores numéricos
        try:
            target_value = float(self.form_target_value_field.value.strip()) if self.form_target_value_field.value.strip() else None
            current_value = float(self.form_current_value_field.value.strip() or "0.0")
        except ValueError:
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text("Los valores deben ser números válidos"),
                bgcolor=ft.Colors.RED
            )
            self.page.snack_bar.open = True
            self.page.update()
            return
        
        unit = self.form_unit_field.value.strip() if self.form_unit_field.value else None
        period = self.form_period_field.value or "mes"
        
        try:
            if self._current_editing_goal:
                # Editar meta existente
                from app.data.models import Goal
                # Verificar si la meta estaba completa antes del cambio
                was_completed = self._current_editing_goal.target_value and self._current_editing_goal.current_value >= self._current_editing_goal.target_value
                old_current_value = self._current_editing_goal.current_value
                
                updated_goal = Goal(
                    id=self._current_editing_goal.id,
                    title=title,
                    description=description,
                    target_value=target_value,
                    current_value=current_value,
                    unit=unit,
                    period=period,
                    created_at=self._current_editing_goal.created_at
                )
                
                self.goal_service.update_goal(updated_goal)
                
                # Si la meta estaba completa y ahora no lo está, restar puntos
                is_completed_now = target_value and current_value >= target_value
                if was_completed and not is_completed_now and self.points_service:
                    self.points_service.add_points(-0.1)  # Restar puntos
                # Si la meta no estaba completa y ahora lo está, sumar puntos
                elif not was_completed and is_completed_now and self.points_service:
                    self.points_service.add_points(0.1)  # Sumar puntos
            else:
                # Crear nueva meta
                self.goal_service.create_goal(
                    title=title,
                    description=description,
                    target_value=target_value,
                    unit=unit,
                    current_value=current_value,
                    period=period,
                    points_service=self.points_service
                )
            
            # Ocultar formulario y recargar metas
            self.form_container.visible = False
            self._load_goals()
            self.page.update()
        except Exception as ex:
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"Error al guardar: {str(ex)}"),
                bgcolor=ft.Colors.RED
            )
            self.page.snack_bar.open = True
            self.page.update()

