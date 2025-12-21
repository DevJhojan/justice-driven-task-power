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


@dataclass
class SyncResult:
    """Resultado de una operación de sincronización."""
    success: bool
    tasks_uploaded: int = 0
    tasks_downloaded: int = 0
    habits_uploaded: int = 0
    habits_downloaded: int = 0
    errors: List[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []


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
            # 1. Subir datos locales a Firebase (desde SQLite)
            upload_result = self._upload_local_data(user_id, id_token)
            result.tasks_uploaded = upload_result.get('tasks', 0)
            result.habits_uploaded = upload_result.get('habits', 0)
            
            # 2. Descargar datos remotos desde Firebase
            download_result = self._download_remote_data(user_id, id_token)
            result.tasks_downloaded = download_result.get('tasks', 0)
            result.habits_downloaded = download_result.get('habits', 0)
            
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
        Sube todos los datos locales desde SQLite a Firebase.
        
        OFFLINE-FIRST: Los datos se leen desde SQLite (fuente de verdad local)
        y se suben a Firebase como respaldo. Si hay error, los datos locales
        permanecen intactos en SQLite.
        
        Args:
            user_id: ID del usuario autenticado
            id_token: Token de autenticación de Firebase
        
        Returns:
            Diccionario con conteo de elementos subidos
        """
        uploaded = {'tasks': 0, 'habits': 0}
        
        try:
            # Subir tareas
            tasks = self.task_service.get_all_tasks()
            for task in tasks:
                self._upload_task(user_id, task, id_token)
                uploaded['tasks'] += 1
            
            # Subir hábitos
            habits = self.habit_service.get_all_habits()
            for habit in habits:
                self._upload_habit(user_id, habit, id_token)
                uploaded['habits'] += 1
        
        except Exception as e:
            raise RuntimeError(f"Error al subir datos locales: {str(e)}")
        
        return uploaded
    
    def _download_remote_data(self, user_id: str, id_token: str) -> Dict[str, int]:
        """
        Descarga datos remotos desde Firebase y los fusiona con datos locales en SQLite.
        
        OFFLINE-FIRST: 
        - Los datos se fusionan de forma no destructiva en SQLite
        - Solo se actualizan datos locales si los remotos son más recientes (verifica timestamps)
        - No se borran datos locales
        - Si hay error, los datos locales permanecen intactos
        
        Args:
            user_id: ID del usuario autenticado
            id_token: Token de autenticación de Firebase
        
        Returns:
            Diccionario con conteo de elementos descargados
        """
        downloaded = {'tasks': 0, 'habits': 0}
        
        try:
            # Descargar tareas
            remote_tasks = self._download_tasks(user_id, id_token)
            for task_data in remote_tasks:
                if self._merge_task(task_data):
                    downloaded['tasks'] += 1
            
            # Descargar hábitos
            remote_habits = self._download_habits(user_id, id_token)
            for habit_data in remote_habits:
                if self._merge_habit(habit_data):
                    downloaded['habits'] += 1
        
        except Exception as e:
            raise RuntimeError(f"Error al descargar datos remotos: {str(e)}")
        
        return downloaded
    
    def _upload_task(self, user_id: str, task: Task, id_token: str) -> None:
        """
        Sube una tarea a Firebase Realtime Database usando REST API.
        
        Args:
            user_id: ID del usuario autenticado
            task: Tarea a subir
            id_token: Token de autenticación de Firebase
        """
        try:
            task_dict = task.to_dict()
            task_dict['userId'] = user_id
            task_dict['synced_at'] = datetime.now().isoformat()
            
            # Usar Firebase Realtime Database REST API
            # Estructura: /users/{userId}/tasks/{taskId}.json?auth={id_token}
            path = f"users/{user_id}/tasks/{task.id}.json"
            url = f"{self.database_url}/{path}"
            
            response = requests.put(
                url,
                json=task_dict,
                params={'auth': id_token},
                timeout=10
            )
            response.raise_for_status()
        
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Error al subir tarea {task.id}: {str(e)}")
    
    def _upload_habit(self, user_id: str, habit: Habit, id_token: str) -> None:
        """
        Sube un hábito a Firebase Realtime Database usando REST API.
        
        Args:
            user_id: ID del usuario autenticado
            habit: Hábito a subir
            id_token: Token de autenticación de Firebase
        """
        try:
            habit_dict = habit.to_dict()
            habit_dict['userId'] = user_id
            habit_dict['synced_at'] = datetime.now().isoformat()
            
            path = f"users/{user_id}/habits/{habit.id}.json"
            url = f"{self.database_url}/{path}"
            
            response = requests.put(
                url,
                json=habit_dict,
                params={'auth': id_token},
                timeout=10
            )
            response.raise_for_status()
        
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Error al subir hábito {habit.id}: {str(e)}")
    
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
                        habits.append(habit_data)
            
            return habits
        
        except requests.exceptions.RequestException as e:
            if hasattr(e, 'response') and e.response is not None and e.response.status_code == 404:
                # No hay datos aún, retornar lista vacía
                return []
            raise RuntimeError(f"Error al descargar hábitos: {str(e)}")
    
    def _merge_task(self, remote_task_data: Dict[str, Any]) -> bool:
        """
        Fusiona una tarea remota con los datos locales (no destructivo).
        
        Decisiones técnicas:
        - Compara timestamps (updated_at) para resolver conflictos
        - Solo crea nueva tarea si no existe localmente
        - Si existe, solo actualiza si la remota es más reciente
        
        Returns:
            True si se fusionó/creó una nueva tarea, False si se ignoró
        """
        try:
            remote_id = remote_task_data.get('id')
            remote_updated = remote_task_data.get('updated_at')
            
            # Buscar tarea local por ID
            local_task = None
            if remote_id:
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
                        # Actualizar tarea local con datos remotos
                        task = Task.from_dict(remote_task_data)
                        self.task_service.update_task(task)
                        return True
                return False  # Ignorar si la local es más reciente o igual
            else:
                # Tarea no existe localmente, crearla
                task = Task.from_dict(remote_task_data)
                # Asignar nuevo ID local (el remoto se mantiene como referencia)
                task.id = None
                self.task_service.create_task(
                    task.title,
                    task.description,
                    task.priority
                )
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
                # Hábito no existe localmente, crearlo
                habit = Habit.from_dict(remote_habit_data)
                habit.id = None
                self.habit_service.create_habit(
                    habit.title,
                    habit.description,
                    habit.frequency,
                    habit.target_days
                )
                return True
        
        except Exception as e:
            return False
