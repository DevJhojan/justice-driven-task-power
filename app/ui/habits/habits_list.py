"""
Lista y tarjetas de hábitos reutilizable para HabitsView
"""

import flet as ft
from datetime import datetime
from typing import Callable, List, Optional

from app.models.habit import Habit
from app.services.habits_service import HabitsService


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

        frequency_labels = {
            "daily": "Diario",
            "weekly": "Semanal",
            "monthly": "Mensual",
            "semiannual": "Semestral",
            "annual": "Anual",
        }

        for habit in habits:
            completed_today = habit.was_completed_today()
            freq_text = frequency_labels.get(habit.frequency, habit.frequency.capitalize())
            if habit.frequency != "daily":
                freq_text = f"{freq_text}: {habit.frequency_times} veces"

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
                                        ft.Text(
                                            f"Frecuencia: {freq_text}",
                                            size=12,
                                            color=ft.Colors.WHITE_70,
                                        ),
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
                                    on_click=lambda e, hid=habit.id: self.on_complete(hid),
                                ),
                                ft.IconButton(
                                    icon=ft.Icons.EDIT,
                                    icon_color=ft.Colors.WHITE,
                                    on_click=lambda e, h=habit: self.on_edit(h),
                                ),
                                ft.IconButton(
                                    icon=ft.Icons.DELETE_OUTLINE,
                                    icon_color=ft.Colors.RED_400,
                                    on_click=lambda e, hid=habit.id: self.on_delete(hid),
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
