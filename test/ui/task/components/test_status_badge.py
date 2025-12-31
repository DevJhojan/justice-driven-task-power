"""
Tests para el componente Status Badge
Verifica la creación y funcionalidad de badges de estado de tareas
"""

import pytest
import flet as ft
from app.ui.task.components.status_badge import create_status_badge, StatusBadge
from app.utils.task_helper import (
    TASK_STATUS_PENDING,
    TASK_STATUS_IN_PROGRESS,
    TASK_STATUS_COMPLETED,
    TASK_STATUS_CANCELLED,
    format_task_status,
    get_task_status_ft_color,
    get_task_status_icon,
)


class TestCreateStatusBadge:
    """Tests para la función create_status_badge"""
    
    def test_create_badge_pending(self, mock_page):
        """Test crear badge con estado pendiente"""
        badge = create_status_badge(TASK_STATUS_PENDING, page=mock_page)
        
        assert isinstance(badge, ft.Container)
        assert badge.content is not None
        assert isinstance(badge.content, ft.Row)
        assert len(badge.content.controls) == 2  # Icono y texto
    
    def test_create_badge_in_progress(self, mock_page):
        """Test crear badge con estado en progreso"""
        badge = create_status_badge(TASK_STATUS_IN_PROGRESS, page=mock_page)
        
        assert isinstance(badge, ft.Container)
        assert badge.content is not None
        assert len(badge.content.controls) == 2
    
    def test_create_badge_completed(self, mock_page):
        """Test crear badge con estado completada"""
        badge = create_status_badge(TASK_STATUS_COMPLETED, page=mock_page)
        
        assert isinstance(badge, ft.Container)
        assert badge.content is not None
        assert len(badge.content.controls) == 2
    
    def test_create_badge_cancelled(self, mock_page):
        """Test crear badge con estado cancelada"""
        badge = create_status_badge(TASK_STATUS_CANCELLED, page=mock_page)
        
        assert isinstance(badge, ft.Container)
        assert badge.content is not None
        assert len(badge.content.controls) == 2
    
    def test_create_badge_without_page(self):
        """Test crear badge sin objeto page (usa valores por defecto)"""
        badge = create_status_badge(TASK_STATUS_PENDING)
        
        assert isinstance(badge, ft.Container)
        assert badge.content is not None
    
    def test_create_badge_show_icon_only(self, mock_page):
        """Test crear badge solo con icono"""
        badge = create_status_badge(
            TASK_STATUS_PENDING,
            page=mock_page,
            show_icon=True,
            show_text=False
        )
        
        assert isinstance(badge, ft.Container)
        assert len(badge.content.controls) == 1
        assert isinstance(badge.content.controls[0], ft.Icon)
    
    def test_create_badge_show_text_only(self, mock_page):
        """Test crear badge solo con texto"""
        badge = create_status_badge(
            TASK_STATUS_PENDING,
            page=mock_page,
            show_icon=False,
            show_text=True
        )
        
        assert isinstance(badge, ft.Container)
        assert len(badge.content.controls) == 1
        assert isinstance(badge.content.controls[0], ft.Text)
    
    def test_create_badge_no_icon_no_text(self, mock_page):
        """Test crear badge sin icono ni texto (retorna container vacío)"""
        badge = create_status_badge(
            TASK_STATUS_PENDING,
            page=mock_page,
            show_icon=False,
            show_text=False
        )
        
        assert isinstance(badge, ft.Container)
        assert badge.content is None or len(badge.content.controls) == 0
    
    def test_create_badge_size_small(self, mock_page):
        """Test crear badge con tamaño small"""
        badge = create_status_badge(
            TASK_STATUS_PENDING,
            page=mock_page,
            size="small"
        )
        
        assert isinstance(badge, ft.Container)
        # Verificar que tiene icono y texto
        assert len(badge.content.controls) == 2
        # Verificar tamaño del icono
        icon = badge.content.controls[0]
        assert icon.size == 14
        # Verificar tamaño del texto
        text = badge.content.controls[1]
        assert text.size == 10
    
    def test_create_badge_size_large(self, mock_page):
        """Test crear badge con tamaño large"""
        badge = create_status_badge(
            TASK_STATUS_PENDING,
            page=mock_page,
            size="large"
        )
        
        assert isinstance(badge, ft.Container)
        # Verificar tamaño del icono
        icon = badge.content.controls[0]
        assert icon.size == 20
        # Verificar tamaño del texto
        text = badge.content.controls[1]
        assert text.size == 14
    
    def test_create_badge_size_medium(self, mock_page):
        """Test crear badge con tamaño medium (usa responsive)"""
        badge = create_status_badge(
            TASK_STATUS_PENDING,
            page=mock_page,
            size="medium"
        )
        
        assert isinstance(badge, ft.Container)
        # Con tamaño medium, usa valores responsive
        assert badge.content is not None
    
    def test_badge_has_correct_text(self, mock_page):
        """Test que el badge muestra el texto correcto"""
        badge = create_status_badge(TASK_STATUS_PENDING, page=mock_page)
        
        text_control = badge.content.controls[1]
        assert isinstance(text_control, ft.Text)
        assert text_control.value == format_task_status(TASK_STATUS_PENDING)
    
    def test_badge_has_correct_icon(self, mock_page):
        """Test que el badge muestra el icono correcto"""
        badge = create_status_badge(TASK_STATUS_PENDING, page=mock_page)
        
        icon_control = badge.content.controls[0]
        assert isinstance(icon_control, ft.Icon)
        # Verificar que el icono tiene un tamaño (indica que está configurado)
        assert icon_control.size is not None
        # Verificar que el icono tiene el color correcto (indica que usa el icono correcto)
        assert icon_control.color == get_task_status_ft_color(TASK_STATUS_PENDING)
    
    def test_badge_has_correct_color(self, mock_page):
        """Test que el badge usa el color correcto"""
        badge = create_status_badge(TASK_STATUS_PENDING, page=mock_page)
        
        icon_control = badge.content.controls[0]
        text_control = badge.content.controls[1]
        
        expected_color = get_task_status_ft_color(TASK_STATUS_PENDING)
        assert icon_control.color == expected_color
        assert text_control.color == expected_color
    
    def test_badge_has_styling(self, mock_page):
        """Test que el badge tiene estilos aplicados"""
        badge = create_status_badge(TASK_STATUS_PENDING, page=mock_page)
        
        # Verificar que tiene border_radius
        assert badge.border_radius is not None
        # Verificar que tiene padding
        assert badge.padding is not None
        # Verificar que tiene bgcolor
        assert badge.bgcolor is not None
        # Verificar que tiene border
        assert badge.border is not None
    
    def test_badge_content_is_row(self, mock_page):
        """Test que el contenido del badge es un Row"""
        badge = create_status_badge(TASK_STATUS_PENDING, page=mock_page)
        
        assert isinstance(badge.content, ft.Row)
        assert badge.content.spacing == 4
        assert badge.content.tight == True
        assert badge.content.alignment == ft.MainAxisAlignment.CENTER
    
    def test_badge_different_statuses_have_different_colors(self, mock_page):
        """Test que diferentes estados tienen diferentes colores"""
        pending_badge = create_status_badge(TASK_STATUS_PENDING, page=mock_page)
        completed_badge = create_status_badge(TASK_STATUS_COMPLETED, page=mock_page)
        
        pending_color = pending_badge.content.controls[0].color
        completed_color = completed_badge.content.controls[0].color
        
        assert pending_color != completed_color


