"""
Tests para el modelo Subtask
"""
import pytest
from datetime import datetime
from app.models.subtask import Subtask


class TestSubtask:
    """Tests para la clase Subtask"""
    
    def test_create_subtask_basic(self):
        """Test crear una subtarea básica"""
        subtask = Subtask(
            id="sub_1",
            task_id="task_1",
            title="Subtarea de prueba"
        )
        assert subtask.id == "sub_1"
        assert subtask.task_id == "task_1"
        assert subtask.title == "Subtarea de prueba"
        assert subtask.completed == False
        assert subtask.urgent == False
        assert subtask.important == False
    
    def test_create_subtask_with_all_fields(self):
        """Test crear subtarea con todos los campos"""
        subtask = Subtask(
            id="sub_1",
            task_id="task_1",
            title="Subtarea completa",
            completed=True,
            urgent=True,
            important=True,
            notes="Notas de la subtarea"
        )
        assert subtask.completed == True
        assert subtask.urgent == True
        assert subtask.important == True
        assert subtask.notes == "Notas de la subtarea"
    
    def test_subtask_validation_empty_title(self):
        """Test validación de título vacío"""
        with pytest.raises(ValueError, match="título.*vacío"):
            Subtask(id="sub_1", task_id="task_1", title="")
        
        with pytest.raises(ValueError, match="título.*vacío"):
            Subtask(id="sub_1", task_id="task_1", title="   ")
    
    def test_toggle_completed(self):
        """Test alternar estado completado"""
        subtask = Subtask(id="sub_1", task_id="task_1", title="Subtarea")
        assert subtask.completed == False
        
        subtask.toggle_completed()
        assert subtask.completed == True
        
        subtask.toggle_completed()
        assert subtask.completed == False
    
    def test_mark_as_completed(self):
        """Test marcar subtarea como completada"""
        subtask = Subtask(id="sub_1", task_id="task_1", title="Subtarea")
        subtask.mark_as_completed()
        assert subtask.completed == True
    
    def test_mark_as_pending(self):
        """Test marcar subtarea como pendiente"""
        subtask = Subtask(
            id="sub_1",
            task_id="task_1",
            title="Subtarea",
            completed=True
        )
        subtask.mark_as_pending()
        assert subtask.completed == False
    
    def test_set_priority(self):
        """Test establecer prioridad"""
        subtask = Subtask(id="sub_1", task_id="task_1", title="Subtarea")
        
        subtask.set_priority(urgent=True, important=True)
        assert subtask.urgent == True
        assert subtask.important == True
        
        subtask.set_priority(urgent=False, important=True)
        assert subtask.urgent == False
        assert subtask.important == True
    
    def test_to_dict(self):
        """Test conversión a diccionario"""
        subtask = Subtask(
            id="sub_1",
            task_id="task_1",
            title="Subtarea",
            completed=True,
            urgent=True,
            important=False,
            notes="Notas"
        )
        
        subtask_dict = subtask.to_dict()
        
        assert subtask_dict["id"] == "sub_1"
        assert subtask_dict["task_id"] == "task_1"
        assert subtask_dict["title"] == "Subtarea"
        assert subtask_dict["completed"] == True
        assert subtask_dict["urgent"] == True
        assert subtask_dict["important"] == False
        assert subtask_dict["notes"] == "Notas"
        assert isinstance(subtask_dict["created_at"], str)
        assert isinstance(subtask_dict["updated_at"], str)
    
    def test_from_dict(self):
        """Test crear subtarea desde diccionario"""
        subtask_dict = {
            "id": "sub_1",
            "task_id": "task_1",
            "title": "Subtarea desde dict",
            "completed": True,
            "urgent": False,
            "important": True,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "notes": "Notas desde dict"
        }
        
        subtask = Subtask.from_dict(subtask_dict)
        
        assert subtask.id == "sub_1"
        assert subtask.task_id == "task_1"
        assert subtask.title == "Subtarea desde dict"
        assert subtask.completed == True
        assert subtask.urgent == False
        assert subtask.important == True
        assert subtask.notes == "Notas desde dict"
    
    def test_from_dict_datetime_objects(self):
        """Test from_dict con objetos datetime en lugar de strings"""
        subtask_dict = {
            "id": "sub_1",
            "task_id": "task_1",
            "title": "Subtarea",
            "completed": False,
            "urgent": False,
            "important": False,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "notes": ""
        }
        
        subtask = Subtask.from_dict(subtask_dict)
        
        assert isinstance(subtask.created_at, datetime)
        assert isinstance(subtask.updated_at, datetime)
    
    def test_from_dict_defaults(self):
        """Test from_dict con valores por defecto"""
        subtask_dict = {
            "id": "sub_1",
            "task_id": "task_1",
            "title": "Subtarea"
        }
        
        subtask = Subtask.from_dict(subtask_dict)
        
        assert subtask.completed == False
        assert subtask.urgent == False
        assert subtask.important == False
        assert subtask.notes == ""
        assert isinstance(subtask.created_at, datetime)
        assert isinstance(subtask.updated_at, datetime)
    
    def test_repr(self):
        """Test representación string de la subtarea"""
        subtask_completed = Subtask(
            id="sub_1",
            task_id="task_1",
            title="Subtarea completada",
            completed=True
        )
        repr_str = repr(subtask_completed)
        
        assert "Subtask" in repr_str
        assert "sub_1" in repr_str
        assert "Subtarea completada" in repr_str
        assert "✓" in repr_str
        
        subtask_pending = Subtask(
            id="sub_2",
            task_id="task_1",
            title="Subtarea pendiente",
            completed=False
        )
        repr_str = repr(subtask_pending)
        assert "○" in repr_str
    
    def test_updated_at_changes_on_modification(self):
        """Test que updated_at se actualiza al modificar la subtarea"""
        subtask = Subtask(id="sub_1", task_id="task_1", title="Subtarea")
        original_updated = subtask.updated_at
        
        # Esperar un poco para asegurar diferencia de tiempo
        import time
        time.sleep(0.01)
        
        subtask.toggle_completed()
        
        assert subtask.updated_at > original_updated

