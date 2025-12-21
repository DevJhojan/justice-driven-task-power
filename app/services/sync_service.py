"""
Servicio de sincronización con Firebase.

Responsabilidades:
- Guardar y leer el estado de autenticación con Firebase
- Persistir el correo electrónico de la cuenta autenticada
- Proporcionar una API sencilla para verificar si hay sincronización activa

Decisiones técnicas:
- Usa la misma base de datos SQLite (tasks.db) para persistencia
- Tabla `sync_settings` con una sola fila (key='firebase') para configuración de sincronización
- Almacena el estado de autenticación y email de forma segura
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from app.data.database import Database


@dataclass
class SyncSettings:
    """Modelo de configuración de sincronización con Firebase."""

    is_authenticated: bool = False
    email: Optional[str] = None
    user_id: Optional[str] = None


class SyncService:
    """
    Servicio para persistir y recuperar configuración de sincronización con Firebase.

    Decisiones técnicas:
    - Se usa la misma base de datos SQLite (`tasks.db`) para no depender
      de almacenamiento adicional.
    - Tabla `sync_settings` con una sola fila (key='firebase') para ajustes
      de sincronización.
    - Los valores se almacenan como texto y se convierten a tipos apropiados.
    """

    def __init__(self, database: Optional[Database] = None) -> None:
        self.db = database or Database()
        self._ensure_table()

    def _ensure_table(self) -> None:
        """Crea la tabla de sincronización si no existe y garantiza la fila de configuración."""
        conn = self.db.get_connection()
        cur = conn.cursor()

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS sync_settings (
                key TEXT PRIMARY KEY,
                is_authenticated INTEGER NOT NULL DEFAULT 0,
                email TEXT,
                user_id TEXT
            )
            """
        )

        cur.execute("SELECT key FROM sync_settings WHERE key = 'firebase'")
        if not cur.fetchone():
            cur.execute(
                """
                INSERT INTO sync_settings (key, is_authenticated, email, user_id)
                VALUES ('firebase', 0, NULL, NULL)
                """
            )

        conn.commit()
        conn.close()

    def get_sync_settings(self) -> SyncSettings:
        """Obtiene la configuración de sincronización actual desde la base de datos."""
        conn = self.db.get_connection()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT is_authenticated, email, user_id 
            FROM sync_settings 
            WHERE key = 'firebase'
            """
        )
        row = cur.fetchone()
        conn.close()

        if not row:
            return SyncSettings()  # valores por defecto

        return SyncSettings(
            is_authenticated=bool(row["is_authenticated"]),
            email=row["email"] if row["email"] else None,
            user_id=row["user_id"] if row["user_id"] else None,
        )

    def update_sync_settings(
        self,
        is_authenticated: Optional[bool] = None,
        email: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> SyncSettings:
        """
        Actualiza la configuración de sincronización.

        Args:
            is_authenticated: Estado de autenticación Firebase
            email: Correo electrónico de la cuenta autenticada
            user_id: ID del usuario en Firebase

        Returns:
            Configuración de sincronización actualizada
        """
        current = self.get_sync_settings()
        new_authenticated = (
            is_authenticated if is_authenticated is not None else current.is_authenticated
        )
        new_email = email if email is not None else current.email
        new_user_id = (
            user_id if user_id is not None else current.user_id
        )

        conn = self.db.get_connection()
        cur = conn.cursor()
        cur.execute(
            """
            UPDATE sync_settings
            SET is_authenticated = ?, email = ?, user_id = ?
            WHERE key = 'firebase'
            """,
            (
                1 if new_authenticated else 0,
                new_email,
                new_user_id,
            ),
        )
        conn.commit()
        conn.close()

        return SyncSettings(
            is_authenticated=new_authenticated,
            email=new_email,
            user_id=new_user_id,
        )

    def clear_sync_settings(self) -> None:
        """Limpia la configuración de sincronización (desautentica)."""
        conn = self.db.get_connection()
        cur = conn.cursor()
        cur.execute(
            """
            UPDATE sync_settings
            SET is_authenticated = 0, email = NULL, user_id = NULL
            WHERE key = 'firebase'
            """
        )
        conn.commit()
        conn.close()

    def is_synced(self) -> bool:
        """Verifica si hay una sincronización activa con Firebase."""
        settings = self.get_sync_settings()
        return settings.is_authenticated and settings.email is not None

