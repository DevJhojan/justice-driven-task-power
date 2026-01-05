"""
Vista de Metas sencilla con lista en memoria.
"""

import uuid
import flet as ft


class GoalsView(ft.Container):
    """Pequeño gestor de metas en una sola vista."""

    def __init__(self):
        super().__init__()
        self.goals = []  # Lista en memoria: [{id, title, description, done}]
        self.title_input = ft.TextField(label="Título de la meta", hint_text="Ej. Leer 10 páginas", autofocus=True)
        self.desc_input = ft.TextField(label="Descripción", hint_text="Detalles opcionales", multiline=True, max_lines=3)
        self.goal_list = ft.Column(spacing=10)

        self._build_content()
        self._refresh_list()

    def _build_content(self):
        toolbar = ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Row(
                    spacing=8,
                    controls=[ft.Icon(ft.Icons.FLAG, color=ft.Colors.BLUE_400), ft.Text("Metas", size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)],
                ),
                ft.IconButton(icon=ft.Icons.REFRESH, tooltip="Limpiar campos", on_click=lambda _: self._reset_form()),
            ],
        )

        add_form = ft.Column(
            spacing=10,
            controls=[
                self.title_input,
                self.desc_input,
                ft.ElevatedButton("Agregar meta", icon=ft.Icons.ADD, on_click=self._add_goal),
            ],
        )

        self.content = ft.Column(
            spacing=16,
            controls=[
                toolbar,
                ft.Divider(color="#333"),
                add_form,
                ft.Divider(color="#333"),
                ft.Text("Tus metas", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                self.goal_list,
            ],
        )

        self.padding = 20
        self.expand = True
        self.bgcolor = None

    def _add_goal(self, _):
        title = (self.title_input.value or "").strip()
        desc = (self.desc_input.value or "").strip()
        if not title:
            self.title_input.error_text = "El título es obligatorio"
            self.update()
            return
        self.title_input.error_text = None
        goal = {
            "id": str(uuid.uuid4()),
            "title": title,
            "description": desc,
            "done": False,
        }
        self.goals.append(goal)
        self._reset_form()
        self._refresh_list()

    def _reset_form(self):
        self.title_input.value = ""
        self.desc_input.value = ""
        self.title_input.error_text = None
        self.update()

    def _toggle_goal(self, goal_id: str):
        for goal in self.goals:
            if goal["id"] == goal_id:
                goal["done"] = not goal["done"]
                break
        self._refresh_list()

    def _delete_goal(self, goal_id: str):
        self.goals = [g for g in self.goals if g["id"] != goal_id]
        self._refresh_list()

    def _build_goal_tile(self, goal: dict) -> ft.Container:
        status_color = ft.Colors.GREEN_400 if goal["done"] else ft.Colors.AMBER
        status_text = "Completada" if goal["done"] else "En progreso"
        return ft.Container(
            border=ft.border.all(1, "#333"),
            border_radius=10,
            padding=12,
            bgcolor="#161616",
            content=ft.Column(
                spacing=6,
                controls=[
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Text(goal["title"], size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                            ft.Row(
                                spacing=6,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                controls=[
                                    ft.Icon(ft.Icons.CIRCLE, size=12, color=status_color),
                                    ft.Text(status_text, size=12, color=status_color),
                                ],
                            ),
                        ],
                    ),
                    ft.Text(goal["description"] or "Sin descripción", size=12, color=ft.Colors.WHITE70),
                    ft.Row(
                        spacing=8,
                        controls=[
                            ft.TextButton(
                                text="Marcar como completada" if not goal["done"] else "Marcar en progreso",
                                icon=ft.Icons.CHECK_CIRCLE if not goal["done"] else ft.Icons.UNDO,
                                on_click=lambda _, gid=goal["id"]: self._toggle_goal(gid),
                            ),
                            ft.TextButton(
                                text="Eliminar",
                                icon=ft.Icons.DELETE,
                                on_click=lambda _, gid=goal["id"]: self._delete_goal(gid),
                                style=ft.ButtonStyle(color={"": ft.Colors.RED_300}),
                            ),
                        ],
                    ),
                ],
            ),
        )

    def _refresh_list(self):
        if not self.goals:
            self.goal_list.controls = [ft.Text("Aún no tienes metas. ¡Crea la primera!", color=ft.Colors.WHITE70, size=12)]
        else:
            self.goal_list.controls = [self._build_goal_tile(goal) for goal in self.goals]
        self.update()

