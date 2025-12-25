"""
Servicio de sincronización con Firebase Realtime Database usando REST API directamente.

ARQUITECTURA OFFLINE-FIRST:
- SQLite es la base de datos principal y fuente de verdad local
- La app funciona completamente offline sin necesidad de conexión a internet
- Firebase es OPCIONAL y solo se usa para respaldo y sincronización entre dispositivos
- La sincronización es completamente bajo demanda del usuario
- Si Firebase no está disponible o hay error de red, la app sigue funcionando normalmente

Este módulo maneja:
- Subida de datos locales (SQLite) a Firebase Realtime Database
- Descarga de datos remotos desde Firebase Realtime Database
- Sincronización bidireccional no destructiva (no borra datos locales)
- Separación de datos por userId
- Resolución de conflictos usando timestamps (solo actualiza si remoto es más reciente)

Decisiones técnicas:
- Usa requests para llamar directamente a Firebase Realtime Database REST API
- Evita dependencias problemáticas como pyrebase4/gcloud
- Mantiene SQLite como base de datos principal (offline-first)
- Firebase solo como respaldo y sincronización
- Usa timestamps para resolución de conflictos (last-write-wins con verificación)
- Cada usuario tiene su propia estructura de datos en Realtime Database
- Estructura: /users/{userId}/tasks/{taskId}, /users/{userId}/habits/{habitId}
- Maneja errores de red sin bloquear la app (offline-first)
"""

import json
from datetime import datetime
from typing import List, Optional, Dict, Any
from dataclasses import dataclass

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    _requests_import_error = "requests no está instalado"

from app.data.database import Database
from app.data.models import Task, SubTask, Habit, HabitCompletion
from app.services.task_service import TaskService
from app.services.habit_service import HabitService
from app.services.firebase_auth_service import FirebaseAuthService


def _field_diff(local_dict: Dict[str, Any], remote_dict: Dict[str, Any], exclude_fields: List[str] = None) -> Dict[str, Any]:
    """
    Calcula la diferencia a nivel de campo entre dos diccionarios.
    
    Retorna un diccionario con solo los campos que han cambiado.
    Si un campo no existe en remote_dict, se considera como cambio.
    
    Args:
        local_dict: Diccionario con datos locales
        remote_dict: Diccionario con datos remotos (puede ser None)
        exclude_fields: Lista de campos a excluir del diff (ej: 'completions', 'subtasks')
    
    Returns:
        Diccionario con solo los campos modificados
    """
    if exclude_fields is None:
        exclude_fields = ['completions', 'subtasks', 'synced_at', 'userId']  # Campos que se sincronizan por separado
    
    if remote_dict is None:
        # No existe en remoto, retornar todos los campos (excepto excluidos)
        return {k: v for k, v in local_dict.items() if k not in exclude_fields}
    
    diff = {}
    for key, local_value in local_dict.items():
        if key in exclude_fields:
            continue  # Estos campos se sincronizan por separado
        
        remote_value = remote_dict.get(key)
        
        # Comparar valores
        if local_value != remote_value:
            diff[key] = local_value
    
    return diff


def _has_field_changes(local_dict: Dict[str, Any], remote_dict: Optional[Dict[str, Any]], exclude_fields: List[str] = None) -> bool:
    """
    Verifica si hay cambios a nivel de campo entre dos diccionarios.
    
    Args:
        local_dict: Diccionario con datos locales
        remote_dict: Diccionario con datos remotos (puede ser None)
        exclude_fields: Lista de campos a excluir del diff
    
    Returns:
        True si hay cambios, False si no
    """
    if remote_dict is None:
        return True  # No existe en remoto, hay cambios
    
    diff = _field_diff(local_dict, remote_dict, exclude_fields)
    return len(diff) > 0


