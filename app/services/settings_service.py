"""
Servicio de ajustes de apariencia (tema y color principal).

Responsabilidades:
- Guardar y leer preferencias de apariencia en SQLite (tabla app_settings).
- Proveer una API sencilla para obtener/actualizar:
  - modo de tema: 'light' o 'dark'
  - color de acento: 'red', 'blue', 'green'
- Aplicar estas preferencias al objeto `ft.Page` de Flet.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Optional

import flet as ft

from app.data.database import Database


ThemeModeLiteral = Literal["light", "dark"]
TasksViewModeLiteral = Literal["lista_normal", "lista_4do", "kanban"]
# Paletas disponibles: fácil de extender añadiendo nuevos valores aquí.
# Usamos claves legibles y cada una mapea a un color HEX concreto.
AccentColorLiteral = Literal[
    # Azules
    "dodger_blue",
    "primary_blue",
    "bootstrap_blue",
    "deep_blue",
    "deepsky_blue",
    "steel_blue",
    "navy_dark",
    # Verdes
    "success_green",
    "emerald",
    "bright_green",
    "material_green",
    "turquoise",
    "green_sea",
    "dark_teal",
    # Rojos
    "danger_red",
    "alizarin",
    "dark_red",
    "soft_red",
    "deep_red",
    "vivid_red",
    # Amarillos / Naranjas
    "amber",
    "soft_yellow",
    "orange",
    "deep_orange",
    "sun_orange",
    "golden",
    # Morados / Rosas
    "ui_purple",
    "amethyst",
    "dark_purple",
    "vibrant_purple",
    "ui_pink",
    "hot_pink",
    # Grises / Neutros
    "dark_gray",
    "charcoal",
    "medium_gray",
    "secondary_gray",
    "light_gray",
    "soft_gray",
    "almost_white",
    # Blancos / Negros útiles
    "black",
    "white",
    "soft_white",
    "true_dark",
    # Modernos / gamer / UI
    "neon_cyan",
    "neon_green",
    "neon_pink",
    "electric_purple",
    "tech_blue",
    "mint_neon",
    "orange_neon",
]


@dataclass
class AppSettings:
    """Modelo de ajustes de apariencia."""

    theme_mode: ThemeModeLiteral = "dark"
    accent_color: AccentColorLiteral = "red"
    tasks_view_mode: TasksViewModeLiteral = "lista_normal"


class SettingsService:
    """
    Servicio para persistir y recuperar ajustes de apariencia.

    Decisiones técnicas:
    - Se usa la misma base de datos SQLite (`tasks.db`) para no depender
      de almacenamiento adicional.
    - Tabla `app_settings` con una sola fila (key='global') para ajustes
      globales de la app.
    """

    def __init__(self, database: Optional[Database] = None) -> None:
        self.db = database or Database()
        self._ensure_table()

    def _ensure_table(self) -> None:
        """Crea la tabla de ajustes si no existe y garantiza la fila global."""
        conn = self.db.get_connection()
        cur = conn.cursor()

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS app_settings (
                key TEXT PRIMARY KEY,
                theme_mode TEXT NOT NULL,
                accent_color TEXT NOT NULL,
                tasks_view_mode TEXT NOT NULL DEFAULT 'lista_normal'
            )
            """
        )
        
        # Migración: Agregar columna tasks_view_mode si no existe
        try:
            cur.execute("SELECT tasks_view_mode FROM app_settings LIMIT 1")
        except Exception:
            # La columna no existe, agregarla
            try:
                cur.execute("ALTER TABLE app_settings ADD COLUMN tasks_view_mode TEXT NOT NULL DEFAULT 'lista_normal'")
            except Exception:
                # Si falla, la columna ya existe o hay otro problema
                pass

        cur.execute("SELECT key FROM app_settings WHERE key = 'global'")
        if not cur.fetchone():
            cur.execute(
                """
                INSERT INTO app_settings (key, theme_mode, accent_color, tasks_view_mode)
                VALUES ('global', 'dark', 'red', 'lista_normal')
                """
            )

        conn.commit()
        conn.close()

    def get_settings(self) -> AppSettings:
        """Obtiene los ajustes actuales desde la base de datos."""
        conn = self.db.get_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT theme_mode, accent_color, tasks_view_mode FROM app_settings WHERE key = 'global'"
        )
        row = cur.fetchone()
        conn.close()

        if not row:
            return AppSettings()  # valores por defecto

        theme_mode = row["theme_mode"] if row["theme_mode"] in ("light", "dark") else "dark"
        
        # Obtener tasks_view_mode con manejo seguro para bases de datos antiguas
        try:
            tasks_view_mode_raw = row["tasks_view_mode"]
        except (KeyError, IndexError):
            tasks_view_mode_raw = "lista_normal"
        
        tasks_view_mode = tasks_view_mode_raw if tasks_view_mode_raw in ("lista_normal", "lista_4do", "kanban") else "lista_normal"
        valid_accents = {
            # Azules
            "dodger_blue",
            "primary_blue",
            "bootstrap_blue",
            "deep_blue",
            "deepsky_blue",
            "steel_blue",
            "navy_dark",
            # Verdes
            "success_green",
            "emerald",
            "bright_green",
            "material_green",
            "turquoise",
            "green_sea",
            "dark_teal",
            # Rojos
            "danger_red",
            "alizarin",
            "dark_red",
            "soft_red",
            "deep_red",
            "vivid_red",
            # Amarillos / Naranjas
            "amber",
            "soft_yellow",
            "orange",
            "deep_orange",
            "sun_orange",
            "golden",
            # Morados / Rosas
            "ui_purple",
            "amethyst",
            "dark_purple",
            "vibrant_purple",
            "ui_pink",
            "hot_pink",
            # Grises / Neutros
            "dark_gray",
            "charcoal",
            "medium_gray",
            "secondary_gray",
            "light_gray",
            "soft_gray",
            "almost_white",
            # Blancos / Negros útiles
            "black",
            "white",
            "soft_white",
            "true_dark",
            # Modernos / gamer / UI
            "neon_cyan",
            "neon_green",
            "neon_pink",
            "electric_purple",
            "tech_blue",
            "mint_neon",
            "orange_neon",
        }
        accent = row["accent_color"] if row["accent_color"] in valid_accents else "dodger_blue"
        return AppSettings(theme_mode=theme_mode, accent_color=accent, tasks_view_mode=tasks_view_mode)

    def update_settings(
        self,
        theme_mode: Optional[ThemeModeLiteral] = None,
        accent_color: Optional[AccentColorLiteral] = None,
        tasks_view_mode: Optional[TasksViewModeLiteral] = None,
    ) -> AppSettings:
        """
        Actualiza los parámetros proporcionados y devuelve los ajustes resultantes.
        """
        current = self.get_settings()
        new_theme = theme_mode if theme_mode is not None else current.theme_mode
        new_accent = accent_color if accent_color is not None else current.accent_color
        new_tasks_view_mode = tasks_view_mode if tasks_view_mode is not None else current.tasks_view_mode

        conn = self.db.get_connection()
        cur = conn.cursor()
        cur.execute(
            """
            UPDATE app_settings
            SET theme_mode = ?, accent_color = ?, tasks_view_mode = ?
            WHERE key = 'global'
            """,
            (new_theme, new_accent, new_tasks_view_mode),
        )
        conn.commit()
        conn.close()

        return AppSettings(theme_mode=new_theme, accent_color=new_accent, tasks_view_mode=new_tasks_view_mode)


