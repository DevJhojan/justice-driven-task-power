"""
Tests para el componente Priority Badge
Verifica la creación y funcionalidad de badges de prioridad según la Matriz de Eisenhower
"""

from pathlib import Path
import sys

# Agregar el directorio raíz al path para imports (necesario cuando se ejecuta directamente)
# Esto debe hacerse ANTES de cualquier import de 'app'
# Desde test/ui/task/components/test_priority_badge.py necesitamos subir 4 niveles para llegar a la raíz
project_root = Path(__file__).resolve().parents[4]  # components -> task -> ui -> test -> raíz
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import pytest
import flet as ft
from app.ui.task.components.priority_badge import (
    create_priority_badge,
    create_priority_badge_from_quadrant,
    PriorityBadge,
)
from app.utils.eisenhower_matrix import (
    get_eisenhower_quadrant,
    get_quadrant_name,
    get_quadrant_ft_color,
    get_quadrant_icon,
    get_priority_label,
    get_priority_badge_text,
    Quadrant,
)


class TestCreatePriorityBadge:
    """Tests para la función create_priority_badge"""
    
    def test_create_badge_q1(self, mock_page):
        """Test crear badge Q1 (urgente e importante)"""
        badge = create_priority_badge(urgent=True, important=True, page=mock_page)
        
        assert isinstance(badge, ft.Container)
        assert badge.content is not None
        assert isinstance(badge.content, ft.Row)
        assert len(badge.content.controls) == 2  # Icono y texto
    
    def test_create_badge_q2(self, mock_page):
        """Test crear badge Q2 (importante pero no urgente)"""
        badge = create_priority_badge(urgent=False, important=True, page=mock_page)
        
        assert isinstance(badge, ft.Container)
        assert badge.content is not None
        assert len(badge.content.controls) == 2
    
    def test_create_badge_q3(self, mock_page):
        """Test crear badge Q3 (urgente pero no importante)"""
        badge = create_priority_badge(urgent=True, important=False, page=mock_page)
        
        assert isinstance(badge, ft.Container)
        assert badge.content is not None
        assert len(badge.content.controls) == 2
    
    def test_create_badge_q4(self, mock_page):
        """Test crear badge Q4 (ni urgente ni importante)"""
        badge = create_priority_badge(urgent=False, important=False, page=mock_page)
        
        assert isinstance(badge, ft.Container)
        assert badge.content is not None
        assert len(badge.content.controls) == 2
    
    def test_create_badge_without_page(self):
        """Test crear badge sin objeto page (usa valores por defecto)"""
        badge = create_priority_badge(urgent=True, important=True)
        
        assert isinstance(badge, ft.Container)
        assert badge.content is not None
    
    def test_create_badge_show_icon_only(self, mock_page):
        """Test crear badge solo con icono"""
        badge = create_priority_badge(
            urgent=True,
            important=True,
            page=mock_page,
            show_icon=True,
            show_text=False
        )
        
        assert isinstance(badge, ft.Container)
        assert len(badge.content.controls) == 1
        assert isinstance(badge.content.controls[0], ft.Icon)
    
    def test_create_badge_show_text_only(self, mock_page):
        """Test crear badge solo con texto"""
        badge = create_priority_badge(
            urgent=True,
            important=True,
            page=mock_page,
            show_icon=False,
            show_text=True
        )
        
        assert isinstance(badge, ft.Container)
        assert len(badge.content.controls) == 1
        assert isinstance(badge.content.controls[0], ft.Text)
    
    def test_create_badge_no_icon_no_text(self, mock_page):
        """Test crear badge sin icono ni texto (retorna container vacío)"""
        badge = create_priority_badge(
            urgent=True,
            important=True,
            page=mock_page,
            show_icon=False,
            show_text=False
        )
        
        assert isinstance(badge, ft.Container)
        assert badge.content is None or len(badge.content.controls) == 0
    
    def test_create_badge_size_small(self, mock_page):
        """Test crear badge con tamaño small"""
        badge = create_priority_badge(
            urgent=True,
            important=True,
            page=mock_page,
            size="small"
        )
        
        assert isinstance(badge, ft.Container)
        assert len(badge.content.controls) == 2
        icon = badge.content.controls[0]
        assert icon.size == 14
        text = badge.content.controls[1]
        assert text.size == 10
    
    def test_create_badge_size_large(self, mock_page):
        """Test crear badge con tamaño large"""
        badge = create_priority_badge(
            urgent=True,
            important=True,
            page=mock_page,
            size="large"
        )
        
        assert isinstance(badge, ft.Container)
        icon = badge.content.controls[0]
        assert icon.size == 20
        text = badge.content.controls[1]
        assert text.size == 14
    
    def test_create_badge_show_quadrant(self, mock_page):
        """Test crear badge mostrando el cuadrante (Q1, Q2, etc.)"""
        badge = create_priority_badge(
            urgent=True,
            important=True,
            page=mock_page,
            show_quadrant=True
        )
        
        assert isinstance(badge, ft.Container)
        text_control = badge.content.controls[1]
        assert isinstance(text_control, ft.Text)
        assert text_control.value == "Q1"
    
    def test_create_badge_show_label(self, mock_page):
        """Test crear badge mostrando la etiqueta completa"""
        badge = create_priority_badge(
            urgent=True,
            important=True,
            page=mock_page,
            show_quadrant=False
        )
        
        assert isinstance(badge, ft.Container)
        text_control = badge.content.controls[1]
        assert isinstance(text_control, ft.Text)
        assert text_control.value == get_priority_label(True, True)
    
    def test_badge_has_correct_color(self, mock_page):
        """Test que el badge usa el color correcto según el cuadrante"""
        q1_badge = create_priority_badge(urgent=True, important=True, page=mock_page)
        q2_badge = create_priority_badge(urgent=False, important=True, page=mock_page)
        
        q1_color = q1_badge.content.controls[0].color
        q2_color = q2_badge.content.controls[0].color
        
        assert q1_color == get_quadrant_ft_color("Q1")
        assert q2_color == get_quadrant_ft_color("Q2")
        assert q1_color != q2_color
    
    def test_badge_has_styling(self, mock_page):
        """Test que el badge tiene estilos aplicados"""
        badge = create_priority_badge(urgent=True, important=True, page=mock_page)
        
        assert badge.border_radius is not None
        assert badge.padding is not None
        assert badge.bgcolor is not None
        assert badge.border is not None
    
    def test_badge_content_is_row(self, mock_page):
        """Test que el contenido del badge es un Row"""
        badge = create_priority_badge(urgent=True, important=True, page=mock_page)
        
        assert isinstance(badge.content, ft.Row)
        assert badge.content.spacing == 4
        assert badge.content.tight == True
        assert badge.content.alignment == ft.MainAxisAlignment.CENTER


