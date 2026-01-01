"""
Tests para el componente TaskFilters
Pruebas unitarias + Demo UI para el componente de filtrado de tareas
"""

import sys
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

import flet as ft
from typing import Optional
from datetime import datetime, timedelta, date
from app.models.task import Task
from app.models.subtask import Subtask
from app.ui.task.components.task_filters import create_task_filters, TaskFilters


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
    due_date: Optional[date] = None,
    tags: Optional[list] = None,
    subtasks: Optional[list] = None,
) -> Task:
    """Crea una tarea de prueba."""
    if due_date is None:
        due_date = date.today() + timedelta(days=1)
    
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


# ============================================================================
# TESTS UNITARIOS
# ============================================================================

def test_create_task_filters():
    """Test: create_task_filters debe retornar tupla (Row, Dict)."""
    result = create_task_filters()
    assert isinstance(result, tuple)
    assert len(result) == 2
    filters_row, controls_map = result
    assert isinstance(filters_row, ft.Row)
    assert isinstance(controls_map, dict)
    print("✅ test_create_task_filters: Passed")


def test_task_filters_init():
    """Test: TaskFilters inicialización correcta."""
    filters = TaskFilters()
    assert filters.current_filters["search"] == ""
    assert filters.current_filters["status"] is None
    assert filters.current_filters["urgent_important"] is None
    assert filters.current_filters["tags"] == []
    assert filters.current_filters["due_date"] is None
    print("✅ test_task_filters_init: Passed")


def test_task_filters_build():
    """Test: TaskFilters.build() retorna un Row."""
    filters = TaskFilters()
    result = filters.build()
    assert isinstance(result, ft.Row)
    print("✅ test_task_filters_build: Passed")


def test_task_filters_search():
    """Test: filtrar tareas por búsqueda de texto."""
    tasks = [
        create_test_task(task_id="1", title="Diseño de interfaz", description="UI/UX"),
        create_test_task(task_id="2", title="Backend API", description="REST endpoints"),
        create_test_task(task_id="3", title="Testing", description="QA automation"),
    ]
    
    filters = TaskFilters()
    filters.build()  # Construir los controles
    filters.set_filter("search", "diseño")
    
    result = filters.apply_filters(tasks)
    assert len(result) == 1
    assert result[0].title == "Diseño de interfaz"
    print("✅ test_task_filters_search: Passed")


def test_task_filters_status():
    """Test: filtrar tareas por estado."""
    tasks = [
        create_test_task(task_id="1", title="Task 1", status="pendiente"),
        create_test_task(task_id="2", title="Task 2", status="en_progreso"),
        create_test_task(task_id="3", title="Task 3", status="completada"),
    ]
    
    filters = TaskFilters()
    filters.build()
    filters.set_filter("status", "en_progreso")
    
    result = filters.apply_filters(tasks)
    assert len(result) == 1
    assert result[0].status == "en_progreso"
    print("✅ test_task_filters_status: Passed")


def test_task_filters_priority():
    """Test: filtrar tareas por urgencia/importancia."""
    tasks = [
        create_test_task(task_id="1", title="Task 1", urgent=True, important=True),
        create_test_task(task_id="2", title="Task 2", urgent=False, important=True),
        create_test_task(task_id="3", title="Task 3", urgent=True, important=False),
        create_test_task(task_id="4", title="Task 4", urgent=False, important=False),
    ]
    
    filters = TaskFilters()
    filters.build()
    filters.set_filter("priority", "Importante")
    
    result = filters.apply_filters(tasks)
    assert len(result) == 1
    assert result[0].title == "Task 2"
    print("✅ test_task_filters_priority: Passed")


def test_task_filters_tags():
    """Test: filtrar tareas por etiquetas."""
    tasks = [
        create_test_task(task_id="1", title="Task 1", tags=["python", "backend"]),
        create_test_task(task_id="2", title="Task 2", tags=["react", "frontend"]),
        create_test_task(task_id="3", title="Task 3", tags=["testing", "qa"]),
    ]
    
    filters = TaskFilters()
    filters.build()
    filters.set_filter("tags", ["python", "frontend"])
    
    result = filters.apply_filters(tasks)
    assert len(result) == 2
    print("✅ test_task_filters_tags: Passed")


