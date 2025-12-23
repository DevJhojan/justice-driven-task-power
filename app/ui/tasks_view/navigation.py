"""
Módulo para la barra de navegación de prioridades.
"""
import flet as ft
from .utils import get_priority_colors, get_screen_width, is_desktop_platform, PRIORITY_DISPLAY


def build_priority_navigation_bar(
    page: ft.Page,
    current_priority_section: str,
    on_priority_click: callable,
    on_add_task_click: callable
) -> ft.Container:
    """
    Construye la barra de navegación con 4 botones para las prioridades.
    
    Args:
        page: Página de Flet.
        current_priority_section: Prioridad activa actual.
        on_priority_click: Callback cuando se hace clic en una prioridad.
        on_add_task_click: Callback cuando se hace clic en agregar tarea.
    
    Returns:
        Container con la barra de navegación.
    """
    is_dark = page.theme_mode == ft.ThemeMode.DARK
    is_desktop = is_desktop_platform(page)
    bgcolor = ft.Colors.BLACK87 if is_dark else ft.Colors.WHITE
    
    buttons = []
    screen_width = get_screen_width(page)
    is_wide_screen = screen_width > 600 if isinstance(screen_width, (int, float)) else False
    
    for priority_key, emoji, label in PRIORITY_DISPLAY:
        colors = get_priority_colors(priority_key, is_dark)
        is_active = current_priority_section == priority_key
        
        # Tamaños responsive basados en ancho de pantalla
        emoji_size = 22 if is_wide_screen else 18
        text_size = 10 if is_wide_screen else 9
        button_padding = 10 if is_wide_screen else 6
        
        button = ft.Container(
            content=ft.Column(
                [
                    ft.Text(emoji, size=emoji_size),
                    ft.Text(
                        label,
                        size=text_size,
                        text_align=ft.TextAlign.CENTER,
                        max_lines=2,
                        overflow=ft.TextOverflow.ELLIPSIS,
                        selectable=False
                    )
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=4,
                tight=True
            ),
            on_click=lambda e, p=priority_key: on_priority_click(p),
            padding=button_padding,
            bgcolor=colors['primary'] if is_active else bgcolor,
            border=ft.border.all(2, colors['primary'] if is_active else ft.Colors.TRANSPARENT),
            border_radius=8,
            expand=True,
            tooltip=colors['text']
        )
        buttons.append(button)
    
    # Botón de agregar tarea
    scheme = page.theme.color_scheme if page.theme else None
    title_color = scheme.primary if scheme and scheme.primary else ft.Colors.RED_400
    button_size = 40 if is_wide_screen else 36
    icon_size = 20 if is_wide_screen else 18
    
    add_button = ft.IconButton(
        icon=ft.Icons.ADD,
        on_click=on_add_task_click,
        bgcolor=title_color,
        icon_color=ft.Colors.WHITE,
        tooltip="Nueva Tarea",
        width=button_size,
        height=button_size,
        icon_size=icon_size
    )
    
    # Contenedor responsive con padding vertical mínimo
    nav_padding = ft.padding.symmetric(
        vertical=4 if is_wide_screen else 3,
        horizontal=20 if is_wide_screen else 12
    )
    button_spacing = 10 if is_wide_screen else 6
    
    # Crear Row con botones de prioridad y botón de agregar
    row_controls = buttons.copy()
    row_controls.append(add_button)
    
    return ft.Container(
        content=ft.Row(
            row_controls,
            spacing=button_spacing,
            scroll=ft.ScrollMode.AUTO if not is_wide_screen else ft.ScrollMode.HIDDEN,
            wrap=False,
            expand=True
        ),
        padding=nav_padding,
        bgcolor=bgcolor,
        border=ft.border.only(bottom=ft.BorderSide(1, ft.Colors.GREY_300 if not is_dark else ft.Colors.GREY_700)),
        expand=True,
        margin=ft.margin.only(bottom=0)
    )

