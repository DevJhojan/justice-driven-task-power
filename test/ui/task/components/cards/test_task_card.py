"""
Tests para el componente Task Card (Orquestador Final)
Verifica la creación y funcionalidad de tarjetas de tareas usando componentes modulares
"""

from pathlib import Path
import sys

# Agregar el directorio raíz al path para imports (necesario cuando se ejecuta directamente)
# Este archivo está en `test/ui/task/components/cards/` por lo que hay que subir 5 niveles
project_root = Path(__file__).resolve().parents[5]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import pytest
import flet as ft
from datetime import date, timedelta
from app.ui.task.components.cards.task_card import create_task_card, TaskCard
from app.models.task import Task
from app.models.subtask import Subtask
from app.utils.task_helper import (
    TASK_STATUS_PENDING,
    TASK_STATUS_IN_PROGRESS,
    TASK_STATUS_COMPLETED,
)


def test_create_task_card_basic(mock_page):
    """Test crear tarjeta de tarea básica"""
    task = Task(id="task_1", title="Tarea de prueba", user_id="user_1")
    card = create_task_card(task, page=mock_page)
    
    assert isinstance(card, ft.Container)
    assert card.content is not None
    assert isinstance(card.content, ft.Column)
    assert len(card.content.controls) > 0


def test_create_task_card_without_page():
    """Test crear tarjeta sin objeto page"""
    task = Task(id="task_1", title="Tarea", user_id="user_1")
    card = create_task_card(task)
    
    assert isinstance(card, ft.Container)
    assert card.content is not None


def test_create_task_card_with_description(mock_page):
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


def test_create_task_card_with_due_date(mock_page):
    """Test crear tarjeta con fecha de vencimiento"""
    future_date = (date.today() + timedelta(days=5))
    task = Task(
        id="task_1",
        title="Tarea con fecha",
        user_id="user_1",
        due_date=future_date
    )
    card = create_task_card(task, page=mock_page)
    
    assert isinstance(card, ft.Container)
    # Debe tener información de fecha
    assert len(card.content.controls) >= 2


def test_create_task_card_with_subtasks(mock_page):
    """Test crear tarjeta con subtareas"""
    task = Task(id="task_1", title="Tarea con subtareas", user_id="user_1")
    subtask1 = Subtask(id="sub_1", task_id="task_1", title="Subtarea 1")
    subtask2 = Subtask(id="sub_2", task_id="task_1", title="Subtarea 2")
    task.subtasks = [subtask1, subtask2]
    
    card = create_task_card(task, page=mock_page, show_subtasks=True)
    
    assert isinstance(card, ft.Container)
    # Debe tener subtareas
    assert len(card.content.controls) >= 3


def test_create_task_card_without_subtasks_display(mock_page):
    """Test crear tarjeta sin mostrar subtareas"""
    task = Task(id="task_1", title="Tarea", user_id="user_1")
    subtask = Subtask(id="sub_1", task_id="task_1", title="Subtarea")
    task.subtasks = [subtask]
    
    card = create_task_card(task, page=mock_page, show_subtasks=False)
    
    assert isinstance(card, ft.Container)
    # No debe mostrar subtareas aunque existan


def test_create_task_card_with_tags(mock_page):
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


def test_create_task_card_without_tags_display(mock_page):
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


def test_create_task_card_with_progress(mock_page):
    """Test crear tarjeta con barra de progreso"""
    task = Task(id="task_1", title="Tarea", user_id="user_1")
    subtask1 = Subtask(id="sub_1", task_id="task_1", title="Subtarea 1", completed=True)
    subtask2 = Subtask(id="sub_2", task_id="task_1", title="Subtarea 2", completed=False)
    task.subtasks = [subtask1, subtask2]
    
    card = create_task_card(task, page=mock_page, show_progress=True)
    
    assert isinstance(card, ft.Container)
    # Debe tener barra de progreso


def test_create_task_card_without_progress(mock_page):
    """Test crear tarjeta sin barra de progreso"""
    task = Task(id="task_1", title="Tarea", user_id="user_1")
    card = create_task_card(task, page=mock_page, show_progress=False)
    
    assert isinstance(card, ft.Container)
    # No debe tener barra de progreso


