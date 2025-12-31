"""
Tests para el componente Task Card
Verifica la creación y funcionalidad de tarjetas de tareas
"""

from pathlib import Path
import sys

# Agregar el directorio raíz al path para imports (necesario cuando se ejecuta directamente)
# Esto debe hacerse ANTES de cualquier import de 'app'
# Desde test/ui/task/components/test_task_card.py necesitamos subir 4 niveles para llegar a la raíz
project_root = Path(__file__).resolve().parents[4]  # components -> task -> ui -> test -> raíz
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import pytest
import flet as ft
from datetime import date, datetime, timedelta
from app.ui.task.components.task_card import create_task_card, TaskCard
from app.models.task import Task
from app.models.subtask import Subtask
from app.utils.task_helper import (
    TASK_STATUS_PENDING,
    TASK_STATUS_IN_PROGRESS,
    TASK_STATUS_COMPLETED,
    TASK_STATUS_CANCELLED,
)


class TestCreateTaskCard:
    """Tests para la función create_task_card"""
    
    def test_create_task_card_basic(self, mock_page):
        """Test crear tarjeta de tarea básica"""
        task = Task(id="task_1", title="Tarea de prueba", user_id="user_1")
        card = create_task_card(task, page=mock_page)
        
        assert isinstance(card, ft.Container)
        assert card.content is not None
        assert isinstance(card.content, ft.Column)
        assert len(card.content.controls) > 0
    
    def test_create_task_card_without_page(self):
        """Test crear tarjeta sin objeto page"""
        task = Task(id="task_1", title="Tarea", user_id="user_1")
        card = create_task_card(task)
        
        assert isinstance(card, ft.Container)
        assert card.content is not None
    
    def test_create_task_card_with_description(self, mock_page):
        """Test crear tarjeta con descripción"""
        task = Task(
            id="task_1",
            title="Tarea con descripción",
            description="Esta es una descripción detallada",
            user_id="user_1"
        )
        card = create_task_card(task, page=mock_page)
        
        assert isinstance(card, ft.Container)
        # Debe tener título y descripción
        assert len(card.content.controls) >= 2
    
    def test_create_task_card_without_description(self, mock_page):
        """Test crear tarjeta sin descripción"""
        task = Task(id="task_1", title="Tarea sin descripción", user_id="user_1")
        card = create_task_card(task, page=mock_page)
        
        assert isinstance(card, ft.Container)
        # Solo debe tener header (título y badges)
        assert len(card.content.controls) >= 1
    
    def test_create_task_card_with_due_date(self, mock_page, mock_date_future):
        """Test crear tarjeta con fecha de vencimiento"""
        task = Task(
            id="task_1",
            title="Tarea con fecha",
            user_id="user_1",
            due_date=mock_date_future
        )
        card = create_task_card(task, page=mock_page)
        
        assert isinstance(card, ft.Container)
        # Debe tener información de fecha
        assert len(card.content.controls) >= 2
    
    def test_create_task_card_with_subtasks(self, mock_page):
        """Test crear tarjeta con subtareas"""
        task = Task(id="task_1", title="Tarea con subtareas", user_id="user_1")
        subtask1 = Subtask(id="sub_1", task_id="task_1", title="Subtarea 1")
        subtask2 = Subtask(id="sub_2", task_id="task_1", title="Subtarea 2")
        task.add_subtask(subtask1)
        task.add_subtask(subtask2)
        
        card = create_task_card(task, page=mock_page, show_subtasks=True)
        
        assert isinstance(card, ft.Container)
        # Debe tener subtareas
        assert len(card.content.controls) >= 3
    
    def test_create_task_card_without_subtasks_display(self, mock_page):
        """Test crear tarjeta sin mostrar subtareas"""
        task = Task(id="task_1", title="Tarea", user_id="user_1")
        subtask = Subtask(id="sub_1", task_id="task_1", title="Subtarea")
        task.add_subtask(subtask)
        
        card = create_task_card(task, page=mock_page, show_subtasks=False)
        
        assert isinstance(card, ft.Container)
        # No debe mostrar subtareas aunque existan
    
    def test_create_task_card_with_tags(self, mock_page):
        """Test crear tarjeta con tags"""
        task = Task(
            id="task_1",
            title="Tarea con tags",
            user_id="user_1",
            tags=["urgente", "trabajo", "importante"]
        )
        card = create_task_card(task, page=mock_page, show_tags=True)
        
        assert isinstance(card, ft.Container)
        # Debe tener tags
        assert len(card.content.controls) >= 2
    
    def test_create_task_card_without_tags_display(self, mock_page):
        """Test crear tarjeta sin mostrar tags"""
        task = Task(
            id="task_1",
            title="Tarea",
            user_id="user_1",
            tags=["tag1", "tag2"]
        )
        card = create_task_card(task, page=mock_page, show_tags=False)
        
        assert isinstance(card, ft.Container)
        # No debe mostrar tags aunque existan
    
    def test_create_task_card_with_progress(self, mock_page):
        """Test crear tarjeta con barra de progreso"""
        task = Task(id="task_1", title="Tarea", user_id="user_1")
        subtask1 = Subtask(id="sub_1", task_id="task_1", title="Subtarea 1", completed=True)
        subtask2 = Subtask(id="sub_2", task_id="task_1", title="Subtarea 2", completed=False)
        task.add_subtask(subtask1)
        task.add_subtask(subtask2)
        
        card = create_task_card(task, page=mock_page, show_progress=True)
        
        assert isinstance(card, ft.Container)
        # Debe tener barra de progreso
    
    def test_create_task_card_without_progress(self, mock_page):
        """Test crear tarjeta sin barra de progreso"""
        task = Task(id="task_1", title="Tarea", user_id="user_1")
        card = create_task_card(task, page=mock_page, show_progress=False)
        
        assert isinstance(card, ft.Container)
        # No debe tener barra de progreso
    
    def test_create_task_card_compact(self, mock_page):
        """Test crear tarjeta en modo compacto"""
        task = Task(id="task_1", title="Tarea compacta", user_id="user_1")
        card = create_task_card(task, page=mock_page, compact=True)
        
        assert isinstance(card, ft.Container)
        assert card.content is not None
    
    def test_create_task_card_has_header(self, mock_page):
        """Test que la tarjeta tiene header con título y badges"""
        task = Task(id="task_1", title="Mi Tarea", user_id="user_1")
        card = create_task_card(task, page=mock_page)
        
        header = card.content.controls[0]
        assert isinstance(header, ft.Row)
        assert len(header.controls) >= 2  # Título y badges
    
    def test_create_task_card_has_styling(self, mock_page):
        """Test que la tarjeta tiene estilos aplicados"""
        task = Task(id="task_1", title="Tarea", user_id="user_1")
        card = create_task_card(task, page=mock_page)
        
        assert card.border_radius is not None
        assert card.padding is not None
        assert card.bgcolor is not None
        assert card.border is not None
    
    def test_create_task_card_different_statuses(self, mock_page):
        """Test crear tarjetas con diferentes estados"""
        pending_task = Task(
            id="task_1",
            title="Tarea pendiente",
            user_id="user_1",
            status=TASK_STATUS_PENDING
        )
        completed_task = Task(
            id="task_2",
            title="Tarea completada",
            user_id="user_1",
            status=TASK_STATUS_COMPLETED
        )
        
        pending_card = create_task_card(pending_task, page=mock_page)
        completed_card = create_task_card(completed_task, page=mock_page)
        
        assert isinstance(pending_card, ft.Container)
        assert isinstance(completed_card, ft.Container)
    
    def test_create_task_card_with_callbacks(self, mock_page):
        """Test crear tarjeta con callbacks"""
        task = Task(id="task_1", title="Tarea", user_id="user_1")
        
        click_called = []
        edit_called = []
        delete_called = []
        toggle_called = []
        
        def handle_click(task_id):
            click_called.append(task_id)
        
        def handle_edit(task_id):
            edit_called.append(task_id)
        
        def handle_delete(task_id):
            delete_called.append(task_id)
        
        def handle_toggle(task_id):
            toggle_called.append(task_id)
        
        card = create_task_card(
            task,
            page=mock_page,
            on_click=handle_click,
            on_edit=handle_edit,
            on_delete=handle_delete,
            on_toggle_status=handle_toggle
        )
        
        assert isinstance(card, ft.Container)
        # Los callbacks se asignan pero no se ejecutan hasta la interacción
        assert card.on_click is not None