class TestCreatePriorityBadgeFromQuadrant:
    """Tests para la función create_priority_badge_from_quadrant"""
    
    def test_create_badge_from_q1(self, mock_page):
        """Test crear badge desde cuadrante Q1"""
        badge = create_priority_badge_from_quadrant("Q1", page=mock_page)
        
        assert isinstance(badge, ft.Container)
        assert badge.content is not None
        assert len(badge.content.controls) == 2
    
    def test_create_badge_from_q2(self, mock_page):
        """Test crear badge desde cuadrante Q2"""
        badge = create_priority_badge_from_quadrant("Q2", page=mock_page)
        
        assert isinstance(badge, ft.Container)
        assert badge.content is not None
    
    def test_create_badge_from_q3(self, mock_page):
        """Test crear badge desde cuadrante Q3"""
        badge = create_priority_badge_from_quadrant("Q3", page=mock_page)
        
        assert isinstance(badge, ft.Container)
        assert badge.content is not None
    
    def test_create_badge_from_q4(self, mock_page):
        """Test crear badge desde cuadrante Q4"""
        badge = create_priority_badge_from_quadrant("Q4", page=mock_page)
        
        assert isinstance(badge, ft.Container)
        assert badge.content is not None
    
    def test_create_badge_from_quadrant_show_quadrant(self, mock_page):
        """Test crear badge desde cuadrante mostrando el código del cuadrante"""
        badge = create_priority_badge_from_quadrant("Q1", page=mock_page, show_quadrant=True)
        
        text_control = badge.content.controls[1]
        assert text_control.value == "Q1"
    
    def test_create_badge_from_quadrant_show_name(self, mock_page):
        """Test crear badge desde cuadrante mostrando el nombre"""
        badge = create_priority_badge_from_quadrant("Q1", page=mock_page, show_quadrant=False)
        
        text_control = badge.content.controls[1]
        assert text_control.value == get_quadrant_name("Q1")