def test_create_task_card_compact(mock_page):
    """Test crear tarjeta en modo compacto"""
    task = Task(id="task_1", title="Tarea compacta", user_id="user_1")
    card = create_task_card(task, page=mock_page, compact=True)
    
    assert isinstance(card, ft.Container)
    assert card.content is not None


def test_create_task_card_has_styling(mock_page):
    """Test que la tarjeta tiene estilos aplicados"""
    task = Task(id="task_1", title="Tarea", user_id="user_1")
    card = create_task_card(task, page=mock_page)
    
    assert card.border_radius is not None
    assert card.padding is not None
    assert card.bgcolor is not None
    assert card.border is not None


def test_create_task_card_different_statuses(mock_page):
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


def test_create_task_card_with_callbacks(mock_page):
    """Test crear tarjeta con callbacks"""
    task = Task(id="task_1", title="Tarea sin subtareas", user_id="user_1")
    task.subtasks = []
    
    click_called = []
    edit_called = []
    delete_called = []
    
    def handle_click(task_id):
        click_called.append(task_id)
    
    def handle_edit(task_id):
        edit_called.append(task_id)
    
    def handle_delete(task_id):
        delete_called.append(task_id)
    
    def handle_toggle(task_id):
        pass
    
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


def test_task_card_class_initialization(mock_page):
    """Test inicialización de TaskCard"""
    task = Task(id="task_1", title="Tarea", user_id="user_1")
    
    task_card = TaskCard(task=task, page=mock_page)
    
    assert task_card.task == task
    assert task_card.page == mock_page
    assert task_card._card is None


def test_task_card_class_build(mock_page):
    """Test construcción de TaskCard"""
    task = Task(id="task_1", title="Tarea para TaskCard", user_id="user_1")
    
    task_card = TaskCard(task=task, page=mock_page)
    card = task_card.build()
    
    assert isinstance(card, ft.Container)
    assert task_card._card is not None
    # Verificar que está en caché
    card2 = task_card.build()
    assert card is card2


def test_task_card_class_refresh(mock_page):
    """Test refresh de TaskCard invalida caché"""
    task = Task(id="task_1", title="Tarea", user_id="user_1")
    
    task_card = TaskCard(task=task, page=mock_page)
    card1 = task_card.build()
    
    # Refresh invalida caché
    task_card.refresh()
    
    assert task_card._card is None
    card2 = task_card.build()
    assert card1 is not card2


def test_task_card_class_update_task(mock_page):
    """Test actualizar tarea en TaskCard"""
    task1 = Task(id="task_1", title="Tarea 1", user_id="user_1")
    task_card = TaskCard(task=task1, page=mock_page)
    
    card1 = task_card.build()
    
    # Actualizar tarea
    task2 = Task(id="task_2", title="Tarea 2", user_id="user_1")
    task_card.update_task(task2)
    
    assert task_card.task == task2
    assert task_card._card is None
    
    card2 = task_card.build()
    assert card1 is not card2


def test_task_card_class_with_callbacks(mock_page):
    """Test TaskCard con callbacks"""
    task = Task(id="task_1", title="Tarea", user_id="user_1")
    task.subtasks = []
    
    def handle_edit(task_id):
        pass
    
    def handle_delete(task_id):
        pass
    
    task_card = TaskCard(
        task=task,
        page=mock_page,
        on_edit=handle_edit,
        on_delete=handle_delete
    )
    
    card = task_card.build()
    assert isinstance(card, ft.Container)


def test_task_card_class_with_all_options(mock_page):
    """Test TaskCard con todas las opciones"""
    task = Task(
        id="task_1",
        title="Tarea completa",
        description="Descripción",
        user_id="user_1",
        tags=["tag1", "tag2"]
    )
    subtask = Subtask(id="sub_1", task_id="task_1", title="Subtarea")
    task.subtasks = [subtask]
    
    task_card = TaskCard(
        task=task,
        page=mock_page,
        show_subtasks=True,
        show_tags=True,
        show_progress=True,
        compact=False,
        subtasks_expanded=True
    )
    
    card = task_card.build()
    assert isinstance(card, ft.Container)
    assert len(card.content.controls) >= 3


