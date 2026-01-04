"""
Vista de Recompensas (Rewards View)
Interfaz para crear, editar y eliminar recompensas
"""

import flet as ft
from typing import Callable, Optional, List
from app.models.reward import Reward
from app.services.rewards_service import RewardsService
from app.services.user_service import UserService
from app.utils.helpers.formats import format_number


class RewardCard(ft.Container):
    """Componente de tarjeta de recompensa"""
    
    def __init__(
        self,
        reward: Reward,
        on_edit: Callable,
        on_delete: Callable,
        is_unlocked: bool = False
    ):
        super().__init__()
        self.reward = reward
        self.on_edit = on_edit
        self.on_delete = on_delete
        self.is_unlocked = is_unlocked
        
        self.bgcolor = reward.color if is_unlocked else "#3a3a3a"
        self.border_radius = 10
        self.padding = 15
        self.margin = ft.margin.symmetric(vertical=8, horizontal=0)
        self.border = ft.border.all(1, "#444")
        
        # Contenido
        self.content = ft.Column(
            spacing=10,
            controls=[
                # Header con icono y título
                ft.Row(
                    spacing=10,
                    controls=[
                        ft.Text(
                            reward.icon,
                            size=32,
                        ),
                        ft.Column(
                            spacing=3,
                            expand=True,
                            controls=[
                                ft.Text(
                                    reward.title,
                                    size=16,
                                    weight="bold",
                                    color="#000" if is_unlocked else "#CCC",
                                ),
                                ft.Text(
                                    f"{format_number(int(reward.points_required))} pts",
                                    size=12,
                                    color="#333" if is_unlocked else "#888",
                                ),
                            ],
                        ),
                        # Estado
                        ft.Chip(
                            label=ft.Text(
                                "Desbloqueada" if is_unlocked else "Bloqueada",
                                size=11,
                                color="#fff",
                            ),
                            bgcolor="#4CAF50" if is_unlocked else "#BDBDBD",
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                
                # Descripción
                ft.Text(
                    reward.description,
                    size=13,
                    color="#000" if is_unlocked else "#BBB",
                    max_lines=2,
                ),
                
                # Categoría
                ft.Row(
                    spacing=5,
                    controls=[
                        ft.Icon(
                            "label",
                            size=14,
                            color="#000" if is_unlocked else "#888",
                        ),
                        ft.Text(
                            reward.category,
                            size=12,
                            color="#000" if is_unlocked else "#888",
                        ),
                    ],
                ),
                
                # Botones de acción
                ft.Row(
                    spacing=5,
                    controls=[
                        ft.IconButton(
                            icon="edit",
                            icon_size=18,
                            tooltip="Editar",
                            on_click=lambda _: on_edit(reward),
                        ),
                        ft.IconButton(
                            icon="delete",
                            icon_size=18,
                            tooltip="Eliminar",
                            on_click=lambda _: on_delete(reward.id),
                        ),
                    ],
                ),
            ],
        )
    
    def update_unlock_status(self, is_unlocked: bool):
        """Actualiza el estado de desbloqueo"""
        self.is_unlocked = is_unlocked
        self.bgcolor = self.reward.color if is_unlocked else "#F5F5F5"
        self.update()


class RewardFormDialog(ft.AlertDialog):
    """Diálogo para crear/editar recompensas"""
    
    def __init__(self, on_save: Callable, reward: Optional[Reward] = None):
        super().__init__()
        self.on_save = on_save
        self.reward = reward
        self.is_editing = reward is not None
        
        # Campos del formulario
        self.title_field = ft.TextField(
            label="Título",
            required=True,
            value=reward.title if reward else "",
        )
        
        self.description_field = ft.TextField(
            label="Descripción",
            multiline=True,
            min_lines=3,
            max_lines=5,
            value=reward.description if reward else "",
        )
        
        self.points_field = ft.TextField(
            label="Puntos requeridos",
            input_filter=ft.NumbersOnlyInputFilter(),
            value=str(int(reward.points_required)) if reward else "",
            required=True,
        )
        
        self.icon_field = ft.TextField(
            label="Icono (emoji)",
            value=reward.icon if reward else "🎁",
        )
        
        self.color_field = ft.TextField(
            label="Color (hex, ej: #FFD700)",
            value=reward.color if reward else "#FFD700",
        )
        
        self.category_dropdown = ft.Dropdown(
            label="Categoría",
            options=[
                ft.dropdown.Option("badge", "Insignia"),
                ft.dropdown.Option("achievement", "Logro"),
                ft.dropdown.Option("milestone", "Hito"),
                ft.dropdown.Option("special", "Especial"),
            ],
            value=reward.category if reward else "badge",
        )
        
        self.active_checkbox = ft.Checkbox(
            label="Activa",
            value=reward.is_active if reward else True,
        )
        
        # Contenido
        self.content = ft.Column(
            spacing=15,
            width=500,
            controls=[
                ft.Text(
                    "Editar Recompensa" if self.is_editing else "Nueva Recompensa",
                    size=18,
                    weight="bold",
                ),
                
                self.title_field,
                self.description_field,
                self.points_field,
                self.icon_field,
                self.color_field,
                self.category_dropdown,
                self.active_checkbox,
            ],
        )
        
        # Botones
        self.actions = [
            ft.TextButton("Cancelar", on_click=self._on_cancel),
            ft.TextButton("Guardar", on_click=self._on_save),
        ]
        
        self.title = ft.Text(
            "Editar Recompensa" if self.is_editing else "Nueva Recompensa"
        )
    
    def _on_save(self, e):
        """Maneja el guardado"""
        # Validar
        if not self.title_field.value or not self.points_field.value:
            self._show_error("Título y puntos requeridos son obligatorios")
            return
        
        try:
            points = float(self.points_field.value)
            if points < 0:
                raise ValueError("Los puntos no pueden ser negativos")
        except ValueError:
            self._show_error("Puntos debe ser un número válido")
            return
        
        reward_data = {
            "id": self.reward.id if self.is_editing else None,
            "title": self.title_field.value,
            "description": self.description_field.value,
            "points_required": float(self.points_field.value),
            "icon": self.icon_field.value or "🎁",
            "color": self.color_field.value or "#FFD700",
            "category": self.category_dropdown.value,
            "is_active": self.active_checkbox.value,
        }
        
        self.on_save(reward_data)
        self.open = False
    
    def _on_cancel(self, e):
        """Maneja la cancelación"""
        self.open = False
    
    def _show_error(self, message: str):
        """Muestra un error"""
        # Aquí podrías mostrar un snackbar o similar
        print(f"Error: {message}")


class RewardsView(ft.Container):
    """Vista principal de recompensas"""
    
    def __init__(self, user_service: Optional[UserService] = None, user_id: str = "default_user"):
        super().__init__()
        
        self.rewards_service = RewardsService()
        self.user_service = user_service
        self.user_id = user_id
        self.current_user_points = 0.0
        self.current_user_level = "Nadie"
        
        # Crear algunas recompensas por defecto
        self._initialize_default_rewards()
        
        # UI
        self.expand = True
        self.bgcolor = "#1a1a1a"
        self.padding = 20
        
        # Lista de recompensas
        self.rewards_list = ft.Column(spacing=5)
        
        # Referencias a elementos de UI para actualizar puntos
        self.points_text = ft.Text("0", size=24, weight="bold", color="#4CAF50")
        self.level_text = ft.Text("Nadie", size=20, weight="bold", color="#FFD700")
        
        # Información del usuario
        self.user_info_row = ft.Row(
            spacing=20,
            controls=[
                ft.Column(
                    spacing=5,
                    controls=[
                        ft.Text("Puntos Actuales", size=12, color="#AAA"),
                        self.points_text,
                    ],
                ),
                ft.Column(
                    spacing=5,
                    controls=[
                        ft.Text("Nivel Actual", size=12, color="#AAA"),
                        self.level_text,
                    ],
                ),
            ],
        )
        
        # Botón para agregar recompensa
        self.add_reward_btn = ft.FloatingActionButton(
            icon="add",
            on_click=self._on_add_reward,
            tooltip="Agregar recompensa",
        )
        
        # Diálogo de formulario
        self.reward_form_dialog = None
        
        self.content = ft.Column(
            spacing=15,
            expand=True,
            controls=[
                # Header
                ft.Text("Recompensas", size=24, weight="bold", color="#FFF"),
                
                # Info del usuario
                self.user_info_row,
                
                # Filtros
                ft.Row(
                    spacing=10,
                    controls=[
                        ft.TextButton(
                            "Todas",
                            on_click=lambda _: self._filter_rewards("all"),
                        ),
                        ft.TextButton(
                            "Desbloqueadas",
                            on_click=lambda _: self._filter_rewards("unlocked"),
                        ),
                        ft.TextButton(
                            "Bloqueadas",
                            on_click=lambda _: self._filter_rewards("locked"),
                        ),
                    ],
                ),
                
                # Lista de recompensas
                ft.Container(
                    expand=True,
                    content=ft.ListView(
                        spacing=0,
                        controls=[self.rewards_list],
                        expand=True,
                    ),
                    border_radius=10,
                    bgcolor="#2a2a2a",
                ),
            ],
        )
        
        # NO renderizar recompensas aquí, se hará cuando se añada a la página
    
    def did_mount(self):
        """Se llama cuando el control es añadido a la página"""
        self._render_rewards()
    
    def _initialize_default_rewards(self):
        """Inicializa recompensas por defecto"""
        default_rewards = [
            {
                "title": "Primer Paso",
                "description": "Completa tu primera tarea",
                "points_required": 50,
                "icon": "👣",
                "color": "#4CAF50",
                "category": "achievement",
            },
            {
                "title": "En Movimiento",
                "description": "Acumula 100 puntos",
                "points_required": 100,
                "icon": "🚀",
                "color": "#2196F3",
                "category": "badge",
            },
            {
                "title": "Imparable",
                "description": "Acumula 500 puntos",
                "points_required": 500,
                "icon": "⚡",
                "color": "#FF9800",
                "category": "milestone",
            },
            {
                "title": "Leyenda",
                "description": "Acumula 1000 puntos",
                "points_required": 1000,
                "icon": "👑",
                "color": "#FFD700",
                "category": "achievement",
            },
            {
                "title": "Semana Completa",
                "description": "Mantén una racha de 7 días",
                "points_required": 150,
                "icon": "🔥",
                "color": "#F44336",
                "category": "special",
            },
        ]
        
        for reward_data in default_rewards:
            self.rewards_service.create_reward(reward_data)
    
    def _render_rewards(self):
        """Renderiza la lista de recompensas"""
        self.rewards_list.controls = [
            RewardCard(
                reward,
                on_edit=self._on_edit_reward,
                on_delete=self._on_delete_reward,
                is_unlocked=reward.points_required <= self.current_user_points,
            )
            for reward in self.rewards_service.get_all_rewards()
        ]
        try:
            self.update()
        except:
            pass  # Control no está en la página aún
    
    def _filter_rewards(self, filter_type: str):
        """Filtra recompensas"""
        self.rewards_list.controls = []
        
        if filter_type == "unlocked":
            rewards = self.rewards_service.get_unlocked_rewards(self.current_user_points)
        elif filter_type == "locked":
            all_rewards = self.rewards_service.get_all_rewards()
            rewards = [r for r in all_rewards if r.points_required > self.current_user_points]
        else:  # all
            rewards = self.rewards_service.get_all_rewards()
        
        self.rewards_list.controls = [
            RewardCard(
                reward,
                on_edit=self._on_edit_reward,
                on_delete=self._on_delete_reward,
                is_unlocked=reward.points_required <= self.current_user_points,
            )
            for reward in rewards
        ]
        if self.page:
            self.update()
    
    def _on_add_reward(self, e):
        """Maneja la adición de recompensa"""
        if not self.page:
            return
        self.reward_form_dialog = RewardFormDialog(
            on_save=self._on_save_reward,
            reward=None,
        )
        self.page.dialog = self.reward_form_dialog
        self.reward_form_dialog.open = True
        self.page.update()
    
    def _on_edit_reward(self, reward: Reward):
        """Maneja la edición de recompensa"""
        if not self.page:
            return
        self.reward_form_dialog = RewardFormDialog(
            on_save=self._on_save_reward,
            reward=reward,
        )
        self.page.dialog = self.reward_form_dialog
        self.reward_form_dialog.open = True
        self.page.update()
    
    def _on_save_reward(self, reward_data: dict):
        """Guarda una recompensa"""
        if reward_data.get("id"):
            # Actualizar
            self.rewards_service.update_reward(reward_data["id"], reward_data)
        else:
            # Crear
            self.rewards_service.create_reward(reward_data)
        
        self._render_rewards()
    
    def _on_delete_reward(self, reward_id: str):
        """Elimina una recompensa"""
        if not self.page:
            return
            
        def confirm_delete(e):
            self.rewards_service.delete_reward(reward_id)
            self._render_rewards()
            dlg.open = False
            if self.page:
                self.page.update()
        
        def cancel_delete(e):
            dlg.open = False
            if self.page:
                self.page.update()
        
        dlg = ft.AlertDialog(
            title=ft.Text("Eliminar Recompensa"),
            content=ft.Text("¿Está seguro que desea eliminar esta recompensa?"),
            actions=[
                ft.TextButton("Cancelar", on_click=cancel_delete),
                ft.TextButton("Eliminar", on_click=confirm_delete),
            ],
        )
        
        self.page.dialog = dlg
        dlg.open = True
        self.page.update()
    
    def set_user_points(self, points: float):
        """Establece los puntos del usuario"""
        self.current_user_points = points
        # Actualizar UI
        self.points_text.value = format_number(int(points))
        self._render_rewards()
        if self.page:
            self.update()
    
    def set_user_level(self, level: str):
        """Establece el nivel del usuario"""
        self.current_user_level = level
        # Actualizar UI
        self.level_text.value = level
        if self.page:
            self.update()
    
    def refresh_from_user_service(self):
        """Actualiza los puntos y nivel desde el UserService"""
        if self.user_service:
            stats = self.user_service.get_user_stats(self.user_id)
            if stats:
                self.set_user_points(stats.get("points", 0.0))
                self.set_user_level(stats.get("level", "Nadie"))
