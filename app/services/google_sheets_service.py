"""
Servicio para importación y exportación de datos usando Google Sheets.

Este módulo se encarga de:
- Exportar datos de todas las tablas a Google Sheets.
- Importar datos desde Google Sheets de forma no destructiva.
- Manejar autenticación OAuth2 con Google.
- Sincronizar datos entre la base de datos local y Google Sheets.
"""

from __future__ import annotations

import os
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.auth.transport.requests import Request
import pickle

from app.data.database import Database


# Scopes necesarios para Google Sheets API
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

# ID de la API (para referencia)
API_KEY = "AIzaSyDoI3Q72rpy57OCFcMi2HDUMxIWPXI0afY"


@dataclass
class SheetsImportResult:
    """Resultado de una importación desde Google Sheets."""
    tasks_imported: int = 0
    subtasks_imported: int = 0
    habits_imported: int = 0
    habit_completions_imported: int = 0
    errors: List[str] = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []


class GoogleSheetsService:
    """Servicio de importación/exportación basado en Google Sheets.
    
    Decisiones técnicas:
    - Usa OAuth2 para autenticación con Google.
    - Cada tabla se exporta a una hoja separada en el mismo spreadsheet.
    - La importación lee desde las hojas y los importa de forma no destructiva.
    - Usa transacciones SQLite para garantizar atomicidad.
    - Detecta duplicados mediante huellas lógicas.
    """
    
    def __init__(self, database: Database | None = None, page=None) -> None:
        self.db = database or Database()
        self.service = None
        self.credentials = None
        self.page = page  # Página de Flet para abrir URLs en Android
        
        # Rutas para credenciales y token
        self.root_dir = Path(__file__).parent.parent.parent
        self.credentials_path = self.root_dir / 'credenciales_android.json'
        self.token_path = self.root_dir / 'token.pickle'
        
    def _get_credentials(self) -> Credentials:
        """
        Obtiene credenciales válidas para Google Sheets API.
        Si no hay credenciales válidas, inicia el flujo OAuth2.
        
        Returns:
            Credenciales de Google OAuth2.
        """
        creds = None
        
        # Cargar token guardado si existe
        if self.token_path.exists():
            try:
                with open(self.token_path, 'rb') as token:
                    creds = pickle.load(token)
            except Exception:
                pass
        
        # Si no hay credenciales válidas, iniciar flujo OAuth2
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                # Refrescar credenciales expiradas
                try:
                    creds.refresh(Request())
                except Exception:
                    creds = None
            
            if not creds:
                # Iniciar flujo OAuth2
                if not self.credentials_path.exists():
                    raise FileNotFoundError(
                        f"Archivo de credenciales no encontrado: {self.credentials_path}\n"
                        "Por favor, asegúrate de que 'credenciales_android.json' esté en la raíz del proyecto."
                    )
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(self.credentials_path), SCOPES
                )
                
                # Para Android, necesitamos un enfoque diferente
                # run_local_server no funciona bien porque requiere localhost
                # Usaremos authorization_url y luego el usuario ingresará el código
                if self.page:
                    # Obtener URL de autorización
                    auth_url, _ = flow.authorization_url(prompt='consent')
                    
                    # Abrir navegador en Android usando Flet
                    try:
                        # launch_url abre el navegador externo en Android
                        self.page.launch_url(auth_url)
                    except Exception as launch_error:
                        # Si falla, intentar método alternativo
                        try:
                            import webbrowser
                            webbrowser.open(auth_url)
                        except Exception:
                            # Si todo falla, lanzar error con instrucciones
                            raise Exception(
                                f"No se pudo abrir el navegador. "
                                f"Por favor, abre manualmente esta URL:\n{auth_url}\n\n"
                                f"Error: {str(launch_error)}"
                            )
                    
                    # Después de abrir el navegador, usar run_console para obtener el código
                    # El usuario copiará el código de la URL de redirección
                    try:
                        # run_console pide al usuario que ingrese el código manualmente
                        creds = flow.run_console()
                    except AttributeError:
                        # Si run_console no existe, usar servidor local
                        # En Android esto puede no funcionar perfectamente
                        creds = flow.run_local_server(port=0, open_browser=False)
                else:
                    # Para escritorio, usar servidor local normal
                    creds = flow.run_local_server(port=0, open_browser=True)
            
            # Guardar credenciales para próximas veces
            try:
                with open(self.token_path, 'wb') as token:
                    pickle.dump(creds, token)
            except Exception:
                pass  # Si no se puede guardar, continuar de todas formas
        
        return creds
    
    def _get_service(self):
        """Obtiene el servicio de Google Sheets API."""
        if self.service is None:
            creds = self._get_credentials()
            # Construir servicio con credenciales OAuth2 y API key (opcional pero recomendado)
            self.service = build('sheets', 'v4', credentials=creds, developerKey=API_KEY)
        return self.service
    
    def authenticate(self) -> bool:
        """
        Autentica con Google Sheets API.
        
        Returns:
            True si la autenticación fue exitosa, False en caso contrario.
        """
        try:
            self._get_service()
            return True
        except Exception as e:
            return False
    
    def create_spreadsheet(self, title: str) -> str:
        """
        Crea un nuevo spreadsheet en Google Sheets.
        
        Args:
            title: Título del spreadsheet.
        
        Returns:
            ID del spreadsheet creado.
        
        Raises:
            HttpError: Si hay un error al crear el spreadsheet.
        """
        service = self._get_service()
        
        spreadsheet = {
            'properties': {
                'title': title
            },
            'sheets': [
                {'properties': {'title': 'tasks'}},
                {'properties': {'title': 'subtasks'}},
                {'properties': {'title': 'habits'}},
                {'properties': {'title': 'habit_completions'}}
            ]
        }
        
        spreadsheet = service.spreadsheets().create(body=spreadsheet).execute()
        return spreadsheet.get('spreadsheetId')
    
    def export_to_sheets(self, spreadsheet_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Exporta todas las tablas a Google Sheets.
        
        Args:
            spreadsheet_id: ID del spreadsheet existente. Si es None, crea uno nuevo.
        
        Returns:
            Diccionario con información del spreadsheet (id, url, etc.).
        
        Raises:
            HttpError: Si hay un error al exportar.
        """
        service = self._get_service()
        
        # Crear spreadsheet si no existe
        created_new = False
        if not spreadsheet_id:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            title = f"Tasks Backup {timestamp}"
            spreadsheet_id = self.create_spreadsheet(title)
            created_new = True
        
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            # Exportar cada tabla a su hoja
            self._export_table_to_sheet(service, spreadsheet_id, cursor, "tasks", "tasks")
            self._export_table_to_sheet(service, spreadsheet_id, cursor, "subtasks", "subtasks")
            self._export_table_to_sheet(service, spreadsheet_id, cursor, "habits", "habits")
            self._export_table_to_sheet(service, spreadsheet_id, cursor, "habit_completions", "habit_completions")
            
            # Obtener URL del spreadsheet
            spreadsheet_url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}"
            
            # Obtener título del spreadsheet
            spreadsheet_info = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
            spreadsheet_title = spreadsheet_info.get('properties', {}).get('title', 'Sin título')
            
            return {
                'spreadsheet_id': spreadsheet_id,
                'url': spreadsheet_url,
                'title': spreadsheet_title,
                'created_new': created_new
            }
        finally:
            conn.close()
    
    def _export_table_to_sheet(self, service, spreadsheet_id: str, cursor: sqlite3.Cursor, 
                                table_name: str, sheet_name: str) -> None:
        """
        Exporta una tabla SQLite a una hoja de Google Sheets.
        
        Args:
            service: Servicio de Google Sheets API.
            spreadsheet_id: ID del spreadsheet.
            cursor: Cursor de la base de datos.
            table_name: Nombre de la tabla en SQLite.
            sheet_name: Nombre de la hoja en Google Sheets.
        """
        # Obtener datos de la tabla
        cursor.execute(f"SELECT * FROM {table_name}")
        rows = cursor.fetchall()
        
        if not rows:
            # Si la tabla está vacía, crear hoja con solo encabezados
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = [row[1] for row in cursor.fetchall()]
            values = [columns]
        else:
            # Obtener nombres de columnas
            column_names = [description[0] for description in cursor.description]
            
            # Preparar valores (encabezados + datos)
            values = [column_names]
            for row in rows:
                # Convertir valores None a strings vacíos
                csv_row = []
                for val in row:
                    if val is None:
                        csv_row.append("")
                    elif isinstance(val, datetime):
                        csv_row.append(val.isoformat())
                    else:
                        csv_row.append(str(val))
                values.append(csv_row)
        
        # Escribir datos a la hoja
        range_name = f"{sheet_name}!A1"
        body = {'values': values}
        
        try:
            service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range=range_name,
                valueInputOption='RAW',
                body=body
            ).execute()
        except HttpError as error:
            # Si la hoja no existe, crearla primero
            if error.resp.status == 400:
                # Intentar crear la hoja
                try:
                    requests = [{
                        'addSheet': {
                            'properties': {
                                'title': sheet_name
                            }
                        }
                    }]
                    service.spreadsheets().batchUpdate(
                        spreadsheetId=spreadsheet_id,
                        body={'requests': requests}
                    ).execute()
                    
                    # Intentar escribir de nuevo
                    service.spreadsheets().values().update(
                        spreadsheetId=spreadsheet_id,
                        range=range_name,
                        valueInputOption='RAW',
                        body=body
                    ).execute()
                except Exception:
                    raise
    
    def import_from_sheets(self, spreadsheet_id: str) -> SheetsImportResult:
        """
        Importa datos desde un Google Sheets spreadsheet.
        
        Args:
            spreadsheet_id: ID del spreadsheet de Google Sheets.
        
        Returns:
            SheetsImportResult con contadores de registros importados y errores.
        
        Raises:
            HttpError: Si hay un error al importar.
        """
        service = self._get_service()
        result = SheetsImportResult()
        
        conn = self.db.get_connection()
        cursor = conn.cursor()
        conn.row_factory = sqlite3.Row
        
        try:
            # Iniciar transacción
            cursor.execute("BEGIN")
            
            # Crear mapas de IDs antiguos -> nuevos para mapeo de relaciones
            task_id_map: Dict[int, int] = {}
            habit_id_map: Dict[int, int] = {}
            
            # Importar cada hoja
            try:
                result.tasks_imported, task_id_map = self._import_sheet_to_table(
                    service, spreadsheet_id, cursor, "tasks", "tasks", result.errors
                )
            except Exception as e:
                result.errors.append(f"Error importando tasks: {str(e)}")
            
            try:
                result.habits_imported, habit_id_map = self._import_sheet_to_table(
                    service, spreadsheet_id, cursor, "habits", "habits", result.errors
                )
            except Exception as e:
                result.errors.append(f"Error importando habits: {str(e)}")
            
            try:
                result.subtasks_imported = self._import_subtasks_from_sheet(
                    service, spreadsheet_id, cursor, "subtasks", task_id_map, result.errors
                )
            except Exception as e:
                result.errors.append(f"Error importando subtasks: {str(e)}")
            
            try:
                result.habit_completions_imported = self._import_habit_completions_from_sheet(
                    service, spreadsheet_id, cursor, "habit_completions", habit_id_map, result.errors
                )
            except Exception as e:
                result.errors.append(f"Error importando habit_completions: {str(e)}")
            
            # Commit si todo fue bien
            conn.commit()
            
        except Exception as e:
            conn.rollback()
            result.errors.append(f"Error durante la importación: {str(e)}")
        finally:
            conn.close()
        
        return result
    
    def _import_sheet_to_table(self, service, spreadsheet_id: str, cursor: sqlite3.Cursor,
                               sheet_name: str, table_name: str, errors: List[str]) -> tuple[int, Dict[int, int]]:
        """
        Importa datos desde una hoja de Google Sheets a una tabla SQLite.
        
        Args:
            service: Servicio de Google Sheets API.
            spreadsheet_id: ID del spreadsheet.
            cursor: Cursor de la base de datos.
            sheet_name: Nombre de la hoja en Google Sheets.
            table_name: Nombre de la tabla en SQLite.
            errors: Lista para agregar errores.
        
        Returns:
            Tupla (número_importados, mapa_id_antiguo -> id_nuevo)
        """
        imported_count = 0
        id_map: Dict[int, int] = {}
        
        try:
            # Leer datos de la hoja
            result = service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id,
                range=sheet_name
            ).execute()
            
            values = result.get('values', [])
            
            if not values:
                return 0, {}
            
            # Primera fila son los encabezados
            headers = values[0]
            data_rows = values[1:]
            
            # Crear diccionario de índices de columnas
            col_indices = {col: i for i, col in enumerate(headers)}
            
            for row in data_rows:
                try:
                    # Extender fila si es necesario (llenar con vacíos)
                    while len(row) < len(headers):
                        row.append("")
                    
                    # Obtener valores según el tipo de tabla
                    if table_name == "tasks":
                        # Obtener old_id de forma segura
                        old_id = None
                        if 'id' in col_indices:
                            try:
                                id_val = row[col_indices['id']] if col_indices['id'] < len(row) else ""
                                if id_val:
                                    old_id = int(id_val)
                            except (ValueError, IndexError):
                                pass
                        
                        title = row[col_indices['title']] if 'title' in col_indices and col_indices['title'] < len(row) else ""
                        description = row[col_indices['description']] if 'description' in col_indices and col_indices['description'] < len(row) else ""
                        created_at = row[col_indices['created_at']] if 'created_at' in col_indices and col_indices['created_at'] < len(row) else ""
                        
                        if not title or not created_at:
                            continue
                        
                        # Verificar si ya existe
                        cursor.execute(
                            """
                            SELECT id FROM tasks
                            WHERE title = ? AND IFNULL(description, '') = ? AND created_at = ?
                            LIMIT 1
                            """,
                            (title, description, created_at),
                        )
                        existing = cursor.fetchone()
                        if existing:
                            if old_id is not None:
                                id_map[old_id] = existing['id']
                            continue
                        
                        # Obtener valores adicionales de forma segura
                        completed = 0
                        if 'completed' in col_indices and col_indices['completed'] < len(row):
                            try:
                                completed = int(row[col_indices['completed']])
                            except (ValueError, IndexError):
                                completed = 0
                        
                        priority = 'medium'
                        if 'priority' in col_indices and col_indices['priority'] < len(row):
                            priority = row[col_indices['priority']] or 'medium'
                        
                        updated_at = created_at
                        if 'updated_at' in col_indices and col_indices['updated_at'] < len(row):
                            updated_at = row[col_indices['updated_at']] or created_at
                        
                        # Insertar nueva tarea
                        cursor.execute(
                            """
                            INSERT INTO tasks (title, description, completed, priority, created_at, updated_at)
                            VALUES (?, ?, ?, ?, ?, ?)
                            """,
                            (title, description, completed, priority, created_at, updated_at),
                        )
                        new_id = cursor.lastrowid
                        imported_count += 1
                        
                        if old_id is not None:
                            id_map[old_id] = new_id
                    
                    elif table_name == "habits":
                        # Obtener old_id de forma segura
                        old_id = None
                        if 'id' in col_indices:
                            try:
                                id_val = row[col_indices['id']] if col_indices['id'] < len(row) else ""
                                if id_val:
                                    old_id = int(id_val)
                            except (ValueError, IndexError):
                                pass
                        
                        title = row[col_indices['title']] if 'title' in col_indices and col_indices['title'] < len(row) else ""
                        description = row[col_indices['description']] if 'description' in col_indices and col_indices['description'] < len(row) else ""
                        frequency = row[col_indices['frequency']] if 'frequency' in col_indices and col_indices['frequency'] < len(row) else "daily"
                        created_at = row[col_indices['created_at']] if 'created_at' in col_indices and col_indices['created_at'] < len(row) else ""
                        
                        if not title or not created_at:
                            continue
                        
                        # Verificar si ya existe
                        cursor.execute(
                            """
                            SELECT id FROM habits
                            WHERE title = ? AND IFNULL(description, '') = ? AND frequency = ? AND created_at = ?
                            LIMIT 1
                            """,
                            (title, description, frequency, created_at),
                        )
                        existing = cursor.fetchone()
                        if existing:
                            if old_id is not None:
                                id_map[old_id] = existing['id']
                            continue
                        
                        # Obtener valores adicionales de forma segura
                        target_days = 1
                        if 'target_days' in col_indices and col_indices['target_days'] < len(row):
                            try:
                                target_days = int(row[col_indices['target_days']])
                            except (ValueError, IndexError):
                                target_days = 1
                        
                        active = 1
                        if 'active' in col_indices and col_indices['active'] < len(row):
                            try:
                                active = int(row[col_indices['active']])
                            except (ValueError, IndexError):
                                active = 1
                        
                        updated_at = created_at
                        if 'updated_at' in col_indices and col_indices['updated_at'] < len(row):
                            updated_at = row[col_indices['updated_at']] or created_at
                        
                        # Insertar nuevo hábito
                        cursor.execute(
                            """
                            INSERT INTO habits (title, description, frequency, target_days, active, created_at, updated_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                            """,
                            (title, description, frequency, target_days, active, created_at, updated_at),
                        )
                        new_id = cursor.lastrowid
                        imported_count += 1
                        
                        if old_id is not None:
                            id_map[old_id] = new_id
                
                except Exception as e:
                    errors.append(f"Error importando fila en {table_name}: {str(e)}")
                    continue
        
        except HttpError as e:
            errors.append(f"Error leyendo hoja {sheet_name}: {str(e)}")
        
        return imported_count, id_map
    
    def _import_subtasks_from_sheet(self, service, spreadsheet_id: str, cursor: sqlite3.Cursor,
                                     sheet_name: str, task_id_map: Dict[int, int], errors: List[str]) -> int:
        """Importa subtareas desde una hoja de Google Sheets."""
        imported_count = 0
        
        try:
            result = service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id,
                range=sheet_name
            ).execute()
            
            values = result.get('values', [])
            
            if not values:
                return 0
            
            headers = values[0]
            data_rows = values[1:]
            col_indices = {col: i for i, col in enumerate(headers)}
            
            for row in data_rows:
                try:
                    while len(row) < len(headers):
                        row.append("")
                    
                    # Obtener task_id de forma segura
                    old_task_id_str = row[col_indices['task_id']] if 'task_id' in col_indices and col_indices['task_id'] < len(row) else ""
                    if not old_task_id_str:
                        continue
                    
                    try:
                        old_task_id = int(old_task_id_str)
                    except (ValueError, TypeError):
                        errors.append(f"Subtarea ignorada: task_id inválido")
                        continue
                    
                    new_task_id = task_id_map.get(old_task_id)
                    if not new_task_id:
                        errors.append(f"Subtarea ignorada: tarea padre (ID {old_task_id}) no encontrada")
                        continue
                    
                    title = row[col_indices['title']] if 'title' in col_indices and col_indices['title'] < len(row) else ""
                    description = row[col_indices['description']] if 'description' in col_indices and col_indices['description'] < len(row) else ""
                    deadline = row[col_indices['deadline']] if 'deadline' in col_indices and col_indices['deadline'] < len(row) else None
                    created_at = row[col_indices['created_at']] if 'created_at' in col_indices and col_indices['created_at'] < len(row) else ""
                    
                    if not title or not created_at:
                        continue
                    
                    # Verificar duplicado
                    cursor.execute(
                        """
                        SELECT id FROM subtasks
                        WHERE task_id = ? AND title = ? AND IFNULL(description, '') = ?
                          AND IFNULL(deadline, '') = ? AND created_at = ?
                        LIMIT 1
                        """,
                        (new_task_id, title, description, deadline or '', created_at),
                    )
                    if cursor.fetchone():
                        continue
                    
                    # Obtener valores adicionales de forma segura
                    completed = 0
                    if 'completed' in col_indices and col_indices['completed'] < len(row):
                        try:
                            completed = int(row[col_indices['completed']])
                        except (ValueError, IndexError):
                            completed = 0
                    
                    updated_at = created_at
                    if 'updated_at' in col_indices and col_indices['updated_at'] < len(row):
                        updated_at = row[col_indices['updated_at']] or created_at
                    
                    # Insertar subtarea
                    cursor.execute(
                        """
                        INSERT INTO subtasks (task_id, title, description, deadline, completed, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                        """,
                        (new_task_id, title, description, deadline if deadline else None, completed, created_at, updated_at),
                    )
                    imported_count += 1
                
                except Exception as e:
                    errors.append(f"Error importando subtarea: {str(e)}")
                    continue
        
        except HttpError as e:
            errors.append(f"Error leyendo hoja {sheet_name}: {str(e)}")
        
        return imported_count
    
    def _import_habit_completions_from_sheet(self, service, spreadsheet_id: str, cursor: sqlite3.Cursor,
                                               sheet_name: str, habit_id_map: Dict[int, int], errors: List[str]) -> int:
        """Importa cumplimientos de hábitos desde una hoja de Google Sheets."""
        imported_count = 0
        
        try:
            result = service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id,
                range=sheet_name
            ).execute()
            
            values = result.get('values', [])
            
            if not values:
                return 0
            
            headers = values[0]
            data_rows = values[1:]
            col_indices = {col: i for i, col in enumerate(headers)}
            
            for row in data_rows:
                try:
                    while len(row) < len(headers):
                        row.append("")
                    
                    old_habit_id_str = row[col_indices['habit_id']] if 'habit_id' in col_indices and col_indices['habit_id'] < len(row) else ""
                    completion_date = row[col_indices['completion_date']] if 'completion_date' in col_indices and col_indices['completion_date'] < len(row) else ""
                    created_at = row[col_indices['created_at']] if 'created_at' in col_indices and col_indices['created_at'] < len(row) else ""
                    
                    if not old_habit_id_str or not completion_date:
                        continue
                    
                    try:
                        old_habit_id = int(old_habit_id_str)
                    except ValueError:
                        errors.append(f"Cumplimiento ignorado: habit_id inválido")
                        continue
                    
                    new_habit_id = habit_id_map.get(old_habit_id)
                    if not new_habit_id:
                        errors.append(f"Cumplimiento ignorado: hábito (ID {old_habit_id}) no encontrado")
                        continue
                    
                    # Verificar si ya existe
                    cursor.execute(
                        """
                        SELECT id FROM habit_completions
                        WHERE habit_id = ? AND completion_date = ?
                        LIMIT 1
                        """,
                        (new_habit_id, completion_date),
                    )
                    if cursor.fetchone():
                        continue
                    
                    # Insertar cumplimiento
                    cursor.execute(
                        """
                        INSERT INTO habit_completions (habit_id, completion_date, created_at)
                        VALUES (?, ?, ?)
                        """,
                        (new_habit_id, completion_date, created_at or completion_date),
                    )
                    imported_count += 1
                
                except Exception as e:
                    errors.append(f"Error importando cumplimiento: {str(e)}")
                    continue
        
        except HttpError as e:
            errors.append(f"Error leyendo hoja {sheet_name}: {str(e)}")
        
        return imported_count
