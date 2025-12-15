"""Servicio para importación y exportación segura mediante archivos CSV.

Este módulo se encarga de:
- Exportar datos de todas las tablas a archivos CSV estructurados.
- Importar datos desde archivos CSV de forma no destructiva.
- Evitar duplicados mediante validaciones y huellas lógicas.
- Mantener la integridad relacional entre tareas/subtareas y hábitos/cumplimientos.
- Usar transacciones SQLite para garantizar consistencia.
"""

from __future__ import annotations

import csv
import os
import sqlite3
import zipfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

from app.data.database import Database


@dataclass
class CSVImportResult:
    """Resultado de una importación desde CSV."""
    tasks_imported: int = 0
    subtasks_imported: int = 0
    habits_imported: int = 0
    habit_completions_imported: int = 0
    errors: List[str] = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []


class CSVBackupService:
    """Servicio de importación/exportación basado en CSV.

    Decisiones técnicas:
    - Exporta cada tabla a su propio CSV dentro de un archivo ZIP para portabilidad.
    - El ZIP contiene: tasks.csv, subtasks.csv, habits.csv, habit_completions.csv.
    - La importación lee el ZIP, extrae los CSV y los importa de forma no destructiva.
    - Usa transacciones SQLite para garantizar atomicidad.
    - Detecta duplicados mediante huellas lógicas (no solo IDs).
    """

    def __init__(self, database: Database | None = None) -> None:
        self.db = database or Database()

    # ------------------------------------------------------------------
    # Exportación CSV
    # ------------------------------------------------------------------

    def export_to_csv(self, target_path: str) -> None:
        """Exporta todas las tablas a un archivo ZIP conteniendo CSVs.

        Estructura del ZIP:
        - tasks.csv
        - subtasks.csv
        - habits.csv
        - habit_completions.csv

        Args:
            target_path: Ruta del archivo ZIP de destino (debe terminar en .zip).

        Raises:
            ValueError: Si la extensión no es .zip.
            OSError: Errores de escritura en el sistema de archivos.
        """
        if not target_path.lower().endswith(".zip"):
            raise ValueError("El archivo de destino debe tener extensión .zip")

        # Crear directorio temporal para los CSV
        temp_dir = Path(target_path).parent / f"_temp_csv_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        temp_dir.mkdir(exist_ok=True)

        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()

            # Exportar cada tabla a su CSV
            self._export_table_to_csv(cursor, "tasks", temp_dir / "tasks.csv")
            self._export_table_to_csv(cursor, "subtasks", temp_dir / "subtasks.csv")
            self._export_table_to_csv(cursor, "habits", temp_dir / "habits.csv")
            self._export_table_to_csv(cursor, "habit_completions", temp_dir / "habit_completions.csv")

            conn.close()

            # Crear el archivo ZIP con todos los CSV
            with zipfile.ZipFile(target_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for csv_file in temp_dir.glob("*.csv"):
                    zipf.write(csv_file, csv_file.name)

        finally:
            # Limpiar directorio temporal
            import shutil
            if temp_dir.exists():
                shutil.rmtree(temp_dir)

    def _export_table_to_csv(self, cursor: sqlite3.Cursor, table_name: str, csv_path: Path) -> None:
        """Exporta una tabla SQLite a un archivo CSV.

        Args:
            cursor: Cursor de la base de datos.
            table_name: Nombre de la tabla a exportar.
            csv_path: Ruta del archivo CSV de destino.
        """
        try:
            # Obtener todos los registros de la tabla
            cursor.execute(f"SELECT * FROM {table_name}")
            rows = cursor.fetchall()

            if not rows:
                # Crear CSV vacío con encabezados
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = [row[1] for row in cursor.fetchall()]
                with open(csv_path, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(columns)
                return

            # Obtener nombres de columnas
            column_names = [description[0] for description in cursor.description]

            # Escribir CSV
            with open(csv_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(column_names)  # Encabezados
                for row in rows:
                    # Convertir valores None a strings vacíos, fechas a ISO format
                    csv_row = []
                    for val in row:
                        if val is None:
                            csv_row.append("")
                        elif isinstance(val, datetime):
                            csv_row.append(val.isoformat())
                        else:
                            csv_row.append(str(val))
                    writer.writerow(csv_row)

        except sqlite3.OperationalError:
            # La tabla no existe, crear CSV vacío
            with open(csv_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([])

    # ------------------------------------------------------------------
    # Importación CSV
    # ------------------------------------------------------------------

    def import_from_csv(self, csv_zip_path: str) -> CSVImportResult:
        """Importa datos desde un archivo ZIP conteniendo CSVs.

        Args:
            csv_zip_path: Ruta al archivo ZIP con los CSV.

        Returns:
            CSVImportResult con contadores de registros importados y errores.

        Raises:
            ValueError: Si el archivo no es un ZIP válido o no contiene CSVs esperados.
            FileNotFoundError: Si el archivo no existe.
        """
        if not os.path.exists(csv_zip_path):
            raise FileNotFoundError(f"El archivo CSV no existe: {csv_zip_path}")

        if not csv_zip_path.lower().endswith(".zip"):
            raise ValueError("El archivo debe ser un ZIP conteniendo archivos CSV")

        result = CSVImportResult()

        # Directorio temporal para extraer CSVs
        temp_dir = Path(csv_zip_path).parent / f"_temp_csv_import_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        temp_dir.mkdir(exist_ok=True)

        try:
            # Extraer ZIP
            with zipfile.ZipFile(csv_zip_path, 'r') as zipf:
                zipf.extractall(temp_dir)

            # Conexión a la base de datos destino
            conn = self.db.get_connection()
            cursor = conn.cursor()
            # Configurar row_factory para acceso por nombre de columna
            conn.row_factory = sqlite3.Row

            try:
                # Iniciar transacción
                conn.execute("BEGIN")

                # Crear mapas de IDs antiguos -> nuevos para mapeo de relaciones
                task_id_map: Dict[int, int] = {}  # old_id -> new_id
                habit_id_map: Dict[int, int] = {}  # old_id -> new_id

                # Importar cada tabla en orden (respetando relaciones)
                if (temp_dir / "tasks.csv").exists():
                    result.tasks_imported, task_id_map = self._import_tasks_with_mapping(
                        cursor, temp_dir / "tasks.csv", result.errors
                    )

                if (temp_dir / "habits.csv").exists():
                    result.habits_imported, habit_id_map = self._import_habits_with_mapping(
                        cursor, temp_dir / "habits.csv", result.errors
                    )

                # Subtareas y cumplimientos dependen de tasks/habits, usando los mapas de IDs
                if (temp_dir / "subtasks.csv").exists():
                    result.subtasks_imported = self._import_subtasks_from_csv(
                        cursor, temp_dir / "subtasks.csv", task_id_map, result.errors
                    )

                if (temp_dir / "habit_completions.csv").exists():
                    result.habit_completions_imported = self._import_habit_completions_from_csv(
                        cursor, temp_dir / "habit_completions.csv", habit_id_map, result.errors
                    )

                # Commit si todo fue bien
                conn.commit()

            except Exception as e:
                conn.rollback()
                result.errors.append(f"Error durante la importación: {str(e)}")
                raise

            finally:
                conn.close()

        finally:
            # Limpiar directorio temporal
            import shutil
            if temp_dir.exists():
                shutil.rmtree(temp_dir)

        return result

    def _import_habit_completions_from_csv(
        self, cursor: sqlite3.Cursor, csv_path: Path, habit_id_map: Dict[int, int], errors: List[str]
    ) -> int:
        """Importa cumplimientos de hábitos desde CSV, mapeando habit_id usando el mapa proporcionado."""
        imported_count = 0

        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                if not reader.fieldnames:
                    return 0

                for row in reader:
                    try:
                        old_habit_id_str = row.get('habit_id', '').strip()
                        completion_date = row.get('completion_date', '').strip()
                        created_at = row.get('created_at', '').strip()

                        if not old_habit_id_str or not completion_date:
                            continue

                        try:
                            old_habit_id = int(old_habit_id_str)
                        except ValueError:
                            errors.append(f"Cumplimiento ignorado: habit_id inválido")
                            continue

                        # Mapear habit_id antiguo -> nuevo
                        new_habit_id = habit_id_map.get(old_habit_id)
                        if not new_habit_id:
                            errors.append(
                                f"Cumplimiento ignorado: hábito (ID {old_habit_id}) no encontrado en la importación"
                            )
                            continue

                        # Usar INSERT OR IGNORE para evitar duplicados (UNIQUE constraint)
                        cursor.execute(
                            """
                            INSERT OR IGNORE INTO habit_completions (habit_id, completion_date, created_at)
                            VALUES (?, ?, ?)
                            """,
                            (new_habit_id, completion_date, created_at or completion_date),
                        )
                        if cursor.rowcount > 0:
                            imported_count += 1

                    except Exception as e:
                        errors.append(f"Error importando cumplimiento: {str(e)}")
                        continue

        except Exception as e:
            errors.append(f"Error leyendo habit_completions.csv: {str(e)}")

        return imported_count
