"""
Servicio para gestión de configuración del usuario.
"""
from datetime import datetime
from typing import Optional

from app.data.database import Database


class UserSettingsService:
    """Servicio para gestionar la configuración del usuario."""
    
    def __init__(self, db: Database):
        """
        Inicializa el servicio.
        
        Args:
            db: Instancia de Database.
        """
        self.db = db
    
    def get_user_name(self) -> str:
        """
        Obtiene el nombre del usuario.
        
        Returns:
            Nombre del usuario, o 'Usuario' por defecto.
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT value FROM user_settings WHERE key = ?", ("user_name",))
        row = cursor.fetchone()
        conn.close()
        
        return row['value'] if row else "Usuario"
    
    def set_user_name(self, name: str) -> bool:
        """
        Establece el nombre del usuario.
        
        Args:
            name: Nuevo nombre del usuario.
        
        Returns:
            True si se actualizó correctamente.
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        now = datetime.now().isoformat()
        cursor.execute("""
            INSERT OR REPLACE INTO user_settings (key, value, updated_at)
            VALUES (?, ?, ?)
        """, ("user_name", name.strip(), now))
        
        conn.commit()
        conn.close()
        
        return True
    
    def get_theme(self) -> str:
        """
        Obtiene el tema configurado.
        
        Returns:
            Tema configurado ('dark' o 'light'), 'dark' por defecto.
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT value FROM user_settings WHERE key = ?", ("theme",))
        row = cursor.fetchone()
        conn.close()
        
        return row['value'] if row and row['value'] in ['dark', 'light'] else "dark"
    
    def set_theme(self, theme: str) -> bool:
        """
        Establece el tema.
        
        Args:
            theme: 'dark' o 'light'.
        
        Returns:
            True si se actualizó correctamente.
        """
        if theme not in ['dark', 'light']:
            return False
        
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        now = datetime.now().isoformat()
        cursor.execute("""
            INSERT OR REPLACE INTO user_settings (key, value, updated_at)
            VALUES (?, ?, ?)
        """, ("theme", theme, now))
        
        conn.commit()
        conn.close()
        
        return True
    
    def get_firebase_email(self) -> Optional[str]:
        """
        Obtiene el email de Firebase del usuario.
        
        Returns:
            Email de Firebase si existe, None en caso contrario.
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT value FROM user_settings WHERE key = ?", ("firebase_email",))
        row = cursor.fetchone()
        conn.close()
        
        return row['value'] if row else None
    
    def set_firebase_email(self, email: Optional[str]) -> bool:
        """
        Establece el email de Firebase del usuario.
        
        Args:
            email: Email de Firebase o None para eliminar.
        
        Returns:
            True si se actualizó correctamente.
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        now = datetime.now().isoformat()
        if email:
            cursor.execute("""
                INSERT OR REPLACE INTO user_settings (key, value, updated_at)
                VALUES (?, ?, ?)
            """, ("firebase_email", email.strip(), now))
        else:
            cursor.execute("DELETE FROM user_settings WHERE key = ?", ("firebase_email",))
        
        conn.commit()
        conn.close()
        
        return True
    
    def get_firebase_user_id(self) -> Optional[str]:
        """
        Obtiene el user_id de Firebase guardado.
        
        Returns:
            user_id de Firebase si existe, None en caso contrario.
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT value FROM user_settings WHERE key = ?", ("firebase_user_id",))
        row = cursor.fetchone()
        conn.close()
        
        return row['value'] if row else None
    
    def set_firebase_user_id(self, user_id: Optional[str]) -> bool:
        """
        Establece el user_id de Firebase.
        
        Args:
            user_id: user_id de Firebase o None para eliminar.
        
        Returns:
            True si se actualizó correctamente.
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        now = datetime.now().isoformat()
        if user_id:
            cursor.execute("""
                INSERT OR REPLACE INTO user_settings (key, value, updated_at)
                VALUES (?, ?, ?)
            """, ("firebase_user_id", user_id.strip(), now))
        else:
            cursor.execute("DELETE FROM user_settings WHERE key = ?", ("firebase_user_id",))
        
        conn.commit()
        conn.close()
        
        return True
    
    def get_firebase_refresh_token(self) -> Optional[str]:
        """
        Obtiene el refresh_token de Firebase guardado.
        
        Returns:
            refresh_token de Firebase si existe, None en caso contrario.
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT value FROM user_settings WHERE key = ?", ("firebase_refresh_token",))
        row = cursor.fetchone()
        conn.close()
        
        return row['value'] if row else None
    
    def set_firebase_refresh_token(self, refresh_token: Optional[str]) -> bool:
        """
        Establece el refresh_token de Firebase.
        
        Args:
            refresh_token: refresh_token de Firebase o None para eliminar.
        
        Returns:
            True si se actualizó correctamente.
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        now = datetime.now().isoformat()
        if refresh_token:
            cursor.execute("""
                INSERT OR REPLACE INTO user_settings (key, value, updated_at)
                VALUES (?, ?, ?)
            """, ("firebase_refresh_token", refresh_token.strip(), now))
        else:
            cursor.execute("DELETE FROM user_settings WHERE key = ?", ("firebase_refresh_token",))
        
        conn.commit()
        conn.close()
        
        return True