class TestStatusBadgeClass:
    """Tests para la clase StatusBadge"""
    
    def test_status_badge_initialization(self, mock_page):
        """Test inicialización de StatusBadge"""
        badge = StatusBadge(
            status=TASK_STATUS_PENDING,
            page=mock_page,
            show_icon=True,
            show_text=True,
            size="medium"
        )
        
        assert badge.status == TASK_STATUS_PENDING
        assert badge.page == mock_page
        assert badge.show_icon == True
        assert badge.show_text == True
        assert badge.size == "medium"
        assert badge._badge is None  # No construido aún
    
    def test_status_badge_build(self, mock_page):
        """Test método build de StatusBadge"""
        badge = StatusBadge(status=TASK_STATUS_PENDING, page=mock_page)
        built_badge = badge.build()
        
        assert isinstance(built_badge, ft.Container)
        assert badge._badge is not None
        assert badge._badge == built_badge
    
    def test_status_badge_build_caches(self, mock_page):
        """Test que build cachea el badge"""
        badge = StatusBadge(status=TASK_STATUS_PENDING, page=mock_page)
        
        first_build = badge.build()
        second_build = badge.build()
        
        # Debe ser la misma instancia (cached)
        assert first_build is second_build
    
    def test_status_badge_update_status(self, mock_page):
        """Test método update_status de StatusBadge"""
        badge = StatusBadge(status=TASK_STATUS_PENDING, page=mock_page)
        
        # Construir primero
        badge.build()
        assert badge._badge is not None
        
        # Actualizar estado
        badge.update_status(TASK_STATUS_COMPLETED)
        
        assert badge.status == TASK_STATUS_COMPLETED
        assert badge._badge is None  # Debe limpiar el cache
    
    def test_status_badge_refresh(self, mock_page):
        """Test método refresh de StatusBadge"""
        badge = StatusBadge(status=TASK_STATUS_PENDING, page=mock_page)
        
        # Construir primero
        badge.build()
        assert badge._badge is not None
        
        # Refrescar
        badge.refresh()
        
        assert badge._badge is None  # Debe limpiar el cache
    
    def test_status_badge_build_after_update(self, mock_page):
        """Test que build después de update crea nuevo badge"""
        badge = StatusBadge(status=TASK_STATUS_PENDING, page=mock_page)
        
        first_badge = badge.build()
        badge.update_status(TASK_STATUS_COMPLETED)
        second_badge = badge.build()
        
        # Deben ser diferentes instancias
        assert first_badge is not second_badge
    
    def test_status_badge_without_page(self):
        """Test StatusBadge sin objeto page"""
        badge = StatusBadge(status=TASK_STATUS_PENDING)
        built_badge = badge.build()
        
        assert isinstance(built_badge, ft.Container)
    
    def test_status_badge_different_sizes(self, mock_page):
        """Test StatusBadge con diferentes tamaños"""
        small_badge = StatusBadge(status=TASK_STATUS_PENDING, page=mock_page, size="small")
        large_badge = StatusBadge(status=TASK_STATUS_PENDING, page=mock_page, size="large")
        
        small_built = small_badge.build()
        large_built = large_badge.build()
        
        # Verificar que tienen diferentes tamaños
        small_icon = small_built.content.controls[0]
        large_icon = large_built.content.controls[0]
        
        assert small_icon.size == 14
        assert large_icon.size == 20
    
    def test_status_badge_show_icon_false(self, mock_page):
        """Test StatusBadge sin icono"""
        badge = StatusBadge(
            status=TASK_STATUS_PENDING,
            page=mock_page,
            show_icon=False,
            show_text=True
        )
        
        built_badge = badge.build()
        assert len(built_badge.content.controls) == 1
        assert isinstance(built_badge.content.controls[0], ft.Text)
    
    def test_status_badge_show_text_false(self, mock_page):
        """Test StatusBadge sin texto"""
        badge = StatusBadge(
            status=TASK_STATUS_PENDING,
            page=mock_page,
            show_icon=True,
            show_text=False
        )
        
        built_badge = badge.build()
        assert len(built_badge.content.controls) == 1
        assert isinstance(built_badge.content.controls[0], ft.Icon)

