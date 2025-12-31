"""
Tests para el componente Subtask Item
Verifica la creación y funcionalidad de items de subtareas
"""

from pathlib import Path
import sys

# Agregar el directorio raíz al path para imports (necesario cuando se ejecuta directamente)
# Esto debe hacerse ANTES de cualquier import de 'app'
# Desde test/ui/task/components/test_subtask_item.py necesitamos subir 4 niveles para llegar a la raíz
project_root = Path(__file__).resolve().parents[4]  # components -> task -> ui -> test -> raíz
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import pytest
import flet as ft
from app.ui.task.components.subtask_item import create_subtask_item, SubtaskItem
from app.models.subtask import Subtask


class TestCreateSubtaskItem:
    """Tests para la función create_subtask_item"""
    
    def test_create_subtask_item_basic(self, mock_page):
        """Test crear item de subtarea básico"""
        subtask = Subtask(id="sub_1", task_id="task_1", title="Subtarea de prueba")
        item = create_subtask_item(subtask, page=mock_page)
        
        assert isinstance(item, ft.Container)
        assert item.content is not None
        assert isinstance(item.content, ft.Row)
        assert len(item.content.controls) >= 2  # Checkbox y título mínimo
    
    def test_create_subtask_item_without_page(self):
        """Test crear item sin objeto page"""
        subtask = Subtask(id="sub_1", task_id="task_1", title="Subtarea")
        item = create_subtask_item(subtask)
        
        assert isinstance(item, ft.Container)
        assert item.content is not None
    
    def test_create_subtask_item_completed(self, mock_page):
        """Test crear item de subtarea completada"""
        subtask = Subtask(
            id="sub_1",
            task_id="task_1",
            title="Subtarea completada",
            completed=True
        )
        item = create_subtask_item(subtask, page=mock_page)
        
        assert isinstance(item, ft.Container)
        # Verificar que el checkbox está marcado
        checkbox = item.content.controls[0]
        assert isinstance(checkbox, ft.Checkbox)
        assert checkbox.value == True
    
    def test_create_subtask_item_pending(self, mock_page):
        """Test crear item de subtarea pendiente"""
        subtask = Subtask(
            id="sub_1",
            task_id="task_1",
            title="Subtarea pendiente",
            completed=False
        )
        item = create_subtask_item(subtask, page=mock_page)
        
        assert isinstance(item, ft.Container)
        checkbox = item.content.controls[0]
        assert isinstance(checkbox, ft.Checkbox)
        assert checkbox.value == False
    
    def test_create_subtask_item_with_priority(self, mock_page):
        """Test crear item con prioridad (muestra badge)"""
        subtask = Subtask(
            id="sub_1",
            task_id="task_1",
            title="Subtarea urgente",
            urgent=True,
            important=True
        )
        item = create_subtask_item(subtask, page=mock_page, show_priority=True)
        
        assert isinstance(item, ft.Container)
        # Debe tener checkbox, título y badge de prioridad
        assert len(item.content.controls) >= 3
    
    def test_create_subtask_item_without_priority_badge(self, mock_page):
        """Test crear item sin mostrar badge de prioridad"""
        subtask = Subtask(
            id="sub_1",
            task_id="task_1",
            title="Subtarea",
            urgent=True,
            important=True
        )
        item = create_subtask_item(subtask, page=mock_page, show_priority=False)
        
        assert isinstance(item, ft.Container)
        # Solo debe tener checkbox y título (sin badge)
        assert len(item.content.controls) == 2
    
    def test_create_subtask_item_with_actions(self, mock_page):
        """Test crear item con botones de acción"""
        subtask = Subtask(id="sub_1", task_id="task_1", title="Subtarea")
        
        def handle_edit(subtask_id):
            pass
        
        def handle_delete(subtask_id):
            pass
        
        item = create_subtask_item(
            subtask,
            page=mock_page,
            on_edit=handle_edit,
            on_delete=handle_delete,
            show_actions=True
        )
        
        assert isinstance(item, ft.Container)
        # Debe tener checkbox, título y botones de acción
        assert len(item.content.controls) >= 4
    
    def test_create_subtask_item_without_actions(self, mock_page):
        """Test crear item sin botones de acción"""
        subtask = Subtask(id="sub_1", task_id="task_1", title="Subtarea")
        item = create_subtask_item(subtask, page=mock_page, show_actions=False)
        
        assert isinstance(item, ft.Container)
        # Solo debe tener checkbox y título
        assert len(item.content.controls) == 2
    
    def test_create_subtask_item_compact(self, mock_page):
        """Test crear item en modo compacto"""
        subtask = Subtask(id="sub_1", task_id="task_1", title="Subtarea")
        item = create_subtask_item(subtask, page=mock_page, compact=True)
        
        assert isinstance(item, ft.Container)
        assert item.content is not None
    
    def test_create_subtask_item_title_text(self, mock_page):
        """Test que el título se muestra correctamente"""
        subtask = Subtask(id="sub_1", task_id="task_1", title="Mi Subtarea")
        item = create_subtask_item(subtask, page=mock_page)
        
        title_container = item.content.controls[1]
        assert isinstance(title_container, ft.Container)
        title_text = title_container.content
        assert isinstance(title_text, ft.Text)
        assert title_text.value == "Mi Subtarea"
    
    def test_create_subtask_item_completed_title_style(self, mock_page):
        """Test que el título completado tiene estilo diferente"""
        subtask = Subtask(
            id="sub_1",
            task_id="task_1",
            title="Subtarea completada",
            completed=True
        )
        item = create_subtask_item(subtask, page=mock_page)
        
        title_container = item.content.controls[1]
        title_text = title_container.content
        assert title_text.color == ft.Colors.WHITE_54
        assert title_text.weight == ft.FontWeight.W_400
    
    def test_create_subtask_item_pending_title_style(self, mock_page):
        """Test que el título pendiente tiene estilo normal"""
        subtask = Subtask(
            id="sub_1",
            task_id="task_1",
            title="Subtarea pendiente",
            completed=False
        )
        item = create_subtask_item(subtask, page=mock_page)
        
        title_container = item.content.controls[1]
        title_text = title_container.content
        assert title_text.color == ft.Colors.WHITE
        assert title_text.weight == ft.FontWeight.W_500
    
    def test_create_subtask_item_has_styling(self, mock_page):
        """Test que el item tiene estilos aplicados"""
        subtask = Subtask(id="sub_1", task_id="task_1", title="Subtarea")
        item = create_subtask_item(subtask, page=mock_page)
        
        assert item.border_radius is not None
        assert item.padding is not None
        assert item.bgcolor is not None
    
    def test_create_subtask_item_content_is_row(self, mock_page):
        """Test que el contenido del item es un Row"""
        subtask = Subtask(id="sub_1", task_id="task_1", title="Subtarea")
        item = create_subtask_item(subtask, page=mock_page)
        
        assert isinstance(item.content, ft.Row)
        assert item.content.spacing == 8
        assert item.content.alignment == ft.MainAxisAlignment.START


