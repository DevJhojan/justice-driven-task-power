"""
Servicio de Base de Datos (Database Service)
Servicio genérico y reutilizable para todos los módulos de la aplicación
"""

import aiosqlite
import json
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from app.utils.helpers import get_database_path, ensure_database_directory


class TableSchema:
    """
    Esquema de una tabla para registro en DatabaseService
    """
    def __init__(
        self,
        table_name: str,
        columns: Dict[str, str],  # {"column_name": "TEXT NOT NULL", ...}
        primary_key: str = "id",
        foreign_keys: Optional[List[Dict[str, str]]] = None,  # [{"column": "task_id", "references": "tasks(id)"}]
        indexes: Optional[List[str]] = None,  # ["user_id", "status"]
    ):
        self.table_name = table_name
        self.columns = columns
        self.primary_key = primary_key
        self.foreign_keys = foreign_keys or []
        self.indexes = indexes or []


class DatabaseService:
    """
    Servicio genérico para gestionar la base de datos SQLite
    Reutilizable para todos los servicios (tasks, goals, habits, settings, etc.)
    """
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Inicializa el servicio de base de datos
        
        Args:
            db_path: Ruta al archivo de base de datos (opcional)
        """
        if db_path is None:
            ensure_database_directory()
            db_path = str(get_database_path("app.db"))
        
        self.db_path = db_path
        self._connection: Optional[aiosqlite.Connection] = None
        self._registered_schemas: Dict[str, TableSchema] = {}
    
    async def connect(self):
        """Establece conexión con la base de datos"""
        if self._connection is None:
            self._connection = await aiosqlite.connect(self.db_path)
            await self._connection.execute("PRAGMA foreign_keys = ON")
            await self._connection.commit()
    
    async def disconnect(self):
        """Cierra la conexión con la base de datos"""
        if self._connection:
            await self._connection.close()
            self._connection = None
    
    async def initialize(self):
        """Inicializa la base de datos creando todas las tablas registradas"""
        await self.connect()
        await self._create_all_tables()
        await self.commit()
    
    # ============================================================================
    # REGISTRO DE ESQUEMAS DE TABLAS
    # ============================================================================
    
    def register_table_schema(self, schema: TableSchema):
        """
        Registra un esquema de tabla para que sea creada automáticamente
        
        Args:
            schema: Esquema de la tabla (TableSchema)
        """
        self._registered_schemas[schema.table_name] = schema
    
    async def _create_all_tables(self):
        """Crea todas las tablas registradas"""
        for schema in self._registered_schemas.values():
            await self._create_table(schema)
            if schema.indexes:
                await self._create_indexes(schema)
    
    async def _create_table(self, schema: TableSchema):
        """Crea una tabla según su esquema"""
        columns_def = []
        
        # Agregar primary key primero si no está en columns
        if schema.primary_key not in schema.columns:
            columns_def.append(f"{schema.primary_key} TEXT PRIMARY KEY")
        
        # Agregar resto de columnas
        for col_name, col_type in schema.columns.items():
            if col_name == schema.primary_key and "PRIMARY KEY" not in col_type.upper():
                col_type = f"{col_type} PRIMARY KEY"
            columns_def.append(f"{col_name} {col_type}")
        
        # Agregar foreign keys
        for fk in schema.foreign_keys:
            columns_def.append(f"FOREIGN KEY ({fk['column']}) REFERENCES {fk['references']} ON DELETE CASCADE")
        
        query = f"CREATE TABLE IF NOT EXISTS {schema.table_name} ({', '.join(columns_def)})"
        await self.execute(query)
    
    async def _create_indexes(self, schema: TableSchema):
        """Crea índices para una tabla"""
        for index_col in schema.indexes:
            index_name = f"idx_{schema.table_name}_{index_col}"
            await self.execute(f"CREATE INDEX IF NOT EXISTS {index_name} ON {schema.table_name}({index_col})")
    
    # ============================================================================
    # MÉTODOS GENÉRICOS DE BASE DE DATOS
    # ============================================================================
    
    async def execute(self, query: str, parameters: tuple = ()) -> aiosqlite.Cursor:
        """Ejecuta una consulta SQL"""
        if self._connection is None:
            await self.connect()
        return await self._connection.execute(query, parameters)
    
    async def executemany(self, query: str, parameters: List[tuple]) -> aiosqlite.Cursor:
        """Ejecuta una consulta SQL múltiples veces"""
        if self._connection is None:
            await self.connect()
        return await self._connection.executemany(query, parameters)
    
    async def commit(self):
        """Confirma los cambios en la base de datos"""
        if self._connection:
            await self._connection.commit()
    
    async def rollback(self):
        """Revierte los cambios en la base de datos"""
        if self._connection:
            await self._connection.rollback()
    
    # ============================================================================
    # MÉTODOS GENÉRICOS CRUD (Reutilizables para cualquier tabla)
    # ============================================================================
    
    async def create(
        self,
        table_name: str,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Crea un registro genérico en cualquier tabla
        
        Args:
            table_name: Nombre de la tabla
            data: Diccionario con los datos del registro
        
        Returns:
            Diccionario con el registro creado
        """
        converted_data = self._convert_to_db(data)
        columns = list(converted_data.keys())
        placeholders = ', '.join(['?' for _ in columns])
        values = tuple(converted_data.values())
        
        query = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"
        await self.execute(query, values)
        await self.commit()
        
        # Retornar el registro creado
        record_id = converted_data.get('id') or data.get('id')
        if record_id:
            return await self.get(table_name, record_id)
        return converted_data
    
    async def get(
        self,
        table_name: str,
        record_id: str,
        id_column: str = "id"
    ) -> Optional[Dict[str, Any]]:
        """
        Obtiene un registro por su ID
        
        Args:
            table_name: Nombre de la tabla
            record_id: ID del registro
            id_column: Nombre de la columna ID (default: "id")
        
        Returns:
            Diccionario con los datos del registro o None
        """
        query = f"SELECT * FROM {table_name} WHERE {id_column} = ?"
        cursor = await self.execute(query, (record_id,))
        row = await cursor.fetchone()
        
        if not row:
            return None
        
        columns = [description[0] for description in cursor.description]
        record = dict(zip(columns, row))
        return self._convert_from_db(record)
    
    async def get_all(
        self,
        table_name: str,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Obtiene todos los registros de una tabla, opcionalmente filtrados
        
        Args:
            table_name: Nombre de la tabla
            filters: Diccionario con filtros (ej: {"status": "pendiente", "user_id": "123"})
            order_by: Columna para ordenar (ej: "created_at DESC")
        
        Returns:
            Lista de diccionarios con los registros
        """
        query = f"SELECT * FROM {table_name} WHERE 1=1"
        parameters = []
        
        if filters:
            for key, value in filters.items():
                # Convertir bool a int para la consulta
                if isinstance(value, bool):
                    value = 1 if value else 0
                query += f" AND {key} = ?"
                parameters.append(value)
        
        if order_by:
            query += f" ORDER BY {order_by}"
        
        cursor = await self.execute(query, tuple(parameters))
        rows = await cursor.fetchall()
        
        columns = [description[0] for description in cursor.description]
        return [self._convert_from_db(dict(zip(columns, row))) for row in rows]
    
    async def update(
        self,
        table_name: str,
        record_id: str,
        data: Dict[str, Any],
        id_column: str = "id"
    ) -> Optional[Dict[str, Any]]:
        """
        Actualiza un registro existente
        
        Args:
            table_name: Nombre de la tabla
            record_id: ID del registro
            data: Diccionario con los datos a actualizar
            id_column: Nombre de la columna ID
        
        Returns:
            Diccionario con el registro actualizado o None
        """
        existing = await self.get(table_name, record_id, id_column)
        if not existing:
            return None
        
        converted_data = self._convert_to_db(data)
        update_fields = []
        parameters = []
        
        for key, value in converted_data.items():
            if key != id_column:
                update_fields.append(f"{key} = ?")
                parameters.append(value)
        
        # Actualizar updated_at si existe
        if 'updated_at' in existing:
            update_fields.append("updated_at = ?")
            parameters.append(datetime.now().isoformat())
        
        if update_fields:
            parameters.append(record_id)
            query = f"UPDATE {table_name} SET {', '.join(update_fields)} WHERE {id_column} = ?"
            await self.execute(query, tuple(parameters))
            await self.commit()
        
        return await self.get(table_name, record_id, id_column)
    
    async def delete(
        self,
        table_name: str,
        record_id: str,
        id_column: str = "id"
    ) -> bool:
        """
        Elimina un registro
        
        Args:
            table_name: Nombre de la tabla
            record_id: ID del registro
            id_column: Nombre de la columna ID
        
        Returns:
            True si se eliminó, False si no existe
        """
        existing = await self.get(table_name, record_id, id_column)
        if not existing:
            return False
        
        query = f"DELETE FROM {table_name} WHERE {id_column} = ?"
        await self.execute(query, (record_id,))
        await self.commit()
        return True
    
    # ============================================================================
    # CONVERSIÓN AUTOMÁTICA DE TIPOS
    # ============================================================================
    
    def _convert_to_db(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Convierte datos de Python a formato de base de datos"""
        converted = {}
        for key, value in data.items():
            if value is None:
                converted[key] = None
            elif isinstance(value, bool):
                converted[key] = 1 if value else 0
            elif isinstance(value, datetime):
                converted[key] = value.isoformat()
            elif isinstance(value, date):
                converted[key] = value.isoformat()
            elif isinstance(value, list):
                converted[key] = json.dumps(value)
            else:
                converted[key] = value
        return converted
    
    def _convert_from_db(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Convierte datos de base de datos a formato Python"""
        converted = {}
        for key, value in data.items():
            if value is None:
                converted[key] = None
            # Detectar columnas booleanas comunes
            elif key in ['urgent', 'important', 'completed']:
                converted[key] = bool(value)
            # Detectar columnas de fecha/hora
            elif key.endswith('_at') or key == 'due_date' or key == 'target_date':
                if isinstance(value, str) and value:
                    try:
                        if 'T' in value or ':' in value:
                            converted[key] = datetime.fromisoformat(value)
                        else:
                            converted[key] = datetime.fromisoformat(value).date()
                    except:
                        converted[key] = value
                else:
                    converted[key] = value
            # Detectar JSON (tags, etc.)
            elif key == 'tags' and isinstance(value, str):
                converted[key] = json.loads(value) if value else []
            else:
                converted[key] = value
        return converted
    
    # ============================================================================
    # MÉTODOS DE UTILIDAD
    # ============================================================================
    
    async def count(
        self,
        table_name: str,
        filters: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Obtiene el número de registros en una tabla
        
        Args:
            table_name: Nombre de la tabla
            filters: Diccionario con filtros (opcional)
        
        Returns:
            Número de registros
        """
        query = f"SELECT COUNT(*) FROM {table_name}"
        parameters = []
        
        if filters:
            query += " WHERE 1=1"
            for key, value in filters.items():
                if isinstance(value, bool):
                    value = 1 if value else 0
                query += f" AND {key} = ?"
                parameters.append(value)
        
        cursor = await self.execute(query, tuple(parameters))
        row = await cursor.fetchone()
        return row[0] if row else 0
