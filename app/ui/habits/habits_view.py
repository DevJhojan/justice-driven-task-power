"""
Vista de Hábitos (Habits) de la aplicación
Sistema completo de hábitos con persistencia en BD, racha diaria y CRUD
"""

import flet as ft
import asyncio
from datetime import datetime
from typing import List, Optional, Callable

from app.services.habits_service import HabitsService
from app.ui.habits.habits_form import HabitsForm


class HabitsView:
    """Clase que representa la vista de hábitos con CRUD y persistencia BD"""
    
    def __init__(self, on_update: Optional[Callable] = None):
        """
        Inicializa la vista de hábitos
        
        Args:
            on_update: Callback opcional al actualizar hábitos
        """
        self.habits_service = HabitsService()
        self.on_update = on_update
        self.showing_form = False

        # UI Components
        self.form: HabitsForm = HabitsForm(on_save=self._handle_save, on_cancel=lambda e: self._toggle_form())
        self.habits_list_container = None
        self.main_column = None
    
    def _handle_save(self, _):
        """Valida y crea un hábito usando el servicio"""
        values = self.form.get_values()
        title = values.get("title", "")
        if not title:
            return
        asyncio.create_task(self._async_create_habit(values))

    async def _async_create_habit(self, values: dict):
        """Crea un hábito de forma asíncrona"""
        try:
            await self.habits_service.create_habit(
                title=values.get("title", ""),
                description=values.get("description", ""),
                frequency=values.get("frequency", "daily"),
            )
            self.form.reset()
            self._toggle_form()
            self._refresh_list()
        except Exception as e:
            print(f"[HabitsView] Error creando hábito: {e}")
    
    def _complete_habit(self, habit_id: str):
        """Marca/desmarca un hábito como completado"""
        asyncio.create_task(self._async_complete_habit(habit_id))
    
    async def _async_complete_habit(self, habit_id: str):
        """Marca/desmarca un hábito como completado de forma asíncrona"""
        try:
            await self.habits_service.complete_habit(habit_id)
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
            self._refresh_list()
        except Exception as e:
            print(f"[HabitsView] Error eliminando hábito: {e}")
    
    def _toggle_form(self):
        """Alterna entre mostrar/ocultar el formulario"""
        self.showing_form = not self.showing_form
        self._update_view()
    
    def _update_view(self):
        """Actualiza la vista según el estado"""
        if self.main_column:
            self.main_column.controls = []
            if self.showing_form:
                self.main_column.controls.append(self._build_form())
            else:
                self.main_column.controls.append(self._build_habits_list())
            self.main_column.update()
    
    def _refresh_list(self):
        """Refresca la lista de hábitos"""
        if self.habits_list_container and not self.showing_form:
            self.habits_list_container.content = ft.Column(
                controls=self._build_habit_cards(),
                scroll=ft.ScrollMode.AUTO,
                expand=True,
            )
            # Solo actualizar si el control está en la página
            try:
                if self.habits_list_container.page:
                    self.habits_list_container.update()
            except Exception as e:
                # Si aún no está en la página, se actualizará cuando se agregue
                pass
    
    def _build_habit_cards(self) -> List[ft.Container]:
        """Construye las tarjetas de hábitos"""
        cards = []
        habits = self.habits_service.get_all_habits()
        
        if not habits:
            return [
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Icon(
                                ft.Icons.LIGHTBULB_OUTLINE,
                                size=40,
                                color=ft.Colors.GREY_400,
                            ),
                            ft.Text(
                                "Sin hábitos aún",
                                color=ft.Colors.WHITE_70,
                                size=16,
                            ),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    alignment=ft.Alignment.CENTER,
                    padding=40,
                )
            ]
        
        for habit in habits:
            completed_today = habit.was_completed_today()
            
            card = ft.Container(
                content=ft.Column(
                    [
                        ft.Row(
                            [
                                ft.Column(
                                    [
                                        ft.Text(
                                            habit.title,
                                            size=16,
                                            weight=ft.FontWeight.BOLD,
                                            color=ft.Colors.WHITE,
                                        ),
                                        ft.Text(
                                            habit.description[:50] if habit.description else "",
                                            size=12,
                                            color=ft.Colors.WHITE_70,
                                        ) if habit.description else ft.Container(),
                                    ],
                                    expand=True,
                                    spacing=4,
                                ),
                                ft.Row(
                                    [
                                        ft.Icon(
                                            ft.Icons.WHATSHOT,
                                            size=20,
                                            color=ft.Colors.RED_400,
                                        ),
                                        ft.Text(
                                            str(habit.streak),
                                            size=16,
                                            weight=ft.FontWeight.BOLD,
                                            color=ft.Colors.RED_400,
                                        ),
                                    ],
                                    spacing=4,
                                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                ),
                            ],
                            spacing=16,
                            expand=True,
                        ),
                        ft.Divider(height=1, color=ft.Colors.WHITE_10),
                        ft.Row(
                            [
                                (
                                    ft.Text(
                                        f"Última vez: {datetime.fromisoformat(habit.last_completed).strftime('%d/%m %H:%M')}",
                                        size=12,
                                        color=ft.Colors.WHITE_60,
                                    )
                                    if habit.last_completed
                                    else ft.Text(
                                        "No completado aún",
                                        size=12,
                                        color=ft.Colors.WHITE_60,
                                    )
                                ),
                                ft.IconButton(
                                    icon=ft.Icons.CHECK_CIRCLE if completed_today else ft.Icons.CIRCLE_OUTLINED,
                                    icon_color=ft.Colors.RED_500 if completed_today else ft.Colors.WHITE_60,
                                    on_click=lambda e, hid=habit.id: self._complete_habit(hid),
                                ),
                                ft.IconButton(
                                    icon=ft.Icons.DELETE_OUTLINE,
                                    icon_color=ft.Colors.RED_400,
                                    on_click=lambda e, hid=habit.id: self._delete_habit(hid),
                                ),
                            ],
                            spacing=8,
                        ),
                    ],
                    spacing=8,
                ),
                bgcolor=ft.Colors.WHITE_10,
                border_radius=8,
                padding=16,
                margin=ft.margin.only(bottom=12),
            )
            cards.append(card)
        
        return cards
    
    def _build_form(self) -> ft.Container:
        """Construye el formulario de crear hábito"""
        return self.form.build()
    
    def _build_habits_list(self) -> ft.Column:
        """Construye la lista de hábitos"""
        self.habits_list_container = ft.Container(
            content=ft.Column(
                controls=self._build_habit_cards(),
                scroll=ft.ScrollMode.AUTO,
                expand=True,
            ),
            expand=True,
        )
        
        # Header fijo en la parte superior
        header = ft.Container(
            content=ft.Row(
                [
                    ft.Text(
                        "Mis Hábitos",
                        size=24,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.WHITE,
                    ),
                    ft.IconButton(
                        icon=ft.Icons.ADD_CIRCLE,
                        icon_size=28,
                        icon_color=ft.Colors.RED_400,
                        on_click=lambda e: self._toggle_form(),
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            padding=ft.padding.only(bottom=16),
            border_radius=0,
        )
        
        return ft.Column(
            [
                header,
                self.habits_list_container,
            ],
            expand=True,
            spacing=0,
        )
    
    def build(self) -> ft.Container:
        """
        Construye y retorna el widget principal de la vista
        
        Returns:
            Container con el contenido de la vista de hábitos
        """
        self.main_column = ft.Column(
            controls=[self._build_habits_list()],
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