class TestSubtaskItemClass:
    """Tests para la clase SubtaskItem"""
    
    def test_subtask_item_initialization(self, mock_page):
        """Test inicialización de SubtaskItem"""
        subtask = Subtask(id="sub_1", task_id="task_1", title="Subtarea")
        
        def handle_toggle(subtask_id):
            pass
        
        item = SubtaskItem(
            subtask=subtask,
            page=mock_page,
            on_toggle_completed=handle_toggle,
            show_priority=True,
            show_actions=True,
            compact=False
        )
        
        assert item.subtask == subtask
        assert item.page == mock_page
        assert item.show_priority == True
        assert item.show_actions == True
        assert item.compact == False
        assert item._item is None
    
    def test_subtask_item_build(self, mock_page):
        """Test método build de SubtaskItem"""
        subtask = Subtask(id="sub_1", task_id="task_1", title="Subtarea")
        item = SubtaskItem(subtask=subtask, page=mock_page)
        built_item = item.build()
        
        assert isinstance(built_item, ft.Container)
        assert item._item is not None
        assert item._item == built_item
    
    def test_subtask_item_build_caches(self, mock_page):
        """Test que build cachea el item"""
        subtask = Subtask(id="sub_1", task_id="task_1", title="Subtarea")
        item = SubtaskItem(subtask=subtask, page=mock_page)
        
        first_build = item.build()
        second_build = item.build()
        
        assert first_build is second_build
    
    def test_subtask_item_update_subtask(self, mock_page):
        """Test método update_subtask de SubtaskItem"""
        subtask1 = Subtask(id="sub_1", task_id="task_1", title="Subtarea 1")
        item = SubtaskItem(subtask=subtask1, page=mock_page)
        item.build()
        assert item._item is not None
        
        subtask2 = Subtask(id="sub_1", task_id="task_1", title="Subtarea 2")
        item.update_subtask(subtask2)
        
        assert item.subtask == subtask2
        assert item._item is None  # Debe limpiar el cache
    
    def test_subtask_item_refresh(self, mock_page):
        """Test método refresh de SubtaskItem"""
        subtask = Subtask(id="sub_1", task_id="task_1", title="Subtarea")
        item = SubtaskItem(subtask=subtask, page=mock_page)
        item.build()
        assert item._item is not None
        
        item.refresh()
        
        assert item._item is None  # Debe limpiar el cache
    
    def test_subtask_item_build_after_update(self, mock_page):
        """Test que build después de update crea nuevo item"""
        subtask1 = Subtask(id="sub_1", task_id="task_1", title="Subtarea 1")
        item = SubtaskItem(subtask=subtask1, page=mock_page)
        
        first_item = item.build()
        subtask2 = Subtask(id="sub_1", task_id="task_1", title="Subtarea 2")
        item.update_subtask(subtask2)
        second_item = item.build()
        
        assert first_item is not second_item
    
    def test_subtask_item_without_page(self):
        """Test SubtaskItem sin objeto page"""
        subtask = Subtask(id="sub_1", task_id="task_1", title="Subtarea")
        item = SubtaskItem(subtask=subtask)
        built_item = item.build()
        
        assert isinstance(built_item, ft.Container)
    
    def test_subtask_item_compact_mode(self, mock_page):
        """Test SubtaskItem en modo compacto"""
        subtask = Subtask(id="sub_1", task_id="task_1", title="Subtarea")
        item = SubtaskItem(subtask=subtask, page=mock_page, compact=True)
        built_item = item.build()
        
        assert isinstance(built_item, ft.Container)
    
    def test_subtask_item_with_callbacks(self, mock_page):
        """Test SubtaskItem con callbacks"""
        subtask = Subtask(id="sub_1", task_id="task_1", title="Subtarea")
        
        toggle_called = []
        edit_called = []
        delete_called = []
        
        def handle_toggle(subtask_id):
            toggle_called.append(subtask_id)
        
        def handle_edit(subtask_id):
            edit_called.append(subtask_id)
        
        def handle_delete(subtask_id):
            delete_called.append(subtask_id)
        
        item = SubtaskItem(
            subtask=subtask,
            page=mock_page,
            on_toggle_completed=handle_toggle,
            on_edit=handle_edit,
            on_delete=handle_delete
        )
        
        built_item = item.build()
        assert isinstance(built_item, ft.Container)
        
        # Los callbacks se asignan pero no se ejecutan hasta la interacción
        assert item.on_toggle_completed == handle_toggle
        assert item.on_edit == handle_edit
        assert item.on_delete == handle_delete