class TestPriorityBadgeClass:
    """Tests para la clase PriorityBadge"""
    
    def test_priority_badge_initialization_with_urgent_important(self, mock_page):
        """Test inicialización de PriorityBadge con urgent e important"""
        badge = PriorityBadge(
            urgent=True,
            important=True,
            page=mock_page,
            show_icon=True,
            show_text=True,
            size="medium"
        )
        
        assert badge.urgent == True
        assert badge.important == True
        assert badge.quadrant == "Q1"
        assert badge.page == mock_page
        assert badge.show_icon == True
        assert badge.show_text == True
        assert badge.size == "medium"
        assert badge._badge is None
    
    def test_priority_badge_initialization_with_quadrant(self, mock_page):
        """Test inicialización de PriorityBadge con cuadrante"""
        badge = PriorityBadge(
            quadrant="Q2",
            page=mock_page
        )
        
        assert badge.quadrant == "Q2"
        assert badge.urgent is None
        assert badge.important is None
        assert badge._badge is None
    
    def test_priority_badge_initialization_error(self, mock_page):
        """Test que PriorityBadge lanza error si no se proporcionan parámetros válidos"""
        with pytest.raises(ValueError, match="Debe proporcionar"):
            PriorityBadge(page=mock_page)
    
    def test_priority_badge_build(self, mock_page):
        """Test método build de PriorityBadge"""
        badge = PriorityBadge(urgent=True, important=True, page=mock_page)
        built_badge = badge.build()
        
        assert isinstance(built_badge, ft.Container)
        assert badge._badge is not None
        assert badge._badge == built_badge
    
    def test_priority_badge_build_caches(self, mock_page):
        """Test que build cachea el badge"""
        badge = PriorityBadge(urgent=True, important=True, page=mock_page)
        
        first_build = badge.build()
        second_build = badge.build()
        
        assert first_build is second_build
    
    def test_priority_badge_update_priority_with_urgent_important(self, mock_page):
        """Test método update_priority con urgent e important"""
        badge = PriorityBadge(urgent=True, important=True, page=mock_page)
        badge.build()
        assert badge._badge is not None
        
        badge.update_priority(urgent=False, important=True)
        
        assert badge.urgent == False
        assert badge.important == True
        assert badge.quadrant == "Q2"
        assert badge._badge is None
    
    def test_priority_badge_update_priority_with_quadrant(self, mock_page):
        """Test método update_priority con cuadrante"""
        badge = PriorityBadge(urgent=True, important=True, page=mock_page)
        badge.build()
        assert badge._badge is not None
        
        badge.update_priority(quadrant="Q3")
        
        assert badge.quadrant == "Q3"
        assert badge._badge is None
    
    def test_priority_badge_refresh(self, mock_page):
        """Test método refresh de PriorityBadge"""
        badge = PriorityBadge(urgent=True, important=True, page=mock_page)
        badge.build()
        assert badge._badge is not None
        
        badge.refresh()
        
        assert badge._badge is None
    
    def test_priority_badge_build_after_update(self, mock_page):
        """Test que build después de update crea nuevo badge"""
        badge = PriorityBadge(urgent=True, important=True, page=mock_page)
        
        first_badge = badge.build()
        badge.update_priority(urgent=False, important=True)
        second_badge = badge.build()
        
        assert first_badge is not second_badge
    
    def test_priority_badge_without_page(self):
        """Test PriorityBadge sin objeto page"""
        badge = PriorityBadge(urgent=True, important=True)
        built_badge = badge.build()
        
        assert isinstance(built_badge, ft.Container)
    
    def test_priority_badge_different_sizes(self, mock_page):
        """Test PriorityBadge con diferentes tamaños"""
        small_badge = PriorityBadge(urgent=True, important=True, page=mock_page, size="small")
        large_badge = PriorityBadge(urgent=True, important=True, page=mock_page, size="large")
        
        small_built = small_badge.build()
        large_built = large_badge.build()
        
        small_icon = small_built.content.controls[0]
        large_icon = large_built.content.controls[0]
        
        assert small_icon.size == 14
        assert large_icon.size == 20
    
    def test_priority_badge_show_quadrant(self, mock_page):
        """Test PriorityBadge con show_quadrant=True"""
        badge = PriorityBadge(
            urgent=True,
            important=True,
            page=mock_page,
            show_quadrant=True
        )
        
        built_badge = badge.build()
        text_control = built_badge.content.controls[1]
        assert text_control.value == "Q1"


