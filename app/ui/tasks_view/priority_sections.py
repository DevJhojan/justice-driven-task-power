"""
Módulo para la construcción de secciones de prioridad.
"""
import flet as ft
from typing import Optional
from .utils import get_priority_colors, get_screen_width, is_desktop_platform


def build_priority_section(
    page: ft.Page,
    priority: str,
    priority_filters: dict,
    tasks_container: ft.Column,
    on_filter_click: callable,
    priority_section_refs: dict
) -> ft.Container:
    """
    Construye una sección de prioridad con su filtro y tareas.
    
    Args:
        page: Página de Flet.
        priority: Prioridad de la sección.
        priority_filters: Diccionario con los filtros por prioridad.
        tasks_container: Contenedor de tareas para esta prioridad.
        on_filter_click: Callback cuando se hace clic en un filtro.
        priority_section_refs: Diccionario para guardar referencias de secciones.
    
    Returns:
        Container con la sección completa.
    """
    is_dark = page.theme_mode == ft.ThemeMode.DARK
    colors = get_priority_colors(priority, is_dark)
    current_filter = priority_filters[priority]
    
    # Detectar si es escritorio o móvil
    is_desktop = is_desktop_platform(page)
    
    # Título de la sección - responsive y adaptable
    screen_width = get_screen_width(page)
    is_wide = screen_width > 600 if isinstance(screen_width, (int, float)) else False
    
    title_size = 20 if is_wide else 16  # Reducido de 22/18 a 20/16
    title_padding_vertical = 6 if is_wide else 4  # Reducido de 10/8 a 6/4
    title_padding_horizontal = 20 if is_wide else 12
    
    section_title = ft.Container(
        content=ft.Row(
            [
                ft.Text(
                    colors['text'],
                    size=title_size,
                    weight=ft.FontWeight.BOLD,
                    color=colors['primary'],
                    expand=True,
                    max_lines=2,
                    overflow=ft.TextOverflow.ELLIPSIS,
                    selectable=False
                )
            ],
            expand=True,
            wrap=False
        ),
        padding=ft.padding.symmetric(
            vertical=title_padding_vertical,
            horizontal=title_padding_horizontal
        ),
        bgcolor=colors['light'],
        border=ft.border.only(bottom=ft.BorderSide(2, colors['primary'])),
        expand=True,
        margin=ft.margin.only(top=0)
    )
    
    # Botones de filtro para esta sección - responsive - más compactos
    active_bg = colors['primary']
    inactive_bg = ft.Colors.GREY_800 if is_dark else ft.Colors.GREY_100
    text_color = ft.Colors.WHITE
    button_height = 36 if is_desktop else 32  # Reducido de 40/36 a 36/32
    button_padding = ft.padding.symmetric(vertical=6 if is_desktop else 4, horizontal=16 if is_desktop else 12)  # Reducido
    
    # Botones de filtro responsive
    filter_buttons = ft.Row(
        [
            ft.ElevatedButton(
                text="Todas",
                on_click=lambda e, p=priority: on_filter_click(p, None),
                bgcolor=active_bg if current_filter is None else inactive_bg,
                color=text_color,
                height=button_height,
                style=ft.ButtonStyle(
                    shape=ft.RoundedRectangleBorder(radius=8)
                ),
                expand=True if is_desktop else False
            ),
            ft.ElevatedButton(
                text="Pendientes",
                on_click=lambda e, p=priority: on_filter_click(p, False),
                bgcolor=active_bg if current_filter is False else inactive_bg,
                color=text_color,
                height=button_height,
                style=ft.ButtonStyle(
                    shape=ft.RoundedRectangleBorder(radius=8)
                ),
                expand=True if is_desktop else False
            ),
            ft.ElevatedButton(
                text="Completadas",
                on_click=lambda e, p=priority: on_filter_click(p, True),
                bgcolor=active_bg if current_filter is True else inactive_bg,
                color=text_color,
                height=button_height,
                style=ft.ButtonStyle(
                    shape=ft.RoundedRectangleBorder(radius=8)
                ),
                expand=True if is_desktop else False
            )
        ],
        spacing=12 if is_desktop else 8,
        scroll=ft.ScrollMode.AUTO if not is_desktop else ft.ScrollMode.HIDDEN,
        wrap=False,
        expand=True
    )
    
    # Contenedor completo de la sección - responsive y adaptable
    section_padding = 20 if is_desktop else 12
    section_container = ft.Container(
        content=ft.Column(
            [
                section_title,
                ft.Container(
                    content=filter_buttons,
                    padding=button_padding,
                    expand=True
                ),
                ft.Container(
                    content=tasks_container,
                    padding=ft.padding.symmetric(
                        horizontal=section_padding
                    ),
                    expand=True
                )
            ],
            spacing=0,
            expand=True
        ),
        key=f"priority_section_{priority}",
        margin=ft.margin.only(
            bottom=12 if is_desktop else 8,  # Reducido de 16/12 a 12/8
            top=0
        ),
        expand=True
    )
    
    # Guardar referencia para scroll
    priority_section_refs[priority] = section_container
    
    return section_container

