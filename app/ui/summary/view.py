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
        self.reward_service.update_reward_statuses()
        
        # Forzar tema oscuro
        is_dark = True
        bg_color = ft.Colors.SURFACE
        text_color = ft.Colors.GREY_400
        title_color = ft.Colors.RED_500
        
        # Construir filtros
        filters = self._build_rewards_filters()
        
        # Construir lista de recompensas
        rewards_list = self._build_rewards_list()
        
        # Botón para agregar nueva recompensa
        add_button = ft.ElevatedButton(
            "➕ Nueva Recompensa",
            on_click=self._show_create_reward_dialog,
            bgcolor=ft.Colors.GREEN_700,
            color=ft.Colors.WHITE,
            icon=ft.icons.ADD
        )
        
        return ft.Container(
            content=ft.Column(
                [
                    ft.Text(
                        "🎁 Recompensas",
                        size=18,
                        weight=ft.FontWeight.BOLD,
                        color=title_color
                    ),
                    filters,
                    rewards_list,
                    add_button
                ],
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
            self._refresh_rewards_list()
        
        return ft.Row(
            [
                ft.ElevatedButton(
                    "🟡 Por Alcanzar",
                    on_click=on_filter_change,
                    data="por_alcanzar",
                    bgcolor=ft.Colors.YELLOW_700 if self._rewards_filter == "por_alcanzar" else ft.Colors.GREY_700,
                    color=ft.Colors.WHITE,
                    expand=True
                ),
                ft.ElevatedButton(
                    "🟢 A Reclamar",
                    on_click=on_filter_change,
                    data="a_reclamar",
                    bgcolor=ft.Colors.GREEN_700 if self._rewards_filter == "a_reclamar" else ft.Colors.GREY_700,
                    color=ft.Colors.WHITE,
                    expand=True
                ),
                ft.ElevatedButton(
                    "⚪ Reclamadas",
                    on_click=on_filter_change,
                    data="reclamada",
                    bgcolor=ft.Colors.GREY_600 if self._rewards_filter == "reclamada" else ft.Colors.GREY_700,
                    color=ft.Colors.WHITE,
                    expand=True
                )
            ],
            spacing=8
        )
    
    def _build_rewards_list(self) -> ft.Column:
        """Construye la lista de recompensas según el filtro actual."""
        rewards = self.reward_service.get_rewards_by_status(self._rewards_filter)
        
        if not rewards:
            empty_text = {
                "por_alcanzar": "No hay recompensas por alcanzar",
                "a_reclamar": "No hay recompensas disponibles para reclamar",
                "reclamada": "No hay recompensas reclamadas"
            }
            
            return ft.Column(
                [
                    ft.Text(
                        empty_text.get(self._rewards_filter, "No hay recompensas"),
                        size=14,
                        color=ft.Colors.GREY_500,
                        text_align=ft.TextAlign.CENTER
                    )
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=8
            )
        
        reward_cards = [self._build_reward_card(reward) for reward in rewards]
        
        self._rewards_container = ft.Column(
            reward_cards,
            spacing=8
        )
        
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
        action_buttons = ft.Row(
            [
                ft.IconButton(
                    ft.icons.EDIT,
                    on_click=lambda e, r=reward: self._show_edit_reward_dialog(r),
                    tooltip="Editar",
                    icon_color=ft.Colors.BLUE
                ) if reward.status != "reclamada" else ft.Container(),
                ft.IconButton(
                    ft.icons.DELETE,
                    on_click=lambda e, r=reward: self._delete_reward(r),
                    tooltip="Eliminar",
                    icon_color=ft.Colors.RED
                )
            ],
            spacing=4
        )
        
        return ft.Container(
            content=ft.Row(
                [
                    checkbox,
                    reward_info,
                    action_buttons
                ],
                spacing=12,
                vertical_alignment=ft.CrossAxisAlignment.START
            ),
            padding=12,
            bgcolor=ft.Colors.GREY_900,
            border_radius=8,
            border=ft.border.all(1, status_color),
            margin=ft.margin.only(bottom=8)
        )
    
    def _on_reward_checkbox_change(self, e, reward):
        """Maneja el cambio en el checkbox de una recompensa."""
        if e.control.value and reward.status == "a_reclamar":
            self._show_claim_reward_dialog(reward)
        elif not e.control.value and reward.status == "reclamada":
            # Si se desmarca una recompensa reclamada, no hacer nada
            e.control.value = True
            self.page.update()
    
    def _show_create_reward_dialog(self, e):
        """Muestra el diálogo para crear una nueva recompensa."""
        name_field = ft.TextField(
            label="Nombre de la recompensa",
            hint_text="Ej: Comprar un libro",
            autofocus=True
        )
        description_field = ft.TextField(
            label="Descripción (opcional)",
            hint_text="Describe tu recompensa",
            multiline=True,
            max_lines=3
        )
        points_field = ft.TextField(
            label="Puntos objetivo",
            hint_text="Ej: 100.5",
            keyboard_type=ft.KeyboardType.NUMBER
        )
        
        def on_create(e):
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
                
                self.reward_service.create_reward(name, description, target_points)
                self._refresh_rewards_list()
                dialog.open = False
                self.page.update()
                self._show_snackbar("Recompensa creada exitosamente", ft.Colors.GREEN)
            except ValueError as ve:
                self._show_snackbar(str(ve), ft.Colors.RED)
            except Exception as ex:
                self._show_snackbar(f"Error: {str(ex)}", ft.Colors.RED)
        
        dialog = ft.AlertDialog(
            title=ft.Text("➕ Nueva Recompensa"),
            content=ft.Column(
                [name_field, description_field, points_field],
                spacing=12,
                height=200,
                width=400
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: setattr(dialog, "open", False) or self.page.update()),
                ft.TextButton("Crear", on_click=on_create)
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )
        
        self.page.dialog = dialog
        dialog.open = True
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
                self.reward_service.update_reward_statuses()  # Actualizar estados
                self._refresh_rewards_list()
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
                self.reward_service.update_reward_statuses()
                self._refresh_rewards_list()
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
                self.reward_service.update_reward_statuses()
                self._refresh_rewards_list()
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
                self._refresh_rewards_list()
                dialog.open = False
                self.page.update()
                self._show_snackbar("Recompensa eliminada", ft.Colors.GREEN)
            except Exception as ex:
                self._show_snackbar(f"Error: {str(ex)}", ft.Colors.RED)
        
        dialog = ft.AlertDialog(
            title=ft.Text("🗑️ Eliminar Recompensa"),
            content=ft.Text(f"¿Estás seguro de eliminar '{reward.name}'?"),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: setattr(dialog, "open", False) or self.page.update()),
                ft.TextButton("Eliminar", on_click=on_confirm, color=ft.Colors.RED)
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )
        
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()
    
    def _refresh_rewards_list(self):
        """Actualiza la lista de recompensas."""
        if self._rewards_container:
            new_list = self._build_rewards_list()
            # Reemplazar el contenido del contenedor
            self._rewards_container.controls = new_list.controls
            self.page.update()
    
    def _show_snackbar(self, message: str, color = None):
        """Muestra un mensaje snackbar."""
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(message),
            bgcolor=color or ft.Colors.GREY_800
        )
        self.page.snack_bar.open = True
        self.page.update()

