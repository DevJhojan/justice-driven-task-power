"""
Vista de Hábitos (Habits) de la aplicación
Sistema completo de hábitos con persistencia en BD, racha diaria y CRUD
"""

import flet as ft
import asyncio
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
import uuid

from app.services.database_service import DatabaseService


@dataclass
class Habit:
    """Modelo de datos para un hábito"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    description: str = ""
    frequency: str = "daily"  # daily o weekly
    streak: int = 0
    last_completed: Optional[str] = None  # ISO format datetime
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> dict:
        """Convierte el hábito a diccionario"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> "Habit":
        """Crea un hábito desde un diccionario"""
        return cls(**data)
    
    def complete_today(self) -> None:
        """Marca el hábito como completado hoy"""
        today = datetime.now().date().isoformat()
        
        if self.last_completed is None:
            # Primera vez completando
            self.streak = 1
        else:
            # Checar si fue completado hoy
            last_date = datetime.fromisoformat(self.last_completed).date().isoformat()
            if last_date != today:
                # Checar si fue completado ayer
                yesterday = (datetime.now().date() - timedelta(days=1)).isoformat()
                if last_date == yesterday:
                    # Continuar la racha
                    self.streak += 1
                else:
                    # Romper la racha
                    self.streak = 1
        
        self.last_completed = datetime.now().isoformat()
    
    def was_completed_today(self) -> bool:
        """Verifica si fue completado hoy"""
        if self.last_completed is None:
            return False
        today = datetime.now().date().isoformat()
        last_date = datetime.fromisoformat(self.last_completed).date().isoformat()
        return last_date == today


