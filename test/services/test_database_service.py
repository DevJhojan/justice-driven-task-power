"""
Tests para DatabaseService
"""
import pytest
from datetime import datetime, date
from app.services.database_service import DatabaseService, TableSchema


class TestTableSchema:
    """Tests para la clase TableSchema"""
    
    def test_create_schema_basic(self):
        """Test crear esquema básico"""
        schema = TableSchema(
            table_name="test_table",
            columns={"id": "TEXT PRIMARY KEY", "name": "TEXT NOT NULL"}
        )
        assert schema.table_name == "test_table"
        assert schema.primary_key == "id"
        assert len(schema.foreign_keys) == 0
        assert len(schema.indexes) == 0
    
    def test_create_schema_with_foreign_keys(self):
        """Test crear esquema con foreign keys"""
        schema = TableSchema(
            table_name="child_table",
            columns={"id": "TEXT PRIMARY KEY", "parent_id": "TEXT NOT NULL"},
            foreign_keys=[{"column": "parent_id", "references": "parent_table(id)"}]
        )
        assert len(schema.foreign_keys) == 1
        assert schema.foreign_keys[0]["column"] == "parent_id"
    
    def test_create_schema_with_indexes(self):
        """Test crear esquema con índices"""
        schema = TableSchema(
            table_name="test_table",
            columns={"id": "TEXT PRIMARY KEY", "user_id": "TEXT"},
            indexes=["user_id", "status"]
        )
        assert len(schema.indexes) == 2
        assert "user_id" in schema.indexes


