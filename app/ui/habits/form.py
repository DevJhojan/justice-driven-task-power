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
    
    def build_view(self) -> ft.View:
        """Construye una vista completa para el formulario."""
        is_editing = self.habit is not None
        is_dark = self.page.theme_mode == ft.ThemeMode.DARK
        title_color = ft.Colors.RED_700 if not is_dark else ft.Colors.RED_500
        bg_color = ft.Colors.WHITE if not is_dark else ft.Colors.BLACK
        btn_color = ft.Colors.RED_700 if not is_dark else ft.Colors.RED_500
        
        # Barra superior con título y botones
        header = ft.Container(
            content=ft.Row(
                [
                    ft.IconButton(
                        icon=ft.Icons.ARROW_BACK,
                        icon_color=title_color,
                        on_click=self._cancel,
                        tooltip="Volver"
                    ),
                    ft.Text(
                        "Editar hábito" if is_editing else "Nuevo hábito",
                        size=20,
                        weight=ft.FontWeight.BOLD,
                        color=title_color,
                        expand=True
                    ),
                    ft.ElevatedButton(
                        "Guardar",
                        icon=ft.Icons.SAVE,
                        on_click=self._save,
                        bgcolor=btn_color,
                        color=ft.Colors.WHITE
                    )
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN
            ),
            padding=16,
            bgcolor=ft.Colors.SURFACE if is_dark else ft.Colors.WHITE,
            border=ft.border.only(bottom=ft.border.BorderSide(1, ft.Colors.OUTLINE))
        )
        
        # Contenido principal con scroll
        content = ft.Container(
            content=ft.Column(
                [
                    self.title_field,
                    self.description_field
                ],
                spacing=16,
                scroll=ft.ScrollMode.AUTO,
                expand=True
            ),
            padding=16,
            expand=True
        )
        
        # Crear la vista
        route = f"/habit-form?id={self.habit.id}" if self.habit and self.habit.id else "/habit-form"
        return ft.View(
            route=route,
            controls=[
                ft.Column(
                    [header, content],
                    spacing=0,
                    expand=True
                )
            ],
            bgcolor=bg_color
        )
    
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
            
            # Ejecutar callback y navegar de vuelta
            if self.on_save:
                self.on_save()
            self.page.go("/")
            # La vista principal se recargará automáticamente al navegar
        except Exception as ex:
            self._show_error(f"Error al guardar: {str(ex)}")
    
    def _cancel(self, e):
        """Cancela el formulario y regresa."""
        self.page.go("/")
    
    def _show_error(self, message: str):
        """Muestra un mensaje de error."""
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(message),
            bgcolor=ft.Colors.RED
        )
        self.page.snack_bar.open = True
        self.page.update()

