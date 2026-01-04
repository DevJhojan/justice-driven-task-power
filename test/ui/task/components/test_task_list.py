"""
Tests para el componente TaskList
Pruebas unitarias + Demo UI para la lista de tareas modularizada
"""

import sys
import os
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

import flet as ft
from typing import Optional
from unittest.mock import Mock, MagicMock
from datetime import datetime, timedelta
from app.models.task import Task
from app.models.subtask import Subtask
from app.ui.task.List.task_list import create_task_list, TaskList


# ============================================================================
# FIXTURES Y HELPERS
# ============================================================================

def create_test_task(
    task_id: str = "test-1",
    title: str = "Test Task",
    description: str = "Test Description",
    status: str = "pendiente",
    urgent: bool = False,
    important: bool = False,
    due_date: Optional[datetime] = None,
    tags: Optional[list] = None,
    subtasks: Optional[list] = None,
) -> Task:
    """Crea una tarea de prueba."""
    if due_date is None:
        due_date = datetime.now() + timedelta(days=1)
    
    if tags is None:
        tags = ["test", "demo"]
    
    if subtasks is None:
        subtasks = []
    
    task = Task(
        id=task_id,
        title=title,
        description=description,
        status=status,
        urgent=urgent,
        important=important,
        due_date=due_date,
        tags=tags,
        subtasks=subtasks,
    )
    return task


def create_test_subtask(
    subtask_id: str = "subtask-1",
    task_id: str = "test-task",
    title: str = "Subtask",
    completed: bool = False,
) -> Subtask:
    """Crea una subtarea de prueba."""
    return Subtask(
        id=subtask_id,
        task_id=task_id,
        title=title,
        completed=completed,
    )


# ============================================================================
# TESTS UNITARIOS
# ============================================================================

def test_create_task_list_empty():
    """Test: crear_task_list con lista vacía debe mostrar mensaje de "No hay tareas"."""
    result = create_task_list(tasks=[])
    assert isinstance(result, ft.Column)
    assert len(result.controls) == 1
    # Debe contener un Container con el mensaje vacío
    container = result.controls[0]
    assert isinstance(container, ft.Container)
    print("✅ test_create_task_list_empty: Passed")


def test_create_task_list_with_tasks():
    """Test: create_task_list con tareas debe crear tarjetas para cada una."""
    task1 = create_test_task(task_id="1", title="Task 1")
    task2 = create_test_task(task_id="2", title="Task 2")
    
    result = create_task_list(tasks=[task1, task2])
    assert isinstance(result, ft.Column)
    assert len(result.controls) == 2
    print("✅ test_create_task_list_with_tasks: Passed")


def test_task_list_init():
    """Test: TaskList inicialización correcta."""
    tasks = [
        create_test_task(task_id="1", title="Task 1"),
        create_test_task(task_id="2", title="Task 2"),
    ]
    
    task_list = TaskList(tasks=tasks)
    assert task_list.tasks == tasks
    assert len(task_list.get_tasks()) == 2
    print("✅ test_task_list_init: Passed")


def test_task_list_init_none():
    """Test: TaskList inicialización con None crea lista vacía."""
    task_list = TaskList(tasks=None)
    assert task_list.tasks == []
    assert len(task_list.get_tasks()) == 0
    print("✅ test_task_list_init_none: Passed")


def test_task_list_build():
    """Test: TaskList.build() retorna un Column."""
    task1 = create_test_task(task_id="1", title="Task 1")
    task_list = TaskList(tasks=[task1])
    
    result = task_list.build()
    assert isinstance(result, ft.Column)
    print("✅ test_task_list_build: Passed")


def test_task_list_add_task():
    """Test: agregar tarea a TaskList."""
    task_list = TaskList()
    task1 = create_test_task(task_id="1", title="Task 1")
    
    task_list.add_task(task1)
    assert len(task_list.get_tasks()) == 1
    assert task_list.get_task("1") == task1
    print("✅ test_task_list_add_task: Passed")


def test_task_list_remove_task():
    """Test: eliminar tarea de TaskList."""
    task1 = create_test_task(task_id="1", title="Task 1")
    task2 = create_test_task(task_id="2", title="Task 2")
    
    task_list = TaskList(tasks=[task1, task2])
    task_list.remove_task("1")
    
    assert len(task_list.get_tasks()) == 1
    assert task_list.get_task("1") is None
    assert task_list.get_task("2") is not None
    print("✅ test_task_list_remove_task: Passed")


