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
            # Detectar si estamos en Android usando la variable de entorno de Flet
            android_data_dir = os.getenv("FLET_APP_STORAGE_DATA")
            
            if android_data_dir:
                # En Android, usar el directorio de datos persistente de Flet
                app_data_dir = Path(android_data_dir)
                try:
                    app_data_dir.mkdir(parents=True, exist_ok=True)
                except Exception as e:
                    print(f"Warning: No se pudo crear directorio en Android: {e}")
                    # Fallback a directorio temporal
                    import tempfile
                    app_data_dir = Path(tempfile.gettempdir()) / "productivity_app"
                    app_data_dir.mkdir(parents=True, exist_ok=True)
            else:
                # En escritorio, usar directorio home
                try:
                    app_data_dir = Path.home() / ".productivity_app"
                    app_data_dir.mkdir(exist_ok=True)
                except Exception as e:
                    print(f"Warning: No se pudo usar Path.home(): {e}")
                    # Fallback a directorio temporal
                    import tempfile
                    app_data_dir = Path(tempfile.gettempdir()) / "productivity_app"
                    app_data_dir.mkdir(parents=True, exist_ok=True)
            
            db_path = str(app_data_dir / "app.db")
            print(f"Database path: {db_path}")
        
        self.db_path = db_path
        try:
            self._init_database()
        except Exception as e:
            print(f"Error crítico al inicializar base de datos: {e}")
            import traceback
            traceback.print_exc()
            # Intentar crear una base de datos en ubicación temporal como último recurso
            import tempfile
            temp_db = Path(tempfile.gettempdir()) / "app_fallback.db"
            self.db_path = str(temp_db)
            print(f"Usando base de datos de respaldo: {self.db_path}")
            try:
                self._init_database()
            except Exception as e2:
                print(f"Error fatal: No se pudo inicializar base de datos ni siquiera en ubicación temporal: {e2}")
                raise
    
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
        
        # Tabla de subtareas
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS subtasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                completed INTEGER NOT NULL DEFAULT 0,
                created_at TEXT,
                updated_at TEXT,
                FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE
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
                period TEXT DEFAULT 'mes',
                created_at TEXT,
                updated_at TEXT
            )
        """)
        
        # Migración: agregar columna period si no existe
        try:
            # Verificar si la columna period existe
            cursor.execute("PRAGMA table_info(goals)")
            columns = [column[1] for column in cursor.fetchall()]
            if 'period' not in columns:
                cursor.execute("ALTER TABLE goals ADD COLUMN period TEXT DEFAULT 'mes'")
                # Actualizar valores existentes
                cursor.execute("UPDATE goals SET period = 'mes' WHERE period IS NULL")
        except sqlite3.OperationalError:
            # La columna ya existe o hubo un error, no hacer nada
            pass
        
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
        
        # Insertar tema por defecto si no existe (tema oscuro por defecto)
        cursor.execute("""
            INSERT OR IGNORE INTO user_settings (key, value, updated_at)
            VALUES ('theme', 'dark', ?)
        """, (datetime.now().isoformat(),))
        
        # Tabla de recompensas
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS rewards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                target_points REAL NOT NULL,
                status TEXT NOT NULL DEFAULT 'por_alcanzar',
                created_at TEXT,
                claimed_at TEXT
            )
        """)
        
        # Crear índices para mejorar el rendimiento
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_subtasks_task_id ON subtasks(task_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_habit_completions_habit_id 
            ON habit_completions(habit_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_habit_completions_date 
            ON habit_completions(completion_date)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_rewards_status ON rewards(status)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_rewards_target_points ON rewards(target_points)
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