# ============================================================================
# DEMO UI - Ejecutar con: python test/ui/task/components/test_subtask_item.py
# ============================================================================

def main(page: ft.Page):
    """
    Demo visual de Subtask Item
    Muestra diferentes items de subtareas en una interfaz visual
    """
    # Configuración de la ventana
    page.title = "Subtask Item - Demo Visual"
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
        "Subtask Item - Demostración Visual",
        size=32,
        weight=ft.FontWeight.BOLD,
        text_align=ft.TextAlign.CENTER,
        color=ft.Colors.WHITE,
    )
    
    # Callbacks de ejemplo
    toggle_count = {"count": 0}
    edit_count = {"count": 0}
    delete_count = {"count": 0}
    
    def handle_toggle(subtask_id):
        toggle_count["count"] += 1
        print(f"Toggle subtarea {subtask_id} (total: {toggle_count['count']})")
    
    def handle_edit(subtask_id):
        edit_count["count"] += 1
        print(f"Editar subtarea {subtask_id} (total: {edit_count['count']})")
    
    def handle_delete(subtask_id):
        delete_count["count"] += 1
        print(f"Eliminar subtarea {subtask_id} (total: {delete_count['count']})")
    
    # Sección 1: Subtareas básicas
    section1_title = ft.Text(
        "1. Subtareas Básicas",
        size=24,
        weight=ft.FontWeight.BOLD,
        color=ft.Colors.WHITE,
    )
    
    basic_subtasks = ft.Column(
        controls=[
            create_subtask_item(
                Subtask(id="sub_1", task_id="task_1", title="Subtarea pendiente"),
                page=page
            ),
            create_subtask_item(
                Subtask(
                    id="sub_2",
                    task_id="task_1",
                    title="Subtarea completada",
                    completed=True
                ),
                page=page
            ),
        ],
        spacing=10,
    )
    
    # Sección 2: Subtareas con prioridad
    section2_title = ft.Text(
        "2. Subtareas con Prioridad",
        size=24,
        weight=ft.FontWeight.BOLD,
        color=ft.Colors.WHITE,
    )
    
    priority_subtasks = ft.Column(
        controls=[
            create_subtask_item(
                Subtask(
                    id="sub_3",
                    task_id="task_1",
                    title="Subtarea Q1 (Urgente e Importante)",
                    urgent=True,
                    important=True
                ),
                page=page,
                show_priority=True
            ),
            create_subtask_item(
                Subtask(
                    id="sub_4",
                    task_id="task_1",
                    title="Subtarea Q2 (Importante, no Urgente)",
                    urgent=False,
                    important=True
                ),
                page=page,
                show_priority=True
            ),
            create_subtask_item(
                Subtask(
                    id="sub_5",
                    task_id="task_1",
                    title="Subtarea Q3 (Urgente, no Importante)",
                    urgent=True,
                    important=False
                ),
                page=page,
                show_priority=True
            ),
        ],
        spacing=10,
    )
    
    # Sección 3: Subtareas con acciones
    section3_title = ft.Text(
        "3. Subtareas con Acciones (Editar/Eliminar)",
        size=24,
        weight=ft.FontWeight.BOLD,
        color=ft.Colors.WHITE,
    )
    
    actions_subtasks = ft.Column(
        controls=[
            create_subtask_item(
                Subtask(id="sub_6", task_id="task_1", title="Subtarea con editar"),
                page=page,
                on_edit=handle_edit,
                show_actions=True
            ),
            create_subtask_item(
                Subtask(id="sub_7", task_id="task_1", title="Subtarea con eliminar"),
                page=page,
                on_delete=handle_delete,
                show_actions=True
            ),
            create_subtask_item(
                Subtask(id="sub_8", task_id="task_1", title="Subtarea con todas las acciones"),
                page=page,
                on_toggle_completed=handle_toggle,
                on_edit=handle_edit,
                on_delete=handle_delete,
                show_actions=True
            ),
        ],
        spacing=10,
    )
    
    # Sección 4: Modo compacto
    section4_title = ft.Text(
        "4. Modo Compacto",
        size=24,
        weight=ft.FontWeight.BOLD,
        color=ft.Colors.WHITE,
    )
    
    compact_subtasks = ft.Column(
        controls=[
            create_subtask_item(
                Subtask(id="sub_9", task_id="task_1", title="Subtarea compacta 1"),
                page=page,
                compact=True
            ),
            create_subtask_item(
                Subtask(
                    id="sub_10",
                    task_id="task_1",
                    title="Subtarea compacta 2",
                    completed=True
                ),
                page=page,
                compact=True
            ),
            create_subtask_item(
                Subtask(
                    id="sub_11",
                    task_id="task_1",
                    title="Subtarea compacta con prioridad",
                    urgent=True,
                    important=True
                ),
                page=page,
                compact=True,
                show_priority=True
            ),
        ],
        spacing=8,
    )
    
    # Sección 5: Sin prioridad ni acciones
    section5_title = ft.Text(
        "5. Sin Prioridad ni Acciones",
        size=24,
        weight=ft.FontWeight.BOLD,
        color=ft.Colors.WHITE,
    )
    
    minimal_subtasks = ft.Column(
        controls=[
            create_subtask_item(
                Subtask(id="sub_12", task_id="task_1", title="Subtarea mínima"),
                page=page,
                show_priority=False,
                show_actions=False
            ),
            create_subtask_item(
                Subtask(
                    id="sub_13",
                    task_id="task_1",
                    title="Subtarea mínima completada",
                    completed=True
                ),
                page=page,
                show_priority=False,
                show_actions=False
            ),
        ],
        spacing=10,
    )
    
    # Sección 6: Usando la clase SubtaskItem
    section6_title = ft.Text(
        "6. Usando la Clase SubtaskItem",
        size=24,
        weight=ft.FontWeight.BOLD,
        color=ft.Colors.WHITE,
    )
    
    class_subtasks = ft.Column(
        controls=[
            SubtaskItem(
                Subtask(id="sub_14", task_id="task_1", title="Subtarea con clase"),
                page=page
            ).build(),
            SubtaskItem(
                Subtask(
                    id="sub_15",
                    task_id="task_1",
                    title="Subtarea con clase completada",
                    completed=True
                ),
                page=page
            ).build(),
        ],
        spacing=10,
    )
    
    # Contenedor principal con scroll
    main_content = ft.Column(
        controls=[
            title,
            ft.Divider(height=30, color=ft.Colors.TRANSPARENT),
            
            section1_title,
            ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
            basic_subtasks,
            ft.Divider(height=30, color=ft.Colors.TRANSPARENT),
            
            section2_title,
            ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
            priority_subtasks,
            ft.Divider(height=30, color=ft.Colors.TRANSPARENT),
            
            section3_title,
            ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
            actions_subtasks,
            ft.Divider(height=30, color=ft.Colors.TRANSPARENT),
            
            section4_title,
            ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
            compact_subtasks,
            ft.Divider(height=30, color=ft.Colors.TRANSPARENT),
            
            section5_title,
            ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
            minimal_subtasks,
            ft.Divider(height=30, color=ft.Colors.TRANSPARENT),
            
            section6_title,
            ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
            class_subtasks,
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

