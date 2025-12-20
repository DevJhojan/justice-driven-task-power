"""
Servicio para importación y exportación de datos usando Google Sheets con gspread.

Este módulo se encarga de:
- Exportar datos de todas las tablas a Google Sheets.
- Importar datos desde Google Sheets de forma no destructiva.
- Manejar autenticación OAuth2 con Google usando credenciales_android.json.
- Sincronizar datos entre la base de datos local y Google Sheets.
"""

from __future__ import annotations

import os
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

try:
    import gspread
    from google.oauth2.service_account import ServiceAccountCredentials
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    import pickle
    GSPREAD_AVAILABLE = True
except ImportError as e:
    GSPREAD_AVAILABLE = False
    _gspread_import_error = str(e)

from app.data.database import Database


# Scopes necesarios para Google Sheets API
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']


class ManualAuthRequired(Exception):
    """Excepción lanzada cuando se requiere autenticación manual (sin wsgiref)."""
    def __init__(self, auth_url: str, state: str):
        self.auth_url = auth_url
        self.state = state
        super().__init__(
            "Autenticación manual requerida debido a la falta de wsgiref en Android."
        )


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
    """Servicio de importación/exportación basado en Google Sheets usando gspread.
    
    Decisiones técnicas:
    - Usa gspread para simplificar el trabajo con Google Sheets.
    - Usa OAuth2 para autenticación con Google usando credenciales_android.json.
    - Cada tabla se exporta a una hoja separada en el mismo spreadsheet.
    - La importación lee desde las hojas y los importa de forma no destructiva.
    - Usa transacciones SQLite para garantizar atomicidad.
    - Detecta duplicados mediante huellas lógicas.
    """
    
    def __init__(self, database: Database | None = None, page=None) -> None:
        if not GSPREAD_AVAILABLE:
            raise ImportError(
                f"gspread no está disponible: {_gspread_import_error}\n\n"
                "Por favor, instala gspread: pip install gspread"
            )
        
        self.db = database or Database()
        self.client = None
        self.credentials = None
        self.page = page  # Página de Flet para abrir URLs en Android
        self.pending_flow = None  # Guardar el flow para autenticación manual
        self.pending_state = None  # Guardar el state para validación
        
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
    
    def complete_manual_auth(self, redirect_url: str) -> Credentials:
        """
        Completa la autenticación manual usando la URL de redirección.
        
        Args:
            redirect_url: URL completa de redirección después de autorizar en el navegador.
        
        Returns:
            Credenciales de Google OAuth2.
        
        Raises:
            ValueError: Si la URL no es válida o no contiene el código de autorización.
        """
        if not self.pending_flow:
            raise ValueError("No hay un flujo de autenticación pendiente. Inicia la autenticación primero.")
        
        # Extraer el código de autorización de la URL
        from urllib.parse import urlparse, parse_qs
        
        parsed = urlparse(redirect_url)
        query_params = parse_qs(parsed.query)
        
        # Obtener el código de autorización
        if 'code' not in query_params:
            raise ValueError(
                f"La URL de redirección no contiene un código de autorización.\n\n"
                f"URL recibida: {redirect_url}\n\n"
                f"Por favor, asegúrate de copiar la URL completa después de autorizar en el navegador."
            )
        
        auth_code = query_params['code'][0]
        
        # Verificar el state (seguridad)
        if 'state' in query_params:
            received_state = query_params['state'][0]
            if received_state != self.pending_state:
                raise ValueError("El state no coincide. La autenticación puede haber sido comprometida.")
        
        # Intercambiar el código por credenciales
        try:
            self.pending_flow.fetch_token(code=auth_code)
            creds = self.pending_flow.credentials
            
            # Guardar credenciales
            try:
                # Asegurar que el directorio existe
                self.token_path.parent.mkdir(parents=True, exist_ok=True)
                with open(self.token_path, 'wb') as token:
                    pickle.dump(creds, token)
            except Exception as save_error:
                # Si no se puede guardar, continuar de todas formas pero mostrar advertencia
                print(f"Advertencia: No se pudo guardar el token: {save_error}")
            
            # Limpiar el flow pendiente
            self.pending_flow = None
            self.pending_state = None
            
            # Actualizar el cliente de gspread
            self.credentials = creds
            try:
                self.client = gspread.authorize(creds)
            except Exception as auth_error:
                # Si hay error al autorizar, limpiar y relanzar
                self.client = None
                raise Exception(f"Error al autorizar con gspread: {str(auth_error)}")
            
            return creds
        except Exception as e:
            raise ValueError(
                f"Error al intercambiar el código por credenciales: {str(e)}\n\n"
                f"Por favor, intenta autorizar nuevamente."
            )
        
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
                
                # Para Android, usar método manual sin wsgiref
                if self.page:
                    # Verificar si wsgiref está disponible
                    wsgiref_available = False
                    try:
                        import wsgiref.simple_server
                        wsgiref_available = True
                    except ImportError:
                        wsgiref_available = False
                    
                    # Obtener URL de autorización
                    auth_url, state = flow.authorization_url(
                        prompt='consent',
                        access_type='offline',  # Para obtener refresh_token
                        include_granted_scopes=True
                    )
                    
                    # Abrir navegador en Android usando Flet
                    browser_opened = False
                    try:
                        # Intentar con launch_url primero
                        self.page.launch_url(auth_url, web_window_name="_blank")
                        browser_opened = True
                    except Exception:
                        # Si falla, intentar método alternativo
                        try:
                            import subprocess
                            import platform
                            
                            if platform.system() == "Linux" or "android" in str(platform.platform()).lower():
                                try:
                                    subprocess.run(
                                        ["am", "start", "-a", "android.intent.action.VIEW", "-d", auth_url],
                                        check=False,
                                        timeout=2
                                    )
                                    browser_opened = True
                                except Exception:
                                    pass
                            
                            if not browser_opened:
                                import webbrowser
                                webbrowser.open(auth_url)
                                browser_opened = True
                        except Exception:
                            browser_opened = False
                    
                    # Intentar usar servidor local solo si wsgiref está disponible
                    if wsgiref_available:
                        try:
                            creds = flow.run_local_server(port=0, open_browser=False)
                        except (ImportError, ModuleNotFoundError) as e:
                            if 'wsgiref' in str(e) or 'wsgi' in str(e).lower():
                                wsgiref_available = False
                            else:
                                raise Exception(
                                    f"Error en la autenticación: {str(e)}\n\n"
                                    f"Por favor, asegúrate de haber autorizado la aplicación en el navegador."
                                )
                    
                    # Si wsgiref no está disponible, usar método manual
                    if not wsgiref_available:
                        # Guardar el flow y state para completar la autenticación manualmente
                        self.pending_flow = flow
                        self.pending_state = state
                        # Lanzar excepción especial que será capturada para mostrar diálogo
                        raise ManualAuthRequired(auth_url, state)
                else:
                    # Para escritorio, usar servidor local normal
                    try:
                        creds = flow.run_local_server(port=0, open_browser=True)
                    except ImportError as e:
                        if 'wsgiref' in str(e) or 'wsgi' in str(e).lower():
                            raise ImportError(
                                "El módulo 'wsgiref' no está disponible.\n\n"
                                "Por favor, asegúrate de que Python esté completamente instalado.\n"
                                "En algunos sistemas, wsgiref puede no estar incluido.\n\n"
                                f"Error original: {str(e)}"
                            )
                        raise
            
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
    
    def _get_client(self):
        """Obtiene el cliente de gspread."""
        if self.client is None:
            try:
                creds = self._get_credentials()
            except ManualAuthRequired:
                # Si se requiere autenticación manual, relanzar la excepción
                raise
            # Crear cliente de gspread con las credenciales
            self.credentials = creds
            try:
                self.client = gspread.authorize(creds)
            except Exception as e:
                # Si hay un error al autorizar, limpiar el cliente y relanzar
                self.client = None
                raise Exception(f"Error al autorizar con gspread: {str(e)}")
        return self.client
    
    def authenticate(self) -> bool:
        """
        Autentica con Google Sheets API.
        
        Returns:
            True si la autenticación fue exitosa, False en caso contrario.
        """
        try:
            self._get_client()
            return True
        except Exception as e:
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
            from googleapiclient.discovery import build
            service = build('oauth2', 'v2', credentials=creds)
            user_info = service.userinfo().get().execute()
            return user_info.get('email')
        except Exception:
            # Si falla, intentar obtener desde el token directamente
            try:
                if hasattr(creds, 'id_token'):
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
        client = self._get_client()
        
        # Crear spreadsheet con gspread
        spreadsheet = client.create(title)
        
        # Crear las hojas necesarias
        sheet_names = ['tasks', 'subtasks', 'habits', 'habit_completions']
        for sheet_name in sheet_names:
            try:
                spreadsheet.add_worksheet(title=sheet_name, rows=1000, cols=20)
            except Exception:
                # La hoja puede ya existir
                pass
        
        # Eliminar la hoja por defecto si existe
        try:
            default_sheet = spreadsheet.sheet1
            if default_sheet.title == 'Sheet1':
                spreadsheet.del_worksheet(default_sheet)
        except Exception:
            pass
        
        return spreadsheet.id
    
    def export_to_sheets(self, spreadsheet_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Exporta todas las tablas a Google Sheets.
        
        Args:
            spreadsheet_id: ID del spreadsheet existente. Si es None, crea uno nuevo.
        
        Returns:
            Diccionario con información del spreadsheet (id, url, etc.).
        """
        client = self._get_client()
        
        # Crear spreadsheet si no existe
        created_new = False
        if not spreadsheet_id:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            title = f"Tasks Backup {timestamp}"
            spreadsheet_id = self.create_spreadsheet(title)
            created_new = True
        
        spreadsheet = client.open_by_key(spreadsheet_id)
        
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            # Exportar cada tabla a su hoja
            self._export_table_to_sheet(spreadsheet, cursor, "tasks", "tasks")
            self._export_table_to_sheet(spreadsheet, cursor, "subtasks", "subtasks")
            self._export_table_to_sheet(spreadsheet, cursor, "habits", "habits")
            self._export_table_to_sheet(spreadsheet, cursor, "habit_completions", "habit_completions")
            
            # Obtener URL del spreadsheet
            spreadsheet_url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}"
            
            return {
                'spreadsheet_id': spreadsheet_id,
                'url': spreadsheet_url,
                'title': spreadsheet.title,
                'created_new': created_new
            }
        finally:
            conn.close()
    
    def _export_table_to_sheet(self, spreadsheet, cursor: sqlite3.Cursor, 
                                table_name: str, sheet_name: str) -> None:
        """
        Exporta una tabla SQLite a una hoja de Google Sheets.
        
        Args:
            spreadsheet: Objeto spreadsheet de gspread.
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
        
        # Obtener o crear la hoja
        try:
            worksheet = spreadsheet.worksheet(sheet_name)
        except gspread.exceptions.WorksheetNotFound:
            worksheet = spreadsheet.add_worksheet(title=sheet_name, rows=1000, cols=20)
        
        # Limpiar la hoja y escribir datos
        worksheet.clear()
        if values:
            worksheet.update('A1', values)
    
    def import_from_sheets(self, spreadsheet_id: str) -> SheetsImportResult:
        """
        Importa datos desde un Google Sheets spreadsheet.
        
        Args:
            spreadsheet_id: ID del spreadsheet de Google Sheets.
        
        Returns:
            SheetsImportResult con contadores de registros importados y errores.
        """
        client = self._get_client()
        result = SheetsImportResult()
        
        try:
            spreadsheet = client.open_by_key(spreadsheet_id)
        except Exception as e:
            result.errors.append(f"Error al abrir el spreadsheet: {str(e)}")
            return result
        
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
                    spreadsheet, cursor, "tasks", "tasks", result.errors
                )
            except Exception as e:
                result.errors.append(f"Error importando tasks: {str(e)}")
            
            try:
                result.habits_imported, habit_id_map = self._import_sheet_to_table(
                    spreadsheet, cursor, "habits", "habits", result.errors
                )
            except Exception as e:
                result.errors.append(f"Error importando habits: {str(e)}")
            
            try:
                result.subtasks_imported = self._import_subtasks_from_sheet(
                    spreadsheet, cursor, "subtasks", task_id_map, result.errors
                )
            except Exception as e:
                result.errors.append(f"Error importando subtasks: {str(e)}")
            
            try:
                result.habit_completions_imported = self._import_habit_completions_from_sheet(
                    spreadsheet, cursor, "habit_completions", habit_id_map, result.errors
                )
            except Exception as e:
                result.errors.append(f"Error importando habit_completions: {str(e)}")
            
            # Commit si todo fue bien
            conn.commit()
            
        except Exception as e:
            conn.rollback()
            result.errors.append(f"Error en la transacción: {str(e)}")
        finally:
            conn.close()
        
        return result
    
    def _import_sheet_to_table(self, spreadsheet, cursor: sqlite3.Cursor,
                               table_name: str, sheet_name: str, errors: List[str]) -> tuple[int, Dict[int, int]]:
        """
        Importa datos desde una hoja de Google Sheets a una tabla SQLite.
        
        Args:
            spreadsheet: Objeto spreadsheet de gspread.
            cursor: Cursor de la base de datos.
            table_name: Nombre de la tabla en SQLite.
            sheet_name: Nombre de la hoja en Google Sheets.
            errors: Lista para agregar errores.
        
        Returns:
            Tupla (número de registros importados, mapa de IDs antiguos -> nuevos).
        """
        try:
            worksheet = spreadsheet.worksheet(sheet_name)
        except gspread.exceptions.WorksheetNotFound:
            errors.append(f"Hoja '{sheet_name}' no encontrada en el spreadsheet")
            return 0, {}
        
        # Obtener todos los valores
        all_values = worksheet.get_all_values()
        
        if not all_values or len(all_values) < 2:
            return 0, {}
        
        # Primera fila son los encabezados
        headers = all_values[0]
        data_rows = all_values[1:]
        
        # Obtener estructura de la tabla
        cursor.execute(f"PRAGMA table_info({table_name})")
        table_info = cursor.fetchall()
        table_columns = {row[1]: row for row in table_info}
        
        id_map: Dict[int, int] = {}
        imported_count = 0
        
        for row_data in data_rows:
            if not row_data or all(not cell for cell in row_data):
                continue
            
            try:
                # Crear diccionario de datos
                data_dict = {}
                old_id = None
                
                for i, header in enumerate(headers):
                    if i >= len(row_data):
                        break
                    
                    value = row_data[i].strip() if row_data[i] else ""
                    
                    if header in table_columns:
                        col_info = table_columns[header]
                        col_type = col_info[2].upper()
                        
                        # Convertir valor según tipo
                        if value == "":
                            data_dict[header] = None
                        elif 'INT' in col_type:
                            try:
                                data_dict[header] = int(value) if value else None
                            except ValueError:
                                data_dict[header] = None
                        elif 'REAL' in col_type or 'FLOAT' in col_type:
                            try:
                                data_dict[header] = float(value) if value else None
                            except ValueError:
                                data_dict[header] = None
                        elif 'TEXT' in col_type or 'VARCHAR' in col_type:
                            data_dict[header] = value if value else None
                        else:
                            data_dict[header] = value
                        
                        # Guardar ID antiguo si existe
                        if header == 'id' and value:
                            try:
                                old_id = int(value)
                            except ValueError:
                                pass
                
                # Insertar registro (sin el ID antiguo para que se genere uno nuevo)
                if 'id' in data_dict:
                    old_id = data_dict.pop('id')
                
                # Construir query de inserción
                columns = list(data_dict.keys())
                placeholders = ', '.join(['?' for _ in columns])
                values = [data_dict[col] for col in columns]
                
                query = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"
                cursor.execute(query, values)
                
                # Obtener el nuevo ID y crear el mapeo
                new_id = cursor.lastrowid
                if old_id is not None:
                    id_map[old_id] = new_id
                
                imported_count += 1
                
            except Exception as e:
                errors.append(f"Error importando fila en {sheet_name}: {str(e)}")
                continue
        
        return imported_count, id_map
    
    def _import_subtasks_from_sheet(self, spreadsheet, cursor: sqlite3.Cursor,
                                     sheet_name: str, task_id_map: Dict[int, int],
                                     errors: List[str]) -> int:
        """Importa subtareas desde una hoja de Google Sheets."""
        try:
            worksheet = spreadsheet.worksheet(sheet_name)
        except gspread.exceptions.WorksheetNotFound:
            errors.append(f"Hoja '{sheet_name}' no encontrada en el spreadsheet")
            return 0
        
        all_values = worksheet.get_all_values()
        
        if not all_values or len(all_values) < 2:
            return 0
        
        headers = all_values[0]
        data_rows = all_values[1:]
        
        imported_count = 0
        
        for row_data in data_rows:
            if not row_data or all(not cell for cell in row_data):
                continue
            
            try:
                data_dict = {}
                
                for i, header in enumerate(headers):
                    if i >= len(row_data):
                        break
                    
                    value = row_data[i].strip() if row_data[i] else ""
                    
                    if header == 'task_id' and value:
                        # Mapear el ID antiguo de la tarea al nuevo
                        try:
                            old_task_id = int(value)
                            if old_task_id in task_id_map:
                                data_dict[header] = task_id_map[old_task_id]
                            else:
                                # Si no hay mapeo, saltar esta subtarea
                                continue
                        except ValueError:
                            continue
                    elif value:
                        if header in ['id', 'completed']:
                            try:
                                data_dict[header] = int(value) if value.lower() not in ['', 'false', '0'] else 0
                            except ValueError:
                                data_dict[header] = 0
                        else:
                            data_dict[header] = value
                
                if 'task_id' not in data_dict:
                    continue
                
                # Eliminar ID antiguo
                if 'id' in data_dict:
                    del data_dict['id']
                
                columns = list(data_dict.keys())
                placeholders = ', '.join(['?' for _ in columns])
                values = [data_dict[col] for col in columns]
                
                query = f"INSERT INTO subtasks ({', '.join(columns)}) VALUES ({placeholders})"
                cursor.execute(query, values)
                imported_count += 1
                
            except Exception as e:
                errors.append(f"Error importando subtarea: {str(e)}")
                continue
        
        return imported_count
    
    def _import_habit_completions_from_sheet(self, spreadsheet, cursor: sqlite3.Cursor,
                                              sheet_name: str, habit_id_map: Dict[int, int],
                                              errors: List[str]) -> int:
        """Importa cumplimientos de hábitos desde una hoja de Google Sheets."""
        try:
            worksheet = spreadsheet.worksheet(sheet_name)
        except gspread.exceptions.WorksheetNotFound:
            errors.append(f"Hoja '{sheet_name}' no encontrada en el spreadsheet")
            return 0
        
        all_values = worksheet.get_all_values()
        
        if not all_values or len(all_values) < 2:
            return 0
        
        headers = all_values[0]
        data_rows = all_values[1:]
        
        imported_count = 0
        
        for row_data in data_rows:
            if not row_data or all(not cell for cell in row_data):
                continue
            
            try:
                data_dict = {}
                
                for i, header in enumerate(headers):
                    if i >= len(row_data):
                        break
                    
                    value = row_data[i].strip() if row_data[i] else ""
                    
                    if header == 'habit_id' and value:
                        # Mapear el ID antiguo del hábito al nuevo
                        try:
                            old_habit_id = int(value)
                            if old_habit_id in habit_id_map:
                                data_dict[header] = habit_id_map[old_habit_id]
                            else:
                                continue
                        except ValueError:
                            continue
                    elif value:
                        if header == 'completion_date':
                            data_dict[header] = value
                        elif header == 'id':
                            pass  # Ignorar ID antiguo
                        else:
                            data_dict[header] = value
                
                if 'habit_id' not in data_dict or 'completion_date' not in data_dict:
                    continue
                
                columns = list(data_dict.keys())
                placeholders = ', '.join(['?' for _ in columns])
                values = [data_dict[col] for col in columns]
                
                query = f"INSERT INTO habit_completions ({', '.join(columns)}) VALUES ({placeholders})"
                cursor.execute(query, values)
                imported_count += 1
                
            except Exception as e:
                errors.append(f"Error importando cumplimiento de hábito: {str(e)}")
                continue
        
        return imported_count
