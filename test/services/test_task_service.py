"""
Tests para TaskService
"""
import pytest
from datetime import datetime, date, timedelta
from app.services.task_service import TaskService
from app.services.database_service import DatabaseService, TableSchema
from app.models.task import Task
from app.models.subtask import Subtask
from app.utils.task_helper import (
    TASK_STATUS_PENDING,
    TASK_STATUS_IN_PROGRESS,
    TASK_STATUS_COMPLETED,
    TASK_STATUS_CANCELLED,
)


@pytest.fixture
async def initialized_task_service(database_service):
    """Fixture para TaskService con BD inicializada"""
    from app.services.task_service import TaskService
    
    # Registrar esquemas
    tasks_schema = TableSchema(
        table_name="tasks",
        columns={
            "id": "TEXT PRIMARY KEY",
            "title": "TEXT NOT NULL",
            "description": "TEXT",
            "status": "TEXT NOT NULL DEFAULT 'pendiente'",
            "urgent": "INTEGER NOT NULL DEFAULT 0",
            "important": "INTEGER NOT NULL DEFAULT 0",
            "due_date": "TEXT",
            "created_at": "TEXT NOT NULL",
            "updated_at": "TEXT NOT NULL",
            "user_id": "TEXT NOT NULL",
            "tags": "TEXT",
            "notes": "TEXT"
        },
        indexes=["user_id", "status"]
    )
    
    subtasks_schema = TableSchema(
        table_name="subtasks",
        columns={
            "id": "TEXT PRIMARY KEY",
            "task_id": "TEXT NOT NULL",
            "title": "TEXT NOT NULL",
            "completed": "INTEGER NOT NULL DEFAULT 0",
            "urgent": "INTEGER NOT NULL DEFAULT 0",
            "important": "INTEGER NOT NULL DEFAULT 0",
            "created_at": "TEXT NOT NULL",
            "updated_at": "TEXT NOT NULL",
            "notes": "TEXT"
        },
        foreign_keys=[{"column": "task_id", "references": "tasks(id)"}],
        indexes=["task_id"]
    )
    
    database_service.register_table_schema(tasks_schema)
    database_service.register_table_schema(subtasks_schema)
    await database_service.initialize()
    
    service = TaskService(database_service=database_service)
    await service.initialize()
    return service


