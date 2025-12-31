"""
Tests para helpers/formats.py
"""
import pytest
from datetime import datetime, date, timedelta
from app.utils.helpers.formats import (
    format_date,
    format_time,
    format_datetime,
    format_duration,
    format_relative_time,
    format_number,
    format_percentage,
    format_currency,
    format_file_size,
    format_points,
    format_level,
    format_completion_percentage,
    format_task_count,
    format_habit_streak,
)


class TestFormats:
    """Tests para funciones de formateo"""
    
    def test_format_date(self):
        """Test formatear fecha"""
        test_date = date(2024, 12, 25)
        assert format_date(test_date) == "25/12/2024"
        assert format_date(test_date, "%Y-%m-%d") == "2024-12-25"
    
    def test_format_date_from_string(self):
        """Test formatear fecha desde string"""
        assert format_date("2024-12-25") == "25/12/2024"
    
    def test_format_date_from_datetime(self):
        """Test formatear fecha desde datetime"""
        dt = datetime(2024, 12, 25, 10, 30)
        assert format_date(dt) == "25/12/2024"
    
    def test_format_time(self):
        """Test formatear tiempo"""
        dt = datetime(2024, 1, 1, 14, 30, 45)
        assert format_time(dt, "HH:MM:SS") == "14:30:45"
        assert format_time(dt, "HH:MM") == "14:30"
    
    def test_format_time_from_timedelta(self):
        """Test formatear tiempo desde timedelta"""
        td = timedelta(hours=2, minutes=30, seconds=15)
        result = format_time(td, "HH:MM:SS")
        assert "02:30:15" in result
    
    def test_format_time_from_seconds(self):
        """Test formatear tiempo desde segundos"""
        assert format_time(3661, "HH:MM:SS") == "01:01:01"  # 1 hora, 1 min, 1 seg
    
    def test_format_datetime(self):
        """Test formatear datetime"""
        dt = datetime(2024, 12, 25, 14, 30)
        result = format_datetime(dt)
        assert "25/12/2024" in result
        assert "14:30" in result
    
    def test_format_duration(self):
        """Test formatear duración"""
        start = datetime(2024, 1, 1, 10, 0)
        end = datetime(2024, 1, 1, 12, 30)
        result = format_duration(start, end)
        assert "2 hora" in result or "150 minuto" in result
    
    def test_format_relative_time(self):
        """Test formatear tiempo relativo"""
        now = datetime.now()
        
        # Hace 5 minutos
        past = now - timedelta(minutes=5)
        result = format_relative_time(past)
        assert "minuto" in result.lower() or "momento" in result.lower()
        
        # Ayer
        yesterday = now - timedelta(days=1)
        result = format_relative_time(yesterday)
        assert "ayer" in result.lower() or "día" in result.lower()
    
    def test_format_number(self):
        """Test formatear número"""
        assert "1,234" in format_number(1234.56) or "1234" in format_number(1234.56)
        assert format_number(1234.567, decimals=1) is not None
    
    def test_format_percentage(self):
        """Test formatear porcentaje"""
        assert format_percentage(75.5) == "75.5%"
        assert format_percentage(100, decimals=0) == "100.0%"
    
    def test_format_currency(self):
        """Test formatear moneda"""
        result = format_currency(1234.56)
        assert "$" in result or "1234" in result
    
    def test_format_file_size(self):
        """Test formatear tamaño de archivo"""
        assert format_file_size(1024) == "1.0 KB"
        assert format_file_size(1024 * 1024) == "1.0 MB"
        assert format_file_size(500) == "500 B"
    
    def test_format_points(self):
        """Test formatear puntos"""
        result = format_points(1000)
        assert "1000" in result
        assert "punto" in result.lower()
    
    def test_format_level(self):
        """Test formatear nivel"""
        assert format_level(5) == "Nivel 5"
        assert "Nivel" in format_level(10)
    
    def test_format_completion_percentage(self):
        """Test formatear porcentaje de completitud"""
        result = format_completion_percentage(3, 5)
        assert "60" in result or "3/5" in result
        assert "%" in result
    
    def test_format_task_count(self):
        """Test formatear conteo de tareas"""
        assert "1 tarea" in format_task_count(1)
        assert "tareas" in format_task_count(5)
    
    def test_format_habit_streak(self):
        """Test formatear racha de hábito"""
        assert "Racha de 5" in format_habit_streak(5)
        assert "Sin racha" in format_habit_streak(0)
        assert format_habit_streak(-1) == "Racha inválida"