# ============================================================================
# DEMO UI - Ejecutar con: python test/ui/task/components/cards/test_task_card.py
# ============================================================================

def main(page: ft.Page):
    page.title = "Task Card - Demo"
    page.window.width = 800
    page.window.height = 1200
    page.padding = 0
    page.theme_mode = ft.ThemeMode.DARK
    
    # 1. Tarea simple sin subtareas
    simple_task = Task(
        id="t1",
        title="Tarea Simple",
        description="Una tarea sencilla sin subtareas",
        user_id="user_demo"
    )
    simple_task.subtasks = []
    
    # 2. Tarea con subtareas (50% completadas)
    task_with_sub = Task(
        id="t2",
        title="Tarea con Subtareas (50%)",
        description="Esta tarea tiene varias subtareas",
        user_id="user_demo",
        tags=["trabajo", "urgente"]
    )
    sub1 = Subtask(id="s1", task_id="t2", title="Subtarea 1", completed=True)
    sub2 = Subtask(id="s2", task_id="t2", title="Subtarea 2", completed=False)
    sub3 = Subtask(id="s3", task_id="t2", title="Subtarea 3", completed=False)
    task_with_sub.subtasks = [sub1, sub2, sub3]
    
    # 3. Tarea con todas subtareas completadas (100%)
    task_all_completed = Task(
        id="t3",
        title="Tarea 100% Completada",
        description="Todas las subtareas están completadas",
        user_id="user_demo",
        tags=["finalizado"]
    )
    sub_c1 = Subtask(id="sc1", task_id="t3", title="Subtarea 1", completed=True)
    sub_c2 = Subtask(id="sc2", task_id="t3", title="Subtarea 2", completed=True)
    task_all_completed.subtasks = [sub_c1, sub_c2]
    
    # 4. Tarea sin subtareas completadas (0%)
    task_no_completed = Task(
        id="t4",
        title="Tarea Sin Avance",
        description="Ninguna subtarea está completada",
        user_id="user_demo",
        tags=["pendiente"]
    )
    sub_nc1 = Subtask(id="snc1", task_id="t4", title="Subtarea 1", completed=False)
    sub_nc2 = Subtask(id="snc2", task_id="t4", title="Subtarea 2", completed=False)
    task_no_completed.subtasks = [sub_nc1, sub_nc2]
    
    # 5. Tarea con vencimiento futuro
    future_date = (date.today() + timedelta(days=7))
    task_future = Task(
        id="t5",
        title="Tarea Vence en 7 Días",
        description="Vencimiento futuro",
        user_id="user_demo",
        due_date=future_date
    )
    task_future.subtasks = []
    
    # 6. Tarea vencida hace poco
    overdue_date = (date.today() - timedelta(days=2))
    task_overdue = Task(
        id="t6",
        title="Tarea Vencida",
        description="Venció hace 2 días",
        user_id="user_demo",
        due_date=overdue_date,
        tags=["urgente", "atrasada"]
    )
    task_overdue.subtasks = []
    
    # 7. Tarea vencida hoy
    task_due_today = Task(
        id="t7",
        title="Tarea Vence Hoy",
        description="El vencimiento es hoy",
        user_id="user_demo",
        due_date=date.today()
    )
    task_due_today.subtasks = []
    
    # 8. Tarea con muchos tags
    task_many_tags = Task(
        id="t8",
        title="Tarea con Muchos Tags",
        description="Demuestra más de 5 tags (solo se muestran 5)",
        user_id="user_demo",
        tags=["tag1", "tag2", "tag3", "tag4", "tag5", "tag6", "tag7", "tag8"]
    )
    task_many_tags.subtasks = []
    
    # 9. Tarea completada (sin subtareas)
    task_completed = Task(
        id="t9",
        title="Tarea Completada",
        description="Esta tarea ya está completada",
        user_id="user_demo",
        status=TASK_STATUS_COMPLETED
    )
    task_completed.subtasks = []
    
    # Variables para manejar estado de la demo
    status_text = ft.Text("", size=12, color=ft.Colors.BLUE_400)
    
    # Callbacks para las acciones
    def on_edit(task_id):
        status_text.value = f"✏️ Editando tarea: {task_id}"
        page.update()
    
    def on_delete(task_id):
        status_text.value = f"🗑️ Eliminando tarea: {task_id}"
        page.update()
    
    def on_toggle_status(task_id):
        status_text.value = f"✓ Alternando estado de: {task_id}"
        page.update()
    
    # Construir tarjetas con callbacks
    cards = [
        ("Tarea Simple (3 botones)", TaskCard(
            task=simple_task, page=page,
            on_edit=on_edit, on_delete=on_delete, on_toggle_status=on_toggle_status
        )),
        ("Tarea con Subtareas 50% (2 botones)", TaskCard(
            task=task_with_sub, page=page, subtasks_expanded=True,
            on_edit=on_edit, on_delete=on_delete, on_toggle_status=on_toggle_status
        )),
        ("Tarea 100% Completada (2 botones)", TaskCard(
            task=task_all_completed, page=page, subtasks_expanded=True,
            on_edit=on_edit, on_delete=on_delete, on_toggle_status=on_toggle_status
        )),
        ("Tarea Sin Avance 0% (2 botones)", TaskCard(
            task=task_no_completed, page=page, subtasks_expanded=True,
            on_edit=on_edit, on_delete=on_delete, on_toggle_status=on_toggle_status
        )),
        ("Tarea Vence en 7 Días (3 botones)", TaskCard(
            task=task_future, page=page,
            on_edit=on_edit, on_delete=on_delete, on_toggle_status=on_toggle_status
        )),
        ("Tarea Vencida (3 botones)", TaskCard(
            task=task_overdue, page=page,
            on_edit=on_edit, on_delete=on_delete, on_toggle_status=on_toggle_status
        )),
        ("Tarea Vence Hoy (3 botones)", TaskCard(
            task=task_due_today, page=page,
            on_edit=on_edit, on_delete=on_delete, on_toggle_status=on_toggle_status
        )),
        ("Tarea con Muchos Tags (3 botones)", TaskCard(
            task=task_many_tags, page=page,
            on_edit=on_edit, on_delete=on_delete, on_toggle_status=on_toggle_status
        )),
        ("Tarea Completada (3 botones)", TaskCard(
            task=task_completed, page=page,
            on_edit=on_edit, on_delete=on_delete, on_toggle_status=on_toggle_status
        )),
    ]
    
    # Construir lista de controles
    controls: list[ft.Control] = [
        ft.Container(
            content=ft.Text("Task Card - Demo UI (Orquestador Final)", size=20, weight=ft.FontWeight.BOLD),
            padding=20,
        ),
        ft.Container(
            content=ft.Text("9 casos de uso diferentes - Prueba los botones de acción", size=14, color=ft.Colors.WHITE_70),
            padding=ft.Padding(left=20, right=20, top=0, bottom=10),
        ),
        ft.Container(
            content=ft.Column(controls=[
                ft.Text("Estado:", size=12, color=ft.Colors.WHITE_70),
                status_text,
            ]),
            padding=ft.Padding(left=20, right=20, top=0, bottom=20),
            bgcolor=ft.Colors.GREY_900,
            border_radius=8,
        ),
    ]
    
    for title, card in cards:
        controls.extend([
            ft.Container(
                content=ft.Divider(),
                padding=ft.Padding(left=20, right=20, top=0, bottom=0),
            ),
            ft.Container(
                content=ft.Text(title, size=16, weight=ft.FontWeight.BOLD),
                padding=ft.Padding(left=20, right=20, top=10, bottom=10),
            ),
            ft.Container(
                content=card.build(),
                padding=20,
            ),
        ])
    
    # Usar ListView en lugar de Column con scroll para mejor funcionamiento
    page.add(
        ft.ListView(
            controls=controls,
            spacing=0,
            expand=True,
        )
    )
    page.update()


from datetime import date

if __name__ == "__main__":
    ft.run(main)
