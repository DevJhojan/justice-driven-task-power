"""
Lista y tarjetas de hábitos reutilizable para HabitsView
"""

import flet as ft
from typing import Callable, List, Optional

from app.models.habit import Habit
from app.services.habits_service import HabitsService
from app.ui.habits.habit_card import create_habit_card


class HabitsList:
    """Componente que construye y refresca la lista de hábitos"""

    def __init__(
        self,
        habits_service: HabitsService,
        on_add: Callable,
        on_complete: Callable[[str], None],
        on_edit: Callable[[Habit], None],
        on_delete: Callable[[str], None],
    ):
        self.habits_service = habits_service
        self.on_add = on_add
        self.on_complete = on_complete
        self.on_edit = on_edit
        self.on_delete = on_delete

        self.list_container: Optional[ft.Container] = None

    def build(self) -> ft.Column:
        """Construye la sección completa: header + lista"""
        self.list_container = ft.Container(
            content=self._cards_column(),
            expand=True,
        )

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
                        on_click=self.on_add,
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
                self.list_container,
            ],
            expand=True,
            spacing=0,
        )

    def refresh(self):
        """Actualiza el listado si ya está construido"""
        if not self.list_container:
            return
        self.list_container.content = self._cards_column()
        try:
            if self.list_container.page:
                self.list_container.update()
        except Exception:
            pass

    # Internos -------------------------------------------------------------
    def _cards_column(self) -> ft.Column:
        return ft.Column(
            controls=self._build_habit_cards(),
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

    def _build_habit_cards(self) -> List[ft.Container]:
        cards: List[ft.Container] = []
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
            cards.append(
                create_habit_card(
                    habit=habit,
                    on_complete=self.on_complete,
                    on_edit=self.on_edit,
                    on_delete=self.on_delete,
                )
            )

        return cards