def test_task_list_get_task():
    """Test: obtener tarea por ID."""
    task1 = create_test_task(task_id="1", title="Task 1")
    task2 = create_test_task(task_id="2", title="Task 2")
    
    task_list = TaskList(tasks=[task1, task2])
    
    result = task_list.get_task("1")
    assert result == task1
    
    result_none = task_list.get_task("999")
    assert result_none is None
    print("✅ test_task_list_get_task: Passed")


def test_task_list_update_task():
    """Test: actualizar tarea existente."""
    task1 = create_test_task(task_id="1", title="Task 1")
    task_list = TaskList(tasks=[task1])
    
    # Actualizar la tarea
    task1_updated = create_test_task(task_id="1", title="Task 1 Updated")
    task_list.update_task(task1_updated)
    
    assert task_list.get_task("1").title == "Task 1 Updated"
    print("✅ test_task_list_update_task: Passed")


def test_task_list_filter_tasks():
    """Test: filtrar tareas por predicado."""
    task_high = create_test_task(task_id="1", title="High Priority", urgent=True, important=True)
    task_low = create_test_task(task_id="2", title="Low Priority", urgent=False, important=False)
    
    task_list = TaskList(tasks=[task_high, task_low])
    
    high_priority_tasks = task_list.filter_tasks(lambda t: t.urgent and t.important)
    assert len(high_priority_tasks) == 1
    assert high_priority_tasks[0].title == "High Priority"
    print("✅ test_task_list_filter_tasks: Passed")


def test_task_list_sort_tasks():
    """Test: ordenar tareas por función clave."""
    task_a = create_test_task(task_id="3", title="Zebra")
    task_b = create_test_task(task_id="1", title="Apple")
    task_c = create_test_task(task_id="2", title="Banana")
    
    task_list = TaskList(tasks=[task_a, task_b, task_c])
    task_list.sort_tasks()
    
    sorted_tasks = task_list.get_tasks()
    assert sorted_tasks[0].title == "Apple"
    assert sorted_tasks[1].title == "Banana"
    assert sorted_tasks[2].title == "Zebra"
    print("✅ test_task_list_sort_tasks: Passed")


def test_task_list_clear():
    """Test: limpiar todas las tareas."""
    task1 = create_test_task(task_id="1", title="Task 1")
    task2 = create_test_task(task_id="2", title="Task 2")
    
    task_list = TaskList(tasks=[task1, task2])
    assert len(task_list.get_tasks()) == 2
    
    task_list.clear()
    assert len(task_list.get_tasks()) == 0
    print("✅ test_task_list_clear: Passed")


def test_task_list_set_tasks():
    """Test: reemplazar la lista de tareas."""
    task1 = create_test_task(task_id="1", title="Task 1")
    task2 = create_test_task(task_id="2", title="Task 2")
    task3 = create_test_task(task_id="3", title="Task 3")
    
    task_list = TaskList(tasks=[task1])
    task_list.set_tasks([task2, task3])
    
    assert len(task_list.get_tasks()) == 2
    assert task_list.get_task("2") is not None
    assert task_list.get_task("3") is not None
    assert task_list.get_task("1") is None
    print("✅ test_task_list_set_tasks: Passed")


def test_task_list_refresh():
    """Test: refresh invalida el caché."""
    task1 = create_test_task(task_id="1", title="Task 1")
    task_list = TaskList(tasks=[task1])
    
    # Build cachea el resultado
    first_build = task_list.build()
    
    # Refresh debe limpiar el caché
    task_list.refresh()
    assert task_list._list_column is None
    
    # Siguiente build debe ser diferente (nuevo objeto)
    second_build = task_list.build()
    assert first_build is not second_build
    print("✅ test_task_list_refresh: Passed")


def test_task_list_get_tasks():
    """Test: obtener copia de la lista de tareas."""
    task1 = create_test_task(task_id="1", title="Task 1")
    task_list = TaskList(tasks=[task1])
    
    retrieved = task_list.get_tasks()
    assert len(retrieved) == 1
    assert retrieved[0] == task1
    
    # Debe ser una copia
    retrieved.append(create_test_task(task_id="999"))
    assert len(task_list.get_tasks()) == 1
    print("✅ test_task_list_get_tasks: Passed")


# ============================================================================
# DEMO UI
# ============================================================================