class TestTaskCardClass:
    """Tests para la clase TaskCard"""
    
    def test_task_card_initialization(self, mock_page):
        """Test inicialización de TaskCard"""
        task = Task(id="task_1", title="Tarea", user_id="user_1")
        
        def handle_click(task_id):
            pass
        
        card = TaskCard(
            task=task,
            page=mock_page,
            on_click=handle_click,
            show_subtasks=True,
            show_tags=True,
            show_progress=True,
            compact=False
        )
        
        assert card.task == task
        assert card.page == mock_page
        assert card.show_subtasks == True
        assert card.show_tags == True
        assert card.show_progress == True
        assert card.compact == False
        assert card._card is None
    
    def test_task_card_build(self, mock_page):
        """Test método build de TaskCard"""
        task = Task(id="task_1", title="Tarea", user_id="user_1")
        card = TaskCard(task=task, page=mock_page)
        built_card = card.build()
        
        assert isinstance(built_card, ft.Container)
        assert card._card is not None
        assert card._card == built_card
    
    def test_task_card_build_caches(self, mock_page):
        """Test que build cachea la tarjeta"""
        task = Task(id="task_1", title="Tarea", user_id="user_1")
        card = TaskCard(task=task, page=mock_page)
        
        first_build = card.build()
        second_build = card.build()
        
        assert first_build is second_build
    
    def test_task_card_update_task(self, mock_page):
        """Test método update_task de TaskCard"""
        task1 = Task(id="task_1", title="Tarea 1", user_id="user_1")
        card = TaskCard(task=task1, page=mock_page)
        card.build()
        assert card._card is not None
        
        task2 = Task(id="task_1", title="Tarea 2", user_id="user_1")
        card.update_task(task2)
        
        assert card.task == task2
        assert card._card is None  # Debe limpiar el cache
    
    def test_task_card_refresh(self, mock_page):
        """Test método refresh de TaskCard"""
        task = Task(id="task_1", title="Tarea", user_id="user_1")
        card = TaskCard(task=task, page=mock_page)
        card.build()
        assert card._card is not None
        
        card.refresh()
        
        assert card._card is None  # Debe limpiar el cache
    
    def test_task_card_build_after_update(self, mock_page):
        """Test que build después de update crea nueva tarjeta"""
        task1 = Task(id="task_1", title="Tarea 1", user_id="user_1")
        card = TaskCard(task=task1, page=mock_page)
        
        first_card = card.build()
        task2 = Task(id="task_1", title="Tarea 2", user_id="user_1")
        card.update_task(task2)
        second_card = card.build()
        
        assert first_card is not second_card
    
    def test_task_card_without_page(self):
        """Test TaskCard sin objeto page"""
        task = Task(id="task_1", title="Tarea", user_id="user_1")
        card = TaskCard(task=task)
        built_card = card.build()
        
        assert isinstance(built_card, ft.Container)
    
    def test_task_card_compact_mode(self, mock_page):
        """Test TaskCard en modo compacto"""
        task = Task(id="task_1", title="Tarea", user_id="user_1")
        card = TaskCard(task=task, page=mock_page, compact=True)
        built_card = card.build()
        
        assert isinstance(built_card, ft.Container)
    
    def test_task_card_with_all_callbacks(self, mock_page):
        """Test TaskCard con todos los callbacks"""
        task = Task(id="task_1", title="Tarea", user_id="user_1")
        
        def handle_click(task_id):
            pass
        
        def handle_edit(task_id):
            pass
        
        def handle_delete(task_id):
            pass
        
        def handle_toggle(task_id):
            pass
        
        def handle_subtask_toggle(task_id, subtask_id):
            pass
        
        card = TaskCard(
            task=task,
            page=mock_page,
            on_click=handle_click,
            on_edit=handle_edit,
            on_delete=handle_delete,
            on_toggle_status=handle_toggle,
            on_subtask_toggle=handle_subtask_toggle
        )
        
        built_card = card.build()
        assert isinstance(built_card, ft.Container)


