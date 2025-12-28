"""
Servicio para gestión de configuración del usuario.
"""
from datetime import datetime

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

