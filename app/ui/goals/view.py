"""
Vista principal de metas.
"""
import flet as ft
from datetime import datetime
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
        self.form_container = None  # Contenedor del formulario
        self._editing_goal_id = None  # ID de la meta que se está editando (None si no hay ninguna)
        self._sort_order = "recent"  # "recent" para más reciente primero, "oldest" para más antiguo primero
    
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
        # Asegurar que form_container no sea None
        if self.form_container is None:
            self.form_container = ft.Container(visible=False)
        
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
                        "🎯 Mis Metas",
                        size=24,
                        weight=ft.FontWeight.BOLD,
                        color=title_color
                    ),
                    ft.Row(
                        [
                            sort_button,
                            ft.IconButton(
                                icon=ft.Icons.ADD,
                                on_click=self._toggle_form,
                                tooltip="Agregar meta",
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
        
        goals = list(self.goal_service.get_all_goals())
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
            # Ordenar las metas según el filtro seleccionado
            if self._sort_order == "recent":
                # Más reciente primero (created_at más reciente)
                goals.sort(key=lambda g: g.created_at if g.created_at else datetime.min, reverse=True)
            else:
                # Más antiguo primero (created_at más antiguo)
                goals.sort(key=lambda g: g.created_at if g.created_at else datetime.max)
            
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
                        # Si esta meta se está editando, mostrar formulario inline en lugar de la tarjeta
                        if self._editing_goal_id == goal.id:
                            self.goals_container.controls.append(
                                self._build_inline_form(goal)
                            )
                        else:
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
        is_dark = self.page.theme_mode == ft.ThemeMode.DARK
        bg_color = ft.Colors.WHITE if not is_dark else ft.Colors.SURFACE
        
        # Determinar si la meta está completada
        is_completed = goal.target_value is not None and goal.current_value >= goal.target_value
        
        # Progreso
        progress = (goal.current_value / goal.target_value * 100) if goal.target_value and goal.target_value > 0 else 0
        progress_text = f"{goal.current_value:.1f} / {goal.target_value:.1f} {goal.unit or ''}" if goal.target_value else f"{goal.current_value:.1f} {goal.unit or ''}"
        
        # Nombre del período
        period_names = {
            "semana": "Semanal",
            "mes": "Mensual",
            "trimestre": "Trimestral",
            "semestre": "Semestral",
            "anual": "Anual"
        }
        period_display = period_names.get(goal.period or "mes", "Mensual")
        
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
        
        content = ft.Column(
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
                            bgcolor=ft.Colors.RED_50 if not is_dark else ft.Colors.RED_900,
                            border_radius=4
                        ),
                        edit_button,
                        delete_button
                    ],
                    spacing=8,
                    vertical_alignment=ft.CrossAxisAlignment.START
                ),
                ft.Text(
                    goal.description or "",
                    size=12,
                    color=ft.Colors.GREY,
                    visible=bool(goal.description)
                ),
                ft.Row(
                    [
                        ft.Container(
                            content=ft.Column(
                                [
                                    ft.Row(
                                        [
                                            ft.Text("Progreso", size=12, color=ft.Colors.GREY_700),
                                            # Botones de incremento/decremento
                                            ft.Row(
                                                [
                                                    ft.IconButton(
                                                        icon=ft.Icons.REMOVE,
                                                        icon_size=20,
                                                        tooltip="Decrementar",
                                                        on_click=lambda e, g=goal: self._decrement_progress(g),
                                                        icon_color=btn_color,
                                                        disabled=goal.current_value <= 0
                                                    ),
                                                    ft.IconButton(
                                                        icon=ft.Icons.ADD,
                                                        icon_size=20,
                                                        tooltip="Incrementar",
                                                        on_click=lambda e, g=goal: self._increment_progress(g),
                                                        icon_color=btn_color
                                                    )
                                                ],
                                                spacing=4,
                                                tight=True
                                            )
                                        ],
                                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                                    ),
                                    ft.Text(progress_text, size=14, weight=ft.FontWeight.BOLD),
                                    ft.ProgressBar(
                                        value=progress / 100,
                                        color=ft.Colors.GREEN if is_completed else ft.Colors.RED_500,
                                        bgcolor=ft.Colors.GREY_300 if not is_dark else ft.Colors.GREY_700,
                                        width=200
                                    )
                                ],
                                spacing=4
                            ),
                            expand=True
                        )
                    ],
                    spacing=8
                )
            ],
            spacing=8
        )
        
        return ft.Container(
            content=content,
            padding=16,
            bgcolor=bg_color,
            border_radius=8,
            margin=ft.margin.only(bottom=8)
        )
    
    def _build_form_container(self) -> ft.Container:
        """Construye el contenedor del formulario para crear/editar metas."""
        is_dark = self.page.theme_mode == ft.ThemeMode.DARK
        bg_color = ft.Colors.WHITE if not is_dark else ft.Colors.BLACK
        btn_color = ft.Colors.RED_700 if not is_dark else ft.Colors.RED_500
        
        # Campos del formulario
        self._form_title_field = ft.TextField(
            label="Título",
            hint_text="Ingresa el título de la meta",
            expand=True
        )
        
        self._form_description_field = ft.TextField(
            label="Descripción",
            hint_text="Descripción de la meta (opcional)",
            multiline=True,
            min_lines=2,
            max_lines=4
        )
        
        self._form_target_value_field = ft.TextField(
            label="Valor objetivo",
            hint_text="Valor objetivo (opcional)",
            keyboard_type=ft.KeyboardType.NUMBER
        )
        
        self._form_current_value_field = ft.TextField(
            label="Valor actual",
            hint_text="Valor actual",
            value="0.0",
            keyboard_type=ft.KeyboardType.NUMBER
        )
        
        self._form_unit_field = ft.TextField(
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
        
        self._form_period_field = ft.Dropdown(
            label="Período",
            hint_text="Selecciona el período de la meta",
            options=period_options,
            value="mes"
        )
        
        # Botones
        save_button = ft.ElevatedButton(
            "Guardar",
            on_click=self._save_goal_from_form,
            bgcolor=btn_color,
            color=ft.Colors.WHITE
        )
        
        cancel_button = ft.TextButton(
            "Cancelar",
            on_click=self._cancel_inline_edit,
            style=ft.ButtonStyle(color=btn_color)
        )
        
        form_content = ft.Column(
            [
                ft.Container(
                    content=ft.Row(
                        [
                            ft.Text(
                                "Nueva Meta",
                                size=20,
                                weight=ft.FontWeight.BOLD,
                                color=ft.Colors.RED_700 if not is_dark else ft.Colors.RED_500
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
                            self._form_title_field,
                            self._form_description_field,
                            self._form_target_value_field,
                            self._form_current_value_field,
                            self._form_unit_field,
                            self._form_period_field
                        ],
                        spacing=16
                    ),
                    padding=16
                )
            ],
            spacing=0
        )
        
        return ft.Container(
            content=form_content,
            visible=False,
            bgcolor=bg_color
        )
    
    def _new_goal_in_form(self):
        """Prepara el formulario para crear una nueva meta."""
        self._form_title_field.value = ""
        self._form_description_field.value = ""
        self._form_target_value_field.value = ""
        self._form_current_value_field.value = "0.0"
        self._form_unit_field.value = ""
        self._form_period_field.value = "mes"
        self.form_container.visible = True
        self.page.update()
    
    def _edit_goal_in_form(self, goal: Goal):
        """Prepara el formulario para editar una meta existente."""
        if self.form_container is None:
            return
        self._form_title_field.value = goal.title
        self._form_description_field.value = goal.description or ""
        self._form_target_value_field.value = str(goal.target_value) if goal.target_value else ""
        self._form_current_value_field.value = str(goal.current_value)
        self._form_unit_field.value = goal.unit or ""
        self._form_period_field.value = goal.period or "mes"
        self.form_container.visible = True
        self.page.update()
    
    def _toggle_form(self, e, goal: Optional[Goal] = None):
        """Muestra u oculta el formulario para crear/editar una meta."""
        if goal:
            self._editing_goal_id = goal.id
            self._edit_goal_in_form(goal)
        else:
            self._editing_goal_id = None
            self._new_goal_in_form()
    
    def _cancel_inline_edit(self, e=None):
        """Cancela la edición inline y oculta el formulario."""
        if self.form_container is not None:
            self.form_container.visible = False
        self._editing_goal_id = None
        self._load_goals()
        self.page.update()
    
    def _save_goal_from_form(self, e):
        """Guarda la meta desde el formulario."""
        try:
            title = self._form_title_field.value.strip()
            if not title:
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text("El título es requerido"),
                    bgcolor=ft.Colors.RED
                )
                self.page.snack_bar.open = True
                self.page.update()
                return
            
            description = self._form_description_field.value.strip() or None
            target_value = float(self._form_target_value_field.value) if self._form_target_value_field.value.strip() else None
            current_value = float(self._form_current_value_field.value) if self._form_current_value_field.value.strip() else 0.0
            unit = self._form_unit_field.value.strip() or None
            period = self._form_period_field.value or "mes"
            
            if self._editing_goal_id:
                # Actualizar meta existente
                goal = self.goal_service.get_goal(self._editing_goal_id)
                if goal:
                    was_completed = goal.target_value and goal.current_value >= goal.target_value
                    
                    updated_goal = Goal(
                        id=goal.id,
                        title=title,
                        description=description,
                        target_value=target_value,
                        current_value=current_value,
                        unit=unit,
                        period=period,
                        created_at=goal.created_at,
                        updated_at=goal.updated_at
                    )
                    # Verificar si la meta cambió de estado (completa/incompleta)
                    is_completed_now = target_value and current_value >= target_value
                    
                    # Actualizar el goal
                    self.goal_service.update_goal(updated_goal)
                    
                    # Si el estado cambió, manejar los puntos
                    if was_completed != is_completed_now:
                        if is_completed_now and not was_completed and self.points_service:
                            self.points_service.add_points(1.00)  # Sumar 1.00 puntos por completar
                        elif was_completed and not is_completed_now and self.points_service:
                            self.points_service.add_points(-1.00)  # Restar 1.00 puntos por descompletar
            else:
                # Crear nueva meta
                self.goal_service.create_goal(
                    title=title,
                    description=description,
                    target_value=target_value,
                    current_value=current_value,
                    unit=unit,
                    period=period,
                    points_service=self.points_service
                )
            
            # Ocultar formulario y recargar metas
            if self.form_container is not None:
                self.form_container.visible = False
            self._editing_goal_id = None
            self._load_goals()
            # Actualizar header y resumen si están visibles
            if hasattr(self.page, '_home_view_ref'):
                home_view = self.page._home_view_ref
                home_view._build_ui()
            else:
                self.page.update()
        except Exception as ex:
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"Error al guardar: {str(ex)}"),
                bgcolor=ft.Colors.RED
            )
            self.page.snack_bar.open = True
            self.page.update()
    
    def _increment_progress(self, goal: Goal):
        """Incrementa el progreso de una meta en 1.0."""
        try:
            if goal.id:
                # Usar el método increment_progress del servicio
                success = self.goal_service.increment_progress(
                    goal.id, 
                    increment=1.0, 
                    points_service=self.points_service
                )
                if success:
                    self._load_goals()
                    # Actualizar header y resumen si están visibles
                    if hasattr(self.page, '_home_view_ref'):
                        home_view = self.page._home_view_ref
                        home_view._build_ui()
        except Exception as e:
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"Error al incrementar progreso: {str(e)}"),
                bgcolor=ft.Colors.RED
            )
            self.page.snack_bar.open = True
            self.page.update()
    
    def _decrement_progress(self, goal: Goal):
        """Decrementa el progreso de una meta en 1.0."""
        try:
            if goal.id and goal.current_value > 0:
                # Verificar si la meta estaba completa antes de decrementar
                was_completed = goal.target_value and goal.current_value >= goal.target_value
                
                # Obtener la meta actualizada y decrementar
                updated_goal = self.goal_service.get_goal(goal.id)
                if updated_goal:
                    new_value = max(0.0, updated_goal.current_value - 1.0)
                    updated_goal.current_value = new_value
                    self.goal_service.update_goal(updated_goal)
                    
                    # Si la meta estaba completa y ahora no lo está, restar puntos
                    if was_completed and self.points_service:
                        if not updated_goal.target_value or new_value < updated_goal.target_value:
                            self.points_service.add_points(-1.00)  # Restar 1.00 puntos
                    
                    self._load_goals()
                    # Actualizar header y resumen si están visibles
                    if hasattr(self.page, '_home_view_ref'):
                        home_view = self.page._home_view_ref
                        home_view._build_ui()
        except Exception as e:
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"Error al decrementar progreso: {str(e)}"),
                bgcolor=ft.Colors.RED
            )
            self.page.snack_bar.open = True
            self.page.update()
    
    def _delete_goal(self, goal: Goal):
        """Elimina una meta."""
        try:
            # Si la meta estaba completada, restar puntos antes de eliminar
            was_completed = goal.target_value and goal.current_value >= goal.target_value
            self.goal_service.delete_goal(goal.id)
            if was_completed and self.points_service:
                self.points_service.add_points(-1.00)  # Restar 1.00 puntos (el valor que se otorga por completar)
            self._load_goals()
            # Actualizar header y resumen si están visibles
            if hasattr(self.page, '_home_view_ref'):
                home_view = self.page._home_view_ref
                home_view._build_ui()
            else:
                self.page.update()
        except Exception as ex:
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"Error al eliminar: {str(ex)}"),
                bgcolor=ft.Colors.RED
            )
            self.page.snack_bar.open = True
            self.page.update()
    
    def _build_inline_form(self, goal: Goal) -> ft.Container:
        """Construye un formulario inline para editar una meta en su posición."""
        is_dark = self.page.theme_mode == ft.ThemeMode.DARK
        bg_color = ft.Colors.WHITE if not is_dark else ft.Colors.BLACK
        btn_color = ft.Colors.RED_700 if not is_dark else ft.Colors.RED_500
        
        # Campos del formulario
        title_field = ft.TextField(
            label="Título",
            value=goal.title,
            expand=True
        )
        
        description_field = ft.TextField(
            label="Descripción",
            value=goal.description or "",
            multiline=True,
            min_lines=2,
            max_lines=4
        )
        
        target_value_field = ft.TextField(
            label="Valor objetivo",
            value=str(goal.target_value) if goal.target_value else "",
            keyboard_type=ft.KeyboardType.NUMBER
        )
        
        current_value_field = ft.TextField(
            label="Valor actual",
            value=str(goal.current_value),
            keyboard_type=ft.KeyboardType.NUMBER
        )
        
        unit_field = ft.TextField(
            label="Unidad",
            value=goal.unit or ""
        )
        
        # Selector de período
        period_options = [
            ft.dropdown.Option("semana", "Semana"),
            ft.dropdown.Option("mes", "Mes"),
            ft.dropdown.Option("trimestre", "Trimestre"),
            ft.dropdown.Option("semestre", "Semestre"),
            ft.dropdown.Option("anual", "Anual")
        ]
        
        period_field = ft.Dropdown(
            label="Período",
            options=period_options,
            value=goal.period or "mes"
        )
        
        # Botones
        save_button = ft.ElevatedButton(
            "Guardar",
            on_click=lambda e: self._save_inline_goal(e, goal, title_field, description_field, target_value_field, current_value_field, unit_field, period_field),
            bgcolor=btn_color,
            color=ft.Colors.WHITE
        )
        
        cancel_button = ft.TextButton(
            "Cancelar",
            on_click=lambda e: self._cancel_inline_edit(e),
            style=ft.ButtonStyle(color=btn_color)
        )
        
        form_content = ft.Column(
            [
                ft.Row(
                    [
                        ft.Text(
                            "Editar Meta",
                            size=18,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.RED_700 if not is_dark else ft.Colors.RED_500,
                            expand=True
                        ),
                        cancel_button,
                        save_button
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                ),
                title_field,
                description_field,
                target_value_field,
                current_value_field,
                unit_field,
                period_field
            ],
            spacing=12
        )
        
        return ft.Container(
            content=form_content,
            padding=16,
            bgcolor=bg_color,
            border_radius=8,
            margin=ft.margin.only(bottom=8)
        )
    
    def _save_inline_goal(self, e, goal: Goal, title_field, description_field, target_value_field, current_value_field, unit_field, period_field):
        """Guarda una meta desde el formulario inline."""
        try:
            title = title_field.value.strip()
            if not title:
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text("El título es requerido"),
                    bgcolor=ft.Colors.RED
                )
                self.page.snack_bar.open = True
                self.page.update()
                return
            
            description = description_field.value.strip() or None
            target_value = float(target_value_field.value) if target_value_field.value.strip() else None
            current_value = float(current_value_field.value) if current_value_field.value.strip() else 0.0
            unit = unit_field.value.strip() or None
            period = period_field.value or "mes"
            
            was_completed = goal.target_value and goal.current_value >= goal.target_value
            
            updated_goal = Goal(
                id=goal.id,
                title=title,
                description=description,
                target_value=target_value,
                current_value=current_value,
                unit=unit,
                period=period,
                created_at=goal.created_at,
                updated_at=goal.updated_at
            )
            self.goal_service.update_goal(updated_goal)
            
            # Si la meta estaba completa y ahora no lo está, restar puntos
            is_completed_now = target_value and current_value >= target_value
            if was_completed and not is_completed_now and self.points_service:
                self.points_service.add_points(-1.00)  # Restar 1.00 puntos
            # Si la meta no estaba completa y ahora lo está, sumar puntos
            elif not was_completed and is_completed_now and self.points_service:
                self.points_service.add_points(1.00)  # Sumar 1.00 puntos
            
            # Ocultar formulario y recargar metas
            self._editing_goal_id = None
            self._load_goals()
            # Actualizar header y resumen si están visibles
            if hasattr(self.page, '_home_view_ref'):
                home_view = self.page._home_view_ref
                home_view._build_ui()
            else:
                self.page.update()
        except Exception as ex:
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"Error al guardar: {str(ex)}"),
                bgcolor=ft.Colors.RED
            )
            self.page.snack_bar.open = True
            self.page.update()
    
    def _toggle_sort_order(self, e):
        """Alterna entre ordenamiento más reciente primero y más antiguo primero."""
        self._sort_order = "oldest" if self._sort_order == "recent" else "recent"
        # Recargar metas con el nuevo orden
        self._load_goals()
        # Notificar a home_view para que reconstruya la UI y actualice el icono
        # Buscar la instancia de HomeView en la página
        if hasattr(self.page, '_home_view_ref'):
            home_view = self.page._home_view_ref
            home_view._build_ui()
        elif self.page:
            self.page.update()
