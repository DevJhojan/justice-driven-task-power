"""
Servicio de sincronización con Firebase Realtime Database.
"""
import json
import os
import warnings
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

# Suprimir advertencias de pkg_resources (deprecation warning de gcloud/pyrebase4)
warnings.filterwarnings('ignore', category=UserWarning, module='pkg_resources')
warnings.filterwarnings('ignore', category=UserWarning, module='gcloud')

try:
    import pyrebase4 as pyrebase
except ImportError:
    try:
        import pyrebase
    except ImportError:
        pyrebase = None

from app.data.database import Database
from app.services.task_service import TaskService
from app.services.habit_service import HabitService
from app.services.goal_service import GoalService
from app.services.points_service import PointsService
from app.services.user_settings_service import UserSettingsService
from app.data.task_repository import TaskRepository
from app.data.habit_repository import HabitRepository
from app.data.goal_repository import GoalRepository


class FirebaseSyncService:
    """Servicio para sincronizar datos con Firebase."""
    
    def __init__(self, db: Database, task_service: TaskService,
                 habit_service: HabitService, goal_service: GoalService,
                 points_service: PointsService, user_settings_service: UserSettingsService):
        """
        Inicializa el servicio de sincronización.
        
        Args:
            db: Instancia de Database.
            task_service: Servicio de tareas.
            habit_service: Servicio de hábitos.
            goal_service: Servicio de metas.
            points_service: Servicio de puntos.
            user_settings_service: Servicio de configuración del usuario.
        """
        if pyrebase is None:
            raise ImportError(
                "pyrebase4 no está instalado. Instala con: pip install pyrebase4"
            )
        
        self.db = db
        self.task_service = task_service
        self.habit_service = habit_service
        self.goal_service = goal_service
        self.points_service = points_service
        self.user_settings_service = user_settings_service
        
        # Cargar configuración de Firebase desde google-services.json
        self.firebase_config = self._load_firebase_config()
        self.firebase = pyrebase.initialize_app(self.firebase_config)
        self.auth = self.firebase.auth()
        self.db_firebase = self.firebase.database()
        
        # Restaurar estado de sesión guardado (persistencia estricta)
        self.user_id: Optional[str] = self.user_settings_service.get_firebase_user_id()
        self.refresh_token: Optional[str] = self.user_settings_service.get_firebase_refresh_token()
        self.auth_token: Optional[str] = None  # No guardamos el auth_token, se refresca cuando se necesita
        
        # Si tenemos user_id y refresh_token guardados, intentar refrescar el token
        if self.user_id and self.refresh_token:
            try:
                if self._refresh_auth_token():
                    print(f"DEBUG __init__ - Sesión restaurada: user_id={self.user_id}")
                else:
                    print(f"DEBUG __init__ - No se pudo refrescar token, pero user_id existe: {self.user_id}")
            except Exception as e:
                print(f"DEBUG __init__ - Error al refrescar token al inicializar: {e}")
                # No borrar el estado guardado, solo registrar el error
    
    def _create_task_with_id(self, task):
        """Crea una tarea con un ID específico para sincronización, evitando duplicados."""
        from datetime import datetime
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        now = datetime.now().isoformat()
        created_at = task.created_at.isoformat() if task.created_at else now
        updated_at = task.updated_at.isoformat() if task.updated_at else now
        
        cursor.execute("""
            INSERT OR REPLACE INTO tasks (id, title, description, due_date, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            task.id,
            task.title,
            task.description,
            task.due_date.isoformat() if task.due_date else None,
            task.status,
            created_at,
            updated_at
        ))
        
        conn.commit()
        conn.close()
    
    def _create_habit_with_id(self, habit):
        """Crea un hábito con un ID específico para sincronización, evitando duplicados."""
        from datetime import datetime
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        now = datetime.now().isoformat()
        created_at = habit.created_at.isoformat() if habit.created_at else now
        updated_at = habit.updated_at.isoformat() if habit.updated_at else now
        
        cursor.execute("""
            INSERT OR REPLACE INTO habits (id, title, description, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
        """, (
            habit.id,
            habit.title,
            habit.description,
            created_at,
            updated_at
        ))
        
        conn.commit()
        conn.close()
    
    def _create_subtask_with_id(self, subtask):
        """Crea una subtarea con un ID específico para sincronización, evitando duplicados."""
        from datetime import datetime
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        now = datetime.now().isoformat()
        created_at = subtask.created_at.isoformat() if subtask.created_at else now
        updated_at = subtask.updated_at.isoformat() if subtask.updated_at else now
        
        cursor.execute("""
            INSERT OR REPLACE INTO subtasks (id, task_id, title, completed, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            subtask.id,
            subtask.task_id,
            subtask.title,
            1 if subtask.completed else 0,
            created_at,
            updated_at
        ))
        
        conn.commit()
        conn.close()
    
    def _create_goal_with_id(self, goal):
        """Crea una meta con un ID específico para sincronización, evitando duplicados."""
        from datetime import datetime
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        now = datetime.now().isoformat()
        created_at = goal.created_at.isoformat() if goal.created_at else now
        updated_at = goal.updated_at.isoformat() if goal.updated_at else now
        
        cursor.execute("""
            INSERT OR REPLACE INTO goals (id, title, description, target_value, current_value, unit, period, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            goal.id,
            goal.title,
            goal.description,
            goal.target_value,
            goal.current_value,
            goal.unit,
            goal.period or "mes",
            created_at,
            updated_at
        ))
        
        conn.commit()
        conn.close()
    
    def _load_firebase_config(self) -> Dict[str, Any]:
        """Carga la configuración de Firebase desde google-services.json."""
        # Buscar google-services.json en el directorio raíz del proyecto
        root_dir = Path(__file__).parent.parent.parent
        google_services_path = root_dir / "google-services.json"
        
        if not google_services_path.exists():
            raise FileNotFoundError(
                f"google-services.json no encontrado en {google_services_path}"
            )
        
        with open(google_services_path, 'r') as f:
            config = json.load(f)
        
        project_info = config['project_info']
        client_info = config['client'][0]
        api_key = client_info['api_key'][0]['current_key']
        
        return {
            "apiKey": api_key,
            "authDomain": f"{project_info['project_id']}.firebaseapp.com",
            "databaseURL": project_info['firebase_url'],
            "storageBucket": project_info['storage_bucket'],
            "projectId": project_info['project_id']
        }
    
    def login(self, email: str, password: str) -> bool:
        """
        Inicia sesión en Firebase.
        
        Args:
            email: Email del usuario.
            password: Contraseña del usuario.
        
        Returns:
            True si el login fue exitoso, False en caso contrario.
        """
        try:
            user = self.auth.sign_in_with_email_and_password(email, password)
            if not user or 'localId' not in user:
                print("Error: Respuesta de Firebase inválida")
                return False
            
            self.user_id = user['localId']
            self.auth_token = user.get('idToken')
            self.refresh_token = user.get('refreshToken')
            
            # Debug: Verificar qué se guardó
            print(f"DEBUG Login - user_id: {self.user_id}")
            print(f"DEBUG Login - auth_token presente: {self.auth_token is not None}")
            print(f"DEBUG Login - refresh_token presente: {self.refresh_token is not None}")
            
            # Verificar que se guardaron los datos correctamente
            if not self.user_id:
                print("Error: No se pudo obtener el user_id")
                return False
            
            # Guardar el estado de la sesión en la base de datos local (persistencia estricta)
            self.user_settings_service.set_firebase_email(email)
            self.user_settings_service.set_firebase_user_id(self.user_id)
            if self.refresh_token:
                self.user_settings_service.set_firebase_refresh_token(self.refresh_token)
            
            print(f"DEBUG Login - Estado guardado en BD local: user_id={self.user_id}, refresh_token={'presente' if self.refresh_token else 'None'}")
            
            # Verificar que la sesión está activa
            if not self.is_logged_in():
                print("Error: La sesión no se estableció correctamente")
                print(f"DEBUG - user_id después de guardar: {self.user_id}")
                return False
            
            print(f"DEBUG Login exitoso - is_logged_in(): {self.is_logged_in()}")
            return True
        except Exception as e:
            print(f"Error al iniciar sesión: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def register(self, email: str, password: str) -> bool:
        """
        Registra un nuevo usuario en Firebase.
        
        Args:
            email: Email del usuario.
            password: Contraseña del usuario.
        
        Returns:
            True si el registro fue exitoso, False en caso contrario.
        """
        try:
            user = self.auth.create_user_with_email_and_password(email, password)
            self.user_id = user['localId']
            self.auth_token = user.get('idToken')
            self.refresh_token = user.get('refreshToken')
            
            # Guardar el estado de la sesión en la base de datos local (persistencia estricta)
            self.user_settings_service.set_firebase_email(email)
            self.user_settings_service.set_firebase_user_id(self.user_id)
            if self.refresh_token:
                self.user_settings_service.set_firebase_refresh_token(self.refresh_token)
            
            print(f"DEBUG Register - Estado guardado en BD local: user_id={self.user_id}, refresh_token={'presente' if self.refresh_token else 'None'}")
            return True
        except Exception as e:
            print(f"Error al registrar usuario: {e}")
            return False
    
    def logout(self):
        """Cierra la sesión de Firebase. Solo se llama explícitamente."""
        # Borrar estado en memoria
        self.user_id = None
        self.auth_token = None
        self.refresh_token = None
        
        # Borrar estado guardado en la base de datos (solo cuando se cierra sesión explícitamente)
        self.user_settings_service.set_firebase_email(None)
        self.user_settings_service.set_firebase_user_id(None)
        self.user_settings_service.set_firebase_refresh_token(None)
        
        print("DEBUG Logout - Estado de sesión borrado completamente")
    
    def is_logged_in(self) -> bool:
        """
        Verifica si hay una sesión activa.
        Restaura el estado desde BD si es necesario (persistencia estricta).
        """
        # Si no hay user_id en memoria, intentar restaurarlo desde BD (persistencia estricta)
        if not self.user_id:
            saved_user_id = self.user_settings_service.get_firebase_user_id()
            if saved_user_id:
                self.user_id = saved_user_id
                print(f"DEBUG is_logged_in - user_id restaurado desde BD: {self.user_id}")
        
        return self.user_id is not None
    
    def _refresh_auth_token(self) -> bool:
        """
        Refresca el token de autenticación si es necesario.
        
        Returns:
            True si el token fue refrescado exitosamente, False en caso contrario.
        """
        if not self.refresh_token:
            # Si no hay refresh_token en memoria, intentar restaurarlo desde BD
            saved_refresh_token = self.user_settings_service.get_firebase_refresh_token()
            if saved_refresh_token:
                self.refresh_token = saved_refresh_token
                print("DEBUG _refresh_auth_token - refresh_token restaurado desde BD")
            else:
                return False
        
        try:
            print(f"DEBUG _refresh_auth_token - Intentando refrescar con refresh_token (longitud: {len(self.refresh_token) if self.refresh_token else 0})")
            # Pyrebase4 maneja el refresh automáticamente, pero podemos intentar refrescar manualmente
            # si tenemos el refresh_token. El método refresh devuelve un nuevo token.
            user = self.auth.refresh(self.refresh_token)
            print(f"DEBUG _refresh_auth_token - Respuesta de refresh recibida: {user is not None}")
            
            if user and 'idToken' in user:
                self.auth_token = user.get('idToken')
                print(f"DEBUG _refresh_auth_token - Token refrescado exitosamente (longitud: {len(self.auth_token) if self.auth_token else 0})")
                
                # Actualizar el refresh_token si está disponible y guardarlo
                if 'refreshToken' in user:
                    new_refresh_token = user.get('refreshToken')
                    if new_refresh_token != self.refresh_token:
                        self.refresh_token = new_refresh_token
                        # Guardar el nuevo refresh_token en BD
                        self.user_settings_service.set_firebase_refresh_token(self.refresh_token)
                        print(f"DEBUG _refresh_auth_token - refresh_token actualizado y guardado en BD")
                return True
            else:
                print(f"DEBUG _refresh_auth_token - ERROR: Respuesta de refresh no contiene idToken")
                if user:
                    print(f"DEBUG _refresh_auth_token - Claves en respuesta: {list(user.keys()) if isinstance(user, dict) else 'No es dict'}")
                return False
        except Exception as e:
            print(f"DEBUG _refresh_auth_token - EXCEPCIÓN al refrescar token: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            # NO borrar la sesión aquí - el estado guardado se mantiene
            # Solo retornar False para que el método que llama decida
            return False
    
    def _ensure_authenticated(self) -> bool:
        """
        Asegura que el usuario esté autenticado y el token sea válido.
        Restaura el estado desde BD si es necesario (persistencia estricta).
        
        Returns:
            True si está autenticado, False en caso contrario.
        """
        # Si no hay user_id en memoria, intentar restaurarlo desde BD (persistencia estricta)
        if not self.user_id:
            saved_user_id = self.user_settings_service.get_firebase_user_id()
            if saved_user_id:
                self.user_id = saved_user_id
                print(f"DEBUG _ensure_authenticated - user_id restaurado desde BD: {self.user_id}")
        
        # Si no hay refresh_token en memoria, intentar restaurarlo desde BD
        if not self.refresh_token:
            saved_refresh_token = self.user_settings_service.get_firebase_refresh_token()
            if saved_refresh_token:
                self.refresh_token = saved_refresh_token
                print(f"DEBUG _ensure_authenticated - refresh_token restaurado desde BD")
        
        print(f"DEBUG _ensure_authenticated - user_id: {self.user_id}")
        print(f"DEBUG _ensure_authenticated - auth_token presente: {self.auth_token is not None}")
        print(f"DEBUG _ensure_authenticated - refresh_token presente: {self.refresh_token is not None}")
        
        if not self.user_id:
            print("DEBUG _ensure_authenticated - No hay user_id, retornando False")
            return False
        
        # Si tenemos user_id pero no tenemos token, intentar refrescar
        # Solo si tenemos refresh_token disponible
        if not self.auth_token and self.refresh_token:
            try:
                # Intentar refrescar el token, pero no borrar la sesión si falla
                # porque el user_id todavía es válido
                if not self._refresh_auth_token():
                    # Si el refresh falla pero tenemos user_id, aún podemos intentar
                    # usar el token que Pyrebase maneja internamente
                    print("Advertencia: No se pudo refrescar el token, pero la sesión sigue activa")
            except Exception as e:
                print(f"Advertencia al refrescar token: {e}")
                # No borrar la sesión aquí, solo registrar el error
        
        result = self.user_id is not None
        print(f"DEBUG _ensure_authenticated - Resultado: {result}")
        return result
    
    def _get_auth_token(self) -> Optional[str]:
        """
        Obtiene el token de autenticación, refrescándolo si es necesario.
        Restaura el estado desde BD si es necesario (persistencia estricta).
        
        Returns:
            El token de autenticación o None si no está disponible.
        """
        # Si no hay user_id en memoria, intentar restaurarlo desde BD (persistencia estricta)
        if not self.user_id:
            saved_user_id = self.user_settings_service.get_firebase_user_id()
            if saved_user_id:
                self.user_id = saved_user_id
                print(f"DEBUG _get_auth_token - user_id restaurado desde BD: {self.user_id}")
            else:
                print(f"DEBUG _get_auth_token - No hay user_id")
                return None
        
        # Si no hay refresh_token en memoria, intentar restaurarlo desde BD
        if not self.refresh_token:
            saved_refresh_token = self.user_settings_service.get_firebase_refresh_token()
            if saved_refresh_token:
                self.refresh_token = saved_refresh_token
                print(f"DEBUG _get_auth_token - refresh_token restaurado desde BD")
        
        print(f"DEBUG _get_auth_token - user_id: {self.user_id}, auth_token presente: {self.auth_token is not None}, refresh_token presente: {self.refresh_token is not None}")
        
        # SIEMPRE intentar refrescar el token si no está presente o si tenemos refresh_token
        # Esto asegura que siempre tengamos un token válido
        if not self.auth_token:
            if self.refresh_token:
                print(f"DEBUG _get_auth_token - No hay auth_token, intentando refrescar con refresh_token...")
                if self._refresh_auth_token():
                    print(f"DEBUG _get_auth_token - Token refrescado exitosamente")
                else:
                    print(f"DEBUG _get_auth_token - ERROR: No se pudo refrescar el token")
                    # No retornar None todavía, intentar usar Pyrebase sin token explícito
            else:
                print(f"DEBUG _get_auth_token - ERROR: No hay auth_token ni refresh_token")
        
        print(f"DEBUG _get_auth_token - Token final presente: {self.auth_token is not None}")
        return self.auth_token
    
    def _handle_firebase_error(self, error: Exception, retry_callback=None) -> Dict[str, Any]:
        """
        Maneja errores de Firebase, especialmente errores de autenticación.
        
        Args:
            error: La excepción capturada.
            retry_callback: Función opcional para reintentar la operación después de refrescar el token.
        
        Returns:
            Diccionario con información del error.
        """
        error_str = str(error)
        
        # Si es un error de permisos (401 Unauthorized), el token probablemente expiró
        if "Permission denied" in error_str or "401" in error_str or "Unauthorized" in error_str:
            # Intentar refrescar el token automáticamente
            if self.refresh_token:
                if self._refresh_auth_token():
                    # Si el refresh fue exitoso, intentar la operación nuevamente automáticamente
                    if retry_callback:
                        try:
                            # Reintentar la operación con el nuevo token
                            return retry_callback()
                        except Exception as retry_error:
                            # Si el reintento también falla, verificar si es otro error de permisos
                            retry_error_str = str(retry_error)
                            if "Permission denied" in retry_error_str or "401" in retry_error_str:
                                # NO borrar la sesión automáticamente - solo informar al usuario
                                # El usuario debe cerrar sesión explícitamente si lo desea
                                return {
                                    "success": False, 
                                    "message": "Error de autenticación. Por favor, intenta la operación nuevamente. Si el problema persiste, cierra sesión y vuelve a iniciar sesión."
                                }
                            # Si es otro tipo de error, devolverlo
                            return {"success": False, "message": f"Error al sincronizar: {retry_error_str}"}
                    else:
                        # Si no hay callback de reintento, informar al usuario
                        return {
                            "success": False, 
                            "message": "Token refrescado. Por favor, intenta la operación nuevamente."
                        }
            
            # Si no se pudo refrescar, NO borrar la sesión automáticamente
            # Solo informar al usuario que puede intentar nuevamente o cerrar sesión si lo desea
            return {
                "success": False, 
                "message": "No se pudo refrescar el token. Por favor, intenta la operación nuevamente. Si el problema persiste, cierra sesión y vuelve a iniciar sesión."
            }
        
        return {"success": False, "message": f"Error al sincronizar: {error_str}"}
    
    def sync_to_firebase(self) -> Dict[str, Any]:
        """
        Sincroniza los datos locales a Firebase usando actualizaciones granulares por campo.
        
        Returns:
            Diccionario con el resultado de la sincronización.
        """
        if not self._ensure_authenticated():
            return {"success": False, "message": "No hay sesión activa. Por favor, inicia sesión nuevamente."}
        
        def _perform_sync():
            """Función interna para realizar la sincronización."""
            # Verificar que tenemos user_id
            if not self.user_id:
                return {"success": False, "message": "No hay sesión activa. Por favor, inicia sesión nuevamente."}
            
            # Obtener token de autenticación
            token = self._get_auth_token()
            if not token:
                # Si no tenemos token, intentar refrescar una vez más antes de fallar
                print(f"DEBUG _perform_sync - No hay token, intentando refrescar una vez más...")
                if self.refresh_token and self._refresh_auth_token():
                    token = self._get_auth_token()
                    print(f"DEBUG _perform_sync - Token obtenido después de refresh: {token is not None}")
                
                if not token:
                    # Si aún no tenemos token, no podemos continuar
                    error_msg = "No se pudo obtener un token de autenticación válido. Por favor, cierra sesión y vuelve a iniciar sesión."
                    print(f"ERROR: {error_msg}")
                    return {"success": False, "message": error_msg}
            
            user_ref = self.db_firebase.child(f"users/{self.user_id}")
            stats = {"tasks_updated": 0, "habits_updated": 0, "goals_updated": 0, "tasks_created": 0, "habits_created": 0, "goals_created": 0}
            
            # Obtener datos remotos para comparar (pasar token explícitamente)
            remote_tasks = user_ref.child("tasks").get(token=token).val() or {}
            remote_habits = user_ref.child("habits").get(token=token).val() or {}
            remote_goals = user_ref.child("goals").get(token=token).val() or {}
            
            # Sincronizar tareas (solo campos modificados)
            tasks = self.task_service.get_all_tasks()
            for task in tasks:
                task_id_str = str(task.id)
                remote_task = remote_tasks.get(task_id_str)
                
                if remote_task:
                    # Actualizar solo campos que hayan cambiado
                    updates = {}
                    if task.title != remote_task.get("title"):
                        updates["title"] = task.title
                    if task.description != remote_task.get("description"):
                        updates["description"] = task.description
                    if (task.due_date.isoformat() if task.due_date else None) != remote_task.get("due_date"):
                        updates["due_date"] = task.due_date.isoformat() if task.due_date else None
                    if task.status != remote_task.get("status"):
                        updates["status"] = task.status
                    if (task.updated_at.isoformat() if task.updated_at else None) != remote_task.get("updated_at"):
                        updates["updated_at"] = task.updated_at.isoformat() if task.updated_at else None
                    
                    if updates:
                        user_ref.child(f"tasks/{task_id_str}").update(updates, token=token)
                        stats["tasks_updated"] += 1
                else:
                    # Nueva tarea, crear completa
                    user_ref.child(f"tasks/{task_id_str}").set({
                        "id": task.id,
                        "title": task.title,
                        "description": task.description,
                        "due_date": task.due_date.isoformat() if task.due_date else None,
                        "status": task.status,
                        "created_at": task.created_at.isoformat() if task.created_at else None,
                        "updated_at": task.updated_at.isoformat() if task.updated_at else None
                    }, token=token)
                    stats["tasks_created"] += 1
            
            # Sincronizar subtareas individualmente (sincronización estricta granular)
            for task in tasks:
                if not task.id:
                    continue
                    
                task_id_str = str(task.id)
                local_subtasks = self.task_service.get_subtasks(task.id)
                
                # Obtener subtareas remotas para esta tarea
                remote_subtasks = user_ref.child(f"tasks/{task_id_str}/subtasks").get(token=token).val() or {}
                local_subtask_ids = {str(s.id) for s in local_subtasks}
                
                # Sincronizar cada subtarea local
                for subtask in local_subtasks:
                    subtask_id_str = str(subtask.id)
                    remote_subtask = remote_subtasks.get(subtask_id_str)
                    
                    if remote_subtask:
                        # Subtarea existe, actualizar solo si cambió
                        updates = {}
                        if subtask.title != remote_subtask.get("title"):
                            updates["title"] = subtask.title
                        if subtask.completed != remote_subtask.get("completed"):
                            updates["completed"] = subtask.completed
                        if (subtask.updated_at.isoformat() if subtask.updated_at else None) != remote_subtask.get("updated_at"):
                            updates["updated_at"] = subtask.updated_at.isoformat() if subtask.updated_at else None
                        
                        if updates:
                            user_ref.child(f"tasks/{task_id_str}/subtasks/{subtask_id_str}").update(updates, token=token)
                    else:
                        # Nueva subtarea, crear individualmente
                        user_ref.child(f"tasks/{task_id_str}/subtasks/{subtask_id_str}").set({
                            "id": subtask.id,
                            "task_id": subtask.task_id,
                            "title": subtask.title,
                            "completed": subtask.completed,
                            "created_at": subtask.created_at.isoformat() if subtask.created_at else None,
                            "updated_at": subtask.updated_at.isoformat() if subtask.updated_at else None
                        }, token=token)
                
                # Eliminar subtareas remotas que ya no existen localmente
                for remote_subtask_id in remote_subtasks:
                    if remote_subtask_id not in local_subtask_ids:
                        user_ref.child(f"tasks/{task_id_str}/subtasks/{remote_subtask_id}").remove(token=token)
            
            # Sincronizar hábitos (solo campos modificados)
            habits = self.habit_service.get_all_habits()
            for habit in habits:
                habit_id_str = str(habit.id)
                remote_habit = remote_habits.get(habit_id_str)
                local_completions = self.habit_service.get_completions(habit.id)
                
                if remote_habit:
                    # Actualizar solo campos que hayan cambiado
                    updates = {}
                    if habit.title != remote_habit.get("title"):
                        updates["title"] = habit.title
                    if habit.description != remote_habit.get("description"):
                        updates["description"] = habit.description
                    if (habit.updated_at.isoformat() if habit.updated_at else None) != remote_habit.get("updated_at"):
                        updates["updated_at"] = habit.updated_at.isoformat() if habit.updated_at else None
                    
                    if updates:
                        user_ref.child(f"habits/{habit_id_str}").update(updates, token=token)
                        stats["habits_updated"] += 1
                else:
                    # Nuevo hábito, crear completo (sin completaciones, se sincronizan por separado)
                    user_ref.child(f"habits/{habit_id_str}").set({
                        "id": habit.id,
                        "title": habit.title,
                        "description": habit.description,
                        "created_at": habit.created_at.isoformat() if habit.created_at else None,
                        "updated_at": habit.updated_at.isoformat() if habit.updated_at else None
                    }, token=token)
                    stats["habits_created"] += 1
                
                # Sincronizar completaciones individualmente (sincronización estricta granular)
                remote_completions_ref = user_ref.child(f"habits/{habit_id_str}/completions")
                remote_completions = remote_completions_ref.get(token=token).val() or {}
                local_completions_set = {d.isoformat() for d in local_completions}
                
                # Agregar/actualizar completaciones locales
                for completion_date in local_completions:
                    date_str = completion_date.isoformat()
                    if date_str not in remote_completions:
                        # Nueva completación, agregar individualmente
                        remote_completions_ref.child(date_str).set(True, token=token)
                
                # Eliminar completaciones que ya no existen localmente
                for remote_date_str in remote_completions:
                    if remote_date_str not in local_completions_set:
                        remote_completions_ref.child(remote_date_str).remove(token=token)
            
            # Sincronizar metas (solo campos modificados)
            goals = self.goal_service.get_all_goals()
            for goal in goals:
                goal_id_str = str(goal.id)
                remote_goal = remote_goals.get(goal_id_str)
                
                if remote_goal:
                    # Actualizar solo campos que hayan cambiado
                    updates = {}
                    if goal.title != remote_goal.get("title"):
                        updates["title"] = goal.title
                    if goal.description != remote_goal.get("description"):
                        updates["description"] = goal.description
                    if goal.target_value != remote_goal.get("target_value"):
                        updates["target_value"] = goal.target_value
                    if goal.current_value != remote_goal.get("current_value"):
                        updates["current_value"] = goal.current_value
                    if goal.unit != remote_goal.get("unit"):
                        updates["unit"] = goal.unit
                    if goal.period != remote_goal.get("period"):
                        updates["period"] = goal.period
                    if (goal.updated_at.isoformat() if goal.updated_at else None) != remote_goal.get("updated_at"):
                        updates["updated_at"] = goal.updated_at.isoformat() if goal.updated_at else None
                    
                    if updates:
                        user_ref.child(f"goals/{goal_id_str}").update(updates, token=token)
                        stats["goals_updated"] += 1
                else:
                    # Nueva meta, crear completa
                    user_ref.child(f"goals/{goal_id_str}").set({
                        "id": goal.id,
                        "title": goal.title,
                        "description": goal.description,
                        "target_value": goal.target_value,
                        "current_value": goal.current_value,
                        "unit": goal.unit,
                        "period": goal.period or "mes",
                        "created_at": goal.created_at.isoformat() if goal.created_at else None,
                        "updated_at": goal.updated_at.isoformat() if goal.updated_at else None
                    }, token=token)
                    stats["goals_created"] += 1
            
            # Sincronizar puntos (solo si cambió)
            total_points = self.points_service.get_total_points()
            remote_points = user_ref.child("points").get(token=token).val() or {}
            remote_total_points = remote_points.get("total_points", 0.0)
            
            if abs(total_points - remote_total_points) > 0.001:  # Tolerancia para floats
                user_ref.child("points").update({
                    "total_points": total_points,
                    "last_updated": datetime.now().isoformat()
                }, token=token)
            
            # Sincronizar configuración del usuario (solo si cambió)
            user_name = self.user_settings_service.get_user_name()
            remote_settings = user_ref.child("user_settings").get(token=token).val() or {}
            remote_user_name = remote_settings.get("user_name", "")
            
            if user_name != remote_user_name:
                user_ref.child("user_settings").update({
                    "user_name": user_name,
                    "last_updated": datetime.now().isoformat()
                }, token=token)
            
            message_parts = []
            if stats["tasks_created"] > 0 or stats["tasks_updated"] > 0:
                message_parts.append(f"{stats['tasks_created']} nuevas, {stats['tasks_updated']} actualizadas tareas")
            if stats["habits_created"] > 0 or stats["habits_updated"] > 0:
                message_parts.append(f"{stats['habits_created']} nuevos, {stats['habits_updated']} actualizados hábitos")
            if stats["goals_created"] > 0 or stats["goals_updated"] > 0:
                message_parts.append(f"{stats['goals_created']} nuevas, {stats['goals_updated']} actualizadas metas")
            
            if not message_parts:
                message = "Sincronización completa. No hay cambios pendientes."
            else:
                message = f"Sincronizado: {', '.join(message_parts)}"
            
            return {"success": True, "message": message, "stats": stats}
        
        try:
            return _perform_sync()
        except Exception as e:
            return self._handle_firebase_error(e, retry_callback=_perform_sync)
    
    def sync_from_firebase(self) -> Dict[str, Any]:
        """
        Sincroniza los datos de Firebase a local usando merge inteligente por campo.
        Evita duplicados y solo actualiza campos que han cambiado.
        
        Returns:
            Diccionario con el resultado de la sincronización.
        """
        if not self._ensure_authenticated():
            return {"success": False, "message": "No hay sesión activa. Por favor, inicia sesión nuevamente."}
        
        def _perform_sync():
            """Función interna para realizar la sincronización."""
            from datetime import date
            
            # Obtener token de autenticación
            token = self._get_auth_token()
            if not token:
                # Si no tenemos token, intentar refrescar una vez más antes de fallar
                print(f"DEBUG _perform_sync (import) - No hay token, intentando refrescar una vez más...")
                if self.refresh_token and self._refresh_auth_token():
                    token = self._get_auth_token()
                    print(f"DEBUG _perform_sync (import) - Token obtenido después de refresh: {token is not None}")
                
                if not token:
                    # Si aún no tenemos token, no podemos continuar
                    error_msg = "No se pudo obtener un token de autenticación válido. Por favor, cierra sesión y vuelve a iniciar sesión."
                    print(f"ERROR: {error_msg}")
                    return {"success": False, "message": error_msg}
            
            user_ref = self.db_firebase.child(f"users/{self.user_id}")
            stats = {"tasks_updated": 0, "habits_updated": 0, "goals_updated": 0, "tasks_created": 0, "habits_created": 0, "goals_created": 0}
            
            # Descargar datos (pasar token explícitamente)
            tasks_data = user_ref.child("tasks").get(token=token).val() or {}
            habits_data = user_ref.child("habits").get(token=token).val() or {}
            goals_data = user_ref.child("goals").get(token=token).val() or {}
            points_data = user_ref.child("points").get(token=token).val() or {}
            user_settings_data = user_ref.child("user_settings").get(token=token).val() or {}
            
            # Obtener datos locales para comparar
            local_tasks = {str(t.id): t for t in self.task_service.get_all_tasks()}
            local_habits = {str(h.id): h for h in self.habit_service.get_all_habits()}
            local_goals = {str(g.id): g for g in self.goal_service.get_all_goals()}
            
            # Sincronizar tareas
            for task_id_str, remote_task in tasks_data.items():
                task_id = int(task_id_str)
                local_task = local_tasks.get(task_id_str)
                
                if local_task:
                    # Tarea existe localmente - actualizar solo campos que cambiaron (usar updated_at como referencia)
                    remote_updated = datetime.fromisoformat(remote_task.get("updated_at")) if remote_task.get("updated_at") else None
                    local_updated = local_task.updated_at if local_task.updated_at else None
                    
                    # Solo actualizar si la versión remota es más reciente
                    if remote_updated and (not local_updated or remote_updated > local_updated):
                        needs_update = False
                        if remote_task.get("title") != local_task.title:
                            local_task.title = remote_task.get("title")
                            needs_update = True
                        if remote_task.get("description") != local_task.description:
                            local_task.description = remote_task.get("description")
                            needs_update = True
                        if remote_task.get("status") != local_task.status:
                            local_task.status = remote_task.get("status")
                            needs_update = True
                        
                        remote_due_date = None
                        if remote_task.get("due_date"):
                            try:
                                remote_due_date = date.fromisoformat(remote_task.get("due_date"))
                            except:
                                pass
                        
                        if remote_due_date != local_task.due_date:
                            local_task.due_date = remote_due_date
                            needs_update = True
                        
                        if needs_update:
                            self.task_service.update_task(local_task)
                            stats["tasks_updated"] += 1
                else:
                    # Nueva tarea desde Firebase - crear localmente
                    from app.data.models import Task
                    due_date = None
                    if remote_task.get("due_date"):
                        try:
                            due_date = date.fromisoformat(remote_task.get("due_date"))
                        except:
                            pass
                        
                    created_at = None
                    if remote_task.get("created_at"):
                        try:
                            created_at = datetime.fromisoformat(remote_task.get("created_at"))
                        except:
                            pass
                    
                    new_task = Task(
                        id=task_id,  # Usar el mismo ID para evitar duplicados
                        title=remote_task.get("title", ""),
                        description=remote_task.get("description"),
                        due_date=due_date,
                        status=remote_task.get("status", "pendiente"),
                        created_at=created_at,
                        updated_at=datetime.fromisoformat(remote_task.get("updated_at")) if remote_task.get("updated_at") else None
                    )
                    
                    # Insertar directamente con ID específico para evitar duplicados
                    self._create_task_with_id(new_task)
                    stats["tasks_created"] += 1
                
                # Sincronizar subtareas individualmente (sincronización estricta granular)
                remote_subtasks_data = user_ref.child(f"tasks/{task_id_str}/subtasks").get(token=token).val() or {}
                local_subtasks = self.task_service.get_subtasks(task_id) if task_id else []
                local_subtasks_dict = {str(s.id): s for s in local_subtasks}
                
                for subtask_id_str, remote_subtask in remote_subtasks_data.items():
                    subtask_id = int(subtask_id_str)
                    local_subtask = local_subtasks_dict.get(subtask_id_str)
                    
                    if local_subtask:
                        # Subtarea existe localmente - actualizar solo si cambió
                        remote_updated = datetime.fromisoformat(remote_subtask.get("updated_at")) if remote_subtask.get("updated_at") else None
                        local_updated = local_subtask.updated_at if local_subtask.updated_at else None
                        
                        if remote_updated and (not local_updated or remote_updated > local_updated):
                            needs_update = False
                            if remote_subtask.get("title") != local_subtask.title:
                                local_subtask.title = remote_subtask.get("title")
                                needs_update = True
                            if remote_subtask.get("completed") != local_subtask.completed:
                                local_subtask.completed = remote_subtask.get("completed", False)
                                needs_update = True
                            
                            if needs_update:
                                self.task_service.update_subtask(local_subtask)
                    else:
                        # Nueva subtarea desde Firebase - crear localmente
                        from app.data.models import Subtask
                        created_at = None
                        if remote_subtask.get("created_at"):
                            try:
                                created_at = datetime.fromisoformat(remote_subtask.get("created_at"))
                            except:
                                pass
                        
                        new_subtask = Subtask(
                            id=subtask_id,
                            task_id=task_id,
                            title=remote_subtask.get("title", ""),
                            completed=remote_subtask.get("completed", False),
                            created_at=created_at,
                            updated_at=datetime.fromisoformat(remote_subtask.get("updated_at")) if remote_subtask.get("updated_at") else None
                        )
                        
                        # Crear subtarea con ID específico
                        self._create_subtask_with_id(new_subtask)
                
                # Eliminar subtareas locales que ya no existen en Firebase
                remote_subtask_ids = set(remote_subtasks_data.keys())
                for local_subtask in local_subtasks:
                    if str(local_subtask.id) not in remote_subtask_ids:
                        self.task_service.delete_subtask(local_subtask.id)
            
            # Sincronizar hábitos
            for habit_id_str, remote_habit in habits_data.items():
                habit_id = int(habit_id_str)
                local_habit = local_habits.get(habit_id_str)
                
                if local_habit:
                    # Hábito existe localmente - actualizar solo campos que cambiaron
                    remote_updated = datetime.fromisoformat(remote_habit.get("updated_at")) if remote_habit.get("updated_at") else None
                    local_updated = local_habit.updated_at if local_habit.updated_at else None
                    
                    if remote_updated and (not local_updated or remote_updated > local_updated):
                        needs_update = False
                        if remote_habit.get("title") != local_habit.title:
                            local_habit.title = remote_habit.get("title")
                            needs_update = True
                        if remote_habit.get("description") != local_habit.description:
                            local_habit.description = remote_habit.get("description")
                            needs_update = True
                        
                        if needs_update:
                            self.habit_service.update_habit(local_habit)
                            stats["habits_updated"] += 1
                else:
                    # Nuevo hábito desde Firebase - crear localmente
                    from app.data.models import Habit
                    created_at = None
                    if remote_habit.get("created_at"):
                        try:
                            created_at = datetime.fromisoformat(remote_habit.get("created_at"))
                        except:
                            pass
                    
                    new_habit = Habit(
                        id=habit_id,
                        title=remote_habit.get("title", ""),
                        description=remote_habit.get("description"),
                        created_at=created_at,
                        updated_at=datetime.fromisoformat(remote_habit.get("updated_at")) if remote_habit.get("updated_at") else None
                    )
                    
                    # Insertar directamente con ID específico para evitar duplicados
                    self._create_habit_with_id(new_habit)
                    stats["habits_created"] += 1
                
                # Sincronizar completaciones individualmente (sincronización estricta granular)
                remote_completions_data = user_ref.child(f"habits/{habit_id_str}/completions").get(token=token).val() or {}
                local_completions = self.habit_service.get_completions(habit_id)
                local_completions_set = {d.isoformat() for d in local_completions}
                
                # Agregar completaciones que existen en Firebase pero no localmente
                for completion_date_str in remote_completions_data:
                    if completion_date_str not in local_completions_set:
                        try:
                            completion_date = date.fromisoformat(completion_date_str)
                            # Usar el servicio para agregar completación (evita puntos duplicados)
                            local_completions_check = self.habit_service.get_completions(habit_id)
                            if completion_date not in local_completions_check:
                                self.habit_service.repository.add_completion(habit_id, completion_date)
                        except:
                            pass
                
                # Eliminar completaciones locales que ya no existen en Firebase
                for local_completion_date in local_completions:
                    date_str = local_completion_date.isoformat()
                    if date_str not in remote_completions_data:
                        try:
                            self.habit_service.repository.remove_completion(habit_id, local_completion_date)
                        except:
                            pass
            
            # Sincronizar metas
            for goal_id_str, remote_goal in goals_data.items():
                goal_id = int(goal_id_str)
                local_goal = local_goals.get(goal_id_str)
                
                if local_goal:
                    # Meta existe localmente - actualizar solo campos que cambiaron
                    remote_updated = datetime.fromisoformat(remote_goal.get("updated_at")) if remote_goal.get("updated_at") else None
                    local_updated = local_goal.updated_at if local_goal.updated_at else None
                    
                    if remote_updated and (not local_updated or remote_updated > local_updated):
                        needs_update = False
                        if remote_goal.get("title") != local_goal.title:
                            local_goal.title = remote_goal.get("title")
                            needs_update = True
                        if remote_goal.get("description") != local_goal.description:
                            local_goal.description = remote_goal.get("description")
                            needs_update = True
                        if remote_goal.get("target_value") != local_goal.target_value:
                            local_goal.target_value = remote_goal.get("target_value")
                            needs_update = True
                        if remote_goal.get("current_value") != local_goal.current_value:
                            local_goal.current_value = remote_goal.get("current_value", 0.0)
                            needs_update = True
                        if remote_goal.get("unit") != local_goal.unit:
                            local_goal.unit = remote_goal.get("unit")
                            needs_update = True
                        if remote_goal.get("period") != local_goal.period:
                            local_goal.period = remote_goal.get("period", "mes")
                            needs_update = True
                        
                        if needs_update:
                            self.goal_service.update_goal(local_goal)
                            stats["goals_updated"] += 1
                else:
                    # Nueva meta desde Firebase - crear localmente
                    from app.data.models import Goal
                    created_at = None
                    if remote_goal.get("created_at"):
                        try:
                            created_at = datetime.fromisoformat(remote_goal.get("created_at"))
                        except:
                            pass
                    
                    new_goal = Goal(
                        id=goal_id,
                        title=remote_goal.get("title", ""),
                        description=remote_goal.get("description"),
                        target_value=remote_goal.get("target_value"),
                        current_value=remote_goal.get("current_value", 0.0),
                        unit=remote_goal.get("unit"),
                        period=remote_goal.get("period", "mes"),
                        created_at=created_at,
                        updated_at=datetime.fromisoformat(remote_goal.get("updated_at")) if remote_goal.get("updated_at") else None
                    )
                    
                    # Insertar directamente con ID específico para evitar duplicados
                    self._create_goal_with_id(new_goal)
                    stats["goals_created"] += 1
            
            # Sincronizar puntos si existen en Firebase
            if points_data and "total_points" in points_data:
                firebase_points = float(points_data.get("total_points", 0.0))
                local_points = self.points_service.get_total_points()
                # Usar el mayor valor entre Firebase y local (merge conservador)
                if firebase_points > local_points:
                    diff = firebase_points - local_points
                    self.points_service.add_points(diff)
            
            # Sincronizar configuración del usuario
            if user_settings_data and "user_name" in user_settings_data:
                firebase_name = user_settings_data.get("user_name", "")
                if firebase_name:
                    self.user_settings_service.set_user_name(firebase_name)
            
            message_parts = []
            if stats["tasks_created"] > 0 or stats["tasks_updated"] > 0:
                message_parts.append(f"{stats['tasks_created']} nuevas, {stats['tasks_updated']} actualizadas tareas")
            if stats["habits_created"] > 0 or stats["habits_updated"] > 0:
                message_parts.append(f"{stats['habits_created']} nuevos, {stats['habits_updated']} actualizados hábitos")
            if stats["goals_created"] > 0 or stats["goals_updated"] > 0:
                message_parts.append(f"{stats['goals_created']} nuevas, {stats['goals_updated']} actualizadas metas")
            
            if not message_parts:
                message = "Sincronización completa. No hay cambios pendientes."
            else:
                message = f"Descargado: {', '.join(message_parts)}"
            
            return {"success": True, "message": message, "stats": stats}
        
        try:
            return _perform_sync()
        except Exception as e:
            return self._handle_firebase_error(e, retry_callback=_perform_sync)

