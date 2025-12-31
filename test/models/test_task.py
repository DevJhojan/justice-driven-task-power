"""
Tests para el modelo Task
"""
import pytest
from datetime import datetime, date, timedelta
from app.models.task import Task
from app.models.subtask import Subtask
from app.utils.task_helper import (
    TASK_STATUS_PENDING,
    TASK_STATUS_IN_PROGRESS,
    TASK_STATUS_COMPLETED,
    TASK_STATUS_CANCELLED,
    VALID_TASK_STATUSES,
)


class TestTask:
    """Tests para la clase Task"""
    
    def test_create_task_basic(self):
        """Test crear una tarea básica"""
        task = Task(
            id="test_1",
            title="Tarea de prueba",
            user_id="user_1"
        )
        assert task.title == "Tarea de prueba"
        assert task.status == TASK_STATUS_PENDING
        assert task.user_id == "user_1"
        assert task.urgent == False
        assert task.important == False
        assert len(task.subtasks) == 0
    
    def test_create_task_with_all_fields(self):
        """Test crear una tarea con todos los campos"""
        due_date = date.today() + timedelta(days=7)
        task = Task(
            id="test_2",
            title="Tarea completa",
            description="Descripción completa",
            status=TASK_STATUS_IN_PROGRESS,
            urgent=True,
            important=True,
            due_date=due_date,
            user_id="user_1",
            tags=["trabajo", "importante"],
            notes="Notas adicionales"
        )
        assert task.title == "Tarea completa"
        assert task.description == "Descripción completa"
        assert task.status == TASK_STATUS_IN_PROGRESS
        assert task.urgent == True
        assert task.important == True
        assert task.due_date == due_date
        assert task.tags == ["trabajo", "importante"]
        assert task.notes == "Notas adicionales"
    
    def test_task_validation_empty_title(self):
        """Test validación de título vacío"""
        with pytest.raises(ValueError, match="título.*vacío"):
            Task(id="test_1", title="", user_id="user_1")
        
        with pytest.raises(ValueError, match="título.*vacío"):
            Task(id="test_1", title="   ", user_id="user_1")
    
    def test_task_validation_invalid_status(self):
        """Test validación de estado inválido"""
        with pytest.raises(ValueError, match="Estado inválido"):
            Task(id="test_1", title="Test", user_id="user_1", status="estado_invalido")
    
    def test_add_subtask(self):
        """Test agregar subtarea a una tarea"""
        task = Task(id="test_1", title="Test", user_id="user_1")
        subtask = Subtask(id="sub_1", task_id="test_1", title="Subtarea")
        
        task.add_subtask(subtask)
        
        assert len(task.subtasks) == 1
        assert task.subtasks[0].id == "sub_1"
        assert task.subtasks[0].task_id == "test_1"
    
    def test_add_subtask_auto_fix_task_id(self):
        """Test que add_subtask corrige el task_id si no coincide"""
        task = Task(id="test_1", title="Test", user_id="user_1")
        subtask = Subtask(id="sub_1", task_id="wrong_id", title="Subtarea")
        
        task.add_subtask(subtask)
        
        assert subtask.task_id == "test_1"
    
    def test_remove_subtask(self):
        """Test eliminar subtarea"""
        task = Task(id="test_1", title="Test", user_id="user_1")
        subtask1 = Subtask(id="sub_1", task_id="test_1", title="Subtarea 1")
        subtask2 = Subtask(id="sub_2", task_id="test_1", title="Subtarea 2")
        
        task.add_subtask(subtask1)
        task.add_subtask(subtask2)
        assert len(task.subtasks) == 2
        
        task.remove_subtask("sub_1")
        
        assert len(task.subtasks) == 1
        assert task.subtasks[0].id == "sub_2"
    
    def test_update_status(self):
        """Test actualizar estado de tarea"""
        task = Task(id="test_1", title="Test", user_id="user_1")
        assert task.status == TASK_STATUS_PENDING
        
        task.update_status(TASK_STATUS_IN_PROGRESS)
        assert task.status == TASK_STATUS_IN_PROGRESS
        
        task.update_status(TASK_STATUS_COMPLETED)
        assert task.status == TASK_STATUS_COMPLETED
    
    def test_update_status_invalid(self):
        """Test actualizar estado inválido"""
        task = Task(id="test_1", title="Test", user_id="user_1")
        
        with pytest.raises(ValueError, match="Estado inválido"):
            task.update_status("estado_invalido")
    
    def test_set_priority(self):
        """Test establecer prioridad"""
        task = Task(id="test_1", title="Test", user_id="user_1")
        
        task.set_priority(urgent=True, important=True)
        assert task.urgent == True
        assert task.important == True
        
        task.set_priority(urgent=False, important=True)
        assert task.urgent == False
        assert task.important == True
    
    def test_mark_as_completed(self):
        """Test marcar tarea como completada"""
        task = Task(id="test_1", title="Test", user_id="user_1")
        task.mark_as_completed()
        assert task.status == TASK_STATUS_COMPLETED
    
    def test_mark_as_in_progress(self):
        """Test marcar tarea como en progreso"""
        task = Task(id="test_1", title="Test", user_id="user_1")
        task.mark_as_in_progress()
        assert task.status == TASK_STATUS_IN_PROGRESS
    
    def test_mark_as_pending(self):
        """Test marcar tarea como pendiente"""
        task = Task(id="test_1", title="Test", user_id="user_1", status=TASK_STATUS_COMPLETED)
        task.mark_as_pending()
        assert task.status == TASK_STATUS_PENDING
    
    def test_cancel(self):
        """Test cancelar tarea"""
        task = Task(id="test_1", title="Test", user_id="user_1")
        task.cancel()
        assert task.status == TASK_STATUS_CANCELLED
    
    def test_to_dict(self):
        """Test conversión a diccionario"""
        due_date = date.today()
        task = Task(
            id="test_1",
            title="Test",
            description="Descripción",
            user_id="user_1",
            due_date=due_date,
            tags=["tag1", "tag2"]
        )
        subtask = Subtask(id="sub_1", task_id="test_1", title="Subtarea")
        task.add_subtask(subtask)
        
        task_dict = task.to_dict()
        
        assert task_dict["id"] == "test_1"
        assert task_dict["title"] == "Test"
        assert task_dict["description"] == "Descripción"
        assert task_dict["user_id"] == "user_1"
        assert task_dict["due_date"] == due_date.isoformat()
        assert task_dict["tags"] == ["tag1", "tag2"]
        assert isinstance(task_dict["created_at"], str)
        assert isinstance(task_dict["updated_at"], str)
        assert len(task_dict["subtasks"]) == 1
        assert task_dict["subtasks"][0]["id"] == "sub_1"
    
    def test_to_dict_no_due_date(self):
        """Test to_dict cuando no hay fecha de vencimiento"""
        task = Task(id="test_1", title="Test", user_id="user_1")
        task_dict = task.to_dict()
        assert task_dict["due_date"] is None
    
    def test_from_dict(self):
        """Test crear tarea desde diccionario"""
        task_dict = {
            "id": "test_1",
            "title": "Tarea desde dict",
            "description": "Descripción",
            "status": TASK_STATUS_PENDING,
            "urgent": True,
            "important": False,
            "due_date": date.today().isoformat(),
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "subtasks": [],
            "user_id": "user_1",
            "tags": ["tag1"],
            "notes": "Notas"
        }
        
        task = Task.from_dict(task_dict)
        
        assert task.id == "test_1"
        assert task.title == "Tarea desde dict"
        assert task.description == "Descripción"
        assert task.status == TASK_STATUS_PENDING
        assert task.urgent == True
        assert task.important == False
        assert isinstance(task.due_date, date)
        assert task.user_id == "user_1"
        assert task.tags == ["tag1"]
        assert task.notes == "Notas"
    
    def test_from_dict_with_subtasks(self):
        """Test crear tarea desde diccionario con subtareas"""
        task_dict = {
            "id": "test_1",
            "title": "Tarea con subtareas",
            "description": "",
            "status": TASK_STATUS_PENDING,
            "urgent": False,
            "important": False,
            "due_date": None,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "subtasks": [
                {
                    "id": "sub_1",
                    "task_id": "test_1",
                    "title": "Subtarea 1",
                    "completed": False,
                    "urgent": False,
                    "important": False,
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat(),
                    "notes": ""
                }
            ],
            "user_id": "user_1",
            "tags": [],
            "notes": ""
        }
        
        task = Task.from_dict(task_dict)
        
        assert len(task.subtasks) == 1
        assert task.subtasks[0].id == "sub_1"
        assert task.subtasks[0].title == "Subtarea 1"
    
    def test_from_dict_date_objects(self):
        """Test from_dict con objetos date/datetime en lugar de strings"""
        task_dict = {
            "id": "test_1",
            "title": "Test",
            "description": "",
            "status": TASK_STATUS_PENDING,
            "urgent": False,
            "important": False,
            "due_date": date.today(),
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "subtasks": [],
            "user_id": "user_1",
            "tags": [],
            "notes": ""
        }
        
        task = Task.from_dict(task_dict)
        
        assert isinstance(task.due_date, date)
        assert isinstance(task.created_at, datetime)
        assert isinstance(task.updated_at, datetime)
    
    def test_repr(self):
        """Test representación string de la tarea"""
        task = Task(id="test_1", title="Tarea de prueba", user_id="user_1")
        repr_str = repr(task)
        
        assert "Task" in repr_str
        assert "test_1" in repr_str
        assert "Tarea de prueba" in repr_str
        assert TASK_STATUS_PENDING in repr_str
    
    def test_updated_at_changes_on_modification(self):
        """Test que updated_at se actualiza al modificar la tarea"""
        task = Task(id="test_1", title="Test", user_id="user_1")
        original_updated = task.updated_at
        
        # Esperar un poco para asegurar diferencia de tiempo
        import time
        time.sleep(0.01)
        
        task.update_status(TASK_STATUS_IN_PROGRESS)
        
        assert task.updated_at > original_updated

