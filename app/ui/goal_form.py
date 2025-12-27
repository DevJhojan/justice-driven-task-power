"""
Formulario para crear y editar objetivos.
"""
import flet as ft
from app.data.models import Goal
from typing import Optional, Callable
from datetime import datetime


class GoalForm:
    """Formulario para crear/editar objetivos."""
    
    def __init__(self, on_save: Callable, on_cancel: Callable, goal: Optional[Goal] = None):
        """
        Inicializa el formulario.
        
        Args:
            on_save: Callback cuando se guarda el objetivo.
            on_cancel: Callback cuando se cancela.
            goal: Objetivo a editar (None para crear nuevo).
        """
        self.on_save = on_save
        self.on_cancel = on_cancel
        self.goal = goal
        
        # Campos del formulario
        self.title_field = ft.TextField(
            label="Título del objetivo",
            hint_text="Ej: Perder 5 kg, Aprender Python, Leer 12 libros",
            autofocus=True,
            expand=True,
            value=goal.title if goal else ""
        )
        
        self.description_field = ft.TextField(
            label="Descripción",
            hint_text="Describe tu objetivo (opcional)",
            multiline=True,
            min_lines=3,
            max_lines=5,
            expand=True,
            value=goal.description if goal else ""
        )
        
        self.frequency_dropdown = ft.Dropdown(
            label="Frecuencia",
            options=[
                ft.dropdown.Option("daily", "Diario"),
                ft.dropdown.Option("weekly", "Semanal"),
                ft.dropdown.Option("monthly", "Mensual"),
                ft.dropdown.Option("quarterly", "Trimestral"),
                ft.dropdown.Option("semiannual", "Semestral"),
                ft.dropdown.Option("annual", "Anual"),
            ],
            value=goal.frequency if goal else "monthly",
            expand=True
        )
        
        # Campo de fecha objetivo
        target_date_value = None
        if goal and goal.target_date:
            target_date_value = goal.target_date.strftime("%Y-%m-%d")
        
        self.target_date_field = ft.TextField(
            label="Fecha objetivo (opcional)",
            hint_text="YYYY-MM-DD",
            value=target_date_value,
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
    
    def _handle_save(self, e):
        """Maneja el guardado del objetivo."""
        title = self.title_field.value.strip()
        if not title:
            self.title_field.error_text = "El título es obligatorio"
            self.title_field.update()
            return
        
        description = self.description_field.value.strip() if self.description_field.value else ""
        frequency = self.frequency_dropdown.value
        
        # Procesar fecha objetivo
        target_date = None
        if self.target_date_field.value:
            try:
                target_date = datetime.strptime(self.target_date_field.value.strip(), "%Y-%m-%d")
            except ValueError:
                self.target_date_field.error_text = "Formato de fecha inválido. Use YYYY-MM-DD"
                self.target_date_field.update()
                return
        
        # Si es edición, pasar el objetivo completo
        if self.goal:
            self.goal.title = title
            self.goal.description = description
            self.goal.frequency = frequency
            self.goal.target_date = target_date
            self.on_save(self.goal)
        else:
            # Crear nuevo objetivo
            self.on_save(title, description, frequency, target_date)
    
    def build(self) -> ft.Container:
        """
        Construye el widget del formulario.
        
        Returns:
            Container con el formulario completo.
        """
        return ft.Container(
            content=ft.Column(
                [
                    self.title_field,
                    self.description_field,
                    self.frequency_dropdown,
                    self.target_date_field,
                    ft.Row(
                        [
                            self.cancel_button,
                            self.save_button
                        ],
                        alignment=ft.MainAxisAlignment.END,
                        spacing=12
                    )
                ],
                spacing=20,
                scroll=ft.ScrollMode.AUTO,
                expand=True
            ),
            padding=20,
            expand=True
        )