# ============================================================================
# DEMO UI - Ejecutar con: python test/ui/task/components/test_priority_badge.py
# ============================================================================

def main(page: ft.Page):
    """
    Demo visual de Priority Badge
    Muestra todos los badges de prioridad en una interfaz visual
    """
    # Configuración de la ventana
    page.title = "Priority Badge - Demo Visual"
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
        "Priority Badge - Demostración Visual",
        size=32,
        weight=ft.FontWeight.BOLD,
        text_align=ft.TextAlign.CENTER,
        color=ft.Colors.WHITE,
    )
    
    # Sección 1: Todos los cuadrantes desde urgent/important
    section1_title = ft.Text(
        "1. Todos los Cuadrantes de Eisenhower",
        size=24,
        weight=ft.FontWeight.BOLD,
        color=ft.Colors.WHITE,
    )
    
    quadrants_demo = ft.Column(
        controls=[
            ft.Row(
                controls=[
                    ft.Text("Q1 (Urgente e Importante):", color=ft.Colors.WHITE_70, size=16, width=200),
                    create_priority_badge(urgent=True, important=True, page=page),
                ],
                spacing=15,
            ),
            ft.Row(
                controls=[
                    ft.Text("Q2 (Importante, no Urgente):", color=ft.Colors.WHITE_70, size=16, width=200),
                    create_priority_badge(urgent=False, important=True, page=page),
                ],
                spacing=15,
            ),
            ft.Row(
                controls=[
                    ft.Text("Q3 (Urgente, no Importante):", color=ft.Colors.WHITE_70, size=16, width=200),
                    create_priority_badge(urgent=True, important=False, page=page),
                ],
                spacing=15,
            ),
            ft.Row(
                controls=[
                    ft.Text("Q4 (Ni Urgente ni Importante):", color=ft.Colors.WHITE_70, size=16, width=200),
                    create_priority_badge(urgent=False, important=False, page=page),
                ],
                spacing=15,
            ),
        ],
        spacing=15,
    )
    
    # Sección 2: Desde cuadrantes directamente
    section2_title = ft.Text(
        "2. Desde Cuadrantes Directamente",
        size=24,
        weight=ft.FontWeight.BOLD,
        color=ft.Colors.WHITE,
    )
    
    from_quadrant_demo = ft.Column(
        controls=[
            ft.Row(
                controls=[
                    ft.Text("Q1:", color=ft.Colors.WHITE_70, size=16, width=120),
                    create_priority_badge_from_quadrant("Q1", page=page),
                ],
                spacing=15,
            ),
            ft.Row(
                controls=[
                    ft.Text("Q2:", color=ft.Colors.WHITE_70, size=16, width=120),
                    create_priority_badge_from_quadrant("Q2", page=page),
                ],
                spacing=15,
            ),
            ft.Row(
                controls=[
                    ft.Text("Q3:", color=ft.Colors.WHITE_70, size=16, width=120),
                    create_priority_badge_from_quadrant("Q3", page=page),
                ],
                spacing=15,
            ),
            ft.Row(
                controls=[
                    ft.Text("Q4:", color=ft.Colors.WHITE_70, size=16, width=120),
                    create_priority_badge_from_quadrant("Q4", page=page),
                ],
                spacing=15,
            ),
        ],
        spacing=15,
    )
    
    # Sección 3: Diferentes tamaños
    section3_title = ft.Text(
        "3. Diferentes Tamaños",
        size=24,
        weight=ft.FontWeight.BOLD,
        color=ft.Colors.WHITE,
    )
    
    sizes_demo = ft.Column(
        controls=[
            ft.Row(
                controls=[
                    ft.Text("Small:", color=ft.Colors.WHITE_70, size=16, width=120),
                    create_priority_badge(urgent=True, important=True, page=page, size="small"),
                ],
                spacing=15,
            ),
            ft.Row(
                controls=[
                    ft.Text("Medium:", color=ft.Colors.WHITE_70, size=16, width=120),
                    create_priority_badge(urgent=True, important=True, page=page, size="medium"),
                ],
                spacing=15,
            ),
            ft.Row(
                controls=[
                    ft.Text("Large:", color=ft.Colors.WHITE_70, size=16, width=120),
                    create_priority_badge(urgent=True, important=True, page=page, size="large"),
                ],
                spacing=15,
            ),
        ],
        spacing=15,
    )
    
    # Sección 4: Mostrar cuadrante vs nombre
    section4_title = ft.Text(
        "4. Mostrar Cuadrante vs Nombre",
        size=24,
        weight=ft.FontWeight.BOLD,
        color=ft.Colors.WHITE,
    )
    
    quadrant_vs_name_demo = ft.Column(
        controls=[
            ft.Row(
                controls=[
                    ft.Text("Con Nombre:", color=ft.Colors.WHITE_70, size=16, width=150),
                    create_priority_badge(urgent=True, important=True, page=page, show_quadrant=False),
                ],
                spacing=15,
            ),
            ft.Row(
                controls=[
                    ft.Text("Con Cuadrante (Q1):", color=ft.Colors.WHITE_70, size=16, width=150),
                    create_priority_badge(urgent=True, important=True, page=page, show_quadrant=True),
                ],
                spacing=15,
            ),
        ],
        spacing=15,
    )
    
    # Sección 5: Variaciones de visualización
    section5_title = ft.Text(
        "5. Variaciones de Visualización",
        size=24,
        weight=ft.FontWeight.BOLD,
        color=ft.Colors.WHITE,
    )
    
    variations_demo = ft.Column(
        controls=[
            ft.Row(
                controls=[
                    ft.Text("Icono + Texto:", color=ft.Colors.WHITE_70, size=16, width=150),
                    create_priority_badge(
                        urgent=True,
                        important=True,
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
                    create_priority_badge(
                        urgent=True,
                        important=True,
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
                    create_priority_badge(
                        urgent=True,
                        important=True,
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
    
    # Sección 6: Usando la clase PriorityBadge
    section6_title = ft.Text(
        "6. Usando la Clase PriorityBadge",
        size=24,
        weight=ft.FontWeight.BOLD,
        color=ft.Colors.WHITE,
    )
    
    badge_class_demo = ft.Column(
        controls=[
            ft.Row(
                controls=[
                    ft.Text("Con urgent/important:", color=ft.Colors.WHITE_70, size=16, width=180),
                    PriorityBadge(
                        urgent=True,
                        important=False,
                        page=page,
                        size="medium"
                    ).build(),
                ],
                spacing=15,
            ),
            ft.Row(
                controls=[
                    ft.Text("Con cuadrante:", color=ft.Colors.WHITE_70, size=16, width=180),
                    PriorityBadge(
                        quadrant="Q2",
                        page=page,
                        size="large"
                    ).build(),
                ],
                spacing=15,
            ),
        ],
        spacing=15,
    )
    
    # Sección 7: Comparación lado a lado
    section7_title = ft.Text(
        "7. Comparación de Cuadrantes",
        size=24,
        weight=ft.FontWeight.BOLD,
        color=ft.Colors.WHITE,
    )
    
    comparison_demo = ft.Row(
        controls=[
            create_priority_badge(urgent=True, important=True, page=page, size="medium"),
            create_priority_badge(urgent=False, important=True, page=page, size="medium"),
            create_priority_badge(urgent=True, important=False, page=page, size="medium"),
            create_priority_badge(urgent=False, important=False, page=page, size="medium"),
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
            quadrants_demo,
            ft.Divider(height=30, color=ft.Colors.TRANSPARENT),
            
            section2_title,
            ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
            from_quadrant_demo,
            ft.Divider(height=30, color=ft.Colors.TRANSPARENT),
            
            section3_title,
            ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
            sizes_demo,
            ft.Divider(height=30, color=ft.Colors.TRANSPARENT),
            
            section4_title,
            ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
            quadrant_vs_name_demo,
            ft.Divider(height=30, color=ft.Colors.TRANSPARENT),
            
            section5_title,
            ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
            variations_demo,
            ft.Divider(height=30, color=ft.Colors.TRANSPARENT),
            
            section6_title,
            ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
            badge_class_demo,
            ft.Divider(height=30, color=ft.Colors.TRANSPARENT),
            
            section7_title,
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

