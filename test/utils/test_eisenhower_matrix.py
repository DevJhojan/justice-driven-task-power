"""
Tests para eisenhower_matrix
"""
import pytest
from app.utils.eisenhower_matrix import (
    get_eisenhower_quadrant,
    get_quadrant_name,
    get_quadrant_description,
    get_quadrant_color,
    get_quadrant_ft_color,
    get_quadrant_icon,
    get_priority_label,
    get_priority_badge_text,
    sort_tasks_by_quadrant,
    get_quadrant_priority_order,
    is_high_priority,
    is_medium_priority,
    is_low_priority,
)


class TestEisenhowerMatrix:
    """Tests para funciones de matriz de Eisenhower"""
    
    def test_get_eisenhower_quadrant_q1(self):
        """Test calcular cuadrante Q1 (urgente e importante)"""
        assert get_eisenhower_quadrant(True, True) == "Q1"
    
    def test_get_eisenhower_quadrant_q2(self):
        """Test calcular cuadrante Q2 (importante pero no urgente)"""
        assert get_eisenhower_quadrant(False, True) == "Q2"
    
    def test_get_eisenhower_quadrant_q3(self):
        """Test calcular cuadrante Q3 (urgente pero no importante)"""
        assert get_eisenhower_quadrant(True, False) == "Q3"
    
    def test_get_eisenhower_quadrant_q4(self):
        """Test calcular cuadrante Q4 (ni urgente ni importante)"""
        assert get_eisenhower_quadrant(False, False) == "Q4"
    
    def test_get_quadrant_name(self):
        """Test obtener nombre de cuadrante"""
        assert get_quadrant_name("Q1") == "Hacer primero"
        assert get_quadrant_name("Q2") == "Programar"
        assert get_quadrant_name("Q3") == "Delegar"
        assert get_quadrant_name("Q4") == "Eliminar"
    
    def test_get_quadrant_description(self):
        """Test obtener descripción de cuadrante"""
        assert "Urgente e Importante" in get_quadrant_description("Q1")
        assert "Importante pero no Urgente" in get_quadrant_description("Q2")
        assert "Urgente pero no Importante" in get_quadrant_description("Q3")
        assert "Ni Urgente ni Importante" in get_quadrant_description("Q4")
    
    def test_get_quadrant_color(self):
        """Test obtener color de cuadrante"""
        assert isinstance(get_quadrant_color("Q1"), str)
        assert get_quadrant_color("Q1").startswith("#")
    
    def test_get_quadrant_ft_color(self):
        """Test obtener color de Flet de cuadrante"""
        import flet as ft
        assert get_quadrant_ft_color("Q1") == ft.Colors.RED_500
        assert get_quadrant_ft_color("Q2") == ft.Colors.BLUE_500
    
    def test_get_quadrant_icon(self):
        """Test obtener icono de cuadrante"""
        import flet as ft
        assert get_quadrant_icon("Q1") == ft.Icons.PRIORITY_HIGH
        assert get_quadrant_icon("Q2") == ft.Icons.SCHEDULE
    
    def test_get_priority_label(self):
        """Test obtener etiqueta de prioridad"""
        assert get_priority_label(True, True) == "Urgente e Importante"
        assert get_priority_label(False, True) == "Importante"
        assert get_priority_label(True, False) == "Urgente"
        assert get_priority_label(False, False) == "Baja Prioridad"
    
    def test_get_priority_badge_text(self):
        """Test obtener texto de badge de prioridad"""
        assert get_priority_badge_text(True, True) == "Q1"
        assert get_priority_badge_text(False, True) == "Q2"
        assert get_priority_badge_text(True, False) == "Q3"
        assert get_priority_badge_text(False, False) == "Q4"
    
    def test_sort_tasks_by_quadrant(self):
        """Test organizar tareas por cuadrante"""
        tasks = [
            {"urgent": True, "important": True, "title": "Q1"},
            {"urgent": False, "important": True, "title": "Q2"},
            {"urgent": True, "important": False, "title": "Q3"},
            {"urgent": False, "important": False, "title": "Q4"},
        ]
        
        sorted_tasks = sort_tasks_by_quadrant(tasks)
        
        assert len(sorted_tasks["Q1"]) == 1
        assert len(sorted_tasks["Q2"]) == 1
        assert len(sorted_tasks["Q3"]) == 1
        assert len(sorted_tasks["Q4"]) == 1
        assert sorted_tasks["Q1"][0]["title"] == "Q1"
    
    def test_get_quadrant_priority_order(self):
        """Test obtener orden de prioridad de cuadrantes"""
        order = get_quadrant_priority_order()
        assert order == ["Q1", "Q2", "Q3", "Q4"]
    
    def test_is_high_priority(self):
        """Test verificar alta prioridad (Q1)"""
        assert is_high_priority(True, True) == True
        assert is_high_priority(False, True) == False
        assert is_high_priority(True, False) == False
        assert is_high_priority(False, False) == False
    
    def test_is_medium_priority(self):
        """Test verificar prioridad media (Q2)"""
        assert is_medium_priority(False, True) == True  # Q2
        assert is_medium_priority(True, False) == False  # Q3 (no es media según código)
        assert is_medium_priority(True, True) == False  # Q1
        assert is_medium_priority(False, False) == False  # Q4
    
    def test_is_low_priority(self):
        """Test verificar baja prioridad (Q3 o Q4 - no importante)"""
        assert is_low_priority(False, False) == True  # Q4
        assert is_low_priority(True, False) == True  # Q3 (no importante)
        assert is_low_priority(True, True) == False  # Q1
        assert is_low_priority(False, True) == False  # Q2

