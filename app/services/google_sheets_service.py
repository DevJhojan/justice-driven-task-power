"""
Servicio para importación y exportación de datos usando Google Sheets API directamente.

Este módulo se encarga de:
- Exportar datos de todas las tablas a Google Sheets usando google-api-python-client.
- Importar datos desde Google Sheets de forma no destructiva.
- Manejar autenticación OAuth2 con Google usando wsgiref como servidor local.
- Sincronizar datos entre la base de datos local y Google Sheets.

Decisiones técnicas:
- Usa google-api-python-client directamente (sin gspread) para mayor control y compatibilidad.
- Usa wsgiref (biblioteca estándar de Python) como servidor local para OAuth2 callback.
- Cada tabla se exporta a una hoja separada en el mismo spreadsheet.
- La importación lee desde las hojas y los importa de forma no destructiva.
- Usa transacciones SQLite para garantizar atomicidad.
- Detecta duplicados mediante huellas lógicas.
"""

from __future__ import annotations

import os
import sqlite3
import threading
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from urllib.parse import urlparse, parse_qs

try:
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    import pickle
    GOOGLE_API_AVAILABLE = True
except ImportError as e:
    GOOGLE_API_AVAILABLE = False
    _google_api_import_error = str(e)

from app.data.database import Database


# Scopes necesarios para Google Sheets API
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']


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
    """Servicio de importación/exportación basado en Google Sheets usando google-api-python-client.
    
    Decisiones técnicas:
    - Usa google-api-python-client directamente para trabajar con Google Sheets API.
    - Usa wsgiref (biblioteca estándar) como servidor local para OAuth2 callback.
    - Cada tabla se exporta a una hoja separada en el mismo spreadsheet.
    - La importación lee desde las hojas y los importa de forma no destructiva.
    - Usa transacciones SQLite para garantizar atomicidad.
    - Detecta duplicados mediante huellas lógicas.
    """
    
    def __init__(self, database: Database | None = None, page=None) -> None:
        if not GOOGLE_API_AVAILABLE:
            raise ImportError(
                f"Google API no está disponible: {_google_api_import_error}\n\n"
                "Por favor, instala las dependencias: pip install google-api-python-client google-auth-oauthlib"
            )
        
        self.db = database or Database()
        self.service = None
        self.credentials = None
        self.page = page  # Página de Flet para abrir URLs en Android
        
        # Rutas para credenciales y token
        self.root_dir = Path(__file__).parent.parent.parent
        self.credentials_path = self.root_dir / 'credenciales_android.json'
        
        # En Android, guardar el token en el directorio de datos persistente
        # En desarrollo, usar el directorio raíz
        app_data_dir = os.getenv("FLET_APP_STORAGE_DATA")
        if app_data_dir:
            # Android: usar directorio persistente
            token_dir = Path(app_data_dir)
            token_dir.mkdir(parents=True, exist_ok=True)
            self.token_path = token_dir / 'google_token.pickle'
        else:
            # Desarrollo: usar directorio raíz
            self.token_path = self.root_dir / 'token.pickle'
    
    def _get_credentials(self) -> Credentials:
        """
        Obtiene credenciales válidas para Google Sheets API.
        Si no hay credenciales válidas, inicia el flujo OAuth2 usando wsgiref.
        
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
                
                # Usar wsgiref para el servidor local OAuth2
                # Esto funciona tanto en desarrollo como en Android si wsgiref está disponible
                try:
                    # Verificar si wsgiref está disponible
                    import wsgiref.simple_server
                    
                    # Usar servidor local con wsgiref
                    # En Android, abrir el navegador manualmente si es necesario
                    if self.page:
                        # Obtener URL de autorización
                        auth_url, _ = flow.authorization_url(
                            prompt='consent',
                            access_type='offline',
                            include_granted_scopes=True
                        )
                        
                        # Intentar abrir el navegador
                        try:
                            self.page.launch_url(auth_url, web_window_name="_blank")
                        except Exception:
                            pass
                    
                    # Ejecutar el servidor local con wsgiref
                    creds = flow.run_local_server(port=0, open_browser=False)
                    
                except ImportError:
                    # Si wsgiref no está disponible, usar método manual
                    raise Exception(
                        "wsgiref no está disponible. "
                        "Por favor, asegúrate de que wsgiref esté incluido en el build de Android."
                    )
                except Exception as e:
                    # Si hay otro error, relanzarlo
                    raise Exception(f"Error en la autenticación OAuth2: {str(e)}")
            
            # Guardar credenciales para próximas veces
            try:
                # Asegurar que el directorio existe
                self.token_path.parent.mkdir(parents=True, exist_ok=True)
                with open(self.token_path, 'wb') as token:
                    pickle.dump(creds, token)
            except Exception as save_error:
                # Si no se puede guardar, continuar de todas formas pero mostrar advertencia
                print(f"Advertencia: No se pudo guardar el token: {save_error}")
        
        return creds
    
    def _get_service(self):
        """Obtiene el servicio de Google Sheets API."""
        if self.service is None:
            try:
                creds = self._get_credentials()
            except Exception as e:
                raise Exception(f"Error al obtener credenciales: {str(e)}")
            
            # Crear servicio de Google Sheets API
            self.credentials = creds
            try:
                self.service = build('sheets', 'v4', credentials=creds)
            except Exception as e:
                self.service = None
                raise Exception(f"Error al crear el servicio de Google Sheets: {str(e)}")
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
            print(f"Error en autenticación: {e}")
            return False
    
    def get_user_email(self) -> Optional[str]:
        """
        Obtiene el correo electrónico del usuario autenticado.
        
        Returns:
            Correo electrónico del usuario o None si no se puede obtener.
        """
        try:
            creds = self._get_credentials()
            if not creds or not creds.valid:
                return None
            
            # Obtener información del usuario desde la API de Google
            service = build('oauth2', 'v2', credentials=creds)
            user_info = service.userinfo().get().execute()
            return user_info.get('email')
        except Exception:
            # Si falla, intentar obtener desde el token directamente
            try:
                if hasattr(creds, 'id_token') and creds.id_token:
                    import base64
                    import json
                    # Decodificar el id_token (JWT)
                    parts = creds.id_token.split('.')
                    if len(parts) >= 2:
                        # Decodificar el payload (segunda parte)
                        payload = parts[1]
                        # Agregar padding si es necesario
                        padding = 4 - len(payload) % 4
                        if padding != 4:
                            payload += '=' * padding
                        decoded = base64.urlsafe_b64decode(payload)
                        data = json.loads(decoded)
                        return data.get('email')
            except Exception:
                pass
            return None
    
    def create_spreadsheet(self, title: str) -> str:
        """
        Crea un nuevo spreadsheet en Google Sheets.
        
        Args:
            title: Título del spreadsheet.
        
        Returns:
            ID del spreadsheet creado.
        """
        service = self._get_service()
        
        # Crear spreadsheet usando la API de Google Sheets
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
        
        try:
            request = service.spreadsheets().create(body=spreadsheet)
            response = request.execute()
            return response['spreadsheetId']
        except HttpError as error:
            raise Exception(f"Error al crear el spreadsheet: {error}")
    
    def export_to_sheets(self, spreadsheet_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Exporta todas las tablas a Google Sheets.
        
        Args:
            spreadsheet_id: ID del spreadsheet existente. Si es None, crea uno nuevo.
        
        Returns:
            Diccionario con información del spreadsheet (id, url, etc.).
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
            
            # Obtener información del spreadsheet
            spreadsheet_info = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
            spreadsheet_title = spreadsheet_info.get('properties', {}).get('title', 'Sin título')
            
            # Obtener URL del spreadsheet
            spreadsheet_url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}"
            
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
        
        # Obtener nombres de columnas
        column_names = [description[0] for description in cursor.description]
        
        # Preparar valores (encabezados + datos)
        values = [column_names]
        for row in rows:
            # Convertir valores a formato compatible con Google Sheets
            row_values = []
            for value in row:
                if value is None:
                    row_values.append('')
                elif isinstance(value, (int, float)):
                    row_values.append(value)
                elif isinstance(value, bool):
                    row_values.append('TRUE' if value else 'FALSE')
                else:
                    row_values.append(str(value))
            values.append(row_values)
        
        # Escribir datos a la hoja usando la API de Google Sheets
        body = {
            'values': values
        }
        
        try:
            service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range=f'{sheet_name}!A1',
                valueInputOption='RAW',
                body=body
            ).execute()
        except HttpError as error:
            raise Exception(f"Error al exportar {table_name} a {sheet_name}: {error}")
    
    def import_from_sheets(self, spreadsheet_id: str) -> SheetsImportResult:
        """
        Importa datos desde un Google Sheets existente.
        
        Args:
            spreadsheet_id: ID del spreadsheet de Google Sheets.
        
        Returns:
            Resultado de la importación con contadores y errores.
        """
        service = self._get_service()
        result = SheetsImportResult()
        
        try:
            # Obtener información del spreadsheet
            spreadsheet_info = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
            sheets = spreadsheet_info.get('sheets', [])
            
            # Mapear nombres de hojas a tablas
            sheet_mapping = {
                'tasks': 'tasks',
                'subtasks': 'subtasks',
                'habits': 'habits',
                'habit_completions': 'habit_completions'
            }
            
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            try:
                # Importar cada hoja
                for sheet in sheets:
                    sheet_title = sheet['properties']['title']
                    if sheet_title in sheet_mapping:
                        table_name = sheet_mapping[sheet_title]
                        imported = self._import_sheet_to_table(
                            service, spreadsheet_id, sheet_title, cursor, table_name, result
                        )
                        
                        if table_name == 'tasks':
                            result.tasks_imported = imported
                        elif table_name == 'subtasks':
                            result.subtasks_imported = imported
                        elif table_name == 'habits':
                            result.habits_imported = imported
                        elif table_name == 'habit_completions':
                            result.habit_completions_imported = imported
                
                conn.commit()
            except Exception as e:
                conn.rollback()
                result.errors.append(f"Error durante la importación: {str(e)}")
            finally:
                conn.close()
                
        except HttpError as error:
            result.errors.append(f"Error al acceder al spreadsheet: {error}")
        
        return result
    
    def _import_sheet_to_table(self, service, spreadsheet_id: str, sheet_name: str,
                               cursor: sqlite3.Cursor, table_name: str, 
                               result: SheetsImportResult) -> int:
        """
        Importa una hoja de Google Sheets a una tabla SQLite.
        
        Args:
            service: Servicio de Google Sheets API.
            spreadsheet_id: ID del spreadsheet.
            sheet_name: Nombre de la hoja en Google Sheets.
            cursor: Cursor de la base de datos.
            table_name: Nombre de la tabla en SQLite.
            result: Objeto de resultado para acumular errores.
        
        Returns:
            Número de registros importados.
        """
        try:
            # Obtener datos de la hoja
            range_name = f'{sheet_name}!A:Z'
            response = service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id,
                range=range_name
            ).execute()
            
            values = response.get('values', [])
            if not values:
                return 0
            
            # Primera fila son los encabezados
            headers = values[0]
            data_rows = values[1:]
            
            # Obtener estructura de la tabla
            cursor.execute(f"PRAGMA table_info({table_name})")
            table_info = cursor.fetchall()
            table_columns = {col[1]: col[2] for col in table_info}  # nombre: tipo
            
            imported_count = 0
            
            # Importar cada fila
            for row in data_rows:
                try:
                    # Asegurar que la fila tenga el mismo número de columnas que los encabezados
                    while len(row) < len(headers):
                        row.append('')
                    
                    # Construir diccionario de valores
                    row_dict = dict(zip(headers, row))
                    
                    # Importar según el tipo de tabla
                    if table_name == 'tasks':
                        imported = self._import_task_row(cursor, row_dict, result)
                    elif table_name == 'subtasks':
                        imported = self._import_subtask_row(cursor, row_dict, result)
                    elif table_name == 'habits':
                        imported = self._import_habit_row(cursor, row_dict, result)
                    elif table_name == 'habit_completions':
                        imported = self._import_habit_completion_row(cursor, row_dict, result)
                    else:
                        imported = False
                    
                    if imported:
                        imported_count += 1
                        
                except Exception as e:
                    result.errors.append(f"Error al importar fila en {sheet_name}: {str(e)}")
            
            return imported_count
            
        except HttpError as error:
            result.errors.append(f"Error al leer la hoja {sheet_name}: {error}")
            return 0
    
    def _import_task_row(self, cursor: sqlite3.Cursor, row_dict: dict, result: SheetsImportResult) -> bool:
        """Importa una fila de tarea."""
        try:
            # Verificar si ya existe (por título y fecha de creación)
            title = row_dict.get('title', '').strip()
            created_at = row_dict.get('created_at', '')
            
            if not title:
                return False
            
            cursor.execute(
                "SELECT id FROM tasks WHERE title = ? AND created_at = ?",
                (title, created_at)
            )
            if cursor.fetchone():
                return False  # Ya existe
            
            # Insertar nueva tarea
            cursor.execute(
                """
                INSERT INTO tasks (title, description, completed, priority, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    title,
                    row_dict.get('description', ''),
                    1 if str(row_dict.get('completed', '0')).upper() in ('1', 'TRUE', 'YES') else 0,
                    row_dict.get('priority', 'medium'),
                    created_at or datetime.now().isoformat(),
                    row_dict.get('updated_at', datetime.now().isoformat())
                )
            )
            return True
        except Exception as e:
            result.errors.append(f"Error al importar tarea: {str(e)}")
            return False
    
    def _import_subtask_row(self, cursor: sqlite3.Cursor, row_dict: dict, result: SheetsImportResult) -> bool:
        """Importa una fila de subtarea."""
        try:
            task_id = row_dict.get('task_id', '')
            title = row_dict.get('title', '').strip()
            
            if not task_id or not title:
                return False
            
            # Verificar si ya existe
            cursor.execute(
                "SELECT id FROM subtasks WHERE task_id = ? AND title = ?",
                (task_id, title)
            )
            if cursor.fetchone():
                return False
            
            # Insertar nueva subtarea
            cursor.execute(
                """
                INSERT INTO subtasks (task_id, title, description, deadline, completed, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    task_id,
                    title,
                    row_dict.get('description', ''),
                    row_dict.get('deadline') or None,
                    1 if str(row_dict.get('completed', '0')).upper() in ('1', 'TRUE', 'YES') else 0,
                    row_dict.get('created_at', datetime.now().isoformat()),
                    row_dict.get('updated_at', datetime.now().isoformat())
                )
            )
            return True
        except Exception as e:
            result.errors.append(f"Error al importar subtarea: {str(e)}")
            return False
    
    def _import_habit_row(self, cursor: sqlite3.Cursor, row_dict: dict, result: SheetsImportResult) -> bool:
        """Importa una fila de hábito."""
        try:
            name = row_dict.get('name', '').strip()
            created_at = row_dict.get('created_at', '')
            
            if not name:
                return False
            
            # Verificar si ya existe
            cursor.execute(
                "SELECT id FROM habits WHERE name = ? AND created_at = ?",
                (name, created_at)
            )
            if cursor.fetchone():
                return False
            
            # Insertar nuevo hábito
            cursor.execute(
                """
                INSERT INTO habits (name, description, frequency, active, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    name,
                    row_dict.get('description', ''),
                    row_dict.get('frequency', 'daily'),
                    1 if str(row_dict.get('active', '1')).upper() in ('1', 'TRUE', 'YES') else 0,
                    created_at or datetime.now().isoformat(),
                    row_dict.get('updated_at', datetime.now().isoformat())
                )
            )
            return True
        except Exception as e:
            result.errors.append(f"Error al importar hábito: {str(e)}")
            return False
    
    def _import_habit_completion_row(self, cursor: sqlite3.Cursor, row_dict: dict, result: SheetsImportResult) -> bool:
        """Importa una fila de cumplimiento de hábito."""
        try:
            habit_id = row_dict.get('habit_id', '')
            completion_date = row_dict.get('completion_date', '')
            
            if not habit_id or not completion_date:
                return False
            
            # Verificar si ya existe
            cursor.execute(
                "SELECT id FROM habit_completions WHERE habit_id = ? AND completion_date = ?",
                (habit_id, completion_date)
            )
            if cursor.fetchone():
                return False
            
            # Insertar nuevo cumplimiento
            cursor.execute(
                """
                INSERT INTO habit_completions (habit_id, completion_date, created_at)
                VALUES (?, ?, ?)
                """,
                (
                    habit_id,
                    completion_date,
                    row_dict.get('created_at', datetime.now().isoformat())
                )
            )
            return True
        except Exception as e:
            result.errors.append(f"Error al importar cumplimiento de hábito: {str(e)}")
            return False