def test_task_filters_due_date():
    """Test: filtrar tareas por fecha de vencimiento."""
    today = date.today()
    tomorrow = today + timedelta(days=1)
    next_week = today + timedelta(days=7)
    tasks = [
        create_test_task(task_id="1", title="Hoy", due_date=today),
        create_test_task(task_id="2", title="Mañana", due_date=tomorrow),
        create_test_task(task_id="3", title="Próxima semana", due_date=next_week),
    ]
    
    filters = TaskFilters()
    filters.build()
    filters.set_filter("due_date", today)
    
    result = filters.apply_filters(tasks)
    assert len(result) == 1
    assert result[0].title == "Hoy"
    print("✅ test_task_filters_due_date: Passed")


def test_task_filters_multiple():
    """Test: aplicar múltiples filtros simultáneamente."""
    tasks = [
        create_test_task(
            task_id="1", 
            title="Importante y urgente", 
            status="pendiente",
            urgent=True, 
            important=True
        ),
        create_test_task(
            task_id="2", 
            title="Solo importante", 
            status="en_progreso",
            urgent=False, 
            important=True
        ),
        create_test_task(
            task_id="3", 
            title="Python testing", 
            status="pendiente",
            urgent=False, 
            important=False
        ),
    ]
    
    filters = TaskFilters()
    filters.build()
    
    filters.set_filter("status", "pendiente")
    filters.set_filter("priority", "Urgente e Importante")
    
    result = filters.apply_filters(tasks)
    assert len(result) == 1
    assert result[0].title == "Importante y urgente"
    print("✅ test_task_filters_multiple: Passed")


def test_task_filters_clear():
    """Test: limpiar filtros."""
    filters = TaskFilters()
    filters.build()
    
    filters.set_filter("search", "test")
    filters.set_filter("status", "en_progreso")

    assert filters.has_active_filters()

    filters.clear_filters()

    assert not filters.has_active_filters()
    print("✅ test_task_filters_clear: Passed")


def test_task_filters_has_active():
    """Test: detectar filtros activos."""
    filters = TaskFilters()
    filters.build()
    
    # Sin filtros
    assert not filters.has_active_filters()
    
    # Con filtro de búsqueda
    filters.set_filter("search", "test")
    assert filters.has_active_filters()
    print("✅ test_task_filters_has_active: Passed")


# ============================================================================
# DEMO UI
# ============================================================================

