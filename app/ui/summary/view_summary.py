"""
Vista de resumen con estadísticas generales.
"""
import flet as ft
from datetime import date

from app.services.task_service import TaskService
from app.services.habit_service import HabitService
from app.services.goal_service import GoalService
from app.services.points_service import PointsService
from app.services.reward_service import RewardService


class SummaryView:
    """Vista de resumen con estadísticas de tareas, hábitos y metas."""
    
    def __init__(self, page: ft.Page, task_service: TaskService,
                 habit_service: HabitService, goal_service: GoalService,
                 points_service: PointsService = None, reward_service: RewardService = None):
        """
        Inicializa la vista de resumen.
        
        Args:
            page: Página de Flet.
            task_service: Servicio de tareas.
            habit_service: Servicio de hábitos.
            goal_service: Servicio de metas.
            points_service: Servicio de puntos (opcional).
            reward_service: Servicio de recompensas (opcional).
        """
        self.page = page
        self.task_service = task_service
        self.habit_service = habit_service
        self.goal_service = goal_service
        self.points_service = points_service
        self.reward_service = reward_service
        
        # Estado del panel de recompensas
        self._rewards_filter = "por_alcanzar"  # por_alcanzar, a_reclamar, reclamada
        self._rewards_container = None
        self._rewards_panel_container = None
        self._filter_buttons = {}  # Diccionario para guardar referencias a los botones de filtro
        self._show_add_form = False  # Controla si se muestra el formulario de agregar
        self._add_form_container = None  # Contenedor del formulario
        self._add_button_ref = None  # Referencia al botón de agregar
        self._claiming_reward_id = None  # ID de la recompensa que se está reclamando (None si no hay ninguna)
        self._claim_panels = {}  # Diccionario para guardar referencias a los paneles de confirmación {reward_id: panel}
    
    def build_ui(self) -> ft.Container:
        """
        Construye la interfaz de usuario del resumen.
        
        Returns:
            Container con la vista de resumen.
        """
        # Forzar tema oscuro (negro) para el resumen
        is_dark = True  # Siempre tema oscuro
        bg_color = ft.Colors.BLACK
        surface_color = ft.Colors.SURFACE
        title_color = ft.Colors.RED_500
        
        title_bar = ft.Container(
            content=ft.Row(
                [
                    ft.Text(
                        "📊 Resumen",
                        size=24,
                        weight=ft.FontWeight.BOLD,
                        color=title_color
                    )
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN
            ),
            padding=16,
            bgcolor=surface_color
        )
        
        # Obtener estadísticas
        stats = self._calculate_stats()
        
        # Contenedor principal con scroll
        content = ft.Column(
            [
                # Sección de nivel y puntos
                self._build_level_card() if self.points_service else ft.Container(),
                
                # Panel de recompensas (justo debajo del panel "Tu Nivel")
                self._build_rewards_panel() if self.reward_service else ft.Container(),
                
                # Estadísticas de Tareas
                self._build_section_card(
                    "📋 Tareas",
                    [
                        ("Total", str(stats['tasks']['total']), ft.Colors.BLUE),
                        ("Pendientes", str(stats['tasks']['pending']), ft.Colors.ORANGE),
                        ("Completadas", str(stats['tasks']['completed']), ft.Colors.GREEN),
                    ]
                ),
                
                # Estadísticas de Hábitos
                self._build_section_card(
                    "🔁 Hábitos",
                    [
                        ("Total", str(stats['habits']['total']), ft.Colors.PURPLE),
                        ("Completados hoy", str(stats['habits']['completed_today']), ft.Colors.GREEN),
                        ("Racha promedio", f"{stats['habits']['avg_streak']:.1f} días", ft.Colors.AMBER),
                    ]
                ),
                
                # Estadísticas de Metas
                self._build_section_card(
                    "🎯 Metas",
                    [
                        ("Total", str(stats['goals']['total']), ft.Colors.RED),
                        ("Con progreso", str(stats['goals']['with_progress']), ft.Colors.GREEN),
                        ("Progreso promedio", f"{stats['goals']['avg_progress']:.1f}%", ft.Colors.BLUE),
                    ]
                ),
                
                # Resumen general
                self._build_summary_card(stats)
            ],
            spacing=16,
            scroll=ft.ScrollMode.AUTO,
            expand=True
        )
        
        # Vista principal
        return ft.Container(
            content=ft.Column(
                [
                    title_bar,
                    ft.Container(
                        content=content,
                        padding=16,
                        expand=True,
                        bgcolor=bg_color
                    )
                ],
                spacing=0,
                expand=True
            ),
            expand=True,
            bgcolor=bg_color
        )
    
    def _calculate_stats(self) -> dict:
        """
        Calcula las estadísticas de tareas, hábitos y metas.
        
        Returns:
            Diccionario con las estadísticas calculadas.
        """
        # Estadísticas de tareas
        all_tasks = self.task_service.get_all_tasks()
        pending_tasks = self.task_service.get_pending_tasks()
        completed_tasks = self.task_service.get_completed_tasks()
        
        # Estadísticas de hábitos
        all_habits = self.habit_service.get_all_habits()
        completed_today = sum(1 for habit in all_habits 
                             if self.habit_service.is_completed_today(habit.id))
        streaks = [self.habit_service.get_streak(habit.id) for habit in all_habits]
        avg_streak = sum(streaks) / len(streaks) if streaks else 0
        
        # Estadísticas de metas
        all_goals = self.goal_service.get_all_goals()
        goals_with_progress = [g for g in all_goals if g.current_value > 0]
        progress_percentages = [self.goal_service.get_progress_percentage(g.id) 
                               for g in all_goals if g.target_value]
        avg_progress = sum(progress_percentages) / len(progress_percentages) if progress_percentages else 0
        
        return {
            'tasks': {
                'total': len(all_tasks),
                'pending': len(pending_tasks),
                'completed': len(completed_tasks)
            },
            'habits': {
                'total': len(all_habits),
                'completed_today': completed_today,
                'avg_streak': avg_streak
            },
            'goals': {
                'total': len(all_goals),
                'with_progress': len(goals_with_progress),
                'avg_progress': avg_progress
            }
        }
    
    def _build_section_card(self, title: str, stats: list) -> ft.Container:
        """
        Construye una tarjeta de estadísticas para una sección.
        
        Args:
            title: Título de la sección.
            stats: Lista de tuplas (label, value, color).
        
        Returns:
            Container con la tarjeta de estadísticas.
        """
        # Forzar tema oscuro para las tarjetas
        is_dark = True  # Siempre tema oscuro
        bg_color = ft.Colors.SURFACE
        text_color = ft.Colors.GREY_400
        
        stat_items = []
        for label, value, color in stats:
            stat_items.append(
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Text(
                                value,
                                size=32,
                                weight=ft.FontWeight.BOLD,
                                color=color
                            ),
                            ft.Text(
                                label,
                                size=12,
                                color=text_color
                            )
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=4,
                        tight=True
                    ),
                    padding=16,
                    expand=True
                )
            )
        
        return ft.Container(
            content=ft.Column(
                [
                    ft.Text(
                        title,
                        size=18,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.RED_500
                    ),
                    ft.Row(
                        stat_items,
                        spacing=8,
                        alignment=ft.MainAxisAlignment.SPACE_EVENLY
                    )
                ],
                spacing=12
            ),
            padding=20,
            bgcolor=bg_color,
            border_radius=12,
            border=ft.border.all(1, ft.Colors.OUTLINE)
        )
    
    def _build_summary_card(self, stats: dict) -> ft.Container:
        """
        Construye una tarjeta de resumen general.
        
        Args:
            stats: Diccionario con todas las estadísticas.
        
        Returns:
            Container con la tarjeta de resumen.
        """
        # Forzar tema oscuro para las tarjetas
        is_dark = True  # Siempre tema oscuro
        bg_color = ft.Colors.SURFACE
        text_color = ft.Colors.GREY_400
        
        total_items = (
            stats['tasks']['total'] +
            stats['habits']['total'] +
            stats['goals']['total']
        )
        
        completion_rate = 0
        if stats['tasks']['total'] > 0:
            completion_rate = (stats['tasks']['completed'] / stats['tasks']['total']) * 100
        
        return ft.Container(
            content=ft.Column(
                [
                    ft.Text(
                        "📈 Resumen General",
                        size=18,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.RED_500
                    ),
                    ft.Divider(),
                    ft.Row(
                        [
                            ft.Column(
                                [
                                    ft.Text(
                                        str(total_items),
                                        size=28,
                                        weight=ft.FontWeight.BOLD,
                                        color=ft.Colors.BLUE
                                    ),
                                    ft.Text(
                                        "Items totales",
                                        size=12,
                                        color=text_color
                                    )
                                ],
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                spacing=4,
                                expand=True
                            ),
                            ft.Column(
                                [
                                    ft.Text(
                                        f"{completion_rate:.1f}%",
                                        size=28,
                                        weight=ft.FontWeight.BOLD,
                                        color=ft.Colors.GREEN
                                    ),
                                    ft.Text(
                                        "Tareas completadas",
                                        size=12,
                                        color=text_color
                                    )
                                ],
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                spacing=4,
                                expand=True
                            )
                        ],
                        spacing=16,
                        alignment=ft.MainAxisAlignment.SPACE_EVENLY
                    )
                ],
                spacing=12
            ),
            padding=20,
            bgcolor=bg_color,
            border_radius=12,
            border=ft.border.all(2, ft.Colors.RED_500)
        )
    
    def _build_level_card(self) -> ft.Container:
        """Construye una tarjeta con información de nivel y puntos."""
        if not self.points_service:
            return ft.Container()
        
        level_info = self.points_service.get_level_info()
        current_level = level_info["current_level"]
        level_display_name = level_info["level_display_name"]
        points = level_info["points"]
        next_level = level_info["next_level"]
        progress = level_info["progress"]
        points_to_next = level_info["points_to_next"]
        
        # Forzar tema oscuro para la tarjeta de nivel
        is_dark = True  # Siempre tema oscuro
        bg_color = ft.Colors.SURFACE
        text_color = ft.Colors.GREY_400
        
        # Color según el nivel (gradiente de colores)
        level_colors = {
            "Nobody": ft.Colors.GREY,
            "Beginner": ft.Colors.BLUE,
            "Novice": ft.Colors.CYAN,
            "Intermediate": ft.Colors.GREEN,
            "Proficient": ft.Colors.LIME,
            "Advance": ft.Colors.AMBER,
            "Expert": ft.Colors.ORANGE,
            "Master": ft.Colors.RED,
            "Guru": ft.Colors.PURPLE,
            "Legendary": ft.Colors.PINK,
            "Like_a_God": ft.Colors.YELLOW
        }
        level_color = level_colors.get(current_level.display_name, ft.Colors.PRIMARY)
        
        return ft.Container(
            content=ft.Column(
                [
                    ft.Text(
                        "🏆 Tu Nivel",
                        size=18,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.RED_500
                    ),
                    ft.Container(
                        content=ft.Column(
                            [
                                ft.Text(
                                    level_display_name,
                                    size=32,
                                    weight=ft.FontWeight.BOLD,
                                    color=level_color,
                                    text_align=ft.TextAlign.CENTER
                                ),
                                ft.Text(
                                    f"{points:.2f} puntos",
                                    size=16,
                                    color=text_color,
                                    text_align=ft.TextAlign.CENTER
                                )
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=4
                        ),
                        padding=16
                    ),
                    ft.ProgressBar(
                        value=progress / 100.0 if progress > 0 else 0,
                        color=level_color,
                        bgcolor=ft.Colors.GREY_700,
                        height=20
                    ),
                    ft.Text(
                        f"Próximo nivel: {next_level.display_name} ({points_to_next:.2f} puntos)",
                        size=12,
                        color=text_color,
                        text_align=ft.TextAlign.CENTER
                    ) if current_level != next_level else ft.Text(
                        "¡Nivel máximo alcanzado!",
                        size=12,
                        color=level_color,
                        text_align=ft.TextAlign.CENTER,
                        weight=ft.FontWeight.BOLD
                    )
                ],
                spacing=12,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER
            ),
            padding=20,
            bgcolor=bg_color,
            border_radius=12,
            border=ft.border.all(2, level_color)
        )
    
    def _build_rewards_panel(self) -> ft.Container:
        """Construye el panel de recompensas."""
        if not self.reward_service:
            return ft.Container()
        
        # Actualizar estados de recompensas basándose en puntos actuales
        # Si alguna recompensa cambió a "a_reclamar", cambiar el filtro automáticamente
        changed_to_available = self.reward_service.update_reward_statuses()
        if changed_to_available and self._rewards_filter == "por_alcanzar":
            # Cambiar automáticamente al filtro "a_reclamar" para mostrar las recompensas disponibles
            self._rewards_filter = "a_reclamar"
        
        # Forzar tema oscuro
        is_dark = True
        bg_color = ft.Colors.SURFACE
        text_color = ft.Colors.GREY_400
        title_color = ft.Colors.RED_500
        
        # Construir filtros
        filters = self._build_rewards_filters()
        
        # Construir lista de recompensas
        rewards_list = self._build_rewards_list()
        
        # Formulario de agregar recompensa (inline)
        add_form = self._build_add_reward_form() if self._show_add_form else None
        
        # Botón para agregar nueva recompensa / cancelar
        add_button = ft.ElevatedButton(
            "➕ Nueva Recompensa" if not self._show_add_form else "❌ Cancelar",
            on_click=self._toggle_add_form,
            bgcolor=ft.Colors.GREEN_700 if not self._show_add_form else ft.Colors.RED_700,
            color=ft.Colors.WHITE,
            icon=ft.Icons.ADD if not self._show_add_form else ft.Icons.CLOSE
        )
        self._add_button_ref = add_button  # Guardar referencia
        
        # Construir contenido del panel
        panel_content = [
            ft.Text(
                "🎁 Recompensas",
                size=18,
                weight=ft.FontWeight.BOLD,
                color=title_color
            ),
            filters,
        ]
        
        # Agregar formulario si está visible
        if self._show_add_form and add_form:
            panel_content.append(add_form)
        
        # Agregar lista de recompensas y botón
        panel_content.extend([rewards_list, add_button])
        
        return ft.Container(
            content=ft.Column(
                panel_content,
                spacing=12,
                horizontal_alignment=ft.CrossAxisAlignment.STRETCH
            ),
            padding=20,
            bgcolor=bg_color,
            border_radius=12,
            border=ft.border.all(2, ft.Colors.GREY_700),
            margin=ft.margin.only(bottom=16)
        )
    
    def _build_rewards_filters(self) -> ft.Row:
        """Construye los filtros de recompensas."""
        def on_filter_change(e):
            self._rewards_filter = e.control.data
            self._update_filter_buttons()
            # Al cambiar de filtro manualmente, NO actualizar estados ni cambiar el filtro automáticamente
            # Solo refrescar la lista con el nuevo filtro
            self._refresh_rewards_list(update_states=False, auto_switch_filter=False)
        
        # Crear botones con referencias
        button_por_alcanzar = ft.ElevatedButton(
            "🟡 Por Alcanzar",
            on_click=on_filter_change,
            data="por_alcanzar",
            bgcolor=ft.Colors.YELLOW_700 if self._rewards_filter == "por_alcanzar" else ft.Colors.GREY_700,
            color=ft.Colors.WHITE,
            expand=True
        )
        
        button_a_reclamar = ft.ElevatedButton(
            "🟢 A Reclamar",
            on_click=on_filter_change,
            data="a_reclamar",
            bgcolor=ft.Colors.GREEN_700 if self._rewards_filter == "a_reclamar" else ft.Colors.GREY_700,
            color=ft.Colors.WHITE,
            expand=True
        )
        
        button_reclamadas = ft.ElevatedButton(
            "⚪ Reclamadas",
            on_click=on_filter_change,
            data="reclamada",
            bgcolor=ft.Colors.GREY_600 if self._rewards_filter == "reclamada" else ft.Colors.GREY_700,
            color=ft.Colors.WHITE,
            expand=True
        )
        
        # Guardar referencias
        self._filter_buttons = {
            "por_alcanzar": button_por_alcanzar,
            "a_reclamar": button_a_reclamar,
            "reclamada": button_reclamadas
        }
        
        return ft.Row(
            [button_por_alcanzar, button_a_reclamar, button_reclamadas],
            spacing=8
        )
    
    def _update_filter_buttons(self):
        """Actualiza los colores de los botones de filtro según el filtro activo."""
        # Colores para cada filtro
        filter_colors = {
            "por_alcanzar": ft.Colors.YELLOW_700,
            "a_reclamar": ft.Colors.GREEN_700,
            "reclamada": ft.Colors.GREY_600
        }
        
        # Actualizar cada botón
        for filter_key, button in self._filter_buttons.items():
            if filter_key == self._rewards_filter:
                button.bgcolor = filter_colors[filter_key]
            else:
                button.bgcolor = ft.Colors.GREY_700
        
        # Actualizar la página para reflejar los cambios
        if self._filter_buttons:
            self.page.update()
    
    def _build_rewards_list(self) -> ft.Column:
        """Construye la lista de recompensas según el filtro actual."""
        rewards = self.reward_service.get_rewards_by_status(self._rewards_filter)
        
        # Si el contenedor ya existe, solo actualizar sus controles
        if self._rewards_container is None:
            self._rewards_container = ft.Column([], spacing=8)
        
        # Limpiar controles existentes
        self._rewards_container.controls.clear()
        
        if not rewards:
            empty_text = {
                "por_alcanzar": "No hay recompensas por alcanzar",
                "a_reclamar": "No hay recompensas disponibles para reclamar",
                "reclamada": "No hay recompensas reclamadas"
            }
            
            self._rewards_container.controls.append(
                ft.Text(
                    empty_text.get(self._rewards_filter, "No hay recompensas"),
                    size=14,
                    color=ft.Colors.GREY_500,
                    text_align=ft.TextAlign.CENTER
                )
            )
            self._rewards_container.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        else:
            reward_cards = [self._build_reward_card(reward) for reward in rewards]
            self._rewards_container.controls.extend(reward_cards)
            self._rewards_container.horizontal_alignment = None
        
        return self._rewards_container
    
    def _build_reward_card(self, reward) -> ft.Container:
        """Construye una tarjeta individual de recompensa."""
        current_points = self.points_service.get_total_points() if self.points_service else 0
        is_available = current_points >= reward.target_points
        
        # Colores según estado
        status_colors = {
            "por_alcanzar": ft.Colors.YELLOW_700,
            "a_reclamar": ft.Colors.GREEN_700,
            "reclamada": ft.Colors.GREY_600
        }
        status_color = status_colors.get(reward.status, ft.Colors.GREY_700)
        
        # Checkbox (habilitado solo si está disponible y en estado "a_reclamar")
        checkbox = ft.Checkbox(
            value=reward.status == "reclamada",
            disabled=not (is_available and reward.status == "a_reclamar"),
            on_change=lambda e, r=reward: self._on_reward_checkbox_change(e, r)
        )
        
        # Información de la recompensa
        reward_info = ft.Column(
            [
                ft.Text(
                    reward.name,
                    size=16,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.WHITE
                ),
                ft.Text(
                    reward.description or "Sin descripción",
                    size=12,
                    color=ft.Colors.GREY_400
                ) if reward.description else ft.Container(),
                ft.Text(
                    f"Objetivo: {reward.target_points:.2f} puntos",
                    size=12,
                    color=status_color
                ),
                ft.Text(
                    f"Puntos actuales: {current_points:.2f}",
                    size=11,
                    color=ft.Colors.GREY_500
                )
            ],
            spacing=4,
            expand=True
        )
        
        # Botones de acción
        action_buttons_list = []
        
        # Botón de editar (solo si no está reclamada)
        if reward.status != "reclamada":
            action_buttons_list.append(
                ft.IconButton(
                    ft.Icons.EDIT,
                    on_click=lambda e, r=reward: self._show_edit_reward_dialog(r),
                    tooltip="Editar",
                    icon_color=ft.Colors.BLUE
                )
            )
        
        # Botón de eliminar (siempre disponible)
        action_buttons_list.append(
            ft.IconButton(
                ft.Icons.DELETE,
                on_click=lambda e, r=reward: self._delete_reward(r),
                tooltip="Eliminar",
                icon_color=ft.Colors.RED
            )
        )
        
        action_buttons = ft.Row(
            action_buttons_list,
            spacing=4
        )
        
        # Panel de confirmación inline (se muestra cuando se hace clic en el checkbox)
        show_panel = self._claiming_reward_id == reward.id
        if show_panel:
            # Siempre crear un nuevo panel para asegurar que esté en el estado inicial (Sí/No visible)
            # Esto garantiza que siempre muestre primero los botones Sí/No
            claim_panel = self._build_claim_confirmation_panel(reward)
            self._claim_panels[reward.id] = claim_panel
        else:
            # Ocultar el panel
            claim_panel = ft.Container(visible=False)
            if reward.id in self._claim_panels:
                self._claim_panels[reward.id].visible = False
        
        # Contenido principal de la tarjeta
        card_content = ft.Column(
            [
                ft.Row(
                    [
                        checkbox,
                        reward_info,
                        action_buttons
                    ],
                    spacing=12,
                    vertical_alignment=ft.CrossAxisAlignment.START
                ),
                claim_panel  # Panel de confirmación debajo de la tarjeta
            ],
            spacing=8
        )
        
        return ft.Container(
            content=card_content,
            padding=12,
            bgcolor=ft.Colors.GREY_900,
            border_radius=8,
            border=ft.border.all(1, status_color),
            margin=ft.margin.only(bottom=8)
        )
    
    def _on_reward_checkbox_change(self, e, reward):
        """Maneja el cambio en el checkbox de una recompensa."""
        if e.control.value and reward.status == "a_reclamar":
            # Mostrar panel de confirmación inline
            self._claiming_reward_id = reward.id
            # Refrescar la lista para mostrar el panel
            self._refresh_rewards_list(update_states=False, auto_switch_filter=False)
        elif not e.control.value:
            # Si se desmarca, ocultar el panel si estaba visible
            if self._claiming_reward_id == reward.id:
                self._claiming_reward_id = None
                self._refresh_rewards_list(update_states=False, auto_switch_filter=False)
            elif reward.status == "reclamada":
                # Si se desmarca una recompensa reclamada, no hacer nada
                e.control.value = True
                self.page.update()
    
    def _build_add_reward_form(self) -> ft.Container:
        """Construye el formulario inline para agregar una nueva recompensa."""
        name_field = ft.TextField(
            label="Nombre de la recompensa",
            hint_text="Ej: Comprar un libro",
            autofocus=True,
            expand=True
        )
        description_field = ft.TextField(
            label="Descripción (opcional)",
            hint_text="Describe tu recompensa",
            multiline=True,
            max_lines=3,
            expand=True
        )
        points_field = ft.TextField(
            label="Puntos objetivo",
            hint_text="Ej: 100.5",
            keyboard_type=ft.KeyboardType.NUMBER,
            expand=True
        )
        
        def on_create(e):
            try:
                name = name_field.value.strip()
                description = description_field.value.strip() if description_field.value else None
                target_points = float(points_field.value) if points_field.value else 0
                
                if not name:
                    self._show_snackbar("El nombre es requerido", ft.Colors.RED)
                    return
                
                if target_points <= 0:
                    self._show_snackbar("Los puntos objetivo deben ser mayores a 0", ft.Colors.RED)
                    return
                
                self.reward_service.create_reward(name, description, target_points)
                
                # Limpiar campos
                name_field.value = ""
                description_field.value = ""
                points_field.value = ""
                
                # Ocultar formulario
                self._show_add_form = False
                # Refrescar lista con actualización de estados (sin cambiar filtro automáticamente al crear)
                self._refresh_rewards_list(update_states=True, auto_switch_filter=False)
                # Reconstruir el panel completo para ocultar el formulario
                if hasattr(self.page, '_home_view_ref'):
                    home_view = self.page._home_view_ref
                    if hasattr(home_view, 'summary_view'):
                        home_view._build_ui()
                        self.page.update()
                self._show_snackbar("Recompensa creada exitosamente", ft.Colors.GREEN)
            except ValueError as ve:
                self._show_snackbar(str(ve), ft.Colors.RED)
            except Exception as ex:
                self._show_snackbar(f"Error: {str(ex)}", ft.Colors.RED)
        
        create_button = ft.ElevatedButton(
            "Crear Recompensa",
            on_click=on_create,
            bgcolor=ft.Colors.GREEN_700,
            color=ft.Colors.WHITE,
            icon=ft.Icons.CHECK,
            expand=True
        )
        
        form_container = ft.Container(
            content=ft.Column(
                [
                    ft.Text(
                        "➕ Nueva Recompensa",
                        size=16,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.GREEN_400
                    ),
                    name_field,
                    description_field,
                    points_field,
                    create_button
                ],
                spacing=12,
                horizontal_alignment=ft.CrossAxisAlignment.STRETCH
            ),
            padding=16,
            bgcolor=ft.Colors.GREY_900,
            border_radius=8,
            border=ft.border.all(2, ft.Colors.GREEN_700),
            margin=ft.margin.only(bottom=8)
        )
        
        self._add_form_container = form_container
        return form_container
    
    def _toggle_add_form(self, e):
        """Muestra u oculta el formulario de agregar recompensa."""
        self._show_add_form = not self._show_add_form
        
        # Actualizar el botón
        if self._add_button_ref:
            self._add_button_ref.text = "➕ Nueva Recompensa" if not self._show_add_form else "❌ Cancelar"
            self._add_button_ref.bgcolor = ft.Colors.GREEN_700 if not self._show_add_form else ft.Colors.RED_700
            self._add_button_ref.icon = ft.Icons.ADD if not self._show_add_form else ft.Icons.CLOSE
        
        # Actualizar el panel completo reconstruyendo la UI
        if hasattr(self.page, '_home_view_ref'):
            home_view = self.page._home_view_ref
            if hasattr(home_view, 'summary_view'):
                # Reconstruir solo la sección de resumen
                home_view._build_ui()
                self.page.update()
    
    def _refresh_rewards_panel(self):
        """Actualiza todo el panel de recompensas."""
        # Reconstruir el panel completo
        if hasattr(self.page, '_home_view_ref'):
            home_view = self.page._home_view_ref
            if hasattr(home_view, 'summary_view'):
                # Reconstruir la UI completa
                home_view._build_ui()
                self.page.update()
    
    def _show_edit_reward_dialog(self, reward):
        """Muestra el diálogo para editar una recompensa."""
        name_field = ft.TextField(
            label="Nombre de la recompensa",
            value=reward.name,
            autofocus=True
        )
        description_field = ft.TextField(
            label="Descripción (opcional)",
            value=reward.description or "",
            multiline=True,
            max_lines=3
        )
        points_field = ft.TextField(
            label="Puntos objetivo",
            value=str(reward.target_points),
            keyboard_type=ft.KeyboardType.NUMBER
        )
        
        def on_save(e):
            try:
                name = name_field.value.strip()
                description = description_field.value.strip() if description_field.value else None
                target_points = float(points_field.value)
                
                if not name:
                    self._show_snackbar("El nombre es requerido", ft.Colors.RED)
                    return
                
                if target_points <= 0:
                    self._show_snackbar("Los puntos objetivo deben ser mayores a 0", ft.Colors.RED)
                    return
                
                reward.name = name
                reward.description = description
                reward.target_points = target_points
                self.reward_service.update_reward(reward)
                # Actualizar estados y refrescar lista (sin cambiar filtro automáticamente al editar)
                self._refresh_rewards_list(update_states=True, auto_switch_filter=False)
                dialog.open = False
                self.page.update()
                self._show_snackbar("Recompensa actualizada exitosamente", ft.Colors.GREEN)
            except ValueError as ve:
                self._show_snackbar(str(ve), ft.Colors.RED)
            except Exception as ex:
                self._show_snackbar(f"Error: {str(ex)}", ft.Colors.RED)
        
        dialog = ft.AlertDialog(
            title=ft.Text("✏️ Editar Recompensa"),
            content=ft.Column(
                [name_field, description_field, points_field],
                spacing=12,
                height=200,
                width=400
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: setattr(dialog, "open", False) or self.page.update()),
                ft.TextButton("Guardar", on_click=on_save)
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )
        
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()
    
    def _build_claim_confirmation_panel(self, reward) -> ft.Container:
        """Construye el panel de confirmación inline para reclamar una recompensa."""
        current_points = self.points_service.get_total_points() if self.points_service else 0
        
        # Campo de nuevos puntos objetivo (inicialmente oculto)
        new_points_field = ft.TextField(
            label="Nuevos puntos objetivo",
            hint_text=f"Ej: {current_points + 10:.2f}",
            keyboard_type=ft.KeyboardType.NUMBER,
            visible=False,
            expand=True
        )
        
        # Botón de confirmar reutilización (inicialmente oculto)
        confirm_reuse_button = ft.ElevatedButton(
            "Confirmar Reutilizar",
            visible=False,
            bgcolor=ft.Colors.GREEN_700,
            color=ft.Colors.WHITE,
            icon=ft.Icons.CHECK,
            expand=True
        )
        
        def on_yes(e):
            """Muestra el input para nuevos puntos objetivo."""
            new_points_field.visible = True
            confirm_reuse_button.visible = True
            yes_button.visible = False
            no_button.visible = False
            self.page.update()
        
        def on_no(e):
            """Reclama la recompensa sin reutilizar."""
            try:
                self.reward_service.claim_reward(reward.id, reuse=False)
                # Ocultar panel y cambiar al filtro "reclamada"
                self._claiming_reward_id = None
                self._rewards_filter = "reclamada"
                self._update_filter_buttons()
                # Actualizar estados y refrescar lista
                self._refresh_rewards_list(update_states=True, auto_switch_filter=False)
                self._show_snackbar("Recompensa reclamada", ft.Colors.GREEN)
            except Exception as ex:
                self._show_snackbar(f"Error: {str(ex)}", ft.Colors.RED)
        
        def on_reuse_confirm(e):
            """Confirma la reutilización con nuevos puntos objetivo."""
            try:
                new_points = float(new_points_field.value) if new_points_field.value else 0
                
                if new_points <= current_points:
                    self._show_snackbar(
                        f"Los nuevos puntos ({new_points:.2f}) deben ser mayores a los actuales ({current_points:.2f})",
                        ft.Colors.RED
                    )
                    return
                
                self.reward_service.claim_reward(reward.id, reuse=True, new_target_points=new_points)
                # Ocultar panel
                self._claiming_reward_id = None
                # Actualizar estados y refrescar lista
                self._refresh_rewards_list(update_states=True, auto_switch_filter=False)
                self._show_snackbar("Recompensa reutilizada", ft.Colors.GREEN)
            except ValueError:
                self._show_snackbar("Por favor ingresa un número válido", ft.Colors.RED)
            except Exception as ex:
                self._show_snackbar(f"Error: {str(ex)}", ft.Colors.RED)
        
        # Botones Sí y No
        yes_button = ft.ElevatedButton(
            "Sí",
            on_click=on_yes,
            bgcolor=ft.Colors.GREEN_700,
            color=ft.Colors.WHITE,
            icon=ft.Icons.CHECK,
            expand=True
        )
        
        no_button = ft.ElevatedButton(
            "No",
            on_click=on_no,
            bgcolor=ft.Colors.RED_700,
            color=ft.Colors.WHITE,
            icon=ft.Icons.CLOSE,
            expand=True
        )
        
        confirm_reuse_button.on_click = on_reuse_confirm
        
        # Panel de confirmación
        panel_content = ft.Column(
            [
                ft.Text(
                    "¿Quieres usar esta misma recompensa para puntos más adelante?",
                    size=14,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.WHITE,
                    text_align=ft.TextAlign.CENTER
                ),
                ft.Row(
                    [yes_button, no_button],
                    spacing=8
                ),
                new_points_field,
                confirm_reuse_button
            ],
            spacing=12,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH
        )
        
        return ft.Container(
            content=panel_content,
            padding=16,
            bgcolor=ft.Colors.GREY_800,
            border_radius=8,
            border=ft.border.all(2, ft.Colors.GREEN_700),
            margin=ft.margin.only(top=8)
        )
    
    def _show_claim_reward_dialog(self, reward):
        """Muestra el diálogo para reclamar una recompensa."""
        new_points_field = ft.TextField(
            label="Nuevos puntos objetivo",
            hint_text="Ej: 200.5",
            keyboard_type=ft.KeyboardType.NUMBER,
            visible=False
        )
        confirm_button = ft.TextButton("Confirmar Reutilizar", visible=False)
        
        def on_yes(e):
            new_points_field.visible = True
            confirm_button.visible = True
            dialog.content.height = 250
            dialog.update()
        
        def on_no(e):
            try:
                self.reward_service.claim_reward(reward.id, reuse=False)
                # Actualizar estados y refrescar lista (sin cambiar filtro automáticamente al reclamar)
                self._refresh_rewards_list(update_states=True, auto_switch_filter=False)
                dialog.open = False
                self.page.update()
                self._show_snackbar("Recompensa reclamada", ft.Colors.GREEN)
            except Exception as ex:
                self._show_snackbar(f"Error: {str(ex)}", ft.Colors.RED)
        
        def on_reuse_confirm(e):
            try:
                new_points = float(new_points_field.value)
                current_points = self.points_service.get_total_points() if self.points_service else 0
                
                if new_points <= current_points:
                    self._show_snackbar(f"Los nuevos puntos ({new_points}) deben ser mayores a los actuales ({current_points})", ft.Colors.RED)
                    return
                
                self.reward_service.claim_reward(reward.id, reuse=True, new_target_points=new_points)
                # Actualizar estados y refrescar lista (sin cambiar filtro automáticamente al reutilizar)
                self._refresh_rewards_list(update_states=True, auto_switch_filter=False)
                dialog.open = False
                self.page.update()
                self._show_snackbar("Recompensa reutilizada", ft.Colors.GREEN)
            except ValueError:
                self._show_snackbar("Por favor ingresa un número válido", ft.Colors.RED)
            except Exception as ex:
                self._show_snackbar(f"Error: {str(ex)}", ft.Colors.RED)
        
        confirm_button.on_click = on_reuse_confirm
        
        dialog = ft.AlertDialog(
            title=ft.Text("🎁 Reclamar Recompensa"),
            content=ft.Column(
                [
                    ft.Text(
                        f"¿Quieres usar esta misma recompensa para puntos más adelante?",
                        size=14
                    ),
                    new_points_field
                ],
                spacing=12,
                height=150,
                width=400
            ),
            actions=[
                ft.TextButton("No", on_click=on_no),
                ft.TextButton("Sí", on_click=on_yes),
                confirm_button
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )
        
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()
    
    def _delete_reward(self, reward):
        """Elimina una recompensa."""
        def on_confirm(e):
            try:
                self.reward_service.delete_reward(reward.id)
                # Refrescar lista sin actualizar estados (la recompensa ya fue eliminada)
                self._refresh_rewards_list(update_states=False, auto_switch_filter=False)
                dialog.open = False
                self.page.update()
                self._show_snackbar("Recompensa eliminada", ft.Colors.GREEN)
            except Exception as ex:
                self._show_snackbar(f"Error: {str(ex)}", ft.Colors.RED)
                dialog.open = False
                self.page.update()
        
        def on_cancel(e):
            dialog.open = False
            self.page.update()
        
        # Crear botón de eliminar con estilo rojo usando ElevatedButton
        delete_button = ft.ElevatedButton(
            "Eliminar",
            on_click=on_confirm,
            bgcolor=ft.Colors.RED_700,
            color=ft.Colors.WHITE,
            icon=ft.Icons.DELETE
        )
        
        cancel_button = ft.TextButton(
            "Cancelar",
            on_click=on_cancel
        )
        
        dialog = ft.AlertDialog(
            title=ft.Text("🗑️ Eliminar Recompensa"),
            content=ft.Text(f"¿Estás seguro de eliminar '{reward.name}'?"),
            actions=[
                cancel_button,
                delete_button
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )
        
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()
    
    def _refresh_rewards_list(self, update_states: bool = True, auto_switch_filter: bool = False):
        """
        Actualiza la lista de recompensas.
        
        Args:
            update_states: Si True, actualiza los estados de las recompensas basándose en los puntos actuales.
            auto_switch_filter: Si True, cambia automáticamente el filtro cuando una recompensa cambia a "a_reclamar".
        """
        # Actualizar estados solo si se solicita
        if update_states:
            changed_to_available = self.reward_service.update_reward_statuses()
            
            # Solo cambiar el filtro automáticamente si se solicita y si alguna recompensa cambió a "a_reclamar"
            if auto_switch_filter and changed_to_available and self._rewards_filter == "por_alcanzar":
                self._rewards_filter = "a_reclamar"
                self._update_filter_buttons()
        
        # Reconstruir la lista (esto actualizará self._rewards_container que es la misma referencia)
        self._build_rewards_list()
        self.page.update()
    
    def _show_snackbar(self, message: str, color = None):
        """Muestra un mensaje snackbar."""
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(message),
            bgcolor=color or ft.Colors.GREY_800
        )
        self.page.snack_bar.open = True
        self.page.update()

