"""
Vista de Hábitos (Habits) de la aplicación
Sistema completo de hábitos con persistencia en BD, racha diaria y CRUD
"""

import flet as ft
import asyncio
from typing import Optional, Callable

from app.services.habits_service import HabitsService
from app.services.progress_service import ProgressService
from app.ui.habits.habits_form import HabitsForm
from app.ui.habits.habits_list import HabitsList
from app.ui.habits.habit_grafics import HabitGraphics


class HabitsView:
    """Clase que representa la vista de hábitos con CRUD y persistencia BD"""
    
    def __init__(self, on_update: Optional[Callable] = None):
        """
        Inicializa la vista de hábitos
        
        Args:
            on_update: Callback opcional al actualizar hábitos
        """
        self.habits_service = HabitsService()
        self.progress_service = ProgressService()
        self.on_update = on_update
        self.showing_form = False
        self.showing_graphs = False
        self.graph_habit = None
        self.editing_habit_id: Optional[str] = None

        # UI Components
        self.form: HabitsForm = HabitsForm(on_save=self._handle_save, on_cancel=lambda e: self._toggle_form())
        self.habits_list = HabitsList(
            habits_service=self.habits_service,
            on_add=lambda e: self._toggle_form(),
            on_complete=self._complete_habit,
            on_edit=self._start_edit,
            on_delete=self._delete_habit,
            on_show_graphs=self._show_graphs,
        )
        self.main_column = None
    
    def _handle_save(self, _):
        """Valida y crea/edita un hábito usando el servicio"""
        values = self.form.get_values()
        title = values.get("title", "")
        if not title:
            return
        if self.editing_habit_id:
            asyncio.create_task(self._async_update_habit(self.editing_habit_id, values))
        else:
            asyncio.create_task(self._async_create_habit(values))

    async def _async_create_habit(self, values: dict):
        """Crea un hábito de forma asíncrona"""
        try:
            await self.habits_service.create_habit(
                title=values.get("title", ""),
                description=values.get("description", ""),
                frequency=values.get("frequency", "daily"),
                frequency_times=values.get("frequency_times", 1),
            )
            self.form.reset()
            self.editing_habit_id = None
            self._toggle_form()
            self._refresh_list()
        except Exception as e:
            print(f"[HabitsView] Error creando hábito: {e}")

    async def _async_update_habit(self, habit_id: str, values: dict):
        """Actualiza un hábito existente"""
        try:
            await self.habits_service.update_habit(
                habit_id,
                title=values.get("title", ""),
                description=values.get("description", ""),
                frequency=values.get("frequency", "daily"),
                frequency_times=values.get("frequency_times", 1),
            )
            self.form.reset()
            self.editing_habit_id = None
            self._toggle_form()
            self._refresh_list()
        except Exception as e:
            print(f"[HabitsView] Error actualizando hábito: {e}")
    
    def _complete_habit(self, habit_id: str):
        """Marca/desmarca un hábito como completado"""
        asyncio.create_task(self._async_complete_habit(habit_id))
    
    async def _async_complete_habit(self, habit_id: str):
        """Marca/desmarca un hábito como completado de forma asíncrona"""
        try:
            was_completed = await self.habits_service.complete_habit(habit_id)
            if was_completed:
                action = self._get_points_action_for_habit(habit_id)
                await self.progress_service.add_points(action)
            self._refresh_list()
            if self.on_update:
                self.on_update()
        except Exception as e:
            print(f"[HabitsView] Error completando hábito: {e}")
    
    def _delete_habit(self, habit_id: str):
        """Elimina un hábito"""
        asyncio.create_task(self._async_delete_habit(habit_id))

    async def _async_delete_habit(self, habit_id: str):
        """Elimina un hábito de forma asíncrona"""
        try:
            await self.habits_service.delete_habit(habit_id)
            if self.editing_habit_id == habit_id:
                self.editing_habit_id = None
                self.form.reset()
            self._refresh_list()
        except Exception as e:
            print(f"[HabitsView] Error eliminando hábito: {e}")

    def _start_edit(self, habit):
        """Inicia la edición de un hábito"""
        self.editing_habit_id = habit.id
        self.form.set_values(habit.title, habit.description, habit.frequency, habit.frequency_times)
        if not self.showing_form:
            self._toggle_form()
    
    def _show_graphs(self, habit):
        """Muestra vista de gráficos del hábito en la misma página"""
        self.graph_habit = habit
        self.showing_graphs = True
        self.showing_form = False
        self._update_view()

    def _hide_graphs(self):
        self.showing_graphs = False
        self.graph_habit = None
        self._update_view()

    def _get_points_action_for_habit(self, habit_id: str) -> str:
        habit = self.habits_service.get_habit(habit_id)
        if not habit:
            return "habit_daily_completed"
        mapping = {
            "daily": "habit_daily_completed",
            "weekly": "habit_weekly_completed",
            "monthly": "habit_monthly_completed",
            "semiannual": "habit_semiannual_completed",
            "annual": "habit_annual_completed",
        }
        return mapping.get(habit.frequency, "habit_daily_completed")

    def _toggle_form(self):
        """Alterna entre mostrar/ocultar el formulario"""
        self.showing_form = not self.showing_form
        if self.showing_form:
            self.showing_graphs = False
        self._update_view()
    
    def _update_view(self):
        """Actualiza la vista según el estado"""
        if self.main_column:
            self.main_column.controls = []
            if self.showing_graphs and self.graph_habit:
                self.main_column.controls.append(self._build_graphs_view())
            elif self.showing_form:
                self.main_column.controls.append(self._build_form())
            else:
                self.main_column.controls.append(self.habits_list.build())
            self.main_column.update()
    
    def _refresh_list(self):
        """Refresca la lista de hábitos"""
        if self.habits_list and not self.showing_form:
            self.habits_list.refresh()
    
    def _build_form(self) -> ft.Container:
        """Construye el formulario de crear hábito"""
        return self.form.build()

    def _build_graphs_view(self) -> ft.Container:
        """Construye la vista de gráficos para el hábito seleccionado"""
        if not self.graph_habit:
            return ft.Container()
        graph_content = HabitGraphics(self.graph_habit).build()
        return ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.IconButton(
                                icon=ft.Icons.ARROW_BACK,
                                icon_color=ft.Colors.WHITE,
                                on_click=lambda e: self._hide_graphs(),
                            ),
                            ft.Text(
                                "Gráficas del hábito",
                                size=20,
                                weight=ft.FontWeight.BOLD,
                                color=ft.Colors.WHITE,
                            ),
                        ],
                        spacing=12,
                        alignment=ft.MainAxisAlignment.START,
                    ),
                    ft.Divider(color=ft.Colors.WHITE_10),
                    graph_content,
                ],
                spacing=16,
                expand=True,
            ),
            padding=20,
            expand=True,
        )
    
    def build(self) -> ft.Container:
        """
        Construye y retorna el widget principal de la vista
        
        Returns:
            Container con el contenido de la vista de hábitos
        """
        self.main_column = ft.Column(
            controls=[self.habits_list.build()],
            expand=True,
        )
        
        # Inicializar BD de forma asíncrona
        async def init():
            await self.habits_service.initialize()
            # Actualizar la lista después de cargar los hábitos
            self._refresh_list()
        
        asyncio.create_task(init())
        
        return ft.Container(
            content=self.main_column,
            padding=20,
            expand=True,
            bgcolor=None,
        )

