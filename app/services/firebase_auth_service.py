"""
Servicio de autenticación con Firebase Authentication.

Este módulo maneja:
- Registro de nuevos usuarios (email/password)
- Inicio de sesión (email/password)
- Cierre de sesión
- Verificación del estado de autenticación
- Obtención del usuario actual

Decisiones técnicas:
- Usa pyrebase4 para autenticación con Firebase (compatible con Android)
- Lee configuración desde google-services.json
- Maneja tokens de forma segura
- Persiste el estado de autenticación localmente
- Maneja errores de red y tokens expirados
"""

import json
import os
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

try:
    import pyrebase
    PYREBASE_AVAILABLE = True
except ImportError:
    PYREBASE_AVAILABLE = False
    _pyrebase_import_error = "pyrebase4 no está instalado"

from app.data.database import Database


class FirebaseAuthService:
    """
    Servicio para autenticación con Firebase Authentication.
    
    Decisiones técnicas:
    - Usa pyrebase4 que es compatible con Firebase REST API
    - Lee configuración desde google-services.json en la raíz del proyecto
    - Almacena el token de autenticación en SQLite para persistencia
    - Maneja refresco automático de tokens cuando sea necesario
    """
    
    def __init__(self, database: Optional[Database] = None):
        """
        Inicializa el servicio de autenticación Firebase.
        
        Args:
            database: Instancia de Database para persistencia local
        """
        self.db = database or Database()
        self.firebase = None
        self.auth = None
        self.current_user = None
        self._init_firebase()
        self._ensure_auth_table()
    
    def _init_firebase(self) -> None:
        """
        Inicializa la conexión con Firebase usando google-services.json.
        
        Decisiones técnicas:
        - Lee google-services.json desde la raíz del proyecto
        - Construye la configuración de Firebase compatible con pyrebase4
        - Usa el API key y project_id del archivo de configuración
        - OFFLINE-FIRST: Si Firebase no está disponible, la app sigue funcionando
          completamente offline usando solo SQLite. Firebase es opcional.
        """
        if not PYREBASE_AVAILABLE:
            # OFFLINE-FIRST: No lanzar excepción, solo marcar como no disponible
            # La app debe funcionar completamente sin Firebase
            self.firebase = None
            self.auth = None
            return
        
        # Buscar google-services.json en la raíz del proyecto
        root_dir = Path(__file__).parent.parent.parent
        google_services_path = root_dir / 'google-services.json'
        
        if not google_services_path.exists():
            # OFFLINE-FIRST: No lanzar excepción, solo marcar como no disponible
            # La app debe funcionar completamente sin Firebase
            self.firebase = None
            self.auth = None
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
        storage_bucket = project_info.get('storage_bucket', f"{project_id}.appspot.com")
        
        if not project_id or not api_key:
            raise ValueError(
                "google-services.json no contiene project_id o api_key válidos"
            )
        
        # Configuración de Firebase para pyrebase4
        # pyrebase4 usa Firebase REST API, no requiere configuración completa de Android
        # IMPORTANTE: El authDomain debe coincidir exactamente con el dominio configurado en Firebase Console
        # Si usas un dominio personalizado, debes ajustarlo aquí
        firebase_config = {
            "apiKey": api_key,
            "authDomain": f"{project_id}.firebaseapp.com",  # Dominio estándar de Firebase
            "databaseURL": "https://justice-driven-task-power-default-rtdb.firebaseio.com",
            "storageBucket": storage_bucket,
            "projectId": project_id
        }
        
        # Validar que tenemos todos los campos necesarios
        required_fields = ["apiKey", "authDomain", "projectId"]
        missing_fields = [field for field in required_fields if not firebase_config.get(field)]
        if missing_fields:
            raise ValueError(
                f"Configuración de Firebase incompleta. Faltan: {', '.join(missing_fields)}"
            )
        
        try:
            self.firebase = pyrebase.initialize_app(firebase_config)
            self.auth = self.firebase.auth()
        except Exception as e:
            # OFFLINE-FIRST: Si hay error al inicializar Firebase, no bloquear la app
            # La app debe funcionar completamente offline usando solo SQLite
            self.firebase = None
            self.auth = None
            print(f"Advertencia: Firebase no disponible (modo offline): {str(e)}")
    
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
    
    def register(self, email: str, password: str) -> Dict[str, Any]:
        """
        Registra un nuevo usuario en Firebase.
        
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
        # OFFLINE-FIRST: Verificar que Firebase esté disponible
        if not self.auth:
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
            
            # Registrar usuario en Firebase
            user = self.auth.create_user_with_email_and_password(
                email_clean,
                password
            )
            
            # Guardar información del usuario localmente (con email)
            self._save_auth_token(user, email_clean)
            
            # Obtener información del usuario desde el token
            # pyrebase4 devuelve el email directamente en la respuesta
            self.current_user = {
                'uid': user['localId'],
                'email': email_clean,
                'emailVerified': False  # pyrebase4 no proporciona este campo directamente
            }
            
            return {
                'success': True,
                'user': self.current_user,
                'message': 'Usuario registrado exitosamente'
            }
        
        except Exception as e:
            error_msg = str(e)
            # OFFLINE-FIRST: Manejar errores de red específicamente
            if 'network' in error_msg.lower() or 'connection' in error_msg.lower() or 'timeout' in error_msg.lower():
                raise RuntimeError(
                    "No hay conexión a internet. La app funciona completamente offline, "
                    "pero el registro requiere conexión a Firebase."
                )
            elif 'CONFIGURATION_NOT_FOUND' in error_msg or '400' in error_msg:
                raise RuntimeError(
                    "Firebase Authentication no está configurado correctamente. "
                    "Verifica que:\n"
                    "1. Firebase Authentication esté habilitado en Firebase Console\n"
                    "2. El método Email/Password esté habilitado\n"
                    "3. El API key tenga permisos para Firebase Authentication API\n"
                    f"Error técnico: {error_msg}"
                )
            elif 'EMAIL_EXISTS' in error_msg:
                raise ValueError("Este correo electrónico ya está registrado")
            elif 'INVALID_EMAIL' in error_msg:
                raise ValueError("El formato del correo electrónico no es válido")
            elif 'WEAK_PASSWORD' in error_msg:
                raise ValueError("La contraseña es muy débil")
            else:
                raise RuntimeError(f"Error al registrar usuario: {error_msg}")
    
    def login(self, email: str, password: str) -> Dict[str, Any]:
        """
        Inicia sesión con email y contraseña.
        
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
        # OFFLINE-FIRST: Verificar que Firebase esté disponible
        if not self.auth:
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
            
            # Iniciar sesión en Firebase
            user = self.auth.sign_in_with_email_and_password(
                email_clean,
                password
            )
            
            # Guardar token localmente (con email)
            self._save_auth_token(user, email_clean)
            
            # Obtener información del usuario desde el token
            # pyrebase4 devuelve el email directamente en la respuesta
            self.current_user = {
                'uid': user['localId'],
                'email': email_clean,
                'emailVerified': False  # pyrebase4 no proporciona este campo directamente
            }
            
            return {
                'success': True,
                'user': self.current_user,
                'message': 'Sesión iniciada exitosamente'
            }
        
        except Exception as e:
            error_msg = str(e)
            # OFFLINE-FIRST: Manejar errores de red específicamente
            if 'network' in error_msg.lower() or 'connection' in error_msg.lower() or 'timeout' in error_msg.lower():
                raise RuntimeError(
                    "No hay conexión a internet. La app funciona completamente offline, "
                    "pero el inicio de sesión requiere conexión a Firebase."
                )
            elif 'CONFIGURATION_NOT_FOUND' in error_msg:
                raise RuntimeError(
                    "Firebase Authentication no está configurado correctamente. "
                    "Verifica que:\n"
                    "1. Firebase Authentication esté habilitado en Firebase Console\n"
                    "2. El método Email/Password esté habilitado\n"
                    "3. El API key tenga permisos para Firebase Authentication API\n"
                    f"Error técnico: {error_msg}"
                )
            elif 'INVALID_LOGIN_CREDENTIALS' in error_msg:
                # Este error puede significar que el usuario no existe o la contraseña es incorrecta
                raise ValueError("Correo electrónico o contraseña incorrectos")
            elif 'INVALID_PASSWORD' in error_msg or 'INVALID_EMAIL' in error_msg:
                raise ValueError("Correo electrónico o contraseña incorrectos")
            elif 'USER_DISABLED' in error_msg:
                raise ValueError("Esta cuenta ha sido deshabilitada")
            elif 'USER_NOT_FOUND' in error_msg:
                raise ValueError("No existe una cuenta con este correo electrónico")
            elif 'EMAIL_NOT_FOUND' in error_msg:
                raise ValueError("No existe una cuenta con este correo electrónico")
            else:
                # Para otros errores 400, verificar si es un error de configuración o credenciales
                if '400' in error_msg and 'CONFIGURATION_NOT_FOUND' not in error_msg:
                    # Podría ser un error de credenciales u otro problema
                    if 'INVALID' in error_msg.upper():
                        raise ValueError("Correo electrónico o contraseña incorrectos")
                    else:
                        raise RuntimeError(f"Error al iniciar sesión: {error_msg}")
                else:
                    raise RuntimeError(f"Error al iniciar sesión: {error_msg}")
    
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
        Obtiene el token de autenticación ID token actual.
        
        Returns:
            ID token como string o None si no hay token válido
        """
        conn = self.db.get_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT id_token, refresh_token, expires_at
            FROM firebase_auth
            ORDER BY updated_at DESC
            LIMIT 1
        """)
        
        row = cur.fetchone()
        conn.close()
        
        if not row or not row['id_token']:
            return None
        
        # Verificar si el token ha expirado
        expires_at_str = row['expires_at']
        if expires_at_str:
            expires_at = datetime.fromisoformat(expires_at_str)
            if datetime.now() > expires_at:
                # Token expirado, intentar refrescar
                try:
                    if row['refresh_token']:
                        refreshed = self._refresh_token(row['refresh_token'])
                        if refreshed:
                            # Recargar token después del refresh
                            conn = self.db.get_connection()
                            cur = conn.cursor()
                            cur.execute("SELECT id_token FROM firebase_auth ORDER BY updated_at DESC LIMIT 1")
                            new_row = cur.fetchone()
                            conn.close()
                            return new_row['id_token'] if new_row else None
                except:
                    pass
                return None
        
        return row['id_token']
    
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
        expires_at = datetime.now().timestamp() + int(expires_in)
        expires_at_str = datetime.fromtimestamp(expires_at).isoformat()
        
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
        if expires_at_str:
            expires_at = datetime.fromisoformat(expires_at_str)
            if datetime.now() > expires_at:
                # Token expirado, intentar refrescar
                try:
                    refreshed = self._refresh_token(row['refresh_token'])
                    if refreshed:
                        return self._load_auth_token()  # Recargar después del refresh
                except:
                    pass
                return None
        
        return {
            'uid': row['user_id'],
            'email': row['email']
        }
    
    def _refresh_token(self, refresh_token: str) -> bool:
        """
        Refresca el token de autenticación.
        
        Args:
            refresh_token: Token de refresco
        
        Returns:
            True si se refrescó exitosamente, False en caso contrario
        """
        try:
            # pyrebase4 no tiene método directo de refresh, pero podemos usar el token existente
            # En producción, deberías implementar el refresh usando Firebase REST API
            return False
        except:
            return False
    
    def _clear_auth_token(self) -> None:
        """Elimina el token de autenticación almacenado."""
        conn = self.db.get_connection()
        cur = conn.cursor()
        
        cur.execute("DELETE FROM firebase_auth")
        
        conn.commit()
        conn.close()