def _accent_palette(accent: AccentColorLiteral) -> dict[str, str]:
    """Devuelve un conjunto de colores base según el acento elegido."""
    # AZULES
    if accent == "dodger_blue":       # #1E90FF
        base = "#1E90FF"
    elif accent == "primary_blue":    # #007BFF
        base = "#007BFF"
    elif accent == "bootstrap_blue":  # #0D6EFD
        base = "#0D6EFD"
    elif accent == "deep_blue":       # #0056B3
        base = "#0056B3"
    elif accent == "deepsky_blue":    # #00BFFF
        base = "#00BFFF"
    elif accent == "steel_blue":      # #4682B4
        base = "#4682B4"
    elif accent == "navy_dark":       # #003366
        base = "#003366"

    # VERDES
    elif accent == "success_green":   # #28A745
        base = "#28A745"
    elif accent == "emerald":         # #2ECC71
        base = "#2ECC71"
    elif accent == "bright_green":    # #00C853
        base = "#00C853"
    elif accent == "material_green":  # #4CAF50
        base = "#4CAF50"
    elif accent == "turquoise":       # #1ABC9C
        base = "#1ABC9C"
    elif accent == "green_sea":       # #16A085
        base = "#16A085"
    elif accent == "dark_teal":       # #00695C
        base = "#00695C"

    # ROJOS
    elif accent == "danger_red":      # #DC3545
        base = "#DC3545"
    elif accent == "alizarin":        # #E74C3C
        base = "#E74C3C"
    elif accent == "dark_red":        # #C0392B
        base = "#C0392B"
    elif accent == "soft_red":        # #FF5252
        base = "#FF5252"
    elif accent == "deep_red":        # #B71C1C
        base = "#B71C1C"
    elif accent == "vivid_red":       # #FF1744
        base = "#FF1744"

    # AMARILLOS / NARANJAS
    elif accent == "amber":           # #FFC107
        base = "#FFC107"
    elif accent == "soft_yellow":     # #FFD54F
        base = "#FFD54F"
    elif accent == "orange":          # #FF9800
        base = "#FF9800"
    elif accent == "deep_orange":     # #FF5722
        base = "#FF5722"
    elif accent == "sun_orange":      # #F39C12
        base = "#F39C12"
    elif accent == "golden":          # #FFB300
        base = "#FFB300"

    # MORADOS / ROSAS
    elif accent == "ui_purple":       # #6F42C1
        base = "#6F42C1"
    elif accent == "amethyst":        # #9B59B6
        base = "#9B59B6"
    elif accent == "dark_purple":     # #8E44AD
        base = "#8E44AD"
    elif accent == "vibrant_purple":  # #E056FD
        base = "#E056FD"
    elif accent == "ui_pink":         # #D63384
        base = "#D63384"
    elif accent == "hot_pink":        # #FF69B4
        base = "#FF69B4"

    # GRISES / NEUTROS
    elif accent == "dark_gray":       # #212529
        base = "#212529"
    elif accent == "charcoal":        # #343A40
        base = "#343A40"
    elif accent == "medium_gray":     # #495057
        base = "#495057"
    elif accent == "secondary_gray":  # #6C757D
        base = "#6C757D"
    elif accent == "light_gray":      # #ADB5BD
        base = "#ADB5BD"
    elif accent == "soft_gray":       # #DEE2E6
        base = "#DEE2E6"
    elif accent == "almost_white":    # #F8F9FA
        base = "#F8F9FA"

    # BLANCOS / NEGROS ÚTILES
    elif accent == "black":           # #000000
        base = "#000000"
    elif accent == "white":           # #FFFFFF
        base = "#FFFFFF"
    elif accent == "soft_white":      # #FAFAFA
        base = "#FAFAFA"
    elif accent == "true_dark":       # #121212
        base = "#121212"

    # MODERNOS / GAMER / UI
    elif accent == "neon_cyan":       # #00E5FF
        base = "#00E5FF"
    elif accent == "neon_green":      # #76FF03
        base = "#76FF03"
    elif accent == "neon_pink":       # #FF4081
        base = "#FF4081"
    elif accent == "electric_purple": # #651FFF
        base = "#651FFF"
    elif accent == "tech_blue":       # #00B0FF
        base = "#00B0FF"
    elif accent == "mint_neon":       # #1DE9B6
        base = "#1DE9B6"
    elif accent == "orange_neon":     # #FF9100
        base = "#FF9100"

    else:
        # Fallback razonable: DodgerBlue
        base = "#1E90FF"

    # Usamos el mismo color para primary/secondary, y una variante
    # ligeramente más oscura para dark_theme usando la misma base.
    return {
        "primary": base,
        "primary_dark": base,
        "secondary": base,
        "secondary_dark": base,
        "error": "#DC3545",  # Danger red común
    }