class HabitsView:
    """Clase que representa la vista de hábitos con CRUD y persistencia BD"""
    
    def __init__(self, on_update: Optional[Callable] = None):
        """
        Inicializa la vista de hábitos
        
        Args:
            on_update: Callback opcional al actualizar hábitos
        """
        self.database_service = DatabaseService()
        self.habits: Dict[str, Habit] = {}
        self.on_update = on_update
        self.showing_form = False
        
        # UI Components
        self.title_input = ft.TextField(label="Título del hábito", expand=True)
        self.description_input = ft.TextField(label="Descripción", expand=True, multiline=True, min_lines=2)
        self.frequency_dropdown = ft.Dropdown(
            label="Frecuencia",
            options=[
                ft.dropdown.Option("daily", "Diario"),
                ft.dropdown.Option("weekly", "Semanal"),
            ],
            value="daily",
        )
        self.form_container = None
        self.habits_list_container = None
        self.main_column = None
    
    async def _init_db(self):
        """Inicializa la tabla de hábitos en la BD"""
        try:
            await self.database_service.execute(
                """
                CREATE TABLE IF NOT EXISTS habits (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    description TEXT,
                    frequency TEXT DEFAULT 'daily',
                    streak INTEGER DEFAULT 0,
                    last_completed TEXT,
                    created_at TEXT
                )
                """
            )
            await self.database_service.commit()
            print("[HabitsView] Tabla de hábitos creada/verificada")
        except Exception as e:
            print(f"[HabitsView] Error inicializando BD: {e}")
    
    async def _load_from_db(self):
        """Carga hábitos desde la BD"""
        try:
            habits_data = await self.database_service.get_all("habits")
            self.habits = {}
            for habit_data in habits_data:
                habit = Habit.from_dict(habit_data)
                self.habits[habit.id] = habit
            print(f"[HabitsView] Cargados {len(self.habits)} hábitos desde BD")
        except Exception as e:
            print(f"[HabitsView] Error cargando hábitos: {e}")
    
    async def _save_to_db(self, habit: Habit):
        """Guarda un hábito en la BD"""
        try:
            await self.database_service.execute(
                """
                INSERT INTO habits (id, title, description, frequency, streak, last_completed, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    habit.id,
                    habit.title,
                    habit.description,
                    habit.frequency,
                    habit.streak,
                    habit.last_completed,
                    habit.created_at,
                ),
            )
            await self.database_service.commit()
        except Exception as e:
            print(f"[HabitsView] Error guardando hábito: {e}")
    
    async def _update_in_db(self, habit: Habit):
        """Actualiza un hábito en la BD"""
        try:
            await self.database_service.execute(
                """
                UPDATE habits
                SET title = ?, description = ?, frequency = ?, streak = ?, last_completed = ?
                WHERE id = ?
                """,
                (
                    habit.title,
                    habit.description,
                    habit.frequency,
                    habit.streak,
                    habit.last_completed,
                    habit.id,
                ),
            )
            await self.database_service.commit()
        except Exception as e:
            print(f"[HabitsView] Error actualizando hábito: {e}")
    
    async def _delete_from_db(self, habit_id: str):
        """Elimina un hábito de la BD"""
        try:
            await self.database_service.execute("DELETE FROM habits WHERE id = ?", (habit_id,))
            await self.database_service.commit()
        except Exception as e:
            print(f"[HabitsView] Error eliminando hábito: {e}")
    
    def _create_habit(self):
        """Crea un nuevo hábito"""
        if not self.title_input.value or self.title_input.value.strip() == "":
            return
        
        habit = Habit(
            title=self.title_input.value,
            description=self.description_input.value or "",
            frequency=self.frequency_dropdown.value or "daily",
        )
        
        self.habits[habit.id] = habit
        asyncio.create_task(self._save_to_db(habit))
        
        # Limpiar inputs
        self.title_input.value = ""
        self.description_input.value = ""
        self.frequency_dropdown.value = "daily"
        
        self._toggle_form()
        self._refresh_list()
    
    def _complete_habit(self, habit_id: str):
        """Marca/desmarca un hábito como completado"""
        if habit_id in self.habits:
            habit = self.habits[habit_id]
            
            # Si ya fue completado hoy, desmarcarlo
            if habit.was_completed_today():
                # Desmarcar: restar 1 a la racha (mínimo 0)
                habit.streak = max(0, habit.streak - 1)
                habit.last_completed = None
            else:
                # Marcar como completado
                habit.complete_today()
            
            asyncio.create_task(self._update_in_db(habit))
            self._refresh_list()
            if self.on_update:
                self.on_update()
    
    def _delete_habit(self, habit_id: str):
        """Elimina un hábito"""
        if habit_id in self.habits:
            del self.habits[habit_id]
            asyncio.create_task(self._delete_from_db(habit_id))
            self._refresh_list()
    
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
            if self.habits_list_container.content:
                self.habits_list_container.update()
    
    def _build_habit_cards(self) -> List[ft.Container]:
        """Construye las tarjetas de hábitos"""
        cards = []
        
        if not self.habits:
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
        
        for habit in self.habits.values():
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
        return ft.Container(
            content=ft.Column(
                [
                    ft.Text(
                        "Nuevo Hábito",
                        size=24,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.WHITE,
                    ),
                    self.title_input,
                    self.description_input,
                    self.frequency_dropdown,
                    ft.Row(
                        [
                            ft.TextButton(
                                "Cancelar",
                                on_click=lambda e: self._toggle_form(),
                                style=ft.ButtonStyle(
                                    color=ft.Colors.WHITE_70,
                                ),
                            ),
                            ft.FilledButton(
                                "Guardar",
                                on_click=lambda e: self._create_habit(),
                                style=ft.ButtonStyle(
                                    bgcolor=ft.Colors.RED_400,
                                    color=ft.Colors.WHITE,
                                ),
                            ),
                        ],
                        spacing=8,
                    ),
                ],
                spacing=16,
                scroll=ft.ScrollMode.AUTO,
            ),
            padding=20,
            expand=True,
        )
    
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
            await self._init_db()
            await self._load_from_db()
            self._refresh_list()
        
        asyncio.create_task(init())
        
        return ft.Container(
            content=self.main_column,
            padding=20,
            expand=True,
            bgcolor=None,
        )