class TestDatabaseService:
    """Tests para DatabaseService"""
    
    @pytest.mark.asyncio
    async def test_initialize_database(self, database_service):
        """Test inicializar base de datos"""
        # Registrar un esquema de prueba
        schema = TableSchema(
            table_name="test_table",
            columns={
                "id": "TEXT PRIMARY KEY",
                "name": "TEXT NOT NULL",
                "value": "INTEGER"
            }
        )
        database_service.register_table_schema(schema)
        await database_service.initialize()
        
        # Verificar que la tabla existe
        cursor = await database_service.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='test_table'"
        )
        result = await cursor.fetchone()
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_create_record(self, database_service):
        """Test crear un registro"""
        schema = TableSchema(
            table_name="test_table",
            columns={
                "id": "TEXT PRIMARY KEY",
                "name": "TEXT NOT NULL",
                "value": "INTEGER"
            }
        )
        database_service.register_table_schema(schema)
        await database_service.initialize()
        
        data = {"id": "test_1", "name": "Test", "value": 100}
        result = await database_service.create("test_table", data)
        
        assert result["id"] == "test_1"
        assert result["name"] == "Test"
        assert result["value"] == 100
    
    @pytest.mark.asyncio
    async def test_create_record_with_bool(self, database_service):
        """Test crear registro con valores booleanos"""
        schema = TableSchema(
            table_name="test_table",
            columns={
                "id": "TEXT PRIMARY KEY",
                "active": "INTEGER",
                "urgent": "INTEGER"
            }
        )
        database_service.register_table_schema(schema)
        await database_service.initialize()
        
        data = {"id": "test_1", "active": True, "urgent": False}
        result = await database_service.create("test_table", data)
        
        assert result["active"] == True
        assert result["urgent"] == False
    
    @pytest.mark.asyncio
    async def test_create_record_with_datetime(self, database_service):
        """Test crear registro con fechas"""
        schema = TableSchema(
            table_name="test_table",
            columns={
                "id": "TEXT PRIMARY KEY",
                "created_at": "TEXT",
                "due_date": "TEXT"
            }
        )
        database_service.register_table_schema(schema)
        await database_service.initialize()
        
        now = datetime.now()
        due = date.today()
        data = {"id": "test_1", "created_at": now, "due_date": due}
        result = await database_service.create("test_table", data)
        
        assert isinstance(result["created_at"], datetime)
        assert isinstance(result["due_date"], date)
    
    @pytest.mark.asyncio
    async def test_create_record_with_list(self, database_service):
        """Test crear registro con lista (JSON)"""
        schema = TableSchema(
            table_name="test_table",
            columns={
                "id": "TEXT PRIMARY KEY",
                "tags": "TEXT"
            }
        )
        database_service.register_table_schema(schema)
        await database_service.initialize()
        
        data = {"id": "test_1", "tags": ["tag1", "tag2", "tag3"]}
        result = await database_service.create("test_table", data)
        
        assert result["tags"] == ["tag1", "tag2", "tag3"]
    
    @pytest.mark.asyncio
    async def test_get_record(self, database_service):
        """Test obtener un registro"""
        schema = TableSchema(
            table_name="test_table",
            columns={
                "id": "TEXT PRIMARY KEY",
                "name": "TEXT NOT NULL"
            }
        )
        database_service.register_table_schema(schema)
        await database_service.initialize()
        
        data = {"id": "test_1", "name": "Test"}
        await database_service.create("test_table", data)
        
        result = await database_service.get("test_table", "test_1")
        assert result is not None
        assert result["id"] == "test_1"
        assert result["name"] == "Test"
    
    @pytest.mark.asyncio
    async def test_get_record_not_found(self, database_service):
        """Test obtener registro que no existe"""
        schema = TableSchema(
            table_name="test_table",
            columns={"id": "TEXT PRIMARY KEY", "name": "TEXT"}
        )
        database_service.register_table_schema(schema)
        await database_service.initialize()
        
        result = await database_service.get("test_table", "nonexistent")
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_all_records(self, database_service):
        """Test obtener todos los registros"""
        schema = TableSchema(
            table_name="test_table",
            columns={"id": "TEXT PRIMARY KEY", "name": "TEXT"}
        )
        database_service.register_table_schema(schema)
        await database_service.initialize()
        
        await database_service.create("test_table", {"id": "test_1", "name": "Test 1"})
        await database_service.create("test_table", {"id": "test_2", "name": "Test 2"})
        
        results = await database_service.get_all("test_table")
        assert len(results) == 2
    
    @pytest.mark.asyncio
    async def test_get_all_with_filters(self, database_service):
        """Test obtener registros con filtros"""
        schema = TableSchema(
            table_name="test_table",
            columns={
                "id": "TEXT PRIMARY KEY",
                "name": "TEXT",
                "active": "INTEGER"
            }
        )
        database_service.register_table_schema(schema)
        await database_service.initialize()
        
        await database_service.create("test_table", {"id": "test_1", "name": "Test 1", "active": True})
        await database_service.create("test_table", {"id": "test_2", "name": "Test 2", "active": False})
        await database_service.create("test_table", {"id": "test_3", "name": "Test 3", "active": True})
        
        results = await database_service.get_all("test_table", filters={"active": True})
        assert len(results) == 2
        assert all(r["active"] == True for r in results)
    
    @pytest.mark.asyncio
    async def test_get_all_with_order_by(self, database_service):
        """Test obtener registros ordenados"""
        schema = TableSchema(
            table_name="test_table",
            columns={"id": "TEXT PRIMARY KEY", "name": "TEXT", "value": "INTEGER"}
        )
        database_service.register_table_schema(schema)
        await database_service.initialize()
        
        await database_service.create("test_table", {"id": "test_1", "name": "A", "value": 3})
        await database_service.create("test_table", {"id": "test_2", "name": "B", "value": 1})
        await database_service.create("test_table", {"id": "test_3", "name": "C", "value": 2})
        
        results = await database_service.get_all("test_table", order_by="value ASC")
        assert results[0]["value"] == 1
        assert results[1]["value"] == 2
        assert results[2]["value"] == 3
    
    @pytest.mark.asyncio
    async def test_update_record(self, database_service):
        """Test actualizar un registro"""
        schema = TableSchema(
            table_name="test_table",
            columns={
                "id": "TEXT PRIMARY KEY",
                "name": "TEXT",
                "value": "INTEGER",
                "updated_at": "TEXT"
            }
        )
        database_service.register_table_schema(schema)
        await database_service.initialize()
        
        await database_service.create("test_table", {
            "id": "test_1",
            "name": "Original",
            "value": 100,
            "updated_at": datetime.now().isoformat()
        })
        
        updated = await database_service.update("test_table", "test_1", {"name": "Updated", "value": 200})
        
        assert updated["name"] == "Updated"
        assert updated["value"] == 200
        assert "updated_at" in updated
    
    @pytest.mark.asyncio
    async def test_update_record_not_found(self, database_service):
        """Test actualizar registro que no existe"""
        schema = TableSchema(
            table_name="test_table",
            columns={"id": "TEXT PRIMARY KEY", "name": "TEXT"}
        )
        database_service.register_table_schema(schema)
        await database_service.initialize()
        
        result = await database_service.update("test_table", "nonexistent", {"name": "Updated"})
        assert result is None
    
    @pytest.mark.asyncio
    async def test_delete_record(self, database_service):
        """Test eliminar un registro"""
        schema = TableSchema(
            table_name="test_table",
            columns={"id": "TEXT PRIMARY KEY", "name": "TEXT"}
        )
        database_service.register_table_schema(schema)
        await database_service.initialize()
        
        await database_service.create("test_table", {"id": "test_1", "name": "Test"})
        
        deleted = await database_service.delete("test_table", "test_1")
        assert deleted == True
        
        result = await database_service.get("test_table", "test_1")
        assert result is None
    
    @pytest.mark.asyncio
    async def test_delete_record_not_found(self, database_service):
        """Test eliminar registro que no existe"""
        schema = TableSchema(
            table_name="test_table",
            columns={"id": "TEXT PRIMARY KEY"}
        )
        database_service.register_table_schema(schema)
        await database_service.initialize()
        
        deleted = await database_service.delete("test_table", "nonexistent")
        assert deleted == False
    
    @pytest.mark.asyncio
    async def test_count_records(self, database_service):
        """Test contar registros"""
        schema = TableSchema(
            table_name="test_table",
            columns={"id": "TEXT PRIMARY KEY", "name": "TEXT"}
        )
        database_service.register_table_schema(schema)
        await database_service.initialize()
        
        await database_service.create("test_table", {"id": "test_1", "name": "Test 1"})
        await database_service.create("test_table", {"id": "test_2", "name": "Test 2"})
        await database_service.create("test_table", {"id": "test_3", "name": "Test 3"})
        
        count = await database_service.count("test_table")
        assert count == 3
    
    @pytest.mark.asyncio
    async def test_count_with_filters(self, database_service):
        """Test contar registros con filtros"""
        schema = TableSchema(
            table_name="test_table",
            columns={
                "id": "TEXT PRIMARY KEY",
                "name": "TEXT",
                "active": "INTEGER"
            }
        )
        database_service.register_table_schema(schema)
        await database_service.initialize()
        
        await database_service.create("test_table", {"id": "test_1", "name": "Test 1", "active": True})
        await database_service.create("test_table", {"id": "test_2", "name": "Test 2", "active": False})
        await database_service.create("test_table", {"id": "test_3", "name": "Test 3", "active": True})
        
        count = await database_service.count("test_table", filters={"active": True})
        assert count == 2
    
    @pytest.mark.asyncio
    async def test_foreign_key_cascade(self, database_service):
        """Test que foreign keys con CASCADE funcionan"""
        # Crear tabla padre
        parent_schema = TableSchema(
            table_name="parent_table",
            columns={"id": "TEXT PRIMARY KEY", "name": "TEXT"}
        )
        database_service.register_table_schema(parent_schema)
        
        # Crear tabla hijo con foreign key
        child_schema = TableSchema(
            table_name="child_table",
            columns={
                "id": "TEXT PRIMARY KEY",
                "parent_id": "TEXT NOT NULL",
                "name": "TEXT"
            },
            foreign_keys=[{"column": "parent_id", "references": "parent_table(id)"}]
        )
        database_service.register_table_schema(child_schema)
        await database_service.initialize()
        
        # Crear registros
        await database_service.create("parent_table", {"id": "parent_1", "name": "Parent"})
        await database_service.create("child_table", {"id": "child_1", "parent_id": "parent_1", "name": "Child"})
        
        # Eliminar padre (debe eliminar hijo por CASCADE)
        await database_service.delete("parent_table", "parent_1")
        
        child = await database_service.get("child_table", "child_1")
        assert child is None
    
    @pytest.mark.asyncio
    async def test_indexes_created(self, database_service):
        """Test que los índices se crean correctamente"""
        schema = TableSchema(
            table_name="test_table",
            columns={
                "id": "TEXT PRIMARY KEY",
                "user_id": "TEXT",
                "status": "TEXT"
            },
            indexes=["user_id", "status"]
        )
        database_service.register_table_schema(schema)
        await database_service.initialize()
        
        # Verificar que los índices existen
        cursor = await database_service.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_test_table%'"
        )
        indexes = await cursor.fetchall()
        assert len(indexes) == 2

