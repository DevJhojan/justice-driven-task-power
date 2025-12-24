"""
Configuración y gestión de la base de datos SQLite.

ARQUITECTURA OFFLINE-FIRST:
- SQLite es la base de datos principal y fuente de verdad local
- La app funciona completamente offline sin necesidad de conexión a internet
- Todos los datos (tareas, hábitos, configuraciones) se almacenan localmente en SQLite
- Firebase es opcional y solo se usa para respaldo y sincronización entre dispositivos
- La sincronización es completamente bajo demanda del usuario

IMPORTANTE para Android:
- En Android, la base de datos debe guardarse en un directorio persistente
- que NO se borre al actualizar o reinstalar la aplicación.
- Usamos FLET_APP_STORAGE_DATA (variable de entorno que Flet establece automáticamente)
- para obtener el directorio de datos persistente en Android.
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
                    En Android, automáticamente usa el directorio de datos persistente.
        """
        if db_path is None:
            db_path = self._get_default_db_path()
        
        self.db_path = db_path
        self._ensure_db_directory()
        self._init_database()
    
    def _get_default_db_path(self) -> str:
        """
        Obtiene la ruta por defecto para la base de datos.
        En Android, usa el directorio de datos persistente que NO se borra al actualizar.
        
        Returns:
            Ruta al archivo de base de datos.
        """
        # SOLUCIÓN PARA ANDROID: Usar directorio de datos persistente
        # Flet establece automáticamente FLET_APP_STORAGE_DATA en Android
        # Este directorio persiste entre actualizaciones de la app
        app_data_dir = os.getenv("FLET_APP_STORAGE_DATA")
        
        if app_data_dir:
            # Estamos en Android: usar directorio de datos persistente
            # Este directorio NO se borra al actualizar la aplicación
            db_dir = Path(app_data_dir)
            db_dir.mkdir(parents=True, exist_ok=True)
            db_path = str(db_dir / 'tasks.db')
            
            # Verificar que podemos escribir en este directorio
            try:
                test_file = db_dir / '.test_write'
                test_file.write_text('test')
                test_file.unlink()
                
                # MIGRACIÓN: Si existe una base de datos antigua en el directorio del proyecto,
                # moverla a la nueva ubicación persistente
                self._migrate_old_database(db_path)
                
                return db_path
            except Exception:
                # Si no podemos escribir, usar fallback
                pass
        
        # Para escritorio/desarrollo o si FLET_APP_STORAGE_DATA no está disponible:
        # usar directorio del proyecto (funciona bien en desarrollo)
        app_dir = Path(__file__).parent.parent.parent
        return str(app_dir / 'tasks.db')
    
    def _migrate_old_database(self, new_db_path: str) -> None:
        """
        Migra la base de datos antigua a la nueva ubicación persistente si existe.
        Esto asegura que los datos no se pierdan al actualizar la app en Android.
        
        IMPORTANTE:
        - Esta función se ejecuta automáticamente la primera vez que se usa
          la nueva ubicación persistente en Android.
        - Si existe una base de datos antigua, se copia a la nueva ubicación.
        - La base de datos antigua se mantiene como respaldo.
        
        Args:
            new_db_path: Ruta a la nueva ubicación de la base de datos.
        """
        new_path = Path(new_db_path)
        
        # Si la nueva base de datos ya existe, no hacer nada
        # (ya fue migrada o es la primera vez que se usa)
        if new_path.exists():
            return
        
        # Buscar base de datos antigua en el directorio del proyecto
        # (ubicación anterior que se borraba al actualizar)
        app_dir = Path(__file__).parent.parent.parent
        old_db_path = app_dir / 'tasks.db'
        
        if old_db_path.exists() and old_db_path.is_file() and old_db_path.stat().st_size > 0:
            try:
                # Copiar la base de datos antigua a la nueva ubicación persistente
                import shutil
                shutil.copy2(old_db_path, new_db_path)
                
                # Verificar que la copia fue exitosa
                if new_path.exists() and new_path.stat().st_size > 0:
                    # La migración fue exitosa
                    # La base de datos antigua se mantiene como respaldo
                    # (se puede eliminar manualmente después de verificar que todo funciona)
                    pass
            except Exception:
                # Si falla la migración, continuar con la nueva base de datos
                # (se creará vacía pero no perderemos funcionalidad)
                # Esto puede ocurrir si hay problemas de permisos o espacio
                pass
    
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
                priority TEXT NOT NULL DEFAULT 'not_urgent_important',
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
        
        # Migración: convertir prioridades antiguas a Matriz de Eisenhower
        # 'high' -> 'urgent_important', 'medium' -> 'not_urgent_important', 'low' -> 'not_urgent_not_important'
        try:
            cursor.execute("UPDATE tasks SET priority = 'urgent_important' WHERE priority = 'high'")
            cursor.execute("UPDATE tasks SET priority = 'not_urgent_important' WHERE priority = 'medium'")
            cursor.execute("UPDATE tasks SET priority = 'not_urgent_not_important' WHERE priority = 'low'")
            # Si hay alguna prioridad desconocida, convertirla a 'not_urgent_important'
            cursor.execute("""
                UPDATE tasks 
                SET priority = 'not_urgent_important' 
                WHERE priority NOT IN ('urgent_important', 'not_urgent_important', 'urgent_not_important', 'not_urgent_not_important')
            """)
            conn.commit()
        except sqlite3.OperationalError as e:
            print(f"Error en migración de prioridades: {e}")
            pass
        
        # Crear índice para mejorar las consultas
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_subtasks_task_id ON subtasks(task_id)
        ''')
        
        # Tabla de hábitos
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS habits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                frequency TEXT NOT NULL DEFAULT 'daily',
                target_days INTEGER NOT NULL DEFAULT 1,
                active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                CHECK(frequency IN ('daily', 'weekly', 'custom')),
                CHECK(target_days >= 1 AND target_days <= 7)
            )
        ''')
        
        # Tabla de cumplimientos de hábitos
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS habit_completions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                habit_id INTEGER NOT NULL,
                completion_date TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (habit_id) REFERENCES habits(id) ON DELETE CASCADE,
                UNIQUE(habit_id, completion_date)
            )
        ''')
        
        # Índices para mejorar el rendimiento de consultas
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_habit_completions_habit_id 
            ON habit_completions(habit_id)
        ''')
        
        # Tabla para rastrear eliminaciones (para sincronización)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS deleted_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_type TEXT NOT NULL,
                item_id INTEGER NOT NULL,
                deleted_at TEXT NOT NULL,
                synced_at TEXT,
                UNIQUE(item_type, item_id)
            )
        ''')
        
        # Índice para mejorar consultas de eliminaciones
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_deleted_items_type_id 
            ON deleted_items(item_type, item_id)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_deleted_items_synced 
            ON deleted_items(synced_at)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_habit_completions_date 
            ON habit_completions(completion_date)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_habits_active 
            ON habits(active)
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

