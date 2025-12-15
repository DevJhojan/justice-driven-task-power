"""
Formulario para crear y editar hábitos.
"""
import flet as ft
from app.data.models import Habit
from typing import Optional, Callable


class HabitForm:
    """Formulario para crear/editar hábitos."""
    
    def __init__(self, on_save: Callable, on_cancel: Callable, habit: Optional[Habit] = None):
        """
        Inicializa el formulario.
        
        Args:
            on_save: Callback cuando se guarda el hábito.
            on_cancel: Callback cuando se cancela.
            habit: Hábito a editar (None para crear nuevo).
        """
        self.on_save = on_save
        self.on_cancel = on_cancel
        self.habit = habit
        
        # Campos del formulario
        self.title_field = ft.TextField(
            label="Título del hábito",
            hint_text="Ej: Hacer ejercicio, Leer 30 minutos",
            autofocus=True,
            expand=True,
            value=habit.title if habit else ""
        )
        
        self.description_field = ft.TextField(
            label="Descripción",
            hint_text="Describe tu hábito (opcional)",
            multiline=True,
            min_lines=3,
            max_lines=5,
            expand=True,
            value=habit.description if habit else ""
        )
        
        self.frequency_dropdown = ft.Dropdown(
            label="Frecuencia",
            options=[
                ft.dropdown.Option("daily", "Diario"),
                ft.dropdown.Option("weekly", "Semanal"),
                ft.dropdown.Option("custom", "Personalizado"),
            ],
            value=habit.frequency if habit else "daily",
            expand=True,
            on_change=self._on_frequency_change
        )
        
        # Campo para días objetivo (solo visible para weekly y custom)
        self.target_days_field = ft.TextField(
            label="Días objetivo por semana",
            hint_text="Número de días (1-7)",
            value=str(habit.target_days) if habit else "7",
            keyboard_type=ft.KeyboardType.NUMBER,
            visible=habit.frequency in ['weekly', 'custom'] if habit else False,
            expand=True
        )
        
        # Botones
        self.save_button = ft.ElevatedButton(
            text="Guardar",
            icon=ft.Icons.SAVE,
            on_click=self._handle_save,
            color=ft.Colors.WHITE,
            bgcolor=ft.Colors.RED_700
        )
        
        self.cancel_button = ft.OutlinedButton(
            text="Cancelar",
            icon=ft.Icons.CANCEL,
            on_click=lambda e: on_cancel()
        )
    
    def _on_frequency_change(self, e):
        """Maneja el cambio de frecuencia."""
        frequency = self.frequency_dropdown.value
        if frequency in ['weekly', 'custom']:
            self.target_days_field.visible = True
            if frequency == 'weekly':
                self.target_days_field.value = "7"
            else:
                self.target_days_field.value = "1"
        else:
            self.target_days_field.visible = False
            self.target_days_field.value = "1"
        self.target_days_field.update()
    
    def build(self) -> ft.Container:
        """
        Construye el widget del formulario.
        
        Returns:
            Container con el formulario completo.
        """
        title = "Editar Hábito" if self.habit else "Nuevo Hábito"
        
        return ft.Container(
            content=ft.Column(
                [
                    ft.Text(
                        title,
                        size=24,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.RED_400
                    ),
                    ft.Divider(),
                    self.title_field,
                    self.description_field,
                    self.frequency_dropdown,
                    self.target_days_field,
                    ft.Row(
                        [
                            self.save_button,
                            self.cancel_button
                        ],
                        alignment=ft.MainAxisAlignment.END,
                        spacing=8
                    )
                ],
                spacing=16,
                scroll=ft.ScrollMode.AUTO
            ),
            padding=20,
            expand=True
        )
    
    def _handle_save(self, e):
        """Maneja el evento de guardar."""
        title = self.title_field.value
        description = self.description_field.value or ""
        frequency = self.frequency_dropdown.value or "daily"
        
        # Validar título
        if not title or not title.strip():
            self.title_field.error_text = "El título es obligatorio"
            self.title_field.update()
            return
        
        self.title_field.error_text = None
        self.title_field.update()
        
        # Validar y obtener días objetivo
        target_days = 1
        if frequency in ['weekly', 'custom']:
            try:
                target_days = int(self.target_days_field.value or "1")
                if target_days < 1 or target_days > 7:
                    self.target_days_field.error_text = "Debe ser un número entre 1 y 7"
                    self.target_days_field.update()
                    return
            except ValueError:
                self.target_days_field.error_text = "Debe ser un número válido"
                self.target_days_field.update()
                return
        
        self.target_days_field.error_text = None
        self.target_days_field.update()
        
        # Crear o actualizar hábito
        if self.habit:
            # Actualizar hábito existente
            self.habit.title = title.strip()
            self.habit.description = description.strip()
            self.habit.frequency = frequency
            self.habit.target_days = target_days
            self.on_save(self.habit)
        else:
            # Crear nuevo hábito
            self.on_save(title.strip(), description.strip(), frequency, target_days)
    
    def get_habit_data(self) -> dict:
        """
        Obtiene los datos del formulario.
        
        Returns:
            Diccionario con los datos del hábito.
        """
        frequency = self.frequency_dropdown.value or "daily"
        target_days = 1
        if frequency in ['weekly', 'custom']:
            try:
                target_days = int(self.target_days_field.value or "1")
            except ValueError:
                target_days = 1
        
        return {
            'title': self.title_field.value or "",
            'description': self.description_field.value or "",
            'frequency': frequency,
            'target_days': target_days
        }
