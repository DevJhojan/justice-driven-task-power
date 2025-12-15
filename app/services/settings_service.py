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
# Paletas disponibles: fácil de extender añadiendo nuevos valores aquí
AccentColorLiteral = Literal[
    "red",
    "pink",
    "purple",
    "deep_purple",
    "indigo",
    "blue",
    "cyan",
    "teal",
    "green",
    "lime",
    "orange",
    "amber",
]


@dataclass
class AppSettings:
    """Modelo de ajustes de apariencia."""

    theme_mode: ThemeModeLiteral = "dark"
    accent_color: AccentColorLiteral = "red"


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
                accent_color TEXT NOT NULL
            )
            """
        )

        cur.execute("SELECT key FROM app_settings WHERE key = 'global'")
        if not cur.fetchone():
            cur.execute(
                """
                INSERT INTO app_settings (key, theme_mode, accent_color)
                VALUES ('global', 'dark', 'red')
                """
            )

        conn.commit()
        conn.close()

    def get_settings(self) -> AppSettings:
        """Obtiene los ajustes actuales desde la base de datos."""
        conn = self.db.get_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT theme_mode, accent_color FROM app_settings WHERE key = 'global'"
        )
        row = cur.fetchone()
        conn.close()

        if not row:
            return AppSettings()  # valores por defecto

        theme_mode = row["theme_mode"] if row["theme_mode"] in ("light", "dark") else "dark"
        valid_accents = {
            "red",
            "pink",
            "purple",
            "deep_purple",
            "indigo",
            "blue",
            "cyan",
            "teal",
            "green",
            "lime",
            "orange",
            "amber",
        }
        accent = row["accent_color"] if row["accent_color"] in valid_accents else "red"
        return AppSettings(theme_mode=theme_mode, accent_color=accent)

    def update_settings(
        self,
        theme_mode: Optional[ThemeModeLiteral] = None,
        accent_color: Optional[AccentColorLiteral] = None,
    ) -> AppSettings:
        """
        Actualiza uno o ambos parámetros y devuelve los ajustes resultantes.
        """
        current = self.get_settings()
        new_theme = theme_mode or current.theme_mode
        new_accent = accent_color or current.accent_color

        conn = self.db.get_connection()
        cur = conn.cursor()
        cur.execute(
            """
            UPDATE app_settings
            SET theme_mode = ?, accent_color = ?
            WHERE key = 'global'
            """,
            (new_theme, new_accent),
        )
        conn.commit()
        conn.close()

        return AppSettings(theme_mode=new_theme, accent_color=new_accent)


def _accent_palette(accent: AccentColorLiteral) -> dict[str, str]:
    """Devuelve un conjunto de colores base según el acento elegido."""
    if accent == "pink":
        return {
            "primary": ft.Colors.PINK_600,
            "primary_dark": ft.Colors.PINK_800,
            "secondary": ft.Colors.PINK_400,
            "secondary_dark": ft.Colors.PINK_500,
            "error": ft.Colors.RED_400,
        }
    if accent == "purple":
        return {
            "primary": ft.Colors.PURPLE_700,
            "primary_dark": ft.Colors.PURPLE_800,
            "secondary": ft.Colors.PURPLE_400,
            "secondary_dark": ft.Colors.PURPLE_500,
            "error": ft.Colors.RED_400,
        }
    if accent == "deep_purple":
        return {
            "primary": ft.Colors.DEEP_PURPLE_700,
            "primary_dark": ft.Colors.DEEP_PURPLE_800,
            "secondary": ft.Colors.DEEP_PURPLE_400,
            "secondary_dark": ft.Colors.DEEP_PURPLE_500,
            "error": ft.Colors.RED_400,
        }
    if accent == "indigo":
        return {
            "primary": ft.Colors.INDIGO_700,
            "primary_dark": ft.Colors.INDIGO_800,
            "secondary": ft.Colors.INDIGO_400,
            "secondary_dark": ft.Colors.INDIGO_500,
            "error": ft.Colors.RED_400,
        }
    if accent == "blue":
        return {
            "primary": ft.Colors.BLUE_700,
            "primary_dark": ft.Colors.BLUE_800,
            "secondary": ft.Colors.BLUE_500,
            "secondary_dark": ft.Colors.BLUE_600,
            "error": ft.Colors.RED_400,
        }
    if accent == "cyan":
        return {
            "primary": ft.Colors.CYAN_700,
            "primary_dark": ft.Colors.CYAN_800,
            "secondary": ft.Colors.CYAN_400,
            "secondary_dark": ft.Colors.CYAN_500,
            "error": ft.Colors.RED_400,
        }
    if accent == "teal":
        return {
            "primary": ft.Colors.TEAL_700,
            "primary_dark": ft.Colors.TEAL_800,
            "secondary": ft.Colors.TEAL_400,
            "secondary_dark": ft.Colors.TEAL_500,
            "error": ft.Colors.RED_400,
        }
    if accent == "green":
        return {
            "primary": ft.Colors.GREEN_700,
            "primary_dark": ft.Colors.GREEN_800,
            "secondary": ft.Colors.GREEN_500,
            "secondary_dark": ft.Colors.GREEN_600,
            "error": ft.Colors.RED_400,
        }
    if accent == "lime":
        return {
            "primary": ft.Colors.LIME_700,
            "primary_dark": ft.Colors.LIME_800,
            "secondary": ft.Colors.LIME_500,
            "secondary_dark": ft.Colors.LIME_600,
            "error": ft.Colors.RED_400,
        }
    if accent == "orange":
        return {
            "primary": ft.Colors.ORANGE_700,
            "primary_dark": ft.Colors.ORANGE_800,
            "secondary": ft.Colors.ORANGE_500,
            "secondary_dark": ft.Colors.ORANGE_600,
            "error": ft.Colors.RED_400,
        }
    if accent == "amber":
        return {
            "primary": ft.Colors.AMBER_700,
            "primary_dark": ft.Colors.AMBER_800,
            "secondary": ft.Colors.AMBER_500,
            "secondary_dark": ft.Colors.AMBER_600,
            "error": ft.Colors.RED_400,
        }
    # Por defecto rojo (como diseño original)
    return {
        "primary": ft.Colors.RED_700,
        "primary_dark": ft.Colors.RED_900,
        "secondary": ft.Colors.RED_600,
        "secondary_dark": ft.Colors.RED_800,
        "error": ft.Colors.RED_400,
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