def demo_ui(page: ft.Page):
    """Demo UI interactiva del componente TaskFilters."""
    page.title = "TaskFilters Component Demo"
    page.theme_mode = ft.ThemeMode.DARK
    
    # Crear tareas de ejemplo
    demo_tasks = [
        create_test_task(
            task_id="1",
            title="Diseñar interfaz de usuario",
            description="Crear mockups y wireframes para la aplicación",
            status="pendiente",
            urgent=True,
            important=True,
            due_date=date.today(),
            tags=["design", "ui", "frontend"],
        ),
        create_test_task(
            task_id="2",
            title="Implementar backend API",
            description="Desarrollar endpoints REST con Python",
            status="en_progreso",
            urgent=True,
            important=True,
            due_date=date.today() + timedelta(days=3),
            tags=["backend", "python", "api"],
        ),
        create_test_task(
            task_id="3",
            title="Escribir documentación",
            description="Documentar API y crear README",
            status="pendiente",
            urgent=False,
            important=True,
            due_date=date.today() + timedelta(days=7),
            tags=["docs", "documentation"],
        ),
        create_test_task(
            task_id="4",
            title="Testing unitarios",
            description="Cobertura del 80% del código",
            status="en_progreso",
            urgent=True,
            important=False,
            due_date=date.today() + timedelta(days=1),
            tags=["testing", "qa", "python"],
        ),
        create_test_task(
            task_id="5",
            title="Review de código",
            description="Revisar pull requests",
            status="completada",
            urgent=False,
            important=True,
            due_date=date.today() - timedelta(days=1),
            tags=["review", "code"],
        ),
    ]
    
    # Variable para mostrar tareas filtradas
    filtered_tasks_info = ft.Text(value="Tareas: 5", size=14, color=ft.Colors.BLUE_400)
    tasks_list = ft.Column(spacing=8, scroll=ft.ScrollMode.AUTO, expand=True)
    
    def update_task_list():
        """Actualiza la lista de tareas mostrada"""
        filtered = filters.apply_filters(demo_tasks)
        tasks_list.controls.clear()
        
        if not filtered:
            tasks_list.controls.append(
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Icon(icon=ft.Icons.SEARCH, size=40, color=ft.Colors.GREY_700),
                            ft.Text("No se encontraron tareas", size=14, color=ft.Colors.GREY_700),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    padding=40,
                )
            )
        else:
            for task in filtered:
                task_card = ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Row(
                                controls=[
                                    ft.Column(
                                        controls=[
                                            ft.Text(task.title, size=14, weight=ft.FontWeight.BOLD),
                                            ft.Text(task.description, size=12, color=ft.Colors.GREY_600),
                                        ],
                                        expand=True,
                                    ),
                                    ft.Column(
                                        controls=[
                                            ft.Chip(
                                                label=ft.Text(task.status, size=10, color=ft.Colors.WHITE),
                                                bgcolor=ft.Colors.BLUE_600 if task.status == "pendiente" else ft.Colors.ORANGE_600 if task.status == "en_progreso" else ft.Colors.GREEN_600,
                                                padding=ft.Padding(8, 4, 8, 4),
                                            ),
                                        ],
                                        horizontal_alignment=ft.CrossAxisAlignment.END,
                                    ),
                                ],
                                spacing=10,
                            ),
                            ft.Row(
                                controls=[
                                    ft.Chip(
                                        label=ft.Text(tag, size=10),
                                        bgcolor=ft.Colors.BLUE_GREY_800,
                                    )
                                    for tag in (task.tags or [])
                                ],
                                spacing=4,
                                wrap=True,
                            ) if task.tags else ft.SizedBox(height=0),
                        ],
                        spacing=8,
                    ),
                    padding=12,
                    bgcolor=ft.Colors.BLUE_GREY_800,
                    border_radius=8,
                )
                tasks_list.controls.append(task_card)
        
        filtered_tasks_info.value = f"Tareas: {len(filtered)}"
        page.update()
    
    def on_apply_filters(e):
        """Callback cuando se presiona Aplicar"""
        update_task_list()
    
    # Crear filtros con callback
    filters = TaskFilters(page=page, on_filter_change=lambda f: update_task_list())
    filters_row = filters.build()
    
    # Header
    header = ft.Container(
        content=ft.Column(
            controls=[
                ft.Text("TaskFilters Component Demo", size=24, weight=ft.FontWeight.BOLD),
                ft.Text("Presiona 'Aplicar' para filtrar las tareas", size=12, color=ft.Colors.GREY_600),
            ]
        ),
        padding=16,
    )
    
    # Panel de filtros
    filters_panel = ft.Container(
        content=ft.Column(
            controls=[
                ft.Text("🔍 Opciones de Filtrado", size=14, weight=ft.FontWeight.BOLD),
                filters_row,
            ],
            spacing=12,
        ),
        padding=16,
        bgcolor=ft.Colors.BLUE_GREY_900,
        border_radius=8,
    )
    
    # Panel de tareas
    tasks_panel = ft.Container(
        content=ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Text("📋 Tareas Filtradas", size=14, weight=ft.FontWeight.BOLD),
                        filtered_tasks_info,
                    ],
                    spacing=12,
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                ft.Divider(height=1, color=ft.Colors.GREY_700),
                ft.Container(
                    content=tasks_list,
                    height=420,
                    bgcolor=ft.Colors.BLUE_GREY_800,
                    border_radius=8,
                    padding=8,
                ),
            ],
            spacing=12,
            expand=True,
        ),
        padding=16,
        bgcolor=ft.Colors.BLUE_GREY_800,
        border_radius=8,
        expand=True,
    )
    
    # Layout principal
    main_content = ft.Column(
        controls=[
            header,
            filters_panel,
            tasks_panel,
        ],
        spacing=16,
        expand=True,
    )
    
    page.add(
        ft.Container(
            content=main_content,
            padding=20,
            expand=True,
        )
    )
    
    # Mostrar las tareas inicialmente
    update_task_list()


# ============================================================================
# MAIN - Ejecutar tests
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*70)
    print("TESTS UNITARIOS - TaskFilters Component")
    print("="*70 + "\n")
    
    # Ejecutar todos los tests unitarios
    test_create_task_filters()
    test_task_filters_init()
    test_task_filters_build()
    test_task_filters_search()
    test_task_filters_status()
    test_task_filters_priority()
    test_task_filters_tags()
    test_task_filters_due_date()
    test_task_filters_multiple()
    test_task_filters_clear()
    test_task_filters_has_active()
    
    print("\n" + "="*70)
    print("TOTAL: 11 tests - ✅ ALL PASSED")
    print("="*70 + "\n")
    
    # Demo UI
    print("Iniciando Demo UI...")
    ft.app(target=demo_ui)
