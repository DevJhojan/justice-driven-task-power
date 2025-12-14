"""
Configuración y gestión de la base de datos SQLite.
"""
import sqlite3
import os
from pathlib import Path
from typing import Optional


class Database:
    """Gestor de base de datos SQLite."""
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Inicializa la conexión a la base de datos.
        
        Args:
            db_path: Ruta al archivo de base de datos. Si es None, usa una ruta por defecto.
        """
        if db_path is None:
            # Usa una ruta en el directorio de la aplicación
            app_dir = Path(__file__).parent.parent.parent
            db_path = str(app_dir / 'tasks.db')
        
        self.db_path = db_path
        self._ensure_db_directory()
        self._init_database()
    
    def _ensure_db_directory(self):
        """Asegura que el directorio de la base de datos existe."""
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
    
    def _init_database(self):
        """Inicializa la base de datos y crea las tablas necesarias."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Tabla de tareas principales
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                completed INTEGER NOT NULL DEFAULT 0,
                priority TEXT NOT NULL DEFAULT 'medium',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        ''')
        
        # Tabla de subtareas
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS subtasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                deadline TEXT,
                completed INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE
            )
        ''')
        
        # Migración: agregar columnas description y deadline si no existen
        try:
            cursor.execute('ALTER TABLE subtasks ADD COLUMN description TEXT')
        except sqlite3.OperationalError:
            pass  # La columna ya existe
        
        try:
            cursor.execute('ALTER TABLE subtasks ADD COLUMN deadline TEXT')
        except sqlite3.OperationalError:
            pass  # La columna ya existe
        
        # Crear índice para mejorar las consultas
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_subtasks_task_id ON subtasks(task_id)
        ''')
        
        conn.commit()
        conn.close()
    
    def get_connection(self) -> sqlite3.Connection:
        """
        Obtiene una conexión a la base de datos.
        
        Returns:
            Conexión SQLite.
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def close(self):
        """Cierra todas las conexiones (no necesario con context managers)."""
        pass