@dataclass
class SyncResult:
    """Resultado de una operación de sincronización."""
    success: bool
    tasks_uploaded: int = 0
    tasks_downloaded: int = 0
    habits_uploaded: int = 0
    habits_downloaded: int = 0
    deletions_uploaded: int = 0
    deletions_downloaded: int = 0
    tasks_skipped: int = 0  # Tareas que no necesitaban sincronización
    habits_skipped: int = 0  # Hábitos que no necesitaban sincronización
    # Sincronización granular
    completions_uploaded: int = 0  # Completions de hábitos subidos
    completions_downloaded: int = 0  # Completions de hábitos descargados
    subtasks_uploaded: int = 0  # Subtareas subidas
    subtasks_downloaded: int = 0  # Subtareas descargadas
    fields_updated: int = 0  # Campos individuales actualizados
    no_changes: bool = False  # True si no hay cambios para sincronizar
    # Detalles específicos de cambios (para feedback preciso)
    changes_summary: List[str] = None  # Lista de cambios específicos
    errors: List[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.changes_summary is None:
            self.changes_summary = []
    
    def add_change(self, message: str):
        """Agrega un mensaje de cambio específico."""
        if message and message not in self.changes_summary:
            self.changes_summary.append(message)


class FirebaseSyncService:
    """
    Servicio para sincronizar datos entre SQLite local y Firebase Realtime Database.
    
    Decisiones técnicas:
    - Usa requests para llamar directamente a Firebase Realtime Database REST API
    - Evita dependencias problemáticas como pyrebase4/gcloud
    - Mantiene arquitectura offline-first: SQLite es la fuente de verdad local
    - Firebase es solo respaldo y sincronización entre dispositivos
    - Cada usuario tiene su propia estructura: /users/{userId}/tasks/{taskId}, /users/{userId}/habits/{habitId}
    - Resolución de conflictos: last-write-wins usando updated_at timestamp
    - No sobrescribe datos locales sin verificar timestamps
    """
    
    def __init__(
        self,
        auth_service: FirebaseAuthService,
        database: Optional[Database] = None
    ):
        """
        Inicializa el servicio de sincronización.
        
        Args:
            auth_service: Servicio de autenticación Firebase
            database: Instancia de Database para acceso local
        """
        if not REQUESTS_AVAILABLE:
            raise ImportError(
                f"requests no está disponible: {_requests_import_error}\n"
                "Instala con: pip install requests"
            )
        
        self.auth_service = auth_service
        self.db = database or Database()
        self.task_service = TaskService()
        self.habit_service = HabitService()
        from app.data.task_repository import TaskRepository
        self.task_repository = TaskRepository(self.db)  # Acceso directo al repositorio para sincronización
        self.database_url = None
        self._initialize_realtime_db()
    
    def _initialize_realtime_db(self) -> None:
        """
        Inicializa la configuración de Firebase Realtime Database.
        
        Decisiones técnicas:
        - Lee google-services.json para obtener la URL de Realtime Database
        - Usa requests para operaciones REST API (compatible con Android)
        - Realtime Database es adecuado para sincronización de datos estructurados
        """
        # Buscar google-services.json
        from pathlib import Path
        root_dir = Path(__file__).parent.parent.parent
        google_services_path = root_dir / 'google-services.json'
        
        if not google_services_path.exists():
            raise FileNotFoundError(
                "google-services.json no encontrado. "
                "Necesario para inicializar Firebase Realtime Database."
            )
        
        # Leer configuración
        with open(google_services_path, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        
        # URL de Realtime Database (ya configurada)
        self.database_url = "https://justice-driven-task-power-default-rtdb.firebaseio.com"
    
    def sync(self) -> SyncResult:
        """
        Sincroniza datos bidireccionalmente entre SQLite y Firebase.
        
        OFFLINE-FIRST: 
        - SQLite es la fuente de verdad principal. La app funciona completamente offline.
        - Firebase es solo respaldo y sincronización entre dispositivos.
        - Si no hay conexión o hay error, la app sigue funcionando normalmente.
        - La sincronización es completamente opcional y bajo demanda del usuario.
        
        Proceso:
        1. Verifica autenticación
        2. Sube datos locales a Firebase (desde SQLite)
        3. Descarga datos remotos desde Firebase
        4. Hace merge no destructivo en SQLite (no sobrescribe datos locales sin verificar timestamps)
        
        Returns:
            SyncResult con el resultado de la sincronización
        """
        result = SyncResult(success=False)
        
        # OFFLINE-FIRST: Verificar que Firebase esté disponible
        if not self.database_url:
            result.errors.append(
                "Firebase no está disponible. La app funciona completamente offline usando SQLite. "
                "Verifica tu conexión a internet y que google-services.json esté configurado."
            )
            return result
        
        # Verificar autenticación
        user = self.auth_service.get_current_user()
        if not user:
            result.errors.append("Usuario no autenticado. Inicia sesión para sincronizar.")
            return result
        
        user_id = user['uid']
        
        # Obtener token de autenticación para operaciones de base de datos
        id_token = self.auth_service.get_id_token()
        if not id_token:
            result.errors.append("Token de autenticación no encontrado. Por favor, inicia sesión nuevamente.")
            return result
        
        try:
            # 1. Subir datos locales a Firebase (desde SQLite) - SOLO si han cambiado (granular)
            upload_result = self._upload_local_data(user_id, id_token)
            result.tasks_uploaded = upload_result.get('tasks', 0)
            result.habits_uploaded = upload_result.get('habits', 0)
            result.deletions_uploaded = upload_result.get('deletions', 0)
            result.tasks_skipped = upload_result.get('tasks_skipped', 0)
            result.habits_skipped = upload_result.get('habits_skipped', 0)
            # Sincronización granular
            result.subtasks_uploaded = upload_result.get('subtasks', 0)
            result.completions_uploaded = upload_result.get('completions', 0)
            result.fields_updated = upload_result.get('fields_updated', 0)
            
            # 2. Descargar datos remotos desde Firebase (granular)
            download_result = self._download_remote_data(user_id, id_token)
            result.tasks_downloaded = download_result.get('tasks', 0)
            result.habits_downloaded = download_result.get('habits', 0)
            result.deletions_downloaded = download_result.get('deletions', 0)
            # Sincronización granular
            result.subtasks_downloaded = download_result.get('subtasks', 0)
            result.completions_downloaded = download_result.get('completions', 0)
            
            # 3. Verificar si hubo cambios para sincronizar
            total_changes = (
                result.tasks_uploaded + result.habits_uploaded + result.deletions_uploaded +
                result.tasks_downloaded + result.habits_downloaded + result.deletions_downloaded +
                result.subtasks_uploaded + result.completions_uploaded +
                result.subtasks_downloaded + result.completions_downloaded
            )
            
            # Generar resumen de cambios específicos
            if result.tasks_uploaded > 0:
                if result.tasks_uploaded == 1:
                    result.add_change("Se agregó una nueva tarea")
                else:
                    result.add_change(f"Se agregaron {result.tasks_uploaded} nuevas tareas")
            
            if result.habits_uploaded > 0:
                if result.habits_uploaded == 1:
                    result.add_change("Se agregó un nuevo hábito")
                else:
                    result.add_change(f"Se agregaron {result.habits_uploaded} nuevos hábitos")
            
            if result.fields_updated > 0:
                if result.fields_updated == 1:
                    result.add_change("Se actualizó un campo")
                else:
                    result.add_change(f"Se actualizaron {result.fields_updated} campos")
            
            if result.completions_uploaded > 0:
                if result.completions_uploaded == 1:
                    result.add_change("Se sincronizó un evento de calendario")
                else:
                    result.add_change(f"Se sincronizaron {result.completions_uploaded} eventos de calendario")
            
            if result.subtasks_uploaded > 0:
                if result.subtasks_uploaded == 1:
                    result.add_change("Se sincronizó una subtarea")
                else:
                    result.add_change(f"Se sincronizaron {result.subtasks_uploaded} subtareas")
            
            if result.deletions_uploaded > 0:
                if result.deletions_uploaded == 1:
                    result.add_change("Se eliminó un elemento")
                else:
                    result.add_change(f"Se eliminaron {result.deletions_uploaded} elementos")
            
            if total_changes == 0:
                result.no_changes = True
                result.add_change("No hay cambios para sincronizar")
            
            result.success = True
            
        except Exception as e:
            error_msg = str(e)
            # OFFLINE-FIRST: Manejar errores de red específicamente
            if 'network' in error_msg.lower() or 'connection' in error_msg.lower() or 'timeout' in error_msg.lower():
                result.errors.append(
                    "No hay conexión a internet. La app funciona completamente offline usando SQLite. "
                    "Intenta sincronizar cuando tengas conexión."
                )
            else:
                result.errors.append(f"Error durante sincronización: {error_msg}")
            result.success = False
        
        return result
    
    def upload_to_cloud(self) -> SyncResult:
        """
        Sube datos locales (SQLite) a Firebase Realtime Database.
        
        Returns:
            SyncResult con el resultado de la subida
        """
        result = SyncResult(success=False)
        
        if not self.database_url:
            result.errors.append(
                "Firebase no está disponible. Verifica tu conexión a internet."
            )
            return result
        
        user = self.auth_service.get_current_user()
        if not user:
            result.errors.append("Usuario no autenticado. Inicia sesión para sincronizar.")
            return result
        
        user_id = user['uid']
        id_token = self.auth_service.get_id_token()
        if not id_token:
            result.errors.append("Token de autenticación no encontrado. Por favor, inicia sesión nuevamente.")
            return result
        
        try:
            upload_result = self._upload_local_data(user_id, id_token)
            result.tasks_uploaded = upload_result.get('tasks', 0)
            result.habits_uploaded = upload_result.get('habits', 0)
            result.deletions_uploaded = upload_result.get('deletions', 0)
            result.tasks_skipped = upload_result.get('tasks_skipped', 0)
            result.habits_skipped = upload_result.get('habits_skipped', 0)
            
            # Verificar si hubo cambios para sincronizar
            total_changes = (
                result.tasks_uploaded + result.habits_uploaded + result.deletions_uploaded
            )
            
            if total_changes == 0:
                result.no_changes = True
            
            result.success = True
        except Exception as e:
            error_msg = str(e)
            if 'network' in error_msg.lower() or 'connection' in error_msg.lower() or 'timeout' in error_msg.lower():
                result.errors.append(
                    "No hay conexión a internet. Intenta cuando tengas conexión."
                )
            else:
                result.errors.append(f"Error al subir datos: {error_msg}")
            result.success = False
        
        return result
    
    def download_from_cloud(self) -> SyncResult:
        """
        Descarga datos desde Firebase Realtime Database y los fusiona con datos locales.
        
        Returns:
            SyncResult con el resultado de la descarga
        """
        result = SyncResult(success=False)
        
        if not self.database_url:
            result.errors.append(
                "Firebase no está disponible. Verifica tu conexión a internet."
            )
            return result
        
        user = self.auth_service.get_current_user()
        if not user:
            result.errors.append("Usuario no autenticado. Inicia sesión para sincronizar.")
            return result
        
        user_id = user['uid']
        id_token = self.auth_service.get_id_token()
        if not id_token:
            result.errors.append("Token de autenticación no encontrado. Por favor, inicia sesión nuevamente.")
            return result
        
        try:
            download_result = self._download_remote_data(user_id, id_token)
            result.tasks_downloaded = download_result.get('tasks', 0)
            result.habits_downloaded = download_result.get('habits', 0)
            result.deletions_downloaded = download_result.get('deletions', 0)
            result.success = True
        except Exception as e:
            error_msg = str(e)
            if 'network' in error_msg.lower() or 'connection' in error_msg.lower() or 'timeout' in error_msg.lower():
                result.errors.append(
                    "No hay conexión a internet. Intenta cuando tengas conexión."
                )
            else:
                result.errors.append(f"Error al descargar datos: {error_msg}")
            result.success = False
        
        return result
    
    def _upload_local_data(self, user_id: str, id_token: str) -> Dict[str, int]:
        """
        Sube datos locales desde SQLite a Firebase SOLO si han cambiado o no existen en la nube.
        
        ALGORITMO DE SINCRONIZACIÓN INTELIGENTE:
        1. Descarga datos remotos para comparar
        2. Compara cada dato local con su versión remota
        3. Solo sube si:
           - No existe en la nube (nuevo)
           - Ha sido modificado localmente (updated_at local > updated_at remoto)
        4. Evita duplicados usando IDs únicos persistentes
        
        OFFLINE-FIRST: Los datos se leen desde SQLite (fuente de verdad local)
        y se suben a Firebase como respaldo. Si hay error, los datos locales
        permanecen intactos en SQLite.
        
        Args:
            user_id: ID del usuario autenticado
            id_token: Token de autenticación de Firebase
        
        Returns:
            Diccionario con conteo de elementos subidos y omitidos
        """
        uploaded = {'tasks': 0, 'habits': 0, 'deletions': 0, 'tasks_skipped': 0, 'habits_skipped': 0}
        
        try:
            # PASO 1: Descargar datos remotos para comparar
            remote_tasks_dict = {}
            remote_habits_dict = {}
            
            try:
                remote_tasks = self._download_tasks(user_id, id_token)
                for task_data in remote_tasks:
                    task_id = task_data.get('id')
                    if task_id:
                        remote_tasks_dict[task_id] = task_data
            except:
                pass  # Si falla, asumir que no hay datos remotos
            
            try:
                remote_habits = self._download_habits(user_id, id_token)
                for habit_data in remote_habits:
                    habit_id = habit_data.get('id')
                    if habit_id:
                        remote_habits_dict[habit_id] = habit_data
            except:
                pass  # Si falla, asumir que no hay datos remotos
            
            # PASO 2: Comparar y subir tareas solo si han cambiado (granular)
            tasks = self.task_service.get_all_tasks()
            for task in tasks:
                remote_task = remote_tasks_dict.get(task.id)
                if self._should_upload_task(task, remote_task):
                    # Verificar qué campos cambiaron para mensaje específico
                    if remote_task:
                        diff = _field_diff(task.to_dict(), remote_task, exclude_fields=['subtasks', 'synced_at', 'userId'])
                        if diff:
                            # Solo subir si realmente hay cambios
                            if self._upload_task(user_id, task, id_token, remote_task):
                                uploaded['tasks'] += 1
                                uploaded['fields_updated'] = uploaded.get('fields_updated', 0) + len(diff)
                        else:
                            uploaded['tasks_skipped'] += 1
                    else:
                        # Nueva tarea
                        if self._upload_task(user_id, task, id_token, remote_task):
                            uploaded['tasks'] += 1
                else:
                    uploaded['tasks_skipped'] += 1
                
                # Sincronizar subtareas por separado (granular)
                subtasks_uploaded = self._upload_subtasks(user_id, task, id_token, remote_task)
                uploaded['subtasks'] = uploaded.get('subtasks', 0) + subtasks_uploaded
            
            # PASO 3: Comparar y subir hábitos solo si han cambiado (granular)
            habits = self.habit_service.get_all_habits()
            for habit in habits:
                remote_habit = remote_habits_dict.get(habit.id)
                if self._should_upload_habit(habit, remote_habit):
                    # Verificar qué campos cambiaron para mensaje específico
                    if remote_habit:
                        diff = _field_diff(habit.to_dict(), remote_habit, exclude_fields=['completions', 'synced_at', 'userId'])
                        if diff:
                            # Solo subir si realmente hay cambios
                            if self._upload_habit(user_id, habit, id_token, remote_habit):
                                uploaded['habits'] += 1
                                uploaded['fields_updated'] = uploaded.get('fields_updated', 0) + len(diff)
                        else:
                            uploaded['habits_skipped'] += 1
                    else:
                        # Nuevo hábito
                        if self._upload_habit(user_id, habit, id_token, remote_habit):
                            uploaded['habits'] += 1
                else:
                    uploaded['habits_skipped'] += 1
                
                # Sincronizar completions por separado (granular)
                completions_uploaded = self._upload_completions(user_id, habit, id_token, remote_habit)
                uploaded['completions'] = uploaded.get('completions', 0) + completions_uploaded
            
            # PASO 4: Subir eliminaciones pendientes (siempre se suben si están pendientes)
            deletions = self._get_pending_deletions()
            for deletion in deletions:
                self._upload_deletion(user_id, deletion, id_token)
                uploaded['deletions'] += 1
                # Marcar como sincronizada
                self._mark_deletion_synced(deletion['item_type'], deletion['item_id'])
        
        except Exception as e:
            raise RuntimeError(f"Error al subir datos locales: {str(e)}")
        
        return uploaded
    
    def _download_remote_data(self, user_id: str, id_token: str) -> Dict[str, int]:
        """
        Descarga datos remotos desde Firebase y los fusiona con datos locales en SQLite.
        
        OFFLINE-FIRST: 
        - Los datos se fusionan de forma no destructiva en SQLite
        - Solo se actualizan datos locales si los remotos son más recientes (verifica timestamps)
        - Aplica eliminaciones remotas localmente
        - Si hay error, los datos locales permanecen intactos
        
        Args:
            user_id: ID del usuario autenticado
            id_token: Token de autenticación de Firebase
        
        Returns:
            Diccionario con conteo de elementos descargados
        """
        downloaded = {'tasks': 0, 'habits': 0, 'deletions': 0, 'subtasks': 0, 'completions': 0}
        
        try:
            # Descargar tareas (sin subtareas, se descargan por separado)
            remote_tasks = self._download_tasks(user_id, id_token)
            for task_data in remote_tasks:
                if self._merge_task(task_data):
                    downloaded['tasks'] += 1
                
                # Descargar subtareas por separado (granular)
                task_id = task_data.get('id')
                if task_id:
                    subtasks_count = self._download_subtasks(user_id, task_id, id_token)
                    downloaded['subtasks'] += subtasks_count
            
            # Descargar hábitos (sin completions, se descargan por separado)
            remote_habits = self._download_habits(user_id, id_token)
            for habit_data in remote_habits:
                if self._merge_habit(habit_data):
                    downloaded['habits'] += 1
                
                # Descargar completions por separado (granular)
                habit_id = habit_data.get('id')
                if habit_id:
                    completions_count = self._download_completions(user_id, habit_id, id_token)
                    downloaded['completions'] += completions_count
            
            # Descargar y aplicar eliminaciones remotas
            remote_deletions = self._download_deletions(user_id, id_token)
            for deletion in remote_deletions:
                if self._apply_deletion(deletion):
                    downloaded['deletions'] += 1
        
        except Exception as e:
            raise RuntimeError(f"Error al descargar datos remotos: {str(e)}")
        
        return downloaded
    
    def _should_upload_task(self, local_task: Task, remote_task_data: Optional[Dict[str, Any]]) -> bool:
        """
        Determina si una tarea local debe subirse a la nube (solo campos del hábito, no subtareas).
        
        SINCRONIZACIÓN GRANULAR:
        - Verifica cambios a nivel de campo (title, description, priority, etc.)
        - Las subtareas se sincronizan por separado
        
        Args:
            local_task: Tarea local
            remote_task_data: Datos de la tarea remota (None si no existe)
        
        Returns:
            True si debe subirse, False si no necesita sincronización
        """
        # Si no existe en la nube, debe subirse
        if remote_task_data is None:
            return True
        
        # Verificar cambios a nivel de campo (excluyendo subtareas)
        local_dict = local_task.to_dict()
        return _has_field_changes(local_dict, remote_task_data, exclude_fields=['subtasks', 'synced_at', 'userId'])
    
    def _should_upload_habit(self, local_habit: Habit, remote_habit_data: Optional[Dict[str, Any]]) -> bool:
        """
        Determina si un hábito local debe subirse a la nube (solo campos del hábito, no completions).
        
        SINCRONIZACIÓN GRANULAR:
        - Verifica cambios a nivel de campo (title, description, frequency, etc.)
        - Las completions se sincronizan por separado
        
        Args:
            local_habit: Hábito local
            remote_habit_data: Datos del hábito remoto (None si no existe)
        
        Returns:
            True si debe subirse, False si no necesita sincronización
        """
        # Si no existe en la nube, debe subirse
        if remote_habit_data is None:
            return True
        
        # Verificar cambios a nivel de campo (excluyendo completions)
        local_dict = local_habit.to_dict()
        return _has_field_changes(local_dict, remote_habit_data, exclude_fields=['completions', 'synced_at', 'userId'])
    
    def _upload_task(self, user_id: str, task: Task, id_token: str, remote_task_data: Optional[Dict[str, Any]] = None) -> None:
        """
        Sube una tarea a Firebase Realtime Database usando REST API.
        
        SINCRONIZACIÓN GRANULAR:
        - Solo sube los campos que han cambiado (diff a nivel de campo)
        - Las subtareas se sincronizan por separado
        
        Args:
            user_id: ID del usuario autenticado
            task: Tarea a subir
            id_token: Token de autenticación de Firebase
            remote_task_data: Datos remotos para calcular diff (opcional)
        """
        try:
            task_dict = task.to_dict()
            
            # Calcular diff: solo campos modificados (excluyendo subtareas)
            if remote_task_data:
                task_dict = _field_diff(task_dict, remote_task_data, exclude_fields=['subtasks', 'synced_at', 'userId'])
                # Si no hay cambios, no subir
                if not task_dict:
                    return
            
            # Agregar metadatos
            task_dict['userId'] = user_id
            task_dict['synced_at'] = datetime.now().isoformat()
            task_dict['id'] = task.id  # Asegurar que el ID esté presente
            
            # Usar Firebase Realtime Database REST API
            # Estructura: /users/{userId}/tasks/{taskId}.json?auth={id_token}
            path = f"users/{user_id}/tasks/{task.id}.json"
            url = f"{self.database_url}/{path}"
            
            # Usar PATCH para actualizar solo campos modificados, o PUT si es nuevo
            if remote_task_data:
                # Actualizar solo campos modificados
                response = requests.patch(
                    url,
                    json=task_dict,
                    params={'auth': id_token},
                    timeout=10
                )
            else:
                # Nueva tarea, subir completa
                response = requests.put(
                    url,
                    json=task_dict,
                    params={'auth': id_token},
                    timeout=10
                )
            response.raise_for_status()
        
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Error al subir tarea {task.id}: {str(e)}")
    
    def _upload_habit(self, user_id: str, habit: Habit, id_token: str, remote_habit_data: Optional[Dict[str, Any]] = None) -> bool:
        """
        Sube un hábito a Firebase Realtime Database usando REST API.
        
        SINCRONIZACIÓN GRANULAR:
        - Solo sube los campos que han cambiado (diff a nivel de campo)
        - Las completions se sincronizan por separado
        
        Args:
            user_id: ID del usuario autenticado
            habit: Hábito a subir
            id_token: Token de autenticación de Firebase
            remote_habit_data: Datos remotos para calcular diff (opcional)
        
        Returns:
            True si se subió algo, False si no había cambios
        """
        try:
            habit_dict = habit.to_dict()
            
            # Calcular diff: solo campos modificados (excluyendo completions)
            if remote_habit_data:
                habit_dict = _field_diff(habit_dict, remote_habit_data, exclude_fields=['completions', 'synced_at', 'userId'])
                # Si no hay cambios, no subir
                if not habit_dict:
                    return False
            
            # Agregar metadatos
            habit_dict['userId'] = user_id
            habit_dict['synced_at'] = datetime.now().isoformat()
            habit_dict['id'] = habit.id  # Asegurar que el ID esté presente
            
            path = f"users/{user_id}/habits/{habit.id}.json"
            url = f"{self.database_url}/{path}"
            
            # Usar PATCH para actualizar solo campos modificados, o PUT si es nuevo
            if remote_habit_data:
                # Actualizar solo campos modificados
                response = requests.patch(
                    url,
                    json=habit_dict,
                    params={'auth': id_token},
                    timeout=10
                )
            else:
                # Nuevo hábito, subir completo
                response = requests.put(
                    url,
                    json=habit_dict,
                    params={'auth': id_token},
                    timeout=10
                )
            response.raise_for_status()
            return True
        
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Error al subir hábito {habit.id}: {str(e)}")
    
    def _upload_completions(self, user_id: str, habit: Habit, id_token: str, remote_habit_data: Optional[Dict[str, Any]] = None) -> int:
        """
        Sincroniza completions de un hábito por separado (sincronización granular).
        
        Solo sube/actualiza completions que han cambiado o no existen en la nube.
        
        Args:
            user_id: ID del usuario autenticado
            habit: Hábito local
            id_token: Token de autenticación de Firebase
            remote_habit_data: Datos remotos del hábito (opcional)
        
        Returns:
            Número de completions subidas
        """
        uploaded_count = 0
        
        try:
            # Obtener completions locales
            from app.data.habit_repository import HabitRepository
            habit_repo = HabitRepository(self.db)
            local_completions = habit_repo.get_completions(habit.id)
            
            # Obtener completions remotos
            remote_completions_dict = {}
            if remote_habit_data:
                remote_completions_list = remote_habit_data.get('completions', [])
                for comp in remote_completions_list:
                    comp_id = comp.get('id')
                    if comp_id:
                        remote_completions_dict[comp_id] = comp
            
            # Sincronizar cada completion local
            for local_completion in local_completions:
                remote_completion = remote_completions_dict.get(local_completion.id) if local_completion.id else None
                
                # Subir si no existe en remoto o si es más reciente
                should_upload = False
                if remote_completion is None:
                    should_upload = True  # No existe en remoto
                elif local_completion.created_at:
                    remote_created = remote_completion.get('created_at')
                    if remote_created:
                        local_created_str = local_completion.created_at.isoformat()
                        if local_created_str > remote_created:
                            should_upload = True  # Local es más reciente
                    else:
                        should_upload = True  # Remoto no tiene timestamp
                
                if should_upload:
                    # Subir completion individual
                    completion_dict = local_completion.to_dict()
                    completion_dict['userId'] = user_id
                    completion_dict['synced_at'] = datetime.now().isoformat()
                    
                    # Estructura: /users/{userId}/habits/{habitId}/completions/{completionId}.json
                    completion_id = local_completion.id or f"temp_{datetime.now().timestamp()}"
                    path = f"users/{user_id}/habits/{habit.id}/completions/{completion_id}.json"
                    url = f"{self.database_url}/{path}"
                    
                    response = requests.put(
                        url,
                        json=completion_dict,
                        params={'auth': id_token},
                        timeout=10
                    )
                    response.raise_for_status()
                    uploaded_count += 1
        
        except Exception as e:
            # No fallar toda la sincronización por un error en completions
            print(f"Advertencia: Error al sincronizar completions del hábito {habit.id}: {str(e)}")
        
        return uploaded_count
    
    def _upload_subtasks(self, user_id: str, task: Task, id_token: str, remote_task_data: Optional[Dict[str, Any]] = None) -> int:
        """
        Sincroniza subtareas de una tarea por separado (sincronización granular).
        
        Solo sube/actualiza subtareas que han cambiado o no existen en la nube.
        
        Args:
            user_id: ID del usuario autenticado
            task: Tarea local
            id_token: Token de autenticación de Firebase
            remote_task_data: Datos remotos de la tarea (opcional)
        
        Returns:
            Número de subtareas subidas
        """
        uploaded_count = 0
        
        try:
            # Obtener subtareas locales
            local_subtasks = task.subtasks if task.subtasks else []
            
            # Obtener subtareas remotas
            remote_subtasks_dict = {}
            if remote_task_data:
                remote_subtasks_list = remote_task_data.get('subtasks', [])
                for subtask in remote_subtasks_list:
                    subtask_id = subtask.get('id')
                    if subtask_id:
                        remote_subtasks_dict[subtask_id] = subtask
            
            # Sincronizar cada subtarea local
            for local_subtask in local_subtasks:
                remote_subtask = remote_subtasks_dict.get(local_subtask.id) if local_subtask.id else None
                
                # Verificar si debe subirse (diff a nivel de campo)
                should_upload = False
                if remote_subtask is None:
                    should_upload = True  # No existe en remoto
                else:
                    # Verificar cambios a nivel de campo
                    local_subtask_dict = local_subtask.to_dict()
                    if _has_field_changes(local_subtask_dict, remote_subtask, exclude_fields=['synced_at', 'userId']):
                        should_upload = True
                
                if should_upload:
                    # Calcular diff si existe remoto
                    subtask_dict = local_subtask.to_dict()
                    if remote_subtask:
                        subtask_dict = _field_diff(subtask_dict, remote_subtask, exclude_fields=['synced_at', 'userId'])
                        if not subtask_dict:
                            continue  # No hay cambios
                    
                    # Agregar metadatos
                    subtask_dict['userId'] = user_id
                    subtask_dict['synced_at'] = datetime.now().isoformat()
                    subtask_dict['id'] = local_subtask.id
                    subtask_dict['task_id'] = task.id
                    
                    # Estructura: /users/{userId}/tasks/{taskId}/subtasks/{subtaskId}.json
                    subtask_id = local_subtask.id or f"temp_{datetime.now().timestamp()}"
                    path = f"users/{user_id}/tasks/{task.id}/subtasks/{subtask_id}.json"
                    url = f"{self.database_url}/{path}"
                    
                    # Usar PATCH si existe remoto, PUT si es nuevo
                    if remote_subtask:
                        response = requests.patch(
                            url,
                            json=subtask_dict,
                            params={'auth': id_token},
                            timeout=10
                        )
                    else:
                        response = requests.put(
                            url,
                            json=subtask_dict,
                            params={'auth': id_token},
                            timeout=10
                        )
                    response.raise_for_status()
                    uploaded_count += 1
        
        except Exception as e:
            # No fallar toda la sincronización por un error en subtareas
            print(f"Advertencia: Error al sincronizar subtareas de la tarea {task.id}: {str(e)}")
        
        return uploaded_count
    
    def _download_tasks(self, user_id: str, id_token: str) -> List[Dict[str, Any]]:
        """
        Descarga todas las tareas del usuario desde Firebase Realtime Database usando REST API.
        
        Args:
            user_id: ID del usuario autenticado
            id_token: Token de autenticación de Firebase
        
        Returns:
            Lista de diccionarios con datos de tareas
        """
        try:
            path = f"users/{user_id}/tasks.json"
            url = f"{self.database_url}/{path}"
            
            response = requests.get(
                url,
                params={'auth': id_token},
                timeout=10
            )
            response.raise_for_status()
            
            tasks_data = response.json()
            if not tasks_data:
                return []
            
            tasks = []
            if isinstance(tasks_data, dict):
                for task_id, task_data in tasks_data.items():
                    if isinstance(task_data, dict):
                        # Asegurar que el ID de la tarea esté presente en los datos
                        if 'id' not in task_data or task_data['id'] is None:
                            task_data['id'] = int(task_id) if task_id.isdigit() else None
                        tasks.append(task_data)
            
            return tasks
        
        except requests.exceptions.RequestException as e:
            if hasattr(e, 'response') and e.response is not None and e.response.status_code == 404:
                # No hay datos aún, retornar lista vacía
                return []
            raise RuntimeError(f"Error al descargar tareas: {str(e)}")
    
    def _download_habits(self, user_id: str, id_token: str) -> List[Dict[str, Any]]:
        """
        Descarga todos los hábitos del usuario desde Firebase Realtime Database usando REST API.
        
        Args:
            user_id: ID del usuario autenticado
            id_token: Token de autenticación de Firebase
        
        Returns:
            Lista de diccionarios con datos de hábitos
        """
        try:
            path = f"users/{user_id}/habits.json"
            url = f"{self.database_url}/{path}"
            
            response = requests.get(
                url,
                params={'auth': id_token},
                timeout=10
            )
            response.raise_for_status()
            
            habits_data = response.json()
            if not habits_data:
                return []
            
            habits = []
            if isinstance(habits_data, dict):
                for habit_id, habit_data in habits_data.items():
                    if isinstance(habit_data, dict):
                        # Asegurar que el ID del hábito esté presente en los datos
                        if 'id' not in habit_data or habit_data['id'] is None:
                            habit_data['id'] = int(habit_id) if habit_id.isdigit() else None
                        habits.append(habit_data)
            
            return habits
        
        except requests.exceptions.RequestException as e:
            if hasattr(e, 'response') and e.response is not None and e.response.status_code == 404:
                # No hay datos aún, retornar lista vacía
                return []
            raise RuntimeError(f"Error al descargar hábitos: {str(e)}")
    
    def _download_completions(self, user_id: str, habit_id: int, id_token: str) -> int:
        """
        Descarga completions de un hábito desde Firebase (sincronización granular).
        
        Args:
            user_id: ID del usuario autenticado
            habit_id: ID del hábito
            id_token: Token de autenticación de Firebase
        
        Returns:
            Número de completions descargadas
        """
        downloaded_count = 0
        
        try:
            # Estructura: /users/{userId}/habits/{habitId}/completions.json
            path = f"users/{user_id}/habits/{habit_id}/completions.json"
            url = f"{self.database_url}/{path}"
            
            response = requests.get(
                url,
                params={'auth': id_token},
                timeout=10
            )
            response.raise_for_status()
            
            completions_data = response.json()
            if not completions_data:
                return 0
            
            # Procesar cada completion
            from app.data.habit_repository import HabitRepository
            habit_repo = HabitRepository(self.db)
            
            if isinstance(completions_data, dict):
                for completion_id, completion_data in completions_data.items():
                    if isinstance(completion_data, dict):
                        # Crear completion desde datos remotos
                        completion = HabitCompletion.from_dict(completion_data)
                        completion.habit_id = habit_id
                        
                        # Verificar si ya existe localmente
                        local_completion = None
                        if completion.id:
                            try:
                                # Buscar por ID
                                local_completions = habit_repo.get_completions(habit_id)
                                local_completion = next((c for c in local_completions if c.id == completion.id), None)
                            except:
                                pass
                        
                        if local_completion:
                            # Ya existe, comparar timestamps
                            local_created = local_completion.created_at.isoformat() if local_completion.created_at else None
                            remote_created = completion_data.get('created_at')
                            
                            if remote_created and local_created:
                                if remote_created > local_created:
                                    # Remoto es más reciente, actualizar
                                    habit_repo.delete_completion(local_completion.id)
                                    habit_repo.create_completion(completion)
                                    downloaded_count += 1
                        else:
                            # No existe localmente, crear
                            # Verificar si existe por fecha (evitar duplicados)
                            completion_date = completion.completion_date.date() if completion.completion_date else None
                            if completion_date and not habit_repo.has_completion_for_date(habit_id, completion_date):
                                habit_repo.create_completion(completion)
                                downloaded_count += 1
        
        except requests.exceptions.RequestException as e:
            if hasattr(e, 'response') and e.response is not None and e.response.status_code == 404:
                # No hay completions aún
                return 0
            # No fallar toda la sincronización por un error en completions
            print(f"Advertencia: Error al descargar completions del hábito {habit_id}: {str(e)}")
        
        return downloaded_count
    
    def _download_subtasks(self, user_id: str, task_id: int, id_token: str) -> int:
        """
        Descarga subtareas de una tarea desde Firebase (sincronización granular).
        
        Args:
            user_id: ID del usuario autenticado
            task_id: ID de la tarea
            id_token: Token de autenticación de Firebase
        
        Returns:
            Número de subtareas descargadas
        """
        downloaded_count = 0
        
        try:
            # Estructura: /users/{userId}/tasks/{taskId}/subtasks.json
            path = f"users/{user_id}/tasks/{task_id}/subtasks.json"
            url = f"{self.database_url}/{path}"
            
            response = requests.get(
                url,
                params={'auth': id_token},
                timeout=10
            )
            response.raise_for_status()
            
            subtasks_data = response.json()
            if not subtasks_data:
                return 0
            
            # Obtener tarea local
            try:
                local_task = self.task_service.get_task(task_id)
            except:
                return 0  # Tarea no existe localmente
            
            # Procesar cada subtarea
            if isinstance(subtasks_data, dict):
                for subtask_id, subtask_data in subtasks_data.items():
                    if isinstance(subtask_data, dict):
                        # Crear subtarea desde datos remotos
                        subtask = SubTask.from_dict(subtask_data)
                        subtask.task_id = task_id
                        
                        # Verificar si ya existe localmente
                        local_subtask = None
                        if subtask.id:
                            local_subtask = next((s for s in local_task.subtasks if s.id == subtask.id), None)
                        
                        if local_subtask:
                            # Ya existe, comparar timestamps y actualizar si remoto es más reciente
                            local_updated = local_subtask.updated_at.isoformat() if local_subtask.updated_at else None
                            remote_updated = subtask_data.get('updated_at')
                            
                            if remote_updated and local_updated:
                                if remote_updated > local_updated:
                                    # Remoto es más reciente, actualizar
                                    # Aplicar diff: solo campos modificados
                                    local_dict = local_subtask.to_dict()
                                    diff = _field_diff(subtask_data, local_dict, exclude_fields=['synced_at', 'userId'])
                                    if diff:
                                        # Actualizar campos modificados
                                        for key, value in diff.items():
                                            setattr(local_subtask, key, value)
                                        self.task_repository.update(local_task)
                                        downloaded_count += 1
                        else:
                            # No existe localmente, crear
                            if subtask.id:
                                # Crear con ID específico
                                self.task_repository._sync_subtasks(task_id, [subtask])
                                downloaded_count += 1
        
        except requests.exceptions.RequestException as e:
            if hasattr(e, 'response') and e.response is not None and e.response.status_code == 404:
                # No hay subtareas aún
                return 0
            # No fallar toda la sincronización por un error en subtareas
            print(f"Advertencia: Error al descargar subtareas de la tarea {task_id}: {str(e)}")
        
        return downloaded_count
    
    def _merge_task(self, remote_task_data: Dict[str, Any]) -> bool:
        """
        Fusiona una tarea remota con los datos locales (no destructivo).
        
        Decisiones técnicas:
        - Compara timestamps (updated_at) para resolver conflictos
        - Solo crea nueva tarea si no existe localmente
        - Si existe, solo actualiza si la remota es más reciente
        - Mantiene el ID remoto para evitar duplicaciones
        - Sincroniza las subtareas
        
        Returns:
            True si se fusionó/creó una nueva tarea, False si se ignoró
        """
        try:
            remote_id = remote_task_data.get('id')
            remote_updated = remote_task_data.get('updated_at')
            
            if not remote_id:
                # Sin ID remoto, no se puede sincronizar
                return False
            
            # Buscar tarea local por ID
            local_task = None
            try:
                local_task = self.task_service.get_task(remote_id)
            except:
                pass
            
            if local_task:
                # Tarea existe localmente, comparar timestamps
                local_updated = local_task.updated_at.isoformat() if local_task.updated_at else None
                
                if remote_updated and local_updated:
                    # Solo actualizar si la remota es más reciente
                    if remote_updated > local_updated:
                        # Actualizar tarea local con datos remotos (incluyendo subtareas)
                        task = Task.from_dict(remote_task_data)
                        task.id = remote_id  # Asegurar que se mantiene el ID
                        self.task_service.update_task(task)
                        return True
                return False  # Ignorar si la local es más reciente o igual
            else:
                # Tarea no existe localmente, crearla con el ID remoto
                task = Task.from_dict(remote_task_data)
                # Mantener el ID remoto para evitar duplicaciones
                task.id = remote_id
                # Usar el repositorio directamente para crear con ID específico
                created_task = self.task_repository.create(task)
                # Sincronizar subtareas si existen
                if task.subtasks:
                    self.task_repository._sync_subtasks(created_task.id, task.subtasks)
                return True
        
        except Exception as e:
            # Error al fusionar, ignorar esta tarea
            return False
    
    def _merge_habit(self, remote_habit_data: Dict[str, Any]) -> bool:
        """
        Fusiona un hábito remoto con los datos locales (no destructivo).
        
        Returns:
            True si se fusionó/creó un nuevo hábito, False si se ignoró
        """
        try:
            remote_id = remote_habit_data.get('id')
            remote_updated = remote_habit_data.get('updated_at')
            
            # Buscar hábito local por ID
            local_habit = None
            if remote_id:
                try:
                    local_habit = self.habit_service.get_habit(remote_id)
                except:
                    pass
            
            if local_habit:
                # Hábito existe localmente, comparar timestamps
                local_updated = local_habit.updated_at.isoformat() if local_habit.updated_at else None
                
                if remote_updated and local_updated:
                    if remote_updated > local_updated:
                        # Actualizar hábito local con datos remotos
                        habit = Habit.from_dict(remote_habit_data)
                        self.habit_service.update_habit(habit)
                        return True
                return False
            else:
                # Hábito no existe localmente, crearlo con el ID remoto para evitar duplicados
                habit = Habit.from_dict(remote_habit_data)
                # IMPORTANTE: Mantener el ID remoto para evitar duplicaciones
                remote_id = remote_habit_data.get('id')
                if remote_id:
                    # Usar el repositorio directamente para crear con ID específico
                    # El repositorio ahora soporta crear con ID específico
                    from app.data.habit_repository import HabitRepository
                    habit_repo = HabitRepository(self.db)
                    # Crear hábito con ID remoto (el repositorio maneja la verificación de duplicados)
                    habit.id = remote_id
                    created_habit = habit_repo.create(habit)
                    return True
                else:
                    # Sin ID remoto, crear normalmente
                    self.habit_service.create_habit(
                        habit.title,
                        habit.description,
                        habit.frequency,
                        habit.target_days
                    )
                    return True
        
        except Exception as e:
            return False
    
    def _get_pending_deletions(self) -> List[Dict[str, Any]]:
        """
        Obtiene las eliminaciones pendientes de sincronizar desde la base de datos local.
        
        Returns:
            Lista de diccionarios con información de eliminaciones pendientes
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT item_type, item_id, deleted_at
                FROM deleted_items
                WHERE synced_at IS NULL
                ORDER BY deleted_at ASC
            ''')
            
            deletions = []
            for row in cursor.fetchall():
                deletions.append({
                    'item_type': row['item_type'],
                    'item_id': row['item_id'],
                    'deleted_at': row['deleted_at']
                })
            
            return deletions
        finally:
            conn.close()
    
    def _upload_deletion(self, user_id: str, deletion: Dict[str, Any], id_token: str) -> None:
        """
        Sube una eliminación a Firebase Realtime Database.
        
        Args:
            user_id: ID del usuario autenticado
            deletion: Diccionario con información de la eliminación (item_type, item_id, deleted_at)
            id_token: Token de autenticación de Firebase
        """
        try:
            item_type = deletion['item_type']
            item_id = deletion['item_id']
            deleted_at = deletion['deleted_at']
            
            # Estructura: /users/{userId}/deletions/{item_type}/{item_id}.json
            path = f"users/{user_id}/deletions/{item_type}/{item_id}.json"
            url = f"{self.database_url}/{path}"
            
            deletion_data = {
                'item_type': item_type,
                'item_id': item_id,
                'deleted_at': deleted_at,
                'synced_at': datetime.now().isoformat()
            }
            
            response = requests.put(
                url,
                json=deletion_data,
                params={'auth': id_token},
                timeout=10
            )
            response.raise_for_status()
            
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Error al subir eliminación {item_type}/{item_id}: {str(e)}")
    
    def _mark_deletion_synced(self, item_type: str, item_id: int) -> None:
        """
        Marca una eliminación como sincronizada en la base de datos local.
        
        Args:
            item_type: Tipo de elemento ('task' o 'habit')
            item_id: ID del elemento eliminado
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            synced_at = datetime.now().isoformat()
            cursor.execute('''
                UPDATE deleted_items
                SET synced_at = ?
                WHERE item_type = ? AND item_id = ?
            ''', (synced_at, item_type, item_id))
            
            conn.commit()
        finally:
            conn.close()
    
    def _download_deletions(self, user_id: str, id_token: str) -> List[Dict[str, Any]]:
        """
        Descarga todas las eliminaciones del usuario desde Firebase Realtime Database.
        
        Args:
            user_id: ID del usuario autenticado
            id_token: Token de autenticación de Firebase
        
        Returns:
            Lista de diccionarios con datos de eliminaciones
        """
        try:
            path = f"users/{user_id}/deletions.json"
            url = f"{self.database_url}/{path}"
            
            response = requests.get(
                url,
                params={'auth': id_token},
                timeout=10
            )
            response.raise_for_status()
            
            deletions_data = response.json()
            if not deletions_data:
                return []
            
            deletions = []
            if isinstance(deletions_data, dict):
                # Estructura: {item_type: {item_id: {deleted_at, synced_at}}}
                for item_type, items in deletions_data.items():
                    if isinstance(items, dict):
                        for item_id, deletion_data in items.items():
                            if isinstance(deletion_data, dict):
                                deletion_data['item_type'] = item_type
                                deletion_data['item_id'] = int(item_id)
                                deletions.append(deletion_data)
            
            return deletions
        
        except requests.exceptions.RequestException as e:
            if hasattr(e, 'response') and e.response is not None and e.response.status_code == 404:
                # No hay eliminaciones aún, retornar lista vacía
                return []
            raise RuntimeError(f"Error al descargar eliminaciones: {str(e)}")
    
    def _apply_deletion(self, deletion: Dict[str, Any]) -> bool:
        """
        Aplica una eliminación remota localmente si es más reciente que la local.
        
        Args:
            deletion: Diccionario con información de la eliminación remota
        
        Returns:
            True si se aplicó la eliminación, False si se ignoró
        """
        try:
            item_type = deletion.get('item_type')
            item_id = deletion.get('item_id')
            remote_deleted_at = deletion.get('deleted_at')
            
            if not item_type or not item_id or not remote_deleted_at:
                return False
            
            # Verificar si el elemento existe localmente
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            try:
                # Verificar si ya está eliminado localmente
                cursor.execute('''
                    SELECT deleted_at FROM deleted_items
                    WHERE item_type = ? AND item_id = ?
                ''', (item_type, item_id))
                
                local_deletion = cursor.fetchone()
                
                if local_deletion:
                    local_deleted_at = local_deletion['deleted_at']
                    # Solo aplicar si la eliminación remota es más reciente
                    if remote_deleted_at <= local_deleted_at:
                        return False
                
                # Aplicar la eliminación localmente
                if item_type == 'task':
                    # Eliminar la tarea
                    cursor.execute('DELETE FROM tasks WHERE id = ?', (item_id,))
                    deleted = cursor.rowcount > 0
                elif item_type == 'habit':
                    # Eliminar el hábito
                    cursor.execute('DELETE FROM habits WHERE id = ?', (item_id,))
                    deleted = cursor.rowcount > 0
                else:
                    return False
                
                if deleted:
                    # Registrar la eliminación en deleted_items
                    cursor.execute('''
                        INSERT OR REPLACE INTO deleted_items (item_type, item_id, deleted_at, synced_at)
                        VALUES (?, ?, ?, ?)
                    ''', (item_type, item_id, remote_deleted_at, datetime.now().isoformat()))
                    
                    conn.commit()
                    return True
                
                return False
            finally:
                conn.close()
        
        except Exception as e:
            # Error al aplicar eliminación, ignorar
            return False
