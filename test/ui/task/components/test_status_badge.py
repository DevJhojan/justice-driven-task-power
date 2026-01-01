"""
Tests para el componente Status Badge
Verifica la creación y funcionalidad de badges de estado de tareas
"""

from pathlib import Path
import sys

# Agregar el directorio raíz al path para imports (necesario cuando se ejecuta directamente)
# Esto debe hacerse ANTES de cualquier import de 'app'
# Desde test/ui/task/components/test_status_badge.py necesitamos subir 4 niveles para llegar a la raíz
project_root = Path(__file__).resolve().parents[4]  # components -> task -> ui -> test -> raíz
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

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


# ============================================================================
# DEMO UI - Ejecutar con: python test/ui/task/components/test_status_badge.py
# ============================================================================

def main(page: ft.Page):
    """
    Demo visual de Status Badge
    Muestra todos los badges de estado en una interfaz visual
    """
    # Configuración de la ventana
    page.title = "Status Badge - Demo Visual"
    page.window.width = 900
    page.window.height = 700
    page.window.min_width = 600
    page.window.min_height = 500
    
    # Configuración del tema
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 20
    page.spacing = 0
    
    # Título principal
    title = ft.Text(
        "Status Badge - Demostración Visual",
        size=32,
        weight=ft.FontWeight.BOLD,
        text_align=ft.TextAlign.CENTER,
        color=ft.Colors.WHITE,
    )
    
    # Sección 1: Todos los estados
    section1_title = ft.Text(
        "1. Todos los Estados de Tareas",
        size=24,
        weight=ft.FontWeight.BOLD,
        color=ft.Colors.WHITE,
    )
    
    states_demo = ft.Column(
        controls=[
            ft.Row(
                controls=[
                    ft.Text("Pendiente:", color=ft.Colors.WHITE_70, size=16, width=120),
                    create_status_badge(TASK_STATUS_PENDING, page=page),
                ],
                spacing=15,
            ),
            ft.Row(
                controls=[
                    ft.Text("En Progreso:", color=ft.Colors.WHITE_70, size=16, width=120),
                    create_status_badge(TASK_STATUS_IN_PROGRESS, page=page),
                ],
                spacing=15,
            ),
            ft.Row(
                controls=[
                    ft.Text("Completada:", color=ft.Colors.WHITE_70, size=16, width=120),
                    create_status_badge(TASK_STATUS_COMPLETED, page=page),
                ],
                spacing=15,
            ),
            ft.Row(
                controls=[
                    ft.Text("Cancelada:", color=ft.Colors.WHITE_70, size=16, width=120),
                    create_status_badge(TASK_STATUS_CANCELLED, page=page),
                ],
                spacing=15,
            ),
        ],
        spacing=15,
    )
    
    # Sección 2: Diferentes tamaños
    section2_title = ft.Text(
        "2. Diferentes Tamaños",
        size=24,
        weight=ft.FontWeight.BOLD,
        color=ft.Colors.WHITE,
    )
    
    sizes_demo = ft.Column(
        controls=[
            ft.Row(
                controls=[
                    ft.Text("Small:", color=ft.Colors.WHITE_70, size=16, width=120),
                    create_status_badge(TASK_STATUS_PENDING, page=page, size="small"),
                ],
                spacing=15,
            ),
            ft.Row(
                controls=[
                    ft.Text("Medium:", color=ft.Colors.WHITE_70, size=16, width=120),
                    create_status_badge(TASK_STATUS_PENDING, page=page, size="medium"),
                ],
                spacing=15,
            ),
            ft.Row(
                controls=[
                    ft.Text("Large:", color=ft.Colors.WHITE_70, size=16, width=120),
                    create_status_badge(TASK_STATUS_PENDING, page=page, size="large"),
                ],
                spacing=15,
            ),
            ft.Row(
                controls=[
                    ft.Text("Responsive:", color=ft.Colors.WHITE_70, size=16, width=120),
                    create_status_badge(TASK_STATUS_PENDING, page=page),  # Sin size = responsive
                ],
                spacing=15,
            ),
        ],
        spacing=15,
    )
    
    # Sección 3: Variaciones (solo icono, solo texto)
    section3_title = ft.Text(
        "3. Variaciones de Visualización",
        size=24,
        weight=ft.FontWeight.BOLD,
        color=ft.Colors.WHITE,
    )
    
    variations_demo = ft.Column(
        controls=[
            ft.Row(
                controls=[
                    ft.Text("Icono + Texto:", color=ft.Colors.WHITE_70, size=16, width=150),
                    create_status_badge(
                        TASK_STATUS_PENDING,
                        page=page,
                        show_icon=True,
                        show_text=True
                    ),
                ],
                spacing=15,
            ),
            ft.Row(
                controls=[
                    ft.Text("Solo Icono:", color=ft.Colors.WHITE_70, size=16, width=150),
                    create_status_badge(
                        TASK_STATUS_PENDING,
                        page=page,
                        show_icon=True,
                        show_text=False
                    ),
                ],
                spacing=15,
            ),
            ft.Row(
                controls=[
                    ft.Text("Solo Texto:", color=ft.Colors.WHITE_70, size=16, width=150),
                    create_status_badge(
                        TASK_STATUS_PENDING,
                        page=page,
                        show_icon=False,
                        show_text=True
                    ),
                ],
                spacing=15,
            ),
        ],
        spacing=15,
    )
    
    # Sección 4: Usando la clase StatusBadge
    section4_title = ft.Text(
        "4. Usando la Clase StatusBadge",
        size=24,
        weight=ft.FontWeight.BOLD,
        color=ft.Colors.WHITE,
    )
    
    badge_class_demo = ft.Column(
        controls=[
            ft.Row(
                controls=[
                    ft.Text("Con Clase:", color=ft.Colors.WHITE_70, size=16, width=150),
                    StatusBadge(
                        status=TASK_STATUS_IN_PROGRESS,
                        page=page,
                        size="medium"
                    ).build(),
                ],
                spacing=15,
            ),
            ft.Row(
                controls=[
                    ft.Text("Actualizado:", color=ft.Colors.WHITE_70, size=16, width=150),
                    StatusBadge(
                        status=TASK_STATUS_COMPLETED,
                        page=page,
                        size="large"
                    ).build(),
                ],
                spacing=15,
            ),
        ],
        spacing=15,
    )
    
    # Sección 5: Comparación lado a lado
    section5_title = ft.Text(
        "5. Comparación de Estados",
        size=24,
        weight=ft.FontWeight.BOLD,
        color=ft.Colors.WHITE,
    )
    
    comparison_demo = ft.Row(
        controls=[
            create_status_badge(TASK_STATUS_PENDING, page=page, size="medium"),
            create_status_badge(TASK_STATUS_IN_PROGRESS, page=page, size="medium"),
            create_status_badge(TASK_STATUS_COMPLETED, page=page, size="medium"),
            create_status_badge(TASK_STATUS_CANCELLED, page=page, size="medium"),
        ],
        spacing=20,
        alignment=ft.MainAxisAlignment.CENTER,
    )
    
    # Contenedor principal con scroll
    main_content = ft.Column(
        controls=[
            title,
            ft.Divider(height=30, color=ft.Colors.TRANSPARENT),
            
            section1_title,
            ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
            states_demo,
            ft.Divider(height=30, color=ft.Colors.TRANSPARENT),
            
            section2_title,
            ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
            sizes_demo,
            ft.Divider(height=30, color=ft.Colors.TRANSPARENT),
            
            section3_title,
            ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
            variations_demo,
            ft.Divider(height=30, color=ft.Colors.TRANSPARENT),
            
            section4_title,
            ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
            badge_class_demo,
            ft.Divider(height=30, color=ft.Colors.TRANSPARENT),
            
            section5_title,
            ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
            comparison_demo,
            ft.Divider(height=30, color=ft.Colors.TRANSPARENT),
        ],
        spacing=0,
        scroll=ft.ScrollMode.AUTO,
        expand=True,
    )
    
    # Agregar contenido a la página
    page.add(main_content)
    page.update()


if __name__ == "__main__":
    # Si se ejecuta directamente, mostrar el demo UI
    ft.run(main)
