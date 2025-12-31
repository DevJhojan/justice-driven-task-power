"""
Configuración compartida para todos los tests
Fixtures y configuraciones globales genéricas
"""
import pytest
import asyncio
from pathlib import Path
import sys
import tempfile
import os
from datetime import datetime, date

# Agregar el directorio raíz al path para imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# ============================================================================
# CONFIGURACIÓN DE EVENT LOOP PARA TESTS ASÍNCRONOS
# ============================================================================

@pytest.fixture(scope="session")
def event_loop():
    """
    Crear event loop para tests asíncronos
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

# ============================================================================
# FIXTURES DE DATOS GENÉRICOS
# ============================================================================

@pytest.fixture
def sample_user_id():
    """ID de usuario de prueba genérico"""
    return "test_user_123"

# ============================================================================
# FIXTURES DE BASE DE DATOS
# ============================================================================

@pytest.fixture
async def temp_database():
    """
    Crea una base de datos temporal para tests
    Retorna la ruta del archivo temporal
    """
    temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    temp_db.close()
    db_path = temp_db.name
    
    yield db_path
    
    # Limpiar después del test
    if os.path.exists(db_path):
        os.unlink(db_path)

@pytest.fixture
async def database_service(temp_database):
    """
    Crea un DatabaseService con base de datos temporal
    """
    from app.services.database_service import DatabaseService
    service = DatabaseService(db_path=temp_database)
    yield service
    await service.disconnect()

# ============================================================================
# FIXTURES DE UTILIDADES
# ============================================================================

@pytest.fixture
def mock_datetime():
    """Fecha/hora fija para tests"""
    return datetime(2024, 1, 15, 10, 30, 0)

@pytest.fixture
def mock_date():
    """Fecha fija para tests"""
    return date(2024, 1, 15)

@pytest.fixture
def mock_date_today():
    """Fecha de hoy para tests"""
    return date.today()

@pytest.fixture
def mock_date_future():
    """Fecha futura para tests (7 días desde hoy)"""
    from datetime import timedelta
    return date.today() + timedelta(days=7)

@pytest.fixture
def mock_date_past():
    """Fecha pasada para tests (1 día antes de hoy)"""
    from datetime import timedelta
    return date.today() - timedelta(days=1)

# ============================================================================
# FIXTURES PARA TESTS DE UI (Flet)
# ============================================================================

@pytest.fixture
def mock_page():
    """
    Mock de página de Flet para tests de UI
    """
    from unittest.mock import MagicMock
    page = MagicMock()
    page.window.width = 800
    page.window.height = 600
    page.theme_mode = "dark"
    return page
