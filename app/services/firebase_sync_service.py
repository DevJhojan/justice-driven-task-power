"""
Servicio de sincronización con Firebase Realtime Database.
"""
import json
import os
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

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
        
        self.user_id: Optional[str] = None
    
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
            self.user_id = user['localId']
            return True
        except Exception as e:
            print(f"Error al iniciar sesión: {e}")
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
            return True
        except Exception as e:
            print(f"Error al registrar usuario: {e}")
            return False
    
    def logout(self):
        """Cierra la sesión de Firebase."""
        self.user_id = None
    
    def is_logged_in(self) -> bool:
        """Verifica si hay una sesión activa."""
        return self.user_id is not None
    
    def sync_to_firebase(self) -> Dict[str, Any]:
        """
        Sincroniza los datos locales a Firebase.
        
        Returns:
            Diccionario con el resultado de la sincronización.
        """
        if not self.user_id:
            return {"success": False, "message": "No hay sesión activa"}
        
        try:
            # Obtener datos locales
            tasks = self.task_service.get_all_tasks()
            habits = self.habit_service.get_all_habits()
            goals = self.goal_service.get_all_goals()
            
            # Convertir a formato JSON
            tasks_data = {}
            for task in tasks:
                tasks_data[str(task.id)] = {
                    "id": task.id,
                    "title": task.title,
                    "description": task.description,
                    "due_date": task.due_date.isoformat() if task.due_date else None,
                    "status": task.status,
                    "created_at": task.created_at.isoformat() if task.created_at else None,
                    "updated_at": task.updated_at.isoformat() if task.updated_at else None
                }
            
            habits_data = {}
            for habit in habits:
                completions = self.habit_service.get_completions(habit.id)
                habits_data[str(habit.id)] = {
                    "id": habit.id,
                    "title": habit.title,
                    "description": habit.description,
                    "created_at": habit.created_at.isoformat() if habit.created_at else None,
                    "updated_at": habit.updated_at.isoformat() if habit.updated_at else None,
                    "completions": [d.isoformat() for d in completions]
                }
            
            goals_data = {}
            for goal in goals:
                goals_data[str(goal.id)] = {
                    "id": goal.id,
                    "title": goal.title,
                    "description": goal.description,
                    "target_value": goal.target_value,
                    "current_value": goal.current_value,
                    "unit": goal.unit,
                    "created_at": goal.created_at.isoformat() if goal.created_at else None,
                    "updated_at": goal.updated_at.isoformat() if goal.updated_at else None
                }
            
            # Obtener puntos y configuración del usuario
            total_points = self.points_service.get_total_points()
            user_name = self.user_settings_service.get_user_name()
            
            points_data = {
                "total_points": total_points,
                "last_updated": datetime.now().isoformat()
            }
            
            user_settings_data = {
                "user_name": user_name,
                "last_updated": datetime.now().isoformat()
            }
            
            # Subir a Firebase
            user_ref = self.db_firebase.child(f"users/{self.user_id}")
            user_ref.child("tasks").set(tasks_data)
            user_ref.child("habits").set(habits_data)
            user_ref.child("goals").set(goals_data)
            user_ref.child("points").set(points_data)
            user_ref.child("user_settings").set(user_settings_data)
            
            return {
                "success": True,
                "message": f"Sincronizado: {len(tasks)} tareas, {len(habits)} hábitos, {len(goals)} metas, puntos: {total_points:.2f}"
            }
        except Exception as e:
            return {"success": False, "message": f"Error al sincronizar: {str(e)}"}
    
    def sync_from_firebase(self) -> Dict[str, Any]:
        """
        Sincroniza los datos de Firebase a local.
        
        Returns:
            Diccionario con el resultado de la sincronización.
        """
        if not self.user_id:
            return {"success": False, "message": "No hay sesión activa"}
        
        try:
            user_ref = self.db_firebase.child(f"users/{self.user_id}")
            
            # Descargar datos
            tasks_data = user_ref.child("tasks").get().val() or {}
            habits_data = user_ref.child("habits").get().val() or {}
            goals_data = user_ref.child("goals").get().val() or {}
            points_data = user_ref.child("points").get().val() or {}
            user_settings_data = user_ref.child("user_settings").get().val() or {}
            
            # Sincronizar puntos si existen en Firebase
            if points_data and "total_points" in points_data:
                firebase_points = float(points_data.get("total_points", 0.0))
                local_points = self.points_service.get_total_points()
                # Usar el mayor valor entre Firebase y local (merge conservador)
                if firebase_points > local_points:
                    # Calcular la diferencia para agregar
                    diff = firebase_points - local_points
                    self.points_service.add_points(diff)
            
            # Sincronizar configuración del usuario
            if user_settings_data and "user_name" in user_settings_data:
                firebase_name = user_settings_data.get("user_name", "")
                if firebase_name:
                    self.user_settings_service.set_user_name(firebase_name)
            
            # TODO: Implementar lógica de merge completa para tareas, hábitos y metas
            # Por ahora, solo retornamos información de lo que se descargó
            
            return {
                "success": True,
                "message": f"Descargado: {len(tasks_data)} tareas, {len(habits_data)} hábitos, {len(goals_data)} metas, puntos sincronizados"
            }
        except Exception as e:
            return {"success": False, "message": f"Error al descargar: {str(e)}"}

