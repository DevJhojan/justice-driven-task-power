"""
Gestión de la base de datos SQLite.
Inicializa la base de datos y crea las tablas necesarias.
"""
import sqlite3
import os
from pathlib import Path
from datetime import datetime
from typing import Optional


class Database:
    """Gestor de la base de datos SQLite."""
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Inicializa la conexión a la base de datos.
        
        Args:
            db_path: Ruta al archivo de base de datos. Si es None, usa la ruta por defecto.
        """
        if db_path is None:
            # Usar directorio de datos de la aplicación
            app_data_dir = Path.home() / ".productivity_app"
            app_data_dir.mkdir(exist_ok=True)
            db_path = str(app_data_dir / "app.db")
        
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Inicializa la base de datos y crea las tablas si no existen."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Tabla de tareas
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                due_date TEXT,
                status TEXT NOT NULL DEFAULT 'pendiente',
                created_at TEXT,
                updated_at TEXT
            )
        """)
        
        # Tabla de hábitos
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS habits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                created_at TEXT,
                updated_at TEXT
            )
        """)
        
        # Tabla de completaciones de hábitos
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS habit_completions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                habit_id INTEGER NOT NULL,
                completion_date TEXT NOT NULL,
                created_at TEXT,
                FOREIGN KEY (habit_id) REFERENCES habits(id) ON DELETE CASCADE,
                UNIQUE(habit_id, completion_date)
            )
        """)
        
        # Tabla de metas
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS goals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                target_value REAL,
                current_value REAL NOT NULL DEFAULT 0.0,
                unit TEXT,
                created_at TEXT,
                updated_at TEXT
            )
        """)
        
        # Tabla de configuración de usuario
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TEXT
            )
        """)
        
        # Insertar nombre de usuario por defecto si no existe
        cursor.execute("""
            INSERT OR IGNORE INTO user_settings (key, value, updated_at)
            VALUES ('user_name', 'Usuario', ?)
        """, (datetime.now().isoformat(),))
        
        # Crear índices para mejorar el rendimiento
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_habit_completions_habit_id 
            ON habit_completions(habit_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_habit_completions_date 
            ON habit_completions(completion_date)
        """)
        
        conn.commit()
        conn.close()
    
    def get_connection(self) -> sqlite3.Connection:
        """
        Obtiene una conexión a la base de datos.
        
        Returns:
            Conexión SQLite.
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Permite acceso a columnas por nombre
        return conn
    
    def close(self):
        """Cierra todas las conexiones. (Por compatibilidad, SQLite las cierra automáticamente)"""
        pass


# Instancia global de la base de datos
_db_instance: Optional[Database] = None


def get_db(db_path: Optional[str] = None) -> Database:
    """
    Obtiene la instancia global de la base de datos.
    
    Args:
        db_path: Ruta al archivo de base de datos. Solo se usa en la primera llamada.
    
    Returns:
        Instancia de Database.
    """
    global _db_instance
    if _db_instance is None:
        _db_instance = Database(db_path)
    return _db_instance

