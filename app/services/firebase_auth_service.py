"""
Servicio de autenticación con Firebase Authentication usando REST API directamente.

Este módulo maneja:
- Registro de nuevos usuarios (email/password)
- Inicio de sesión (email/password)
- Cierre de sesión
- Verificación del estado de autenticación
- Obtención del usuario actual

Decisiones técnicas:
- Usa requests para llamar directamente a Firebase REST API (sin dependencias problemáticas)
- Lee configuración desde google-services.json
- Maneja tokens de forma segura
- Persiste el estado de autenticación localmente
- Maneja errores de red y tokens expirados
- OFFLINE-FIRST: La app funciona completamente sin Firebase
"""

import json
import os
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    _requests_import_error = "requests no está instalado"

from app.data.database import Database


class FirebaseAuthService:
    """
    Servicio para autenticación con Firebase Authentication usando REST API.
    
    Decisiones técnicas:
    - Usa requests para llamar directamente a Firebase REST API
    - Evita dependencias problemáticas como pyrebase4/gcloud
    - Lee configuración desde google-services.json en la raíz del proyecto
    - Almacena el token de autenticación en SQLite para persistencia
    - Maneja refresco automático de tokens cuando sea necesario
    - OFFLINE-FIRST: La app funciona completamente sin Firebase
    """
    
    def __init__(self, database: Optional[Database] = None):
        """
        Inicializa el servicio de autenticación Firebase.
        
        Args:
            database: Instancia de Database para persistencia local
        """
        self.db = database or Database()
        self.api_key = None
        self.auth_domain = None
        self.project_id = None
        self.current_user = None
        self._init_firebase()
        self._ensure_auth_table()
        self._load_current_user_from_local()
    
    def _init_firebase(self) -> None:
        """
        Inicializa la configuración de Firebase usando google-services.json.
        
        Decisiones técnicas:
        - Lee google-services.json desde la raíz del proyecto
        - Extrae API key y project_id necesarios para REST API
        - OFFLINE-FIRST: Si Firebase no está disponible, la app sigue funcionando
          completamente offline usando solo SQLite. Firebase es opcional.
        """
        if not REQUESTS_AVAILABLE:
            # OFFLINE-FIRST: No lanzar excepción, solo marcar como no disponible
            self.api_key = None
            self.auth_domain = None
            self.project_id = None
            return
        
        # Buscar google-services.json en la raíz del proyecto
        root_dir = Path(__file__).parent.parent.parent
        google_services_path = root_dir / 'google-services.json'
        
        if not google_services_path.exists():
            # OFFLINE-FIRST: No lanzar excepción, solo marcar como no disponible
            self.api_key = None
            self.auth_domain = None
            self.project_id = None
            return
        
        # Leer configuración de Firebase
        with open(google_services_path, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        
        # Extraer información necesaria de google-services.json
        project_info = config_data.get('project_info', {})
        client_info = config_data.get('client', [{}])[0]
        api_key_info = client_info.get('api_key', [{}])[0]
        
        project_id = project_info.get('project_id')
        api_key = api_key_info.get('current_key')
        
        if not project_id or not api_key:
            # OFFLINE-FIRST: No lanzar excepción, solo marcar como no disponible
            self.api_key = None
            self.auth_domain = None
            self.project_id = None
            return
        
        self.api_key = api_key
        self.project_id = project_id
        self.auth_domain = f"{project_id}.firebaseapp.com"
    
    def _ensure_auth_table(self) -> None:
        """Crea la tabla para almacenar tokens de autenticación."""
        conn = self.db.get_connection()
        cur = conn.cursor()
        
        cur.execute("""
            CREATE TABLE IF NOT EXISTS firebase_auth (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT UNIQUE NOT NULL,
                email TEXT NOT NULL,
                id_token TEXT,
                refresh_token TEXT,
                expires_at TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        
        conn.commit()
        conn.close()
    
    def _load_current_user_from_local(self) -> None:
        """Carga el usuario actual desde almacenamiento local al iniciar."""
        stored_user = self._load_auth_token()
        if stored_user:
            self.current_user = stored_user
    
    def register(self, email: str, password: str) -> Dict[str, Any]:
        """
        Registra un nuevo usuario en Firebase usando REST API.
        
        OFFLINE-FIRST: Requiere conexión a internet. Si Firebase no está disponible,
        la app sigue funcionando completamente offline usando solo SQLite.
        
        Args:
            email: Correo electrónico del usuario
            password: Contraseña (mínimo 6 caracteres según Firebase)
        
        Returns:
            Diccionario con información del usuario registrado
        
        Raises:
            ValueError: Si el email o password son inválidos
            RuntimeError: Si hay error en Firebase o no hay conexión
        """
        if not REQUESTS_AVAILABLE or not self.api_key:
            raise RuntimeError(
                "Firebase no está disponible. Verifica tu conexión a internet y "
                "que google-services.json esté configurado correctamente."
            )
        
        if not email or not email.strip():
            raise ValueError("El email no puede estar vacío")
        
        if not password or len(password) < 6:
            raise ValueError("La contraseña debe tener al menos 6 caracteres")
        
        try:
            email_clean = email.strip().lower()
            
            # Registrar usuario usando Firebase REST API
            url = f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={self.api_key}"
            payload = {
                "email": email_clean,
                "password": password,
                "returnSecureToken": True
            }
            
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            user_data = response.json()
            
            # Guardar información del usuario localmente
            self._save_auth_token(user_data, email_clean)
            
            # Obtener información del usuario
            self.current_user = {
                'uid': user_data.get('localId'),
                'email': email_clean,
                'emailVerified': user_data.get('emailVerified', False)
            }
            
            return {
                'success': True,
                'user': self.current_user,
                'message': 'Usuario registrado exitosamente'
            }
        
        except requests.exceptions.RequestException as e:
            error_msg = str(e)
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_data = e.response.json()
                    error_msg = error_data.get('error', {}).get('message', error_msg)
                except:
                    pass
            
            # Manejar errores específicos de Firebase
            if 'EMAIL_EXISTS' in error_msg:
                raise ValueError("Este correo electrónico ya está registrado")
            elif 'INVALID_EMAIL' in error_msg:
                raise ValueError("El formato del correo electrónico no es válido")
            elif 'WEAK_PASSWORD' in error_msg:
                raise ValueError("La contraseña es muy débil")
            elif 'CONFIGURATION_NOT_FOUND' in error_msg or '400' in error_msg:
                raise RuntimeError(
                    "Firebase Authentication no está configurado correctamente. "
                    "Verifica que:\n"
                    "1. Firebase Authentication esté habilitado en Firebase Console\n"
                    "2. El método Email/Password esté habilitado\n"
                    "3. El API key tenga permisos para Firebase Authentication API\n"
                    f"Error técnico: {error_msg}"
                )
            elif 'network' in error_msg.lower() or 'connection' in error_msg.lower() or 'timeout' in error_msg.lower():
                raise RuntimeError(
                    "No hay conexión a internet. La app funciona completamente offline, "
                    "pero el registro requiere conexión a Firebase."
                )
            else:
                raise RuntimeError(f"Error al registrar usuario: {error_msg}")
        except Exception as e:
            raise RuntimeError(f"Error al registrar usuario: {str(e)}")
    
    def login(self, email: str, password: str) -> Dict[str, Any]:
        """
        Inicia sesión con email y contraseña usando REST API.
        
        OFFLINE-FIRST: Requiere conexión a internet. Si Firebase no está disponible,
        la app sigue funcionando completamente offline usando solo SQLite.
        
        Args:
            email: Correo electrónico del usuario
            password: Contraseña
        
        Returns:
            Diccionario con información del usuario autenticado
        
        Raises:
            ValueError: Si las credenciales son inválidas
            RuntimeError: Si hay error en Firebase o no hay conexión
        """
        if not REQUESTS_AVAILABLE or not self.api_key:
            raise RuntimeError(
                "Firebase no está disponible. Verifica tu conexión a internet y "
                "que google-services.json esté configurado correctamente."
            )
        
        if not email or not email.strip():
            raise ValueError("El email no puede estar vacío")
        
        if not password:
            raise ValueError("La contraseña no puede estar vacía")
        
        try:
            email_clean = email.strip().lower()
            
            # Iniciar sesión usando Firebase REST API
            url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={self.api_key}"
            payload = {
                "email": email_clean,
                "password": password,
                "returnSecureToken": True
            }
            
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            user_data = response.json()
            
            # Guardar token localmente
            self._save_auth_token(user_data, email_clean)
            
            # Obtener información del usuario
            self.current_user = {
                'uid': user_data.get('localId'),
                'email': email_clean,
                'emailVerified': user_data.get('emailVerified', False)
            }
            
            return {
                'success': True,
                'user': self.current_user,
                'message': 'Sesión iniciada exitosamente'
            }
        
        except requests.exceptions.RequestException as e:
            error_msg = str(e)
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_data = e.response.json()
                    error_msg = error_data.get('error', {}).get('message', error_msg)
                except:
                    pass
            
            # Manejar errores específicos de Firebase
            if 'INVALID_LOGIN_CREDENTIALS' in error_msg or 'INVALID_PASSWORD' in error_msg or 'INVALID_EMAIL' in error_msg:
                raise ValueError("Correo electrónico o contraseña incorrectos")
            elif 'USER_DISABLED' in error_msg:
                raise ValueError("Esta cuenta ha sido deshabilitada")
            elif 'USER_NOT_FOUND' in error_msg or 'EMAIL_NOT_FOUND' in error_msg:
                raise ValueError("No existe una cuenta con este correo electrónico")
            elif 'CONFIGURATION_NOT_FOUND' in error_msg:
                raise RuntimeError(
                    "Firebase Authentication no está configurado correctamente. "
                    "Verifica que:\n"
                    "1. Firebase Authentication esté habilitado en Firebase Console\n"
                    "2. El método Email/Password esté habilitado\n"
                    "3. El API key tenga permisos para Firebase Authentication API\n"
                    f"Error técnico: {error_msg}"
                )
            elif 'network' in error_msg.lower() or 'connection' in error_msg.lower() or 'timeout' in error_msg.lower():
                raise RuntimeError(
                    "No hay conexión a internet. La app funciona completamente offline, "
                    "pero el inicio de sesión requiere conexión a Firebase."
                )
            else:
                raise RuntimeError(f"Error al iniciar sesión: {error_msg}")
        except Exception as e:
            raise RuntimeError(f"Error al iniciar sesión: {str(e)}")
    
    def logout(self) -> None:
        """Cierra la sesión del usuario actual."""
        self.current_user = None
        self._clear_auth_token()
    
    def get_current_user(self) -> Optional[Dict[str, Any]]:
        """
        Obtiene el usuario actual autenticado.
        
        Returns:
            Diccionario con información del usuario o None si no hay sesión activa
        """
        if self.current_user:
            return self.current_user
        
        # Intentar cargar desde almacenamiento local
        stored_user = self._load_auth_token()
        if stored_user:
            self.current_user = stored_user
            return stored_user
        
        return None
    
    def is_authenticated(self) -> bool:
        """
        Verifica si hay un usuario autenticado.
        
        Returns:
            True si hay un usuario autenticado, False en caso contrario
        """
        return self.get_current_user() is not None
    
    def get_id_token(self) -> Optional[str]:
        """
        Obtiene el token de ID actual del usuario autenticado.
        Si el token ha expirado, intenta refrescarlo.
        
        Returns:
            El token de ID como string o None si no hay token válido.
        """
        conn = self.db.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT id_token, refresh_token, expires_at FROM firebase_auth WHERE user_id = ? LIMIT 1", (self.current_user['uid'],))
        row = cur.fetchone()
        conn.close()

        if not row:
            return None

        id_token = row['id_token']
        refresh_token = row['refresh_token']
        expires_at_str = row['expires_at']

        if expires_at_str:
            expires_at = datetime.fromisoformat(expires_at_str)
            if datetime.now() >= expires_at - timedelta(minutes=5):  # Refrescar 5 minutos antes de expirar
                # Token expirado o a punto de expirar, intentar refrescar
                if refresh_token and refresh_token.strip():
                    try:
                        refreshed_user = self._refresh_token(refresh_token)
                        if refreshed_user and refreshed_user.get('id_token'):
                            self._save_auth_token(refreshed_user, self.current_user['email'])
                            return refreshed_user['id_token']
                        else:
                            # Refresh falló, limpiar tokens y requerir nuevo login
                            self._clear_auth_token()
                            self.current_user = None
                            return None
                    except Exception as e:
                        # Error inesperado, limpiar y requerir nuevo login
                        print(f"Error inesperado al refrescar token: {e}")
                        self._clear_auth_token()
                        self.current_user = None
                        return None
                else:
                    # No hay refresh_token válido, limpiar y requerir nuevo login
                    self._clear_auth_token()
                    self.current_user = None
                    return None
        return id_token
    
    def _save_auth_token(self, user_data: Dict[str, Any], email: str = '') -> None:
        """
        Guarda el token de autenticación en la base de datos local.
        
        Args:
            user_data: Datos del usuario de Firebase (contiene idToken, refreshToken, etc.)
            email: Correo electrónico del usuario (se pasa explícitamente)
        """
        conn = self.db.get_connection()
        cur = conn.cursor()
        
        now = datetime.now().isoformat()
        user_id = user_data.get('localId')
        id_token = user_data.get('idToken')
        refresh_token = user_data.get('refreshToken')
        expires_in = user_data.get('expiresIn', '3600')  # Por defecto 1 hora
        
        # Calcular fecha de expiración
        expires_at = datetime.now() + timedelta(seconds=int(expires_in))
        expires_at_str = expires_at.isoformat()
        
        # Insertar o actualizar token
        cur.execute("""
            INSERT OR REPLACE INTO firebase_auth 
            (user_id, email, id_token, refresh_token, expires_at, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, COALESCE((SELECT created_at FROM firebase_auth WHERE user_id = ?), ?), ?)
        """, (user_id, email, id_token, refresh_token, expires_at_str, user_id, now, now))
        
        conn.commit()
        conn.close()
    
    def _load_auth_token(self) -> Optional[Dict[str, Any]]:
        """
        Carga el token de autenticación desde la base de datos local.
        
        Returns:
            Diccionario con información del usuario o None si no hay token válido
        """
        conn = self.db.get_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT user_id, email, id_token, refresh_token, expires_at
            FROM firebase_auth
            ORDER BY updated_at DESC
            LIMIT 1
        """)
        
        row = cur.fetchone()
        conn.close()
        
        if not row:
            return None
        
        # Verificar si el token ha expirado
        expires_at_str = row['expires_at']
        refresh_token = row['refresh_token']
        
        if expires_at_str:
            expires_at = datetime.fromisoformat(expires_at_str)
            if datetime.now() > expires_at:
                # Token expirado, intentar refrescar solo si hay refresh_token válido
                if refresh_token and refresh_token.strip():
                    try:
                        refreshed = self._refresh_token(refresh_token)
                        if refreshed:
                            return self._load_auth_token()  # Recargar después del refresh
                    except Exception as e:
                        # Error al refrescar, retornar None para requerir nuevo login
                        print(f"Error al refrescar token en _load_auth_token: {e}")
                        pass
                # No hay refresh_token o falló el refresh, requerir nuevo login
                return None
        
        return {
            'uid': row['user_id'],
            'email': row['email']
        }
    
    def _refresh_token(self, refresh_token: str) -> Optional[Dict[str, Any]]:
        """
        Refresca el token de autenticación usando Firebase REST API.
        
        Args:
            refresh_token: Token de refresco
        
        Returns:
            Diccionario con nuevos tokens o None si falla
        """
        if not REQUESTS_AVAILABLE or not self.api_key:
            return None
        
        # Validar que el refresh_token existe y no está vacío
        if not refresh_token or not refresh_token.strip():
            return None
        
        try:
            url = f"https://securetoken.googleapis.com/v1/token?key={self.api_key}"
            payload = {
                "grant_type": "refresh_token",
                "refresh_token": refresh_token.strip()
            }
            
            response = requests.post(url, json=payload, timeout=10)
            
            # Manejar errores específicos
            if response.status_code == 400:
                # Token inválido o expirado, no intentar más
                error_data = response.json() if response.text else {}
                error_message = error_data.get('error', {}).get('message', 'Token inválido o expirado')
                print(f"Token de refresco inválido o expirado: {error_message}")
                return None
            
            response.raise_for_status()
            token_data = response.json()
            
            # Validar que la respuesta contiene los campos necesarios
            if not token_data.get('id_token') or not token_data.get('refresh_token'):
                print("Respuesta de refresh token incompleta")
                return None
            
            # Convertir formato de respuesta a formato esperado
            return {
                'localId': token_data.get('user_id'),
                'idToken': token_data.get('id_token'),
                'refreshToken': token_data.get('refresh_token'),
                'expiresIn': token_data.get('expires_in', '3600')
            }
        except requests.exceptions.RequestException as e:
            # Manejar errores de red específicamente
            if hasattr(e, 'response') and e.response is not None:
                if e.response.status_code == 400:
                    # Token inválido, no loguear como error crítico
                    return None
                error_data = {}
                try:
                    error_data = e.response.json()
                except:
                    pass
                error_message = error_data.get('error', {}).get('message', str(e))
                print(f"Error al refrescar token (HTTP {e.response.status_code}): {error_message}")
            else:
                print(f"Error de red al refrescar token: {e}")
            return None
        except Exception as e:
            print(f"Error inesperado al refrescar token: {e}")
            return None
    
    def _clear_auth_token(self) -> None:
        """Elimina el token de autenticación almacenado."""
        conn = self.db.get_connection()
        cur = conn.cursor()
        
        cur.execute("DELETE FROM firebase_auth")
        
        conn.commit()
        conn.close()