# ============================================================================
# DEMO UI - Ejecutar con: python test/ui/task/components/test_task_card.py
# ============================================================================

def main(page: ft.Page):
    """
    Demo visual de Task Card
    Muestra diferentes tarjetas de tareas en una interfaz visual
    """
    # Configuración de la ventana
    page.title = "Task Card - Demo Visual"
    page.window.width = 1000
    page.window.height = 800
    page.window.min_width = 700
    page.window.min_height = 600
    
    # Configuración del tema
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 20
    page.spacing = 0
    
    # Título principal
    title = ft.Text(
        "Task Card - Demostración Visual",
        size=32,
        weight=ft.FontWeight.BOLD,
        text_align=ft.TextAlign.CENTER,
        color=ft.Colors.WHITE,
    )
    
    # Callbacks de ejemplo
    def handle_click(task_id):
        print(f"Clic en tarea {task_id}")
    
    def handle_edit(task_id):
        print(f"Editar tarea {task_id}")
    
    def handle_delete(task_id):
        print(f"Eliminar tarea {task_id}")
    
    def handle_toggle(task_id):
        print(f"Cambiar estado de tarea {task_id}")
    
    def handle_subtask_toggle(task_id, subtask_id):
        print(f"Toggle subtarea {subtask_id} de tarea {task_id}")
    
    # Sección 1: Tareas básicas
    section1_title = ft.Text(
        "1. Tareas Básicas",
        size=24,
        weight=ft.FontWeight.BOLD,
        color=ft.Colors.WHITE,
    )
    
    basic_tasks = ft.Column(
        controls=[
            create_task_card(
                Task(id="task_1", title="Tarea simple", user_id="user_1"),
                page=page
            ),
            create_task_card(
                Task(
                    id="task_2",
                    title="Tarea con descripción",
                    description="Esta es una descripción detallada de la tarea que puede contener información importante.",
                    user_id="user_1"
                ),
                page=page
            ),
        ],
        spacing=15,
    )
    
    # Sección 2: Tareas con diferentes estados
    section2_title = ft.Text(
        "2. Tareas con Diferentes Estados",
        size=24,
        weight=ft.FontWeight.BOLD,
        color=ft.Colors.WHITE,
    )
    
    status_tasks = ft.Column(
        controls=[
            create_task_card(
                Task(
                    id="task_3",
                    title="Tarea Pendiente",
                    user_id="user_1",
                    status=TASK_STATUS_PENDING
                ),
                page=page
            ),
            create_task_card(
                Task(
                    id="task_4",
                    title="Tarea En Progreso",
                    user_id="user_1",
                    status=TASK_STATUS_IN_PROGRESS
                ),
                page=page
            ),
            create_task_card(
                Task(
                    id="task_5",
                    title="Tarea Completada",
                    user_id="user_1",
                    status=TASK_STATUS_COMPLETED
                ),
                page=page
            ),
        ],
        spacing=15,
    )
    
    # Sección 3: Tareas con prioridad
    section3_title = ft.Text(
        "3. Tareas con Prioridad (Matriz de Eisenhower)",
        size=24,
        weight=ft.FontWeight.BOLD,
        color=ft.Colors.WHITE,
    )
    
    priority_tasks = ft.Column(
        controls=[
            create_task_card(
                Task(
                    id="task_6",
                    title="Tarea Q1 (Urgente e Importante)",
                    user_id="user_1",
                    urgent=True,
                    important=True
                ),
                page=page
            ),
            create_task_card(
                Task(
                    id="task_7",
                    title="Tarea Q2 (Importante, no Urgente)",
                    user_id="user_1",
                    urgent=False,
                    important=True
                ),
                page=page
            ),
        ],
        spacing=15,
    )
    
    # Sección 4: Tareas con fecha de vencimiento
    section4_title = ft.Text(
        "4. Tareas con Fecha de Vencimiento",
        size=24,
        weight=ft.FontWeight.BOLD,
        color=ft.Colors.WHITE,
    )
    
    from datetime import timedelta
    today = date.today()
    
    date_tasks = ft.Column(
        controls=[
            create_task_card(
                Task(
                    id="task_8",
                    title="Tarea vence hoy",
                    user_id="user_1",
                    due_date=today
                ),
                page=page
            ),
            create_task_card(
                Task(
                    id="task_9",
                    title="Tarea vence pronto (3 días)",
                    user_id="user_1",
                    due_date=today + timedelta(days=3)
                ),
                page=page
            ),
            create_task_card(
                Task(
                    id="task_10",
                    title="Tarea vencida",
                    user_id="user_1",
                    due_date=today - timedelta(days=2)
                ),
                page=page
            ),
        ],
        spacing=15,
    )
    
    # Sección 5: Tareas con subtareas
    section5_title = ft.Text(
        "5. Tareas con Subtareas",
        size=24,
        weight=ft.FontWeight.BOLD,
        color=ft.Colors.WHITE,
    )
    
    task_with_subtasks = Task(
        id="task_11",
        title="Tarea con múltiples subtareas",
        description="Esta tarea tiene varias subtareas para completar",
        user_id="user_1"
    )
    task_with_subtasks.add_subtask(Subtask(id="sub_1", task_id="task_11", title="Subtarea 1", completed=True))
    task_with_subtasks.add_subtask(Subtask(id="sub_2", task_id="task_11", title="Subtarea 2", completed=False))
    task_with_subtasks.add_subtask(Subtask(id="sub_3", task_id="task_11", title="Subtarea 3", completed=True))
    
    subtasks_tasks = ft.Column(
        controls=[
            create_task_card(
                task_with_subtasks,
                page=page,
                on_subtask_toggle=handle_subtask_toggle,
                show_subtasks=True,
                show_progress=True
            ),
        ],
        spacing=15,
    )
    
    # Sección 6: Tareas con tags
    section6_title = ft.Text(
        "6. Tareas con Tags",
        size=24,
        weight=ft.FontWeight.BOLD,
        color=ft.Colors.WHITE,
    )
    
    tags_tasks = ft.Column(
        controls=[
            create_task_card(
                Task(
                    id="task_12",
                    title="Tarea con tags",
                    user_id="user_1",
                    tags=["urgente", "trabajo", "importante"]
                ),
                page=page,
                show_tags=True
            ),
            create_task_card(
                Task(
                    id="task_13",
                    title="Tarea con muchos tags",
                    user_id="user_1",
                    tags=["tag1", "tag2", "tag3", "tag4", "tag5", "tag6"]
                ),
                page=page,
                show_tags=True
            ),
        ],
        spacing=15,
    )
    
    # Sección 7: Tareas con acciones
    section7_title = ft.Text(
        "7. Tareas con Acciones",
        size=24,
        weight=ft.FontWeight.BOLD,
        color=ft.Colors.WHITE,
    )
    
    actions_tasks = ft.Column(
        controls=[
            create_task_card(
                Task(id="task_14", title="Tarea con todas las acciones", user_id="user_1"),
                page=page,
                on_click=handle_click,
                on_edit=handle_edit,
                on_delete=handle_delete,
                on_toggle_status=handle_toggle
            ),
        ],
        spacing=15,
    )
    
    # Sección 8: Modo compacto
    section8_title = ft.Text(
        "8. Modo Compacto",
        size=24,
        weight=ft.FontWeight.BOLD,
        color=ft.Colors.WHITE,
    )
    
    compact_tasks = ft.Column(
        controls=[
            create_task_card(
                Task(id="task_15", title="Tarea compacta 1", user_id="user_1"),
                page=page,
                compact=True
            ),
            create_task_card(
                Task(
                    id="task_16",
                    title="Tarea compacta 2",
                    description="Descripción corta",
                    user_id="user_1"
                ),
                page=page,
                compact=True
            ),
        ],
        spacing=10,
    )
    
    # Sección 9: Tarea completa
    section9_title = ft.Text(
        "9. Tarea Completa (Todos los Elementos)",
        size=24,
        weight=ft.FontWeight.BOLD,
        color=ft.Colors.WHITE,
    )
    
    complete_task = Task(
        id="task_17",
        title="Tarea completa con todos los elementos",
        description="Esta es una tarea que incluye todos los elementos posibles: descripción, fecha de vencimiento, tags, subtareas, y acciones.",
        user_id="user_1",
        status=TASK_STATUS_IN_PROGRESS,
        urgent=True,
        important=True,
        due_date=today + timedelta(days=2),
        tags=["urgente", "trabajo", "importante", "proyecto"]
    )
    complete_task.add_subtask(Subtask(id="sub_4", task_id="task_17", title="Subtarea completada", completed=True))
    complete_task.add_subtask(Subtask(id="sub_5", task_id="task_17", title="Subtarea pendiente", completed=False))
    complete_task.add_subtask(Subtask(id="sub_6", task_id="task_17", title="Otra subtarea", completed=True))
    
    complete_tasks = ft.Column(
        controls=[
            create_task_card(
                complete_task,
                page=page,
                on_click=handle_click,
                on_edit=handle_edit,
                on_delete=handle_delete,
                on_toggle_status=handle_toggle,
                on_subtask_toggle=handle_subtask_toggle,
                show_subtasks=True,
                show_tags=True,
                show_progress=True
            ),
        ],
        spacing=15,
    )
    
    # Sección 10: Usando la clase TaskCard
    section10_title = ft.Text(
        "10. Usando la Clase TaskCard",
        size=24,
        weight=ft.FontWeight.BOLD,
        color=ft.Colors.WHITE,
    )
    
    class_tasks = ft.Column(
        controls=[
            TaskCard(
                Task(id="task_18", title="Tarea con clase", user_id="user_1"),
                page=page
            ).build(),
            TaskCard(
                Task(
                    id="task_19",
                    title="Tarea con clase completada",
                    user_id="user_1",
                    status=TASK_STATUS_COMPLETED
                ),
                page=page
            ).build(),
        ],
        spacing=15,
    )
    
    # Contenedor principal con scroll
    main_content = ft.Column(
        controls=[
            title,
            ft.Divider(height=30, color=ft.Colors.TRANSPARENT),
            
            section1_title,
            ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
            basic_tasks,
            ft.Divider(height=30, color=ft.Colors.TRANSPARENT),
            
            section2_title,
            ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
            status_tasks,
            ft.Divider(height=30, color=ft.Colors.TRANSPARENT),
            
            section3_title,
            ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
            priority_tasks,
            ft.Divider(height=30, color=ft.Colors.TRANSPARENT),
            
            section4_title,
            ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
            date_tasks,
            ft.Divider(height=30, color=ft.Colors.TRANSPARENT),
            
            section5_title,
            ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
            subtasks_tasks,
            ft.Divider(height=30, color=ft.Colors.TRANSPARENT),
            
            section6_title,
            ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
            tags_tasks,
            ft.Divider(height=30, color=ft.Colors.TRANSPARENT),
            
            section7_title,
            ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
            actions_tasks,
            ft.Divider(height=30, color=ft.Colors.TRANSPARENT),
            
            section8_title,
            ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
            compact_tasks,
            ft.Divider(height=30, color=ft.Colors.TRANSPARENT),
            
            section9_title,
            ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
            complete_tasks,
            ft.Divider(height=30, color=ft.Colors.TRANSPARENT),
            
            section10_title,
            ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
            class_tasks,
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

