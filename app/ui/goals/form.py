"""
Formulario para crear y editar metas.
"""
import flet as ft
from typing import Optional

from app.data.models import Goal
from app.services.goal_service import GoalService


class GoalForm:
    """Formulario de meta."""
    
    def __init__(self, page: ft.Page, goal_service: GoalService,
                 goal: Optional[Goal] = None, on_save: Optional[callable] = None,
                 points_service=None):
        """
        Inicializa el formulario.
        
        Args:
            page: Página de Flet.
            goal_service: Servicio de metas.
            goal: Meta a editar (None para crear nueva).
            on_save: Callback a ejecutar después de guardar.
            points_service: Servicio de puntos (opcional).
        """
        self.page = page
        self.goal_service = goal_service
        self.goal = goal
        self.on_save = on_save
        self.points_service = points_service
        
        # Campos del formulario
        self.title_field = ft.TextField(
            label="Título",
            hint_text="Ingresa el título de la meta",
            autofocus=True,
            value=goal.title if goal else ""
        )
        
        self.description_field = ft.TextField(
            label="Descripción",
            hint_text="Descripción de la meta (opcional)",
            multiline=True,
            min_lines=3,
            max_lines=5,
            value=goal.description if goal else ""
        )
        
        self.target_value_field = ft.TextField(
            label="Valor objetivo",
            hint_text="Valor objetivo (opcional)",
            value=str(goal.target_value) if goal and goal.target_value else ""
        )
        
        self.current_value_field = ft.TextField(
            label="Valor actual",
            hint_text="Valor actual",
            value=str(goal.current_value) if goal else "0.0"
        )
        
        self.unit_field = ft.TextField(
            label="Unidad",
            hint_text="Unidad de medida (ej: días, tareas, horas) - opcional",
            value=goal.unit if goal else ""
        )
        
        self._show_dialog()
    
    def _show_dialog(self):
        """Muestra el diálogo del formulario."""
        is_editing = self.goal is not None
        
        is_dark = self.page.theme_mode == ft.ThemeMode.DARK
        title_color = ft.Colors.RED_700 if not is_dark else ft.Colors.RED_500
        
        self.page.dialog = ft.AlertDialog(
            title=ft.Text(
                "Editar meta" if is_editing else "Nueva meta",
                color=title_color,
                weight=ft.FontWeight.BOLD
            ),
            content=ft.Container(
                content=ft.Column(
                    [
                        self.title_field,
                        self.description_field,
                        self.target_value_field,
                        self.current_value_field,
                        self.unit_field
                    ],
                    spacing=16,
                    tight=True,
                    scroll=ft.ScrollMode.AUTO
                ),
                width=400,
                padding=16
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=self._cancel),
                ft.TextButton("Guardar", on_click=self._save)
            ],
            modal=True
        )
        self.page.dialog.open = True
        self.page.update()
    
    def _save(self, e):
        """Guarda la meta."""
        title = self.title_field.value.strip()
        if not title:
            self._show_error("El título es requerido")
            return
        
        description = self.description_field.value.strip() or None
        
        # Validar valores numéricos
        try:
            target_value = float(self.target_value_field.value.strip()) if self.target_value_field.value.strip() else None
            current_value = float(self.current_value_field.value.strip() or "0.0")
        except ValueError:
            self._show_error("Los valores deben ser números válidos")
            return
        
        unit = self.unit_field.value.strip() or None
        
        try:
            if self.goal:
                # Actualizar meta existente
                # Verificar si la meta estaba completa antes del cambio
                was_completed = self.goal.target_value and self.goal.current_value >= self.goal.target_value
                old_current_value = self.goal.current_value
                
                self.goal.title = title
                self.goal.description = description
                self.goal.target_value = target_value
                self.goal.current_value = current_value
                self.goal.unit = unit
                
                # Usar update_progress para verificar si se completó la meta (para otorgar puntos)
                self.goal_service.update_progress(self.goal.id, current_value, self.points_service)
            else:
                # Crear nueva meta con valor inicial
                self.goal_service.create_goal(title, description, target_value, unit, current_value, self.points_service)
            
            self.page.close_dialog()
            if self.on_save:
                self.on_save()
        except Exception as ex:
            self._show_error(f"Error al guardar: {str(ex)}")
    
    def _cancel(self, e):
        """Cancela el formulario."""
        self.page.close_dialog()
    
    def _show_error(self, message: str):
        """Muestra un mensaje de error."""
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(message),
            bgcolor=ft.Colors.RED
        )
        self.page.snack_bar.open = True
        self.page.update()

