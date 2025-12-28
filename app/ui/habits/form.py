"""
Formulario para crear y editar hábitos.
"""
import flet as ft
from typing import Optional

from app.data.models import Habit
from app.services.habit_service import HabitService


class HabitForm:
    """Formulario de hábito."""
    
    def __init__(self, page: ft.Page, habit_service: HabitService,
                 habit: Optional[Habit] = None, on_save: Optional[callable] = None):
        """
        Inicializa el formulario.
        
        Args:
            page: Página de Flet.
            habit_service: Servicio de hábitos.
            habit: Hábito a editar (None para crear nuevo).
            on_save: Callback a ejecutar después de guardar.
        """
        self.page = page
        self.habit_service = habit_service
        self.habit = habit
        self.on_save = on_save
        
        # Campos del formulario
        self.title_field = ft.TextField(
            label="Título",
            hint_text="Ingresa el título del hábito",
            autofocus=True,
            value=habit.title if habit else ""
        )
        
        self.description_field = ft.TextField(
            label="Descripción",
            hint_text="Descripción del hábito (opcional)",
            multiline=True,
            min_lines=3,
            max_lines=5,
            value=habit.description if habit else ""
        )
        
        self._show_dialog()
    
    def _show_dialog(self):
        """Muestra el diálogo del formulario."""
        is_editing = self.habit is not None
        
        is_dark = self.page.theme_mode == ft.ThemeMode.DARK
        title_color = ft.Colors.RED_700 if not is_dark else ft.Colors.RED_500
        
        self.page.dialog = ft.AlertDialog(
            title=ft.Text(
                "Editar hábito" if is_editing else "Nuevo hábito",
                color=title_color,
                weight=ft.FontWeight.BOLD
            ),
            content=ft.Container(
                content=ft.Column(
                    [
                        self.title_field,
                        self.description_field
                    ],
                    spacing=16,
                    tight=True
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
        """Guarda el hábito."""
        title = self.title_field.value.strip()
        if not title:
            self._show_error("El título es requerido")
            return
        
        description = self.description_field.value.strip() or None
        
        try:
            if self.habit:
                # Actualizar hábito existente
                self.habit.title = title
                self.habit.description = description
                self.habit_service.update_habit(self.habit)
            else:
                # Crear nuevo hábito
                self.habit_service.create_habit(title, description)
            
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

