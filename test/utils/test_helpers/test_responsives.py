"""
Tests para helpers/responsives.py
"""
import pytest
from unittest.mock import MagicMock
from app.utils.helpers.responsives import (
    MOBILE_BREAKPOINT,
    TABLET_BREAKPOINT,
    DESKTOP_BREAKPOINT,
    get_responsive_padding,
    get_responsive_size,
    get_responsive_icon_size,
    get_responsive_width,
    get_responsive_max_width,
    get_responsive_columns,
    get_responsive_spacing,
    get_responsive_card_width,
    get_responsive_border_radius,
    get_responsive_elevation,
    is_mobile,
    is_tablet,
    is_desktop,
    get_device_type,
)


class TestResponsives:
    """Tests para funciones responsive"""
    
    def test_breakpoints(self):
        """Test que los breakpoints están definidos"""
        assert MOBILE_BREAKPOINT == 600
        assert TABLET_BREAKPOINT == 900
        assert DESKTOP_BREAKPOINT == 1200
    
    def test_get_responsive_padding_mobile(self):
        """Test padding en móvil"""
        assert get_responsive_padding(window_width=500) == 10
        assert get_responsive_padding(window_width=MOBILE_BREAKPOINT - 1) == 10
    
    def test_get_responsive_padding_desktop(self):
        """Test padding en desktop"""
        assert get_responsive_padding(window_width=800) == 20
        assert get_responsive_padding(window_width=MOBILE_BREAKPOINT) == 20
    
    def test_get_responsive_padding_with_page(self):
        """Test padding con objeto page"""
        page = MagicMock()
        page.window.width = 500
        assert get_responsive_padding(page=page) == 10
        
        page.window.width = 800
        assert get_responsive_padding(page=page) == 20
    
    def test_get_responsive_size(self):
        """Test tamaño responsive"""
        assert get_responsive_size(window_width=500) == 14  # Mobile
        assert get_responsive_size(window_width=700) == 16  # Tablet
        assert get_responsive_size(window_width=1000) == 18  # Desktop
    
    def test_get_responsive_icon_size(self):
        """Test tamaño de icono responsive"""
        assert get_responsive_icon_size(window_width=500) == 24  # Mobile
        assert get_responsive_icon_size(window_width=700) == 32  # Tablet
        assert get_responsive_icon_size(window_width=1000) == 40  # Desktop
    
    def test_get_responsive_width(self):
        """Test ancho responsive"""
        width = get_responsive_width(window_width=800)
        assert width < 800  # Debe restar padding
        assert width > 0
    
    def test_get_responsive_width_with_max(self):
        """Test ancho responsive con máximo"""
        width = get_responsive_width(window_width=2000, max_width=1200)
        assert width <= 1200
    
    def test_get_responsive_max_width(self):
        """Test ancho máximo responsive"""
        from app.utils.helpers.responsives import get_responsive_max_width
        # La función devuelve None si no se pasan parámetros
        result = get_responsive_max_width(window_width=500)
        assert result is None  # Sin parámetros devuelve None
        
        # Con parámetros devuelve el valor correspondiente
        result = get_responsive_max_width(window_width=500, mobile=400, tablet=600, desktop=800)
        assert result == 400
    
    def test_get_responsive_columns(self):
        """Test columnas responsive"""
        assert get_responsive_columns(window_width=500) == 1  # Mobile
        assert get_responsive_columns(window_width=700) == 2  # Tablet
        assert get_responsive_columns(window_width=1000) == 3  # Desktop
    
    def test_get_responsive_spacing(self):
        """Test espaciado responsive"""
        assert get_responsive_spacing(window_width=500) == 8  # Mobile
        assert get_responsive_spacing(window_width=700) == 12  # Tablet
        assert get_responsive_spacing(window_width=1000) == 16  # Desktop
    
    def test_get_responsive_card_width(self):
        """Test ancho de tarjeta responsive"""
        # La función devuelve -1 para móvil (expand) o un valor calculado
        result = get_responsive_card_width(window_width=500)
        assert result == -1 or result > 0  # -1 indica expand en Flet para 1 columna
    
    def test_get_responsive_border_radius(self):
        """Test radio de borde responsive"""
        assert get_responsive_border_radius(window_width=500) == 8  # Mobile
        assert get_responsive_border_radius(window_width=700) == 10  # Tablet
        assert get_responsive_border_radius(window_width=1000) == 12  # Desktop
    
    def test_get_responsive_elevation(self):
        """Test elevación responsive"""
        assert get_responsive_elevation(window_width=500) == 1  # Mobile
        assert get_responsive_elevation(window_width=700) == 2  # Tablet
        assert get_responsive_elevation(window_width=1000) == 3  # Desktop
    
    def test_is_mobile(self):
        """Test verificar si es móvil"""
        assert is_mobile(window_width=500) == True
        assert is_mobile(window_width=MOBILE_BREAKPOINT - 1) == True
        assert is_mobile(window_width=MOBILE_BREAKPOINT) == False
        assert is_mobile(window_width=800) == False
    
    def test_is_tablet(self):
        """Test verificar si es tablet"""
        assert is_tablet(window_width=700) == True
        assert is_tablet(window_width=MOBILE_BREAKPOINT) == True
        assert is_tablet(window_width=TABLET_BREAKPOINT - 1) == True
        assert is_tablet(window_width=TABLET_BREAKPOINT) == False
        assert is_tablet(window_width=500) == False
    
    def test_is_desktop(self):
        """Test verificar si es desktop"""
        assert is_desktop(window_width=1000) == True
        assert is_desktop(window_width=TABLET_BREAKPOINT) == True
        assert is_desktop(window_width=500) == False
        assert is_desktop(window_width=700) == False
    
    def test_get_device_type(self):
        """Test obtener tipo de dispositivo"""
        assert get_device_type(window_width=500) == "mobile"
        assert get_device_type(window_width=700) == "tablet"
        assert get_device_type(window_width=1000) == "desktop"
    
    def test_get_device_type_with_page(self):
        """Test obtener tipo de dispositivo con page"""
        page = MagicMock()
        page.window.width = 500
        assert get_device_type(page=page) == "mobile"
        
        page.window.width = 1000
        assert get_device_type(page=page) == "desktop"