def apply_theme_to_page(page: ft.Page, settings: AppSettings) -> None:
    """
    Aplica los ajustes de tema y color al objeto Page.

    - Configura `page.theme` (claro) y `page.dark_theme` (oscuro).
    - Establece `page.theme_mode` acorde a los ajustes.
    - Ajusta `page.bgcolor` para consistencia.
    """
    palette = _accent_palette(settings.accent_color)

    page.theme = ft.Theme(
        color_scheme_seed=palette["primary"],
        use_material3=True,
        color_scheme=ft.ColorScheme(
            primary=palette["primary"],
            on_primary=ft.Colors.WHITE,
            secondary=palette["secondary"],
            on_secondary=ft.Colors.WHITE,
            surface=ft.Colors.WHITE,
            on_surface=ft.Colors.BLACK87,
            background=ft.Colors.GREY_50,
            on_background=ft.Colors.BLACK87,
            error=palette["error"],
            on_error=ft.Colors.WHITE,
        ),
    )

    page.dark_theme = ft.Theme(
        color_scheme_seed=palette["primary_dark"],
        use_material3=True,
        color_scheme=ft.ColorScheme(
            primary=palette["primary"],
            on_primary=ft.Colors.WHITE,
            secondary=palette["secondary_dark"],
            on_secondary=ft.Colors.WHITE,
            surface=ft.Colors.BLACK87,
            on_surface=ft.Colors.WHITE,
            background=ft.Colors.BLACK,
            on_background=ft.Colors.WHITE,
            error=palette["error"],
            on_error=ft.Colors.WHITE,
        ),
    )

    page.theme_mode = (
        ft.ThemeMode.DARK if settings.theme_mode == "dark" else ft.ThemeMode.LIGHT
    )
    page.bgcolor = (
        ft.Colors.BLACK if page.theme_mode == ft.ThemeMode.DARK else ft.Colors.GREY_50
    )

