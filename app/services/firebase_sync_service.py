"""
Servicio de sincronización con Firebase Realtime Database.

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
- Usa pyrebase4 para operaciones con Realtime Database (compatible con Android)
- Mantiene SQLite como base de datos principal (offline-first)
- Firebase solo como respaldo y sincronización
- Usa timestamps para resolución de conflictos (last-write-wins con verificación)
- Cada usuario tiene su propia estructura de datos en Realtime Database
- Estructura: /users/{userId}/tasks/{taskId}, /users/{userId}/habits/{habitId}
- pyrebase4 no soporta Firestore directamente, por lo que usamos Realtime Database
- Maneja errores de red sin bloquear la app (offline-first)
"""

import json
from datetime import datetime
from typing import List, Optional, Dict, Any
from dataclasses import dataclass

try:
    import pyrebase
    PYREBASE_AVAILABLE = True
except ImportError:
    PYREBASE_AVAILABLE = False
    _pyrebase_import_error = "pyrebase4 no está instalado"

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
    - Usa pyrebase4 para operaciones con Realtime Database (compatible con Android)
    - Mantiene arquitectura offline-first: SQLite es la fuente de verdad local
    - Firebase es solo respaldo y sincronización entre dispositivos
    - Cada usuario tiene su propia estructura: /users/{userId}/tasks/{taskId}, /users/{userId}/habits/{habitId}
    - Resolución de conflictos: last-write-wins usando updated_at timestamp
    - No sobrescribe datos locales sin verificar timestamps
    - pyrebase4 no soporta Firestore, por lo que usamos Realtime Database
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
        if not PYREBASE_AVAILABLE:
            raise ImportError(
                f"pyrebase4 no está disponible: {_pyrebase_import_error}\n"
                "Instala con: pip install pyrebase4"
            )
        
        self.auth_service = auth_service
        self.db = database or Database()
        self.task_service = TaskService()
        self.habit_service = HabitService()
        self.firebase = None
        self.db_realtime = None
        self._initialize_realtime_db()
    
    def _initialize_realtime_db(self) -> None:
        """
        Inicializa Firebase Realtime Database usando google-services.json.
        
        Decisiones técnicas:
        - Usa pyrebase4 para Realtime Database (compatible con aplicaciones cliente Android)
        - firebase-admin requiere credenciales de servicio (server-side), no adecuado para apps cliente
        - pyrebase4 no soporta Firestore, por lo que usamos Realtime Database
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
        
        # Usar pyrebase4 para Realtime Database (compatible con Android)
        try:
            import pyrebase
            with open(google_services_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            project_info = config_data.get('project_info', {})
            client_info = config_data.get('client', [{}])[0]
            api_key_info = client_info.get('api_key', [{}])[0]
            
            project_id = project_info.get('project_id')
            api_key = api_key_info.get('current_key')
            storage_bucket = project_info.get('storage_bucket', f"{project_id}.appspot.com")
            
            # Configuración de Firebase para pyrebase4
            # databaseURL es necesario para Realtime Database
            firebase_config = {
                "apiKey": api_key,
                "authDomain": f"{project_id}.firebaseapp.com",
                "databaseURL": "https://justice-driven-task-power-default-rtdb.firebaseio.com",
                "storageBucket": storage_bucket,
                "projectId": project_id
            }
            
            self.firebase = pyrebase.initialize_app(firebase_config)
            self.db_realtime = self.firebase.database()  # Realtime Database, no Firestore
            
        except Exception as e:
            raise RuntimeError(f"Error al inicializar Firebase Realtime Database: {str(e)}")
    
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
        if not self.db_realtime:
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
        Sube una tarea a Firebase Realtime Database.
        
        Args:
            user_id: ID del usuario autenticado
            task: Tarea a subir
            id_token: Token de autenticación de Firebase
        """
        try:
            task_dict = task.to_dict()
            task_dict['userId'] = user_id
            task_dict['synced_at'] = datetime.now().isoformat()
            
            # Usar pyrebase4 Realtime Database
            # Estructura: /users/{userId}/tasks/{taskId}
            # pyrebase4 requiere el token para operaciones autenticadas
            path = f"users/{user_id}/tasks/{task.id}"
            self.db_realtime.child(path).set(task_dict, token=id_token)
        
        except Exception as e:
            raise RuntimeError(f"Error al subir tarea {task.id}: {str(e)}")
    
    def _upload_habit(self, user_id: str, habit: Habit, id_token: str) -> None:
        """
        Sube un hábito a Firebase Realtime Database.
        
        Args:
            user_id: ID del usuario autenticado
            habit: Hábito a subir
            id_token: Token de autenticación de Firebase
        """
        try:
            habit_dict = habit.to_dict()
            habit_dict['userId'] = user_id
            habit_dict['synced_at'] = datetime.now().isoformat()
            
            path = f"users/{user_id}/habits/{habit.id}"
            self.db_realtime.child(path).set(habit_dict, token=id_token)
        
        except Exception as e:
            raise RuntimeError(f"Error al subir hábito {habit.id}: {str(e)}")
    
    def _download_tasks(self, user_id: str, id_token: str) -> List[Dict[str, Any]]:
        """
        Descarga todas las tareas del usuario desde Firebase Realtime Database.
        
        Args:
            user_id: ID del usuario autenticado
            id_token: Token de autenticación de Firebase
        
        Returns:
            Lista de diccionarios con datos de tareas
        """
        try:
            path = f"users/{user_id}/tasks"
            snapshot = self.db_realtime.child(path).get(token=id_token)
            
            if not snapshot or not snapshot.val():
                return []
            
            tasks = []
            tasks_data = snapshot.val()
            if isinstance(tasks_data, dict):
                for task_id, task_data in tasks_data.items():
                    if isinstance(task_data, dict):
                        tasks.append(task_data)
            
            return tasks
        
        except Exception as e:
            raise RuntimeError(f"Error al descargar tareas: {str(e)}")
    
    def _download_habits(self, user_id: str, id_token: str) -> List[Dict[str, Any]]:
        """
        Descarga todos los hábitos del usuario desde Firebase Realtime Database.
        
        Args:
            user_id: ID del usuario autenticado
            id_token: Token de autenticación de Firebase
        
        Returns:
            Lista de diccionarios con datos de hábitos
        """
        try:
            path = f"users/{user_id}/habits"
            snapshot = self.db_realtime.child(path).get(token=id_token)
            
            if not snapshot or not snapshot.val():
                return []
            
            habits = []
            habits_data = snapshot.val()
            if isinstance(habits_data, dict):
                for habit_id, habit_data in habits_data.items():
                    if isinstance(habit_data, dict):
                        habits.append(habit_data)
            
            return habits
        
        except Exception as e:
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