class TestTaskService:
    """Tests para TaskService"""
    
    @pytest.mark.asyncio
    async def test_create_task(self, initialized_task_service, sample_user_id):
        """Test crear una tarea"""
        task_data = {
            "title": "Tarea de prueba",
            "description": "Descripción",
            "user_id": sample_user_id
        }
        
        task = await initialized_task_service.create_task(task_data)
        
        assert task.title == "Tarea de prueba"
        assert task.description == "Descripción"
        assert task.user_id == sample_user_id
        assert task.id is not None
        assert task.status == TASK_STATUS_PENDING
    
    @pytest.mark.asyncio
    async def test_create_task_missing_title(self, initialized_task_service, sample_user_id):
        """Test crear tarea sin título debe fallar"""
        task_data = {
            "description": "Sin título",
            "user_id": sample_user_id
        }
        
        with pytest.raises(ValueError, match="título.*requerido"):
            await initialized_task_service.create_task(task_data)
    
    @pytest.mark.asyncio
    async def test_create_task_missing_user_id(self, initialized_task_service):
        """Test crear tarea sin user_id debe fallar"""
        task_data = {
            "title": "Tarea sin usuario"
        }
        
        with pytest.raises(ValueError, match="user_id.*requerido"):
            await initialized_task_service.create_task(task_data)
    
    @pytest.mark.asyncio
    async def test_get_task(self, initialized_task_service, sample_user_id):
        """Test obtener una tarea"""
        task_data = {
            "title": "Tarea para obtener",
            "user_id": sample_user_id
        }
        created_task = await initialized_task_service.create_task(task_data)
        
        retrieved = await initialized_task_service.get_task(created_task.id)
        
        assert retrieved is not None
        assert retrieved.id == created_task.id
        assert retrieved.title == "Tarea para obtener"
    
    @pytest.mark.asyncio
    async def test_get_task_not_found(self, initialized_task_service):
        """Test obtener tarea que no existe"""
        result = await initialized_task_service.get_task("nonexistent")
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_all_tasks(self, initialized_task_service, sample_user_id):
        """Test obtener todas las tareas"""
        await initialized_task_service.create_task({
            "title": "Tarea 1",
            "user_id": sample_user_id
        })
        await initialized_task_service.create_task({
            "title": "Tarea 2",
            "user_id": sample_user_id
        })
        
        tasks = await initialized_task_service.get_all_tasks()
        assert len(tasks) >= 2
    
    @pytest.mark.asyncio
    async def test_get_all_tasks_with_user_filter(self, initialized_task_service):
        """Test obtener tareas filtradas por usuario"""
        user1 = "user_1"
        user2 = "user_2"
        
        await initialized_task_service.create_task({"title": "Tarea 1", "user_id": user1})
        await initialized_task_service.create_task({"title": "Tarea 2", "user_id": user1})
        await initialized_task_service.create_task({"title": "Tarea 3", "user_id": user2})
        
        tasks = await initialized_task_service.get_all_tasks(user_id=user1)
        assert len(tasks) == 2
        assert all(t.user_id == user1 for t in tasks)
    
    @pytest.mark.asyncio
    async def test_get_all_tasks_with_status_filter(self, initialized_task_service, sample_user_id):
        """Test obtener tareas filtradas por estado"""
        await initialized_task_service.create_task({
            "title": "Pendiente",
            "user_id": sample_user_id,
            "status": TASK_STATUS_PENDING
        })
        await initialized_task_service.create_task({
            "title": "Completada",
            "user_id": sample_user_id,
            "status": TASK_STATUS_COMPLETED
        })
        
        pending = await initialized_task_service.get_all_tasks(
            user_id=sample_user_id,
            filters={"status": TASK_STATUS_PENDING}
        )
        assert len(pending) >= 1
        assert all(t.status == TASK_STATUS_PENDING for t in pending)
    
    @pytest.mark.asyncio
    async def test_update_task(self, initialized_task_service, sample_user_id):
        """Test actualizar una tarea"""
        task = await initialized_task_service.create_task({
            "title": "Tarea original",
            "user_id": sample_user_id
        })
        
        updated = await initialized_task_service.update_task(task.id, {
            "title": "Tarea actualizada",
            "description": "Nueva descripción"
        })
        
        assert updated is not None
        assert updated.title == "Tarea actualizada"
        assert updated.description == "Nueva descripción"
    
    @pytest.mark.asyncio
    async def test_update_task_status(self, initialized_task_service, sample_user_id):
        """Test actualizar estado de tarea"""
        task = await initialized_task_service.create_task({
            "title": "Tarea",
            "user_id": sample_user_id
        })
        
        updated = await initialized_task_service.update_task(task.id, {
            "status": TASK_STATUS_IN_PROGRESS
        })
        
        assert updated.status == TASK_STATUS_IN_PROGRESS
    
    @pytest.mark.asyncio
    async def test_update_task_not_found(self, initialized_task_service):
        """Test actualizar tarea que no existe"""
        result = await initialized_task_service.update_task("nonexistent", {"title": "Nuevo"})
        assert result is None
    
    @pytest.mark.asyncio
    async def test_delete_task(self, initialized_task_service, sample_user_id):
        """Test eliminar una tarea"""
        task = await initialized_task_service.create_task({
            "title": "Tarea a eliminar",
            "user_id": sample_user_id
        })
        
        deleted = await initialized_task_service.delete_task(task.id)
        assert deleted == True
        
        retrieved = await initialized_task_service.get_task(task.id)
        assert retrieved is None
    
    @pytest.mark.asyncio
    async def test_delete_task_not_found(self, initialized_task_service):
        """Test eliminar tarea que no existe"""
        deleted = await initialized_task_service.delete_task("nonexistent")
        assert deleted == False
    
    @pytest.mark.asyncio
    async def test_create_subtask(self, initialized_task_service, sample_user_id):
        """Test crear una subtarea"""
        task = await initialized_task_service.create_task({
            "title": "Tarea padre",
            "user_id": sample_user_id
        })
        
        subtask = await initialized_task_service.create_subtask(task.id, {
            "title": "Subtarea"
        })
        
        assert subtask is not None
        assert subtask.title == "Subtarea"
        assert subtask.task_id == task.id
    
    @pytest.mark.asyncio
    async def test_create_subtask_task_not_found(self, initialized_task_service):
        """Test crear subtarea en tarea inexistente"""
        result = await initialized_task_service.create_subtask("nonexistent", {
            "title": "Subtarea"
        })
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_subtask(self, initialized_task_service, sample_user_id):
        """Test obtener una subtarea"""
        task = await initialized_task_service.create_task({
            "title": "Tarea",
            "user_id": sample_user_id
        })
        subtask = await initialized_task_service.create_subtask(task.id, {
            "title": "Subtarea"
        })
        
        retrieved = await initialized_task_service.get_subtask(subtask.id)
        assert retrieved is not None
        assert retrieved.id == subtask.id
    
    @pytest.mark.asyncio
    async def test_get_subtasks_by_task(self, initialized_task_service, sample_user_id):
        """Test obtener subtareas de una tarea"""
        task = await initialized_task_service.create_task({
            "title": "Tarea",
            "user_id": sample_user_id
        })
        
        await initialized_task_service.create_subtask(task.id, {"title": "Subtarea 1"})
        await initialized_task_service.create_subtask(task.id, {"title": "Subtarea 2"})
        
        subtasks = await initialized_task_service.get_subtasks_by_task(task.id)
        assert len(subtasks) == 2
    
    @pytest.mark.asyncio
    async def test_update_subtask(self, initialized_task_service, sample_user_id):
        """Test actualizar una subtarea"""
        task = await initialized_task_service.create_task({
            "title": "Tarea",
            "user_id": sample_user_id
        })
        subtask = await initialized_task_service.create_subtask(task.id, {
            "title": "Subtarea original"
        })
        
        updated = await initialized_task_service.update_subtask(subtask.id, {
            "title": "Subtarea actualizada",
            "completed": True
        })
        
        assert updated is not None
        assert updated.title == "Subtarea actualizada"
        assert updated.completed == True
    
    @pytest.mark.asyncio
    async def test_delete_subtask(self, initialized_task_service, sample_user_id):
        """Test eliminar una subtarea"""
        task = await initialized_task_service.create_task({
            "title": "Tarea",
            "user_id": sample_user_id
        })
        subtask = await initialized_task_service.create_subtask(task.id, {
            "title": "Subtarea a eliminar"
        })
        
        deleted = await initialized_task_service.delete_subtask(subtask.id)
        assert deleted == True
        
        retrieved = await initialized_task_service.get_subtask(subtask.id)
        assert retrieved is None
    
    @pytest.mark.asyncio
    async def test_get_tasks_by_status(self, initialized_task_service, sample_user_id):
        """Test obtener tareas por estado"""
        await initialized_task_service.create_task({
            "title": "Pendiente",
            "user_id": sample_user_id,
            "status": TASK_STATUS_PENDING
        })
        await initialized_task_service.create_task({
            "title": "Completada",
            "user_id": sample_user_id,
            "status": TASK_STATUS_COMPLETED
        })
        
        pending = await initialized_task_service.get_tasks_by_status(
            TASK_STATUS_PENDING,
            user_id=sample_user_id
        )
        assert len(pending) >= 1
        assert all(t.status == TASK_STATUS_PENDING for t in pending)
    
    @pytest.mark.asyncio
    async def test_get_tasks_by_quadrant(self, initialized_task_service, sample_user_id):
        """Test obtener tareas por cuadrante"""
        await initialized_task_service.create_task({
            "title": "Q1",
            "user_id": sample_user_id,
            "urgent": True,
            "important": True
        })
        await initialized_task_service.create_task({
            "title": "Q2",
            "user_id": sample_user_id,
            "urgent": False,
            "important": True
        })
        
        q1_tasks = await initialized_task_service.get_tasks_by_quadrant(
            "Q1",
            user_id=sample_user_id
        )
        assert len(q1_tasks) >= 1
        assert all(t.urgent and t.important for t in q1_tasks)
    
    @pytest.mark.asyncio
    async def test_get_overdue_tasks(self, initialized_task_service, sample_user_id):
        """Test obtener tareas vencidas"""
        await initialized_task_service.create_task({
            "title": "Vencida",
            "user_id": sample_user_id,
            "due_date": date.today() - timedelta(days=1)
        })
        
        overdue = await initialized_task_service.get_overdue_tasks(user_id=sample_user_id)
        assert len(overdue) >= 1
    
    @pytest.mark.asyncio
    async def test_get_tasks_due_today(self, initialized_task_service, sample_user_id):
        """Test obtener tareas que vencen hoy"""
        await initialized_task_service.create_task({
            "title": "Vence hoy",
            "user_id": sample_user_id,
            "due_date": date.today()
        })
        
        due_today = await initialized_task_service.get_tasks_due_today(user_id=sample_user_id)
        assert len(due_today) >= 1
    
    @pytest.mark.asyncio
    async def test_search_tasks(self, initialized_task_service, sample_user_id):
        """Test buscar tareas"""
        await initialized_task_service.create_task({
            "title": "Tarea de búsqueda",
            "description": "Esta tarea contiene la palabra clave",
            "user_id": sample_user_id
        })
        await initialized_task_service.create_task({
            "title": "Otra tarea",
            "user_id": sample_user_id
        })
        
        results = await initialized_task_service.search_tasks(
            "búsqueda",
            user_id=sample_user_id
        )
        assert len(results) >= 1
        assert any("búsqueda" in t.title.lower() or "búsqueda" in t.description.lower() for t in results)
    
    @pytest.mark.asyncio
    async def test_get_task_statistics(self, initialized_task_service, sample_user_id):
        """Test obtener estadísticas de tareas"""
        await initialized_task_service.create_task({
            "title": "Pendiente",
            "user_id": sample_user_id,
            "status": TASK_STATUS_PENDING
        })
        await initialized_task_service.create_task({
            "title": "Completada",
            "user_id": sample_user_id,
            "status": TASK_STATUS_COMPLETED
        })
        await initialized_task_service.create_task({
            "title": "Q1",
            "user_id": sample_user_id,
            "urgent": True,
            "important": True
        })
        
        stats = await initialized_task_service.get_task_statistics(user_id=sample_user_id)
        
        assert stats["total"] >= 3
        assert stats["pending"] >= 1
        assert stats["completed"] >= 1
        assert "quadrants" in stats
        assert stats["quadrants"]["Q1"] >= 1

