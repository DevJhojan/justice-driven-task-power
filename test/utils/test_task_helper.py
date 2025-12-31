"""
Tests para task_helper
"""
import pytest
from datetime import date, timedelta
from app.utils.task_helper import (
    TASK_STATUS_PENDING,
    TASK_STATUS_IN_PROGRESS,
    TASK_STATUS_COMPLETED,
    TASK_STATUS_CANCELLED,
    format_task_status,
    get_task_status_color,
    get_task_status_ft_color,
    get_task_status_icon,
    calculate_completion_percentage,
    format_completion_percentage,
    is_task_overdue,
    is_task_due_today,
    is_task_due_soon,
    get_task_urgency_indicator,
    count_subtasks,
    count_completed_subtasks,
    has_subtasks,
    is_task_completed,
    is_task_pending,
    is_task_in_progress,
    filter_tasks_by_status,
)
from app.models.task import Task
from app.models.subtask import Subtask


class TestTaskHelper:
    """Tests para funciones de task_helper"""
    
    def test_format_task_status(self):
        """Test formateo de estado"""
        assert format_task_status(TASK_STATUS_PENDING) == "Pendiente"
        assert format_task_status(TASK_STATUS_IN_PROGRESS) == "En Progreso"
        assert format_task_status(TASK_STATUS_COMPLETED) == "Completada"
        assert format_task_status(TASK_STATUS_CANCELLED) == "Cancelada"
    
    def test_get_task_status_color(self):
        """Test obtener color de estado"""
        assert get_task_status_color(TASK_STATUS_PENDING) == "#F59E0B"
        assert get_task_status_color(TASK_STATUS_COMPLETED) == "#10B981"
        assert isinstance(get_task_status_color("unknown"), str)
    
    def test_get_task_status_ft_color(self):
        """Test obtener color de Flet"""
        import flet as ft
        assert get_task_status_ft_color(TASK_STATUS_PENDING) == ft.Colors.ORANGE_500
        assert get_task_status_ft_color(TASK_STATUS_COMPLETED) == ft.Colors.GREEN_500
    
    def test_get_task_status_icon(self):
        """Test obtener icono de estado"""
        import flet as ft
        assert get_task_status_icon(TASK_STATUS_PENDING) == ft.Icons.HOURGLASS_EMPTY
        assert get_task_status_icon(TASK_STATUS_COMPLETED) == ft.Icons.CHECK_CIRCLE
    
    def test_calculate_completion_percentage_no_subtasks(self):
        """Test calcular porcentaje sin subtareas"""
        task = Task(id="test_1", title="Test", user_id="user_1")
        assert calculate_completion_percentage(task) == 0.0
    
    def test_calculate_completion_percentage_with_subtasks(self):
        """Test calcular porcentaje con subtareas"""
        task = Task(id="test_1", title="Test", user_id="user_1")
        subtask1 = Subtask(id="sub_1", task_id="test_1", title="Sub 1", completed=True)
        subtask2 = Subtask(id="sub_2", task_id="test_1", title="Sub 2", completed=False)
        task.add_subtask(subtask1)
        task.add_subtask(subtask2)
        
        assert calculate_completion_percentage(task) == 50.0
    
    def test_calculate_completion_percentage_all_completed(self):
        """Test calcular porcentaje con todas completadas"""
        task = Task(id="test_1", title="Test", user_id="user_1")
        subtask1 = Subtask(id="sub_1", task_id="test_1", title="Sub 1", completed=True)
        subtask2 = Subtask(id="sub_2", task_id="test_1", title="Sub 2", completed=True)
        task.add_subtask(subtask1)
        task.add_subtask(subtask2)
        
        assert calculate_completion_percentage(task) == 100.0
    
    def test_format_completion_percentage(self):
        """Test formatear porcentaje de completitud"""
        task = Task(id="test_1", title="Test", user_id="user_1")
        subtask1 = Subtask(id="sub_1", task_id="test_1", title="Sub 1", completed=True)
        subtask2 = Subtask(id="sub_2", task_id="test_1", title="Sub 2", completed=False)
        task.add_subtask(subtask1)
        task.add_subtask(subtask2)
        
        result = format_completion_percentage(task)
        assert "50" in result
        assert "1/2" in result
    
    def test_is_task_overdue(self):
        """Test verificar si tarea está vencida"""
        task = Task(
            id="test_1",
            title="Test",
            user_id="user_1",
            due_date=date.today() - timedelta(days=1),
            status=TASK_STATUS_PENDING
        )
        assert is_task_overdue(task) == True
        
        task.due_date = date.today() + timedelta(days=1)
        assert is_task_overdue(task) == False
        
        task.status = TASK_STATUS_COMPLETED
        assert is_task_overdue(task) == False
    
    def test_is_task_overdue_no_due_date(self):
        """Test is_task_overdue sin fecha de vencimiento"""
        task = Task(id="test_1", title="Test", user_id="user_1")
        assert is_task_overdue(task) == False
    
    def test_is_task_due_today(self):
        """Test verificar si tarea vence hoy"""
        task = Task(
            id="test_1",
            title="Test",
            user_id="user_1",
            due_date=date.today(),
            status=TASK_STATUS_PENDING
        )
        assert is_task_due_today(task) == True
        
        task.due_date = date.today() + timedelta(days=1)
        assert is_task_due_today(task) == False
    
    def test_is_task_due_soon(self):
        """Test verificar si tarea vence pronto"""
        task = Task(
            id="test_1",
            title="Test",
            user_id="user_1",
            due_date=date.today() + timedelta(days=2),
            status=TASK_STATUS_PENDING
        )
        assert is_task_due_soon(task, days=3) == True
        
        task.due_date = date.today() + timedelta(days=5)
        assert is_task_due_soon(task, days=3) == False
    
    def test_get_task_urgency_indicator(self):
        """Test obtener indicador de urgencia"""
        overdue_task = Task(
            id="test_1",
            title="Test",
            user_id="user_1",
            due_date=date.today() - timedelta(days=1),
            status=TASK_STATUS_PENDING
        )
        assert "🔴" in get_task_urgency_indicator(overdue_task)
        
        today_task = Task(
            id="test_2",
            title="Test",
            user_id="user_1",
            due_date=date.today(),
            status=TASK_STATUS_PENDING
        )
        assert "🟠" in get_task_urgency_indicator(today_task)
        
        soon_task = Task(
            id="test_3",
            title="Test",
            user_id="user_1",
            due_date=date.today() + timedelta(days=2),
            status=TASK_STATUS_PENDING
        )
        assert "🟡" in get_task_urgency_indicator(soon_task)
    
    def test_count_subtasks(self):
        """Test contar subtareas"""
        task = Task(id="test_1", title="Test", user_id="user_1")
        assert count_subtasks(task) == 0
        
        task.add_subtask(Subtask(id="sub_1", task_id="test_1", title="Sub 1"))
        task.add_subtask(Subtask(id="sub_2", task_id="test_1", title="Sub 2"))
        assert count_subtasks(task) == 2
    
    def test_count_completed_subtasks(self):
        """Test contar subtareas completadas"""
        task = Task(id="test_1", title="Test", user_id="user_1")
        task.add_subtask(Subtask(id="sub_1", task_id="test_1", title="Sub 1", completed=True))
        task.add_subtask(Subtask(id="sub_2", task_id="test_1", title="Sub 2", completed=False))
        task.add_subtask(Subtask(id="sub_3", task_id="test_1", title="Sub 3", completed=True))
        
        assert count_completed_subtasks(task) == 2
    
    def test_has_subtasks(self):
        """Test verificar si tiene subtareas"""
        task = Task(id="test_1", title="Test", user_id="user_1")
        assert has_subtasks(task) == False
        
        task.add_subtask(Subtask(id="sub_1", task_id="test_1", title="Sub 1"))
        assert has_subtasks(task) == True
    
    def test_is_task_completed(self):
        """Test verificar si tarea está completada"""
        task = Task(id="test_1", title="Test", user_id="user_1", status=TASK_STATUS_COMPLETED)
        assert is_task_completed(task) == True
        
        task.status = TASK_STATUS_PENDING
        assert is_task_completed(task) == False
    
    def test_is_task_pending(self):
        """Test verificar si tarea está pendiente"""
        task = Task(id="test_1", title="Test", user_id="user_1", status=TASK_STATUS_PENDING)
        assert is_task_pending(task) == True
        
        task.status = TASK_STATUS_COMPLETED
        assert is_task_pending(task) == False
    
    def test_is_task_in_progress(self):
        """Test verificar si tarea está en progreso"""
        task = Task(id="test_1", title="Test", user_id="user_1", status=TASK_STATUS_IN_PROGRESS)
        assert is_task_in_progress(task) == True
        
        task.status = TASK_STATUS_PENDING
        assert is_task_in_progress(task) == False
    
    def test_filter_tasks_by_status(self):
        """Test filtrar tareas por estado"""
        tasks = [
            Task(id="t1", title="T1", user_id="u1", status=TASK_STATUS_PENDING),
            Task(id="t2", title="T2", user_id="u1", status=TASK_STATUS_COMPLETED),
            Task(id="t3", title="T3", user_id="u1", status=TASK_STATUS_PENDING),
        ]
        
        pending = filter_tasks_by_status(tasks, TASK_STATUS_PENDING)
        assert len(pending) == 2
        assert all(t.status == TASK_STATUS_PENDING for t in pending)
        
        completed = filter_tasks_by_status(tasks, TASK_STATUS_COMPLETED)
        assert len(completed) == 1