def demo_ui(page: ft.Page):
    """Demo UI interactiva del componente TaskList."""
    page.title = "Demo: TaskList Component"
    page.theme_mode = ft.ThemeMode.DARK
    
    # Crear tareas de ejemplo
    demo_tasks = [
        create_test_task(
            task_id="1",
            title="Diseñar interfaz de usuario",
            description="Crear mockups y wireframes para la nueva vista de tareas",
            urgent=True,
            important=True,
            subtasks=[
                create_test_subtask(subtask_id="1.1", task_id="1", title="Crear mockups", completed=False),
                create_test_subtask(subtask_id="1.2", task_id="1", title="Definir colores", completed=False),
                create_test_subtask(subtask_id="1.3", task_id="1", title="Revisar con equipo", completed=False),
            ],
        ),
        create_test_task(
            task_id="2",
            title="Implementar backend",
            description="Desarrollar API REST para gestión de tareas",
            urgent=True,
            important=True,
            subtasks=[
                create_test_subtask(subtask_id="2.1", task_id="2", title="Configurar base de datos", completed=True),
                create_test_subtask(subtask_id="2.2", task_id="2", title="Crear endpoints", completed=False),
                create_test_subtask(subtask_id="2.3", task_id="2", title="Agregar validaciones", completed=False),
            ],
        ),
        create_test_task(
            task_id="3",
            title="Escribir documentación",
            description="Documentar API y componentes",
            urgent=False,
            important=True,
            subtasks=[
                create_test_subtask(subtask_id="3.1", task_id="3", title="Documentar endpoints", completed=False),
            ],
        ),
        create_test_task(
            task_id="4",
            title="Testing",
            description="Escribir pruebas unitarias",
            urgent=False,
            important=True,
            subtasks=[],
        ),
    ]
    
    # Crear handlers para demostración
    def handle_task_click(task_id: str):
        print(f"📌 Click en tarea: {task_id}")
    
    def handle_task_edit(task_id: str):
        print(f"✏️ Editar tarea: {task_id}")
    
    def handle_task_delete(task_id: str):
        print(f"🗑️ Eliminar tarea: {task_id}")
    
    def handle_task_toggle_status(task_id: str):
        print(f"🔄 Toggle status tarea: {task_id}")
    
    def handle_subtask_toggle(task_id: str, subtask_id: str):
        print(f"✓ Toggle subtarea: {subtask_id} en tarea {task_id}")
    
    # ========== Case 1: Lista con tareas ==========
    case1_title = ft.Text("Case 1: Lista con múltiples tareas", size=20, weight=ft.FontWeight.BOLD)
    task_list_1 = TaskList(
        tasks=demo_tasks,
        page=page,
        on_task_click=handle_task_click,
        on_task_edit=handle_task_edit,
        on_task_delete=handle_task_delete,
        on_task_toggle_status=handle_task_toggle_status,
        on_subtask_toggle=handle_subtask_toggle,
    )
    case1_content = task_list_1.build()
    case1 = ft.Container(
        content=ft.Column([case1_title, case1_content], spacing=16),
        bgcolor=ft.Colors.BLUE_GREY_900,
        padding=20,
        border_radius=10,
    )
    
    # ========== Case 2: Lista vacía ==========
    case2_title = ft.Text("Case 2: Lista vacía", size=20, weight=ft.FontWeight.BOLD)
    task_list_2 = TaskList(
        tasks=[],
        page=page,
        on_task_edit=handle_task_edit,
        on_task_delete=handle_task_delete,
    )
    case2_content = task_list_2.build()
    case2 = ft.Container(
        content=ft.Column([case2_title, case2_content], spacing=16),
        bgcolor=ft.Colors.BLUE_GREY_900,
        padding=20,
        border_radius=10,
    )
    
    # ========== Case 3: Agregar/Eliminar dinámico ==========
    case3_title = ft.Text("Case 3: Operaciones dinámicas (Add/Remove)", size=20, weight=ft.FontWeight.BOLD)
    task_list_3 = TaskList(
        tasks=[demo_tasks[0]],
        page=page,
        on_task_edit=handle_task_edit,
        on_task_delete=handle_task_delete,
        on_subtask_toggle=handle_subtask_toggle,
    )
    task_list_3_content = ft.Container(
        content=task_list_3.build(),
        expand=True,
        bgcolor=ft.Colors.BLUE_GREY_800,
        padding=10,
        border_radius=8,
    )
    
    def add_task_click(e):
        new_task = create_test_task(
            task_id=f"new-{len(task_list_3.get_tasks())}",
            title=f"Nueva tarea {len(task_list_3.get_tasks()) + 1}",
            urgent=False,
            important=True,
        )
        task_list_3.add_task(new_task)
        task_list_3_content.content = task_list_3.build()
        page.update()
    
    def remove_task_click(e):
        tasks = task_list_3.get_tasks()
        if tasks:
            task_list_3.remove_task(tasks[0].id)
            task_list_3_content.content = task_list_3.build()
            page.update()
    
    case3_buttons = ft.Row([
        ft.ElevatedButton("Agregar tarea", on_click=add_task_click, icon=ft.Icons.ADD),
        ft.ElevatedButton("Eliminar primera", on_click=remove_task_click, icon=ft.Icons.DELETE),
    ], spacing=10)
    
    case3 = ft.Container(
        content=ft.Column([case3_title, case3_buttons, task_list_3_content], spacing=16),
        bgcolor=ft.Colors.BLUE_GREY_900,
        padding=20,
        border_radius=10,
        expand=True,
    )
    
    # ========== Case 4: Filtrar por prioridad ==========
    case4_title = ft.Text("Case 4: Filtrar por prioridad (URGENT & IMPORTANT)", size=20, weight=ft.FontWeight.BOLD)
    task_list_4 = TaskList(
        tasks=demo_tasks,
        page=page,
        on_task_edit=handle_task_edit,
        on_task_delete=handle_task_delete,
    )
    high_priority = task_list_4.filter_tasks(lambda t: t.urgent and t.important)
    high_priority_list = create_task_list(
        high_priority,
        page=page,
        on_task_edit=handle_task_edit,
        on_task_delete=handle_task_delete,
        on_subtask_toggle=handle_subtask_toggle,
    )
    case4 = ft.Container(
        content=ft.Column([case4_title, high_priority_list], spacing=16),
        bgcolor=ft.Colors.BLUE_GREY_900,
        padding=20,
        border_radius=10,
    )
    
    # ========== Case 5: Ordenar alfabéticamente ==========
    case5_title = ft.Text("Case 5: Tareas ordenadas alfabéticamente", size=20, weight=ft.FontWeight.BOLD)
    task_list_5 = TaskList(
        tasks=demo_tasks.copy(),
        page=page,
        on_task_edit=handle_task_edit,
        on_task_delete=handle_task_delete,
        on_subtask_toggle=handle_subtask_toggle,
    )
    task_list_5.sort_tasks()
    case5_content = task_list_5.build()
    case5 = ft.Container(
        content=ft.Column([case5_title, case5_content], spacing=16),
        bgcolor=ft.Colors.BLUE_GREY_900,
        padding=20,
        border_radius=10,
    )
    
    # ========== Statstics Section ==========
    stats_title = ft.Text("Estadísticas", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_400)
    
    total_tasks = len(demo_tasks)
    high_priority_count = len(task_list_4.filter_tasks(lambda t: t.urgent and t.important))
    important_count = len(task_list_4.filter_tasks(lambda t: t.important))
    
    stats_content = ft.Column([
        ft.Text(f"Total de tareas: {total_tasks}", size=14),
        ft.Text(f"Urgentes e Importantes: {high_priority_count}", size=14, color=ft.Colors.RED_400),
        ft.Text(f"Importantes: {important_count}", size=14, color=ft.Colors.ORANGE_400),
    ], spacing=8)
    
    stats = ft.Container(
        content=ft.Column([stats_title, stats_content], spacing=10),
        bgcolor=ft.Colors.BLUE_GREY_900,
        padding=20,
        border_radius=10,
    )
    
    # Main layout
    main_column = ft.Column([
        ft.Text("TaskList Component - Demo UI", size=28, weight=ft.FontWeight.BOLD),
        ft.Divider(),
        case1,
        case2,
        case3,
        case4,
        case5,
        stats,
    ], spacing=20, scroll=ft.ScrollMode.AUTO)
    
    page.add(
        ft.Container(
            content=main_column,
            padding=20,
            expand=True,
        )
    )


# ============================================================================
# MAIN - Ejecutar tests
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*70)
    print("TESTS UNITARIOS - TaskList Component")
    print("="*70 + "\n")
    
    # Ejecutar todos los tests unitarios
    test_create_task_list_empty()
    test_create_task_list_with_tasks()
    test_task_list_init()
    test_task_list_init_none()
    test_task_list_build()
    test_task_list_add_task()
    test_task_list_remove_task()
    test_task_list_get_task()
    test_task_list_update_task()
    test_task_list_filter_tasks()
    test_task_list_sort_tasks()
    test_task_list_clear()
    test_task_list_set_tasks()
    test_task_list_refresh()
    test_task_list_get_tasks()
    
    print("\n" + "="*70)
    print("TOTAL: 15 tests - ✅ ALL PASSED")
    print("="*70 + "\n")
    
    # Demo UI
    print("Iniciando Demo UI...")
    ft.run(demo_ui)
