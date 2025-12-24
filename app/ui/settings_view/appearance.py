"""
Módulo para la gestión de apariencia (tema y colores).
"""
import flet as ft
from app.services.settings_service import SettingsService, apply_theme_to_page


def build_appearance_section(
    page: ft.Page,
    settings_service: SettingsService,
    on_toggle_theme: callable,
    on_open_accent_dialog: callable
) -> list:
    """
    Construye la sección de apariencia con controles de tema y color.
    
    Args:
        page: Página de Flet.
        settings_service: Servicio de configuración.
        on_toggle_theme: Callback para cambiar tema.
        on_open_accent_dialog: Callback para abrir diálogo de colores.
    
    Returns:
        Lista de controles para la sección de apariencia.
    """
    scheme = page.theme.color_scheme if page.theme else None
    preview_color = scheme.primary if scheme and scheme.primary else ft.Colors.RED_600
    
    current_settings = settings_service.get_settings()
    
    # Botón de luna/sol para alternar tema
    theme_icon = (
        ft.Icons.DARK_MODE if current_settings.theme_mode == "dark" else ft.Icons.LIGHT_MODE
    )
    theme_icon_button = ft.IconButton(
        icon=theme_icon,
        tooltip="Cambiar modo de tema",
        on_click=on_toggle_theme,
    )
    
    return [
        ft.Text(
            "Apariencia",
            size=18,
            weight=ft.FontWeight.BOLD,
            color=preview_color
        ),
        ft.Text(
            "Ajusta el modo de tema y el color principal de la aplicación.",
            size=14,
            color=ft.Colors.GREY_600
        ),
        ft.Row(
            [
                ft.Text("Modo de tema", size=14),
                theme_icon_button,
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        ),
        ft.Text(
            "Color principal",
            size=14,
            weight=ft.FontWeight.BOLD
        ),
        ft.Row(
            [
                ft.Container(
                    content=ft.Icon(ft.Icons.CIRCLE, color=preview_color, size=20),
                    border=ft.border.all(1, ft.Colors.GREY_400),
                    border_radius=20,
                    padding=6,
                ),
                ft.ElevatedButton(
                    text="Elegir matiz",
                    icon=ft.Icons.COLOR_LENS,
                    on_click=on_open_accent_dialog,
                )
            ],
            spacing=12,
            alignment=ft.MainAxisAlignment.START,
        ),
    ]


def toggle_theme(page: ft.Page, settings_service: SettingsService, on_rebuild_view: callable):
    """
    Cambia entre tema claro y oscuro.
    
    Args:
        page: Página de Flet.
        settings_service: Servicio de configuración.
        on_rebuild_view: Callback para reconstruir la vista después del cambio.
    """
    current = settings_service.get_settings()
    new_mode = "light" if current.theme_mode == "dark" else "dark"
    updated = settings_service.update_settings(theme_mode=new_mode)
    apply_theme_to_page(page, updated)
    
    # Reconstruir vista
    if on_rebuild_view:
        on_rebuild_view()
    
    page.update()


def build_accent_color_dialog(
    page: ft.Page,
    settings_service: SettingsService,
    accent_dialog: ft.AlertDialog,
    on_color_selected: callable
):
    """
    Construye y muestra el diálogo de selección de color de acento.
    
    Args:
        page: Página de Flet.
        settings_service: Servicio de configuración.
        accent_dialog: Diálogo de acento existente.
        on_color_selected: Callback cuando se selecciona un color.
    """
    current_settings = settings_service.get_settings()
    
    # Secciones de colores con sus opciones
    sections: list[tuple[str, list[tuple[str, str, str]]]] = [
        (
            "Azules",
            [
                ("dodger_blue", "#1E90FF", "DodgerBlue"),
                ("primary_blue", "#007BFF", "Primary Blue"),
                ("bootstrap_blue", "#0D6EFD", "Bootstrap Blue"),
                ("deep_blue", "#0056B3", "Deep Blue"),
                ("deepsky_blue", "#00BFFF", "DeepSkyBlue"),
                ("steel_blue", "#4682B4", "SteelBlue"),
                ("navy_dark", "#003366", "Navy Dark"),
            ],
        ),
        (
            "Verdes",
            [
                ("success_green", "#28A745", "Success Green"),
                ("emerald", "#2ECC71", "Emerald"),
                ("bright_green", "#00C853", "Bright Green"),
                ("material_green", "#4CAF50", "Material Green"),
                ("turquoise", "#1ABC9C", "Turquoise"),
                ("green_sea", "#16A085", "Green Sea"),
                ("dark_teal", "#00695C", "Dark Teal"),
            ],
        ),
        (
            "Rojos",
            [
                ("danger_red", "#DC3545", "Danger Red"),
                ("alizarin", "#E74C3C", "Alizarin"),
                ("dark_red", "#C0392B", "Dark Red"),
                ("soft_red", "#FF5252", "Soft Red"),
                ("deep_red", "#B71C1C", "Deep Red"),
                ("vivid_red", "#FF1744", "Vivid Red"),
            ],
        ),
        (
            "Amarillos / Naranjas",
            [
                ("amber", "#FFC107", "Amber"),
                ("soft_yellow", "#FFD54F", "Soft Yellow"),
                ("orange", "#FF9800", "Orange"),
                ("deep_orange", "#FF5722", "Deep Orange"),
                ("sun_orange", "#F39C12", "Sun Orange"),
                ("golden", "#FFB300", "Golden"),
            ],
        ),
        (
            "Morados / Rosas",
            [
                ("ui_purple", "#6F42C1", "Purple UI"),
                ("amethyst", "#9B59B6", "Amethyst"),
                ("dark_purple", "#8E44AD", "Dark Purple"),
                ("vibrant_purple", "#E056FD", "Vibrant Purple"),
                ("ui_pink", "#D63384", "Pink"),
                ("hot_pink", "#FF69B4", "Hot Pink"),
            ],
        ),
        (
            "Grises / Neutros",
            [
                ("dark_gray", "#212529", "Dark Gray"),
                ("charcoal", "#343A40", "Charcoal"),
                ("medium_gray", "#495057", "Medium Gray"),
                ("secondary_gray", "#6C757D", "Secondary Gray"),
                ("light_gray", "#ADB5BD", "Light Gray"),
                ("soft_gray", "#DEE2E6", "Soft Gray"),
                ("almost_white", "#F8F9FA", "Almost White"),
            ],
        ),
        (
            "Blancos / Negros",
            [
                ("black", "#000000", "Black"),
                ("white", "#FFFFFF", "White"),
                ("soft_white", "#FAFAFA", "Soft White"),
                ("true_dark", "#121212", "True Dark Mode"),
            ],
        ),
        (
            "Colores gamer / UI",
            [
                ("neon_cyan", "#00E5FF", "Neon Cyan"),
                ("neon_green", "#76FF03", "Neon Green"),
                ("neon_pink", "#FF4081", "Neon Pink"),
                ("electric_purple", "#651FFF", "Electric Purple"),
                ("tech_blue", "#00B0FF", "Tech Blue"),
                ("mint_neon", "#1DE9B6", "Mint Neon"),
                ("orange_neon", "#FF9100", "Orange Neon"),
            ],
        ),
    ]

    section_controls: list[ft.Control] = []

    for title, options in sections:
        # Título de sección
        section_controls.append(
            ft.Text(
                title,
                size=16,
                weight=ft.FontWeight.BOLD,
            )
        )

        # Botones de la sección, organizados en filas
        buttons: list[ft.Container] = []
        for value, color, label in options:
            selected = value == current_settings.accent_color
            buttons.append(
                ft.Container(
                    content=ft.IconButton(
                        icon=ft.Icons.CIRCLE,
                        icon_color=color,
                        tooltip=label,
                        data=value,
                        on_click=lambda e, v=value: on_color_selected(v),
                    ),
                    border=ft.border.all(
                        2,
                        color if selected else ft.Colors.TRANSPARENT,
                    ),
                    border_radius=20,
                    padding=4,
                )
            )

        # Agrupar botones en filas de 4 para mejor uso de espacio
        for i in range(0, len(buttons), 4):
            section_controls.append(
                ft.Row(
                    controls=buttons[i : i + 4],
                    spacing=8,
                    alignment=ft.MainAxisAlignment.START,
                )
            )

        # Separador entre secciones
        section_controls.append(ft.Divider())

    # Contenido scrollable ocupando ~70% del ancho de la pantalla
    try:
        content_width = page.width * 0.7 if (hasattr(page, 'width') and page.width is not None and isinstance(page.width, (int, float))) else None
    except (AttributeError, TypeError):
        content_width = None

    accent_dialog.title = ft.Text("Selecciona un matiz")
    accent_dialog.content = ft.Container(
        width=content_width,
        content=ft.Column(
            controls=section_controls,
            spacing=8,
            scroll=ft.ScrollMode.AUTO,
        ),
    )
    accent_dialog.actions = [
        ft.TextButton("Cerrar", on_click=lambda ev: close_accent_dialog(accent_dialog, page))
    ]
    accent_dialog.open = True
    page.dialog = accent_dialog
    page.update()


def close_accent_dialog(accent_dialog: ft.AlertDialog, page: ft.Page):
    """Cierra el diálogo de selección de matiz si está abierto."""
    if accent_dialog:
        accent_dialog.open = False
        page.update()


def select_accent_color(
    page: ft.Page,
    settings_service: SettingsService,
    value: str,
    on_rebuild_view: callable,
    accent_dialog: ft.AlertDialog
):
    """
    Cambia el color principal de la aplicación.
    
    Args:
        page: Página de Flet.
        settings_service: Servicio de configuración.
        value: Valor del color seleccionado.
        on_rebuild_view: Callback para reconstruir la vista.
        accent_dialog: Diálogo de acento para cerrar.
    """
    # La validación se hace de forma implícita en SettingsService mediante AccentColorLiteral,
    # aquí solo comprobamos que exista algún valor.
    if not value:
        return

    updated = settings_service.update_settings(accent_color=value)
    apply_theme_to_page(page, updated)

    # Reconstruir la vista actual
    if on_rebuild_view:
        on_rebuild_view()

    # Cerrar el diálogo de selección si está abierto
    close_accent_dialog(accent_dialog, page)
    page.update()

