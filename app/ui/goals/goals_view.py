"""
Vista principal de metas, usa GoalsList y GoalsForm
"""
import flet as ft
from app.services.goals_service import GoalsService
from app.models.goal import Goal
from app.ui.goals.goals_list import GoalsList
from app.ui.goals.goals_form import GoalsForm

class GoalsView(ft.Container):
    def __init__(self, goals_service: GoalsService = None):
        super().__init__()
        self.goals_service = goals_service or GoalsService()
        self.goals = self.goals_service.list_goals()
        self.selected_goal = None
        self.showing_form = False
        self.form_container = ft.Container(visible=False)
        self.list_container = ft.Container()
        self.add_btn = ft.IconButton(
            icon=ft.Icons.ADD.value,
            tooltip="Agregar meta",
            on_click=self._show_add_form,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
        )

        self.goals_list = GoalsList(
            self.goals,
            on_edit=self._show_edit_form,
            on_delete=self._delete_goal,
            on_progress_update=self._update_progress,
        )
        self.list_container.content = self.goals_list

        # Encabezado con título y botón
        self.header = ft.Row([
            ft.Text("Metas", size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_400, expand=True),
            self.add_btn,
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER)

        self.content = ft.Column([
            self.header,
            self.list_container,
            self.form_container,
        ], expand=True)
        self.expand = True

    def build(self, page=None):
        """
        Devuelve el propio contenedor para integración con HomeView
        """
        return self

    def _show_add_form(self, _):
        self.selected_goal = None
        self.form_container.content = GoalsForm(
            on_save=self._add_goal,
            on_cancel=self._hide_form,
        )
        self.form_container.visible = True
        self.list_container.visible = False
        self.add_btn.visible = False
        self.update()

    def _show_edit_form(self, goal: Goal):
        self.selected_goal = goal
        self.form_container.content = GoalsForm(
            on_save=self._edit_goal,
            on_cancel=self._hide_form,
            editing_goal=goal,
        )
        self.form_container.visible = True
        self.list_container.visible = False
        self.add_btn.visible = False
        self.update()

    def _hide_form(self, *_):
        self.form_container.visible = False
        self.list_container.visible = True
        self.add_btn.visible = True
        self.update()

    def _add_goal(self, values):
        goal = self.goals_service.create_goal(**values)
        self.goals = self.goals_service.list_goals()
        self.goals_list.set_goals(self.goals)
        self._hide_form()

    def _edit_goal(self, values):
        self.goals_service.update_goal(self.selected_goal.id, **values)
        self.goals = self.goals_service.list_goals()
        self.goals_list.set_goals(self.goals)
        self._hide_form()

    def _delete_goal(self, goal: Goal):
        self.goals_service.delete_goal(goal.id)
        self.goals = self.goals_service.list_goals()
        self.goals_list.set_goals(self.goals)
        self.update()

    def _update_progress(self, goal: Goal):
        # Simple: suma 1 a progreso, puedes personalizar
        self.goals_service.update_goal(goal.id, progress=goal.progress + 1)
        self.goals = self.goals_service.list_goals()
        self.goals_list.set_goals(self.goals)
        self.update()
