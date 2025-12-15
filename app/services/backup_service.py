"""Servicio para importaciรณn y exportaciรณn segura de la base de datos.

Este mรณdulo se encarga de:
- Importar datos desde otro archivo .db de la misma app sin sobrescribir tasks.db.
- Evitar duplicados y conflictos de claves.
- Mantener la integridad relacional entre tareas/subtareas y hรกbitos/cumplimientos.
- Exportar la base de datos completa para copias de seguridad o migraciรณn.
"""

from __future__ import annotations

import os
import shutil
import sqlite3
from dataclasses import dataclass
from typing import Dict, Any

from app.data.database import Database


@dataclass
class ImportResult:
    tasks_imported: int = 0
    subtasks_imported: int = 0
    habits_imported: int = 0
    habit_completions_imported: int = 0


class BackupService:
    """Servicio de importaciรณn/exportaciรณn basado en SQLite.

    Decisiones tรฉcnicas clave:
    - Se trabaja siempre sobre la base de datos actual (Database.db_path).
    - La importaciรณn usa dos conexiones (origen y destino) y una transacciรณn en destino.
    - Se usan "huellas" (fingerprints) lรณgicas para detectar duplicados y remapear claves.
    - No se importa estructura, solo datos conocidos (tasks, subtasks, habits, habit_completions).
    """

    def __init__(self, database: Database | None = None) -> None:
        self.db = database or Database()

    # ------------------------------------------------------------------
    # Exportaciรณn
    # ------------------------------------------------------------------
    def export_database(self, target_path: str) -> None:
        """Exporta el archivo tasks.db completo a target_path.

        Args:
            target_path: Ruta de destino (debe terminar en .db idealmente).

        Raises:
            ValueError: Si la extensiรณn no es .db.
            OSError: Errores de copia en el sistema de archivos.
        """
        if not target_path.lower().endswith(".db"):
            raise ValueError("El archivo de destino debe tener extensiรณn .db")

        source_path = self.db.db_path
        if not os.path.exists(source_path):
            raise FileNotFoundError(f"Base de datos origen no encontrada: {source_path}")

        # Obtener tamaño del archivo origen para verificación
        source_size = os.path.getsize(source_path)
        if source_size == 0:
            raise ValueError("El archivo de base de datos origen está vacío")

        # Asegurar directorio de destino
        target_dir = os.path.dirname(target_path)
        if target_dir and not os.path.exists(target_dir):
            try:
                os.makedirs(target_dir, exist_ok=True)
            except (OSError, PermissionError) as e:
                raise OSError(f"No se pudo crear el directorio de destino: {e}")

        # Copia a nivel de archivo (incluye toda la estructura y datos)
        try:
            shutil.copy2(source_path, target_path)
        except (OSError, PermissionError, IOError) as e:
            raise OSError(f"Error al copiar el archivo: {e}. Verifica los permisos de almacenamiento.")

        # Verificar que el archivo se copió correctamente
        if not os.path.exists(target_path):
            raise OSError("El archivo de destino no se creó correctamente")

        target_size = os.path.getsize(target_path)
        if target_size == 0:
            raise OSError(
                "El archivo exportado tiene 0 bytes. "
                "Esto generalmente indica un problema de permisos de almacenamiento en Android. "
                "Intenta guardar en una ubicación diferente (por ejemplo, Descargas)."
            )

        if target_size != source_size:
            raise OSError(
                f"El archivo exportado tiene un tamaño incorrecto "
                f"({target_size} bytes vs {source_size} bytes esperados). "
                "La exportación puede estar incompleta."
            )

    # ------------------------------------------------------------------
    # Importaciรณn
    # ------------------------------------------------------------------
    def import_from_database(self, external_db_path: str) -> ImportResult:
        """Importa datos desde otro archivo .db a la base actual.

        Estrategia:
        - Solo acepta archivos .db.
        - No sobrescribe la base actual; solo inserta nuevos registros.
        - Usa huellas para evitar duplicados y resolver mapping de IDs.
        - Respeta las relaciones:
          - tasks -> subtasks
          - habits -> habit_completions

        Args:
            external_db_path: Ruta al archivo .db externo.

        Returns:
            ImportResult con contadores de registros realmente insertados.
        """
        if not external_db_path.lower().endswith(".db"):
            raise ValueError("Solo se permiten archivos con extensiรณn .db")

        if not os.path.exists(external_db_path):
            raise FileNotFoundError("El archivo .db externo no existe")

        result = ImportResult()

        # Conexiรณn origen
        src_conn = sqlite3.connect(external_db_path)
        src_conn.row_factory = sqlite3.Row
        src_cur = src_conn.cursor()

        # Conexiรณn destino
        dst_conn = self.db.get_connection()
        dst_cur = dst_conn.cursor()

        try:
            # Iniciar transacciรณn explรญcita en destino
            dst_conn.execute("BEGIN")

            # Tablas conocidas y con relaciones
            tables_with_data = self._detect_tables_with_data(src_cur)

            # Mapas de IDs para mantener relaciones
            task_id_map: Dict[int, int] = {}
            habit_id_map: Dict[int, int] = {}

            # ------------------------------------------------------
            # Importar tareas
            # ------------------------------------------------------
            if "tasks" in tables_with_data:
                src_cur.execute("SELECT * FROM tasks")
                for row in src_cur.fetchall():
                    old_id = row["id"]
                    # Huella lรณgica para tarea
                    title = row["title"]
                    description = row["description"] or ""
                    created_at = row["created_at"]

                    dst_cur.execute(
                        """
                        SELECT id FROM tasks
                        WHERE title = ? AND IFNULL(description, '') = ? AND created_at = ?
                        LIMIT 1
                        """,
                        (title, description, created_at),
                    )
                    existing = dst_cur.fetchone()
                    if existing:
                        # Ya existe: remapear ID antiguo al existente
                        new_id = existing["id"]
                        task_id_map[old_id] = new_id
                        continue

                    dst_cur.execute(
                        """
                        INSERT INTO tasks (title, description, completed, priority, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        (
                            title,
                            description,
                            row["completed"],
                            row["priority"],
                            row["created_at"],
                            row["updated_at"],
                        ),
                    )
                    new_id = dst_cur.lastrowid
                    task_id_map[old_id] = new_id
                    result.tasks_imported += 1

            # ------------------------------------------------------
            # Importar subtareas (requiere mapping de tasks)
            # ------------------------------------------------------
            if "subtasks" in tables_with_data and task_id_map:
                src_cur.execute("SELECT * FROM subtasks")
                for row in src_cur.fetchall():
                    old_task_id = row["task_id"]
                    new_task_id = task_id_map.get(old_task_id)
                    if not new_task_id:
                        # Tarea padre no fue importada ni encontrada
                        continue

                    title = row["title"]
                    description = row["description"] or ""
                    deadline = row["deadline"] or ""
                    created_at = row["created_at"]

                    # Evitar duplicados por huella lรณgica
                    dst_cur.execute(
                        """
                        SELECT id FROM subtasks
                        WHERE task_id = ?
                          AND title = ?
                          AND IFNULL(description, '') = ?
                          AND IFNULL(deadline, '') = ?
                          AND created_at = ?
                        LIMIT 1
                        """,
                        (new_task_id, title, description, deadline, created_at),
                    )
                    if dst_cur.fetchone():
                        continue

                    dst_cur.execute(
                        """
                        INSERT INTO subtasks (task_id, title, description, deadline, completed, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            new_task_id,
                            title,
                            description,
                            row["deadline"],
                            row["completed"],
                            row["created_at"],
                            row["updated_at"],
                        ),
                    )
                    result.subtasks_imported += 1

            # ------------------------------------------------------
            # Importar hรกbitos
            # ------------------------------------------------------
            if "habits" in tables_with_data:
                src_cur.execute("SELECT * FROM habits")
                for row in src_cur.fetchall():
                    old_id = row["id"]
                    title = row["title"]
                    description = row["description"] or ""
                    frequency = row["frequency"]
                    created_at = row["created_at"]

                    # Huella lรณgica para hรกbito
                    dst_cur.execute(
                        """
                        SELECT id FROM habits
                        WHERE title = ?
                          AND IFNULL(description, '') = ?
                          AND frequency = ?
                          AND created_at = ?
                        LIMIT 1
                        """,
                        (title, description, frequency, created_at),
                    )
                    existing = dst_cur.fetchone()
                    if existing:
                        new_id = existing["id"]
                        habit_id_map[old_id] = new_id
                        continue

                    dst_cur.execute(
                        """
                        INSERT INTO habits (title, description, frequency, target_days, active, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            title,
                            description,
                            frequency,
                            row["target_days"],
                            row["active"],
                            row["created_at"],
                            row["updated_at"],
                        ),
                    )
                    new_id = dst_cur.lastrowid
                    habit_id_map[old_id] = new_id
                    result.habits_imported += 1

            # ------------------------------------------------------
            # Importar cumplimientos de hรกbitos
            # ------------------------------------------------------
            if "habit_completions" in tables_with_data and habit_id_map:
                src_cur.execute("SELECT * FROM habit_completions")
                for row in src_cur.fetchall():
                    old_habit_id = row["habit_id"]
                    new_habit_id = habit_id_map.get(old_habit_id)
                    if not new_habit_id:
                        continue

                    completion_date = row["completion_date"]
                    created_at = row["created_at"]

                    # Usar UNIQUE(habit_id, completion_date) para evitar duplicados
                    dst_cur.execute(
                        """
                        INSERT OR IGNORE INTO habit_completions (habit_id, completion_date, created_at)
                        VALUES (?, ?, ?)
                        """,
                        (new_habit_id, completion_date, created_at),
                    )
                    if dst_cur.rowcount > 0:
                        result.habit_completions_imported += 1

            dst_conn.commit()
            return result
        except Exception:
            dst_conn.rollback()
            raise
        finally:
            src_conn.close()
            dst_conn.close()

    # ------------------------------------------------------------------
    # Utilidades internas
    # ------------------------------------------------------------------
    def _detect_tables_with_data(self, cursor: sqlite3.Cursor) -> Dict[str, int]:
        """Devuelve un dict {tabla: num_registros} solo para tablas con datos.

        Solo se consideran las tablas conocidas por la app para evitar sorpresas
        con estructuras externas.
        """
        tables = ["tasks", "subtasks", "habits", "habit_completions"]
        result: Dict[str, int] = {}
        for table in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) AS c FROM {table}")
                row = cursor.fetchone()
                if row and row["c"] > 0:
                    result[table] = row["c"]
            except sqlite3.OperationalError:
                # La tabla no existe en la base externa, ignorar
                continue
        return result
