"""
Módulo para la navegación y construcción de formularios de objetivos.
"""
import flet as ft
from typing import Optional
from app.data.models import Goal
from app.ui.goal_form import GoalForm


def navigate_to_goal_form(
    page: ft.Page,
    editing_goal: Optional[Goal],
    on_save: callable,
    on_go_back: callable
):
    """
    Navega a la vista del formulario de objetivo.
    
    Args:
        page: Página de Flet.
        editing_goal: Objetivo a editar (None si es nuevo).
        on_save: Callback cuando se guarda el objetivo.
        on_go_back: Callback para volver.
    """
    title = "Editar Objetivo" if editing_goal else "Nuevo Objetivo"
    
    # Crear el formulario
    form = GoalForm(
        on_save=on_save,
        on_cancel=on_go_back,
        goal=editing_goal
    )
    
    # Detectar el tema actual
    is_dark = page.theme_mode == ft.ThemeMode.DARK
    bgcolor = ft.Colors.BLACK if is_dark else ft.Colors.GREY_50
    
    # Crear la barra de título con botón de volver
    scheme = page.theme.color_scheme if page.theme else None
    title_color = scheme.primary if scheme and scheme.primary else ft.Colors.RED_400
    
    back_button = ft.IconButton(
        icon=ft.Icons.ARROW_BACK,
        on_click=lambda e: on_go_back(),
        icon_color=title_color,
        tooltip="Volver"
    )
    
    title_bar = ft.Container(
        content=ft.Row(
            [
                back_button,
                ft.Text(
                    title,
                    size=24,
                    weight=ft.FontWeight.BOLD,
                    color=title_color,
                    expand=True
                )
            ],
            alignment=ft.MainAxisAlignment.START,
            vertical_alignment=ft.CrossAxisAlignment.CENTER
        ),
        padding=ft.padding.symmetric(vertical=16, horizontal=20),
        bgcolor=ft.Colors.BLACK87 if is_dark else ft.Colors.RED_50
    )
    
    # Construir la vista del formulario
    form_view = ft.View(
        route="/goal-form",
        controls=[
            title_bar,
            ft.Container(
                content=form.build(),
                expand=True,
                padding=20
            )
        ],
        bgcolor=bgcolor
    )
    
    # Agregar la vista y navegar a ella
    page.views.append(form_view)
    page.go("/goal-form")

