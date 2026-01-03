"""
Tests para el componente TaskForm
"""

import sys
import os
from pathlib import Path

# Agregar el directorio raíz al PYTHONPATH
root_dir = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(root_dir))

import pytest
import flet as ft
from datetime import datetime, date, timedelta
from app.ui.task.task_form import TaskForm
from app.models.task import Task
from app.models.subtask import Subtask
from app.utils.task_helper import (
    TASK_STATUS_PENDING,
    TASK_STATUS_IN_PROGRESS,
    TASK_STATUS_COMPLETED,
)


class TestTaskForm:
    """Tests para el formulario de tareas"""
    
    def test_form_initialization_create_mode(self, page: ft.Page):
        """Test: inicialización del formulario en modo crear"""
        form = TaskForm(page=page)
        
        assert form.page == page
        assert form.task is None
        assert form.is_edit_mode is False
        assert form.on_save is None
        assert form.on_cancel is None
        assert len(form.subtasks) == 0
        assert form.selected_date is None
    
    def test_form_initialization_edit_mode(self, page: ft.Page, sample_task: Task):
        """Test: inicialización del formulario en modo editar"""
        form = TaskForm(page=page, task=sample_task)
        
        assert form.page == page
        assert form.task == sample_task
        assert form.is_edit_mode is True
        assert form.selected_date == sample_task.due_date
        assert len(form.subtasks) == len(sample_task.subtasks)
    
    def test_form_build_creates_all_controls(self, page: ft.Page):
        """Test: build() crea todos los controles necesarios"""
        form = TaskForm(page=page)
        container = form.build()
        
        assert isinstance(container, ft.Container)
        assert form.title_field is not None
        assert form.description_field is not None
        assert form.status_dropdown is not None
        assert form.urgent_checkbox is not None
        assert form.important_checkbox is not None
        assert form.due_date_picker is not None
        assert form.due_date_text is not None
        assert form.tags_field is not None
        assert form.notes_field is not None
        assert form.subtasks_column is not None
        assert form.error_text is not None

    def test_form_is_scrollable(self, page: ft.Page):
        """Test: el formulario debe ser desplazable para poder navegar en pantallas pequeñas"""
        form = TaskForm(page=page)
        container = form.build()

        # El contenedor debe poder expandir para usar todo el espacio disponible
        assert isinstance(container, ft.Container)
        assert getattr(container, 'expand', False) is True

        # El contenido debe ser una Column desplazable y expandible
        content = container.content
        assert isinstance(content, ft.Column)
        assert getattr(content, 'scroll', None) == ft.ScrollMode.AUTO
        assert getattr(content, 'expand', False) is True

    def test_textfields_do_not_expand(self, page: ft.Page):
        """Test: los TextField no deben usar expand en vertical para no bloquear el scroll"""
        form = TaskForm(page=page)
        form.build()

        assert form.title_field is not None
        assert form.description_field is not None
        # Expand no debe ser True (puede ser False o None según la implementación)
        assert getattr(form.title_field, 'expand', None) is not True
        assert getattr(form.description_field, 'expand', None) is not True
    
    def test_form_loads_task_data_in_edit_mode(self, page: ft.Page, sample_task: Task):
        """Test: el formulario carga datos de la tarea en modo editar"""
        form = TaskForm(page=page, task=sample_task)
        form.build()
        
        assert form.title_field is not None
        assert form.description_field is not None
        assert form.status_dropdown is not None
        assert form.urgent_checkbox is not None
        assert form.important_checkbox is not None
        assert form.tags_field is not None
        
        assert form.title_field.value == sample_task.title
        assert form.description_field.value == sample_task.description
        assert form.status_dropdown.value == sample_task.status
        assert form.urgent_checkbox.value == sample_task.urgent
        assert form.important_checkbox.value == sample_task.important
        
        if sample_task.tags:
            expected_tags = ", ".join(sample_task.tags)
            assert form.tags_field.value == expected_tags
    
    def test_validate_empty_title_shows_error(self, page: ft.Page):
        """Test: validación falla con título vacío"""
        form = TaskForm(page=page)
        form.build()
        
        assert form.title_field is not None
        assert form.error_text is not None
        
        form.title_field.value = ""
        result = form._validate_and_save()
        
        assert result is False
        assert form.error_text.visible is True
        assert "título es obligatorio" in form.error_text.value.lower()
    
    def test_validate_title_too_long_shows_error(self, page: ft.Page):
        """Test: validación falla con título demasiado largo"""
        form = TaskForm(page=page)
        form.build()
        
        assert form.title_field is not None
        assert form.error_text is not None
        
        form.title_field.value = "x" * 101
        result = form._validate_and_save()
        
        assert result is False
        assert form.error_text.visible is True
        assert "100 caracteres" in form.error_text.value
    
    def test_validate_description_too_long_shows_error(self, page: ft.Page):
        """Test: validación falla con descripción demasiado larga"""
        form = TaskForm(page=page)
        form.build()
        
        assert form.title_field is not None
        assert form.description_field is not None
        assert form.error_text is not None
        
        form.title_field.value = "Tarea válida"
        form.description_field.value = "x" * 501
        result = form._validate_and_save()
        
        assert result is False
        assert form.error_text.visible is True
        assert "500 caracteres" in form.error_text.value
    
    def test_validate_too_many_tags_shows_error(self, page: ft.Page):
        """Test: validación falla con más de 10 tags"""
        form = TaskForm(page=page)
        form.build()
        
        assert form.title_field is not None
        assert form.tags_field is not None
        assert form.error_text is not None
        
        form.title_field.value = "Tarea válida"
        form.tags_field.value = ", ".join([f"tag{i}" for i in range(11)])
        result = form._validate_and_save()
        
        assert result is False
        assert form.error_text.visible is True
        assert "10 etiquetas" in form.error_text.value.lower()
    
    def test_validate_success_with_valid_data(self, page: ft.Page):
        """Test: validación exitosa con datos válidos"""
        form = TaskForm(page=page)
        form.build()
        
        assert form.title_field is not None
        assert form.description_field is not None
        assert form.error_text is not None
        
        form.title_field.value = "Tarea válida"
        form.description_field.value = "Descripción válida"
        result = form._validate_and_save()
        
        assert result is True
        assert form.error_text.visible is False
    
    def test_build_task_creates_new_task(self, page: ft.Page):
        """Test: _build_task() crea una nueva tarea"""
        form = TaskForm(page=page)
        form.build()
        
        assert form.title_field is not None
        assert form.description_field is not None
        assert form.status_dropdown is not None
        assert form.urgent_checkbox is not None
        assert form.important_checkbox is not None
        assert form.tags_field is not None
        assert form.notes_field is not None
        
        form.title_field.value = "Nueva Tarea"
        form.description_field.value = "Descripción de prueba"
        form.status_dropdown.value = TASK_STATUS_PENDING
        form.urgent_checkbox.value = True
        form.important_checkbox.value = False
        form.tags_field.value = "python, testing"
        form.notes_field.value = "Notas de prueba"
        
        task = form._build_task()
        
        assert isinstance(task, Task)
        assert task.title == "Nueva Tarea"
        assert task.description == "Descripción de prueba"
        assert task.status == TASK_STATUS_PENDING
        assert task.urgent is True
        assert task.important is False
        assert "python" in task.tags
        assert "testing" in task.tags
        assert task.notes == "Notas de prueba"
        assert task.created_at is not None
        assert task.updated_at is not None
    
    def test_build_task_updates_existing_task(self, page: ft.Page, sample_task: Task):
        """Test: _build_task() actualiza una tarea existente"""
        original_created_at = sample_task.created_at
        form = TaskForm(page=page, task=sample_task)
        form.build()
        
        assert form.title_field is not None
        assert form.description_field is not None
        assert form.status_dropdown is not None
        assert form.urgent_checkbox is not None
        assert form.important_checkbox is not None
        
        form.title_field.value = "Título actualizado"
        form.description_field.value = "Descripción actualizada"
        form.status_dropdown.value = TASK_STATUS_COMPLETED
        form.urgent_checkbox.value = False
        form.important_checkbox.value = True
        
        task = form._build_task()
        
        assert task == sample_task  # Es la misma instancia
        assert task.title == "Título actualizado"
        assert task.description == "Descripción actualizada"
        assert task.status == TASK_STATUS_COMPLETED
        assert task.urgent is False
        assert task.important is True
        assert task.created_at == original_created_at  # No cambió
        assert task.updated_at > original_created_at  # Se actualizó
    
    def test_build_task_parses_tags_correctly(self, page: ft.Page):
        """Test: _build_task() parsea tags correctamente"""
        form = TaskForm(page=page)
        form.build()
        
        assert form.title_field is not None
        assert form.tags_field is not None

        form.title_field.value = "Tarea"
        form.tags_field.value = "python, backend, api, testing"
        
        task = form._build_task()
        
        assert len(task.tags) == 4
        assert "python" in task.tags
        assert "backend" in task.tags
        assert "api" in task.tags
        assert "testing" in task.tags
    
    def test_build_task_handles_empty_tags(self, page: ft.Page):
        """Test: _build_task() maneja tags vacíos"""
        form = TaskForm(page=page)
        form.build()
        
        assert form.title_field is not None
        assert form.tags_field is not None
        
        form.title_field.value = "Tarea"
        form.tags_field.value = ""
        
        task = form._build_task()
        
        assert task.tags == []
    
    def test_build_task_includes_subtasks(self, page: ft.Page):
        """Test: _build_task() incluye subtareas"""
        form = TaskForm(page=page)
        form.build()
        
        assert form.title_field is not None
        
        form.title_field.value = "Tarea con subtareas"
        form.subtasks = [
            Subtask(id="1", task_id="", title="Subtarea 1", completed=False),
            Subtask(id="2", task_id="", title="Subtarea 2", completed=True),
        ]
        
        task = form._build_task()
        
        assert len(task.subtasks) == 2
        assert task.subtasks[0].title == "Subtarea 1"
        assert task.subtasks[0].completed is False
        assert task.subtasks[1].title == "Subtarea 2"
        assert task.subtasks[1].completed is True
    
    def test_render_subtasks_shows_empty_message(self, page: ft.Page):
        """Test: _render_subtasks() muestra mensaje cuando no hay subtareas"""
        form = TaskForm(page=page)
        form.build()
        
        form.subtasks = []
        form._render_subtasks()
        
        assert form.subtasks_column is not None
        assert len(form.subtasks_column.controls) == 1
        assert isinstance(form.subtasks_column.controls[0], ft.Text)
        assert "No hay subtareas" in form.subtasks_column.controls[0].value
    
    def test_render_subtasks_displays_all_subtasks(self, page: ft.Page):
        """Test: _render_subtasks() muestra todas las subtareas"""
        form = TaskForm(page=page)
        form.build()
        
        assert form.subtasks_column is not None
        
        form.subtasks = [
            Subtask(id="1", task_id="", title="Subtarea 1", completed=False),
            Subtask(id="2", task_id="", title="Subtarea 2", completed=True),
            Subtask(id="3", task_id="", title="Subtarea 3", completed=False),
        ]
        form._render_subtasks()
        
        assert len(form.subtasks_column.controls) == 3
    
    def test_delete_subtask_removes_subtask(self, page: ft.Page):
        """Test: _delete_subtask() elimina una subtarea"""
        form = TaskForm(page=page)
        form.build()
        
        form.subtasks = [
            Subtask(id="1", task_id="", title="Subtarea 1", completed=False),
            Subtask(id="2", task_id="", title="Subtarea 2", completed=False),
            Subtask(id="3", task_id="", title="Subtarea 3", completed=False),
        ]
        
        form._delete_subtask(1)
        
        assert len(form.subtasks) == 2
        assert form.subtasks[0].title == "Subtarea 1"
        assert form.subtasks[1].title == "Subtarea 3"
    
    def test_delete_subtask_ignores_invalid_index(self, page: ft.Page):
        """Test: _delete_subtask() ignora índices inválidos"""
        form = TaskForm(page=page)
        form.build()
        
        form.subtasks = [
            Subtask(id="1", task_id="", title="Subtarea 1", completed=False),
        ]
        
        form._delete_subtask(10)
        
        assert len(form.subtasks) == 1
    
    def test_toggle_subtask_changes_completed_state(self, page: ft.Page):
        """Test: _toggle_subtask() cambia el estado completado"""
        form = TaskForm(page=page)
        form.build()
        
        form.subtasks = [
            Subtask(id="1", task_id="", title="Subtarea 1", completed=False),
        ]
        
        form._toggle_subtask(0, True)
        
        assert form.subtasks[0].completed is True
        
        form._toggle_subtask(0, False)
        
        assert form.subtasks[0].completed is False
    
    def test_callbacks_are_called(self, page: ft.Page):
        """Test: callbacks on_save y on_cancel se ejecutan"""
        save_called = False
        cancel_called = False
        saved_task = None
        
        def on_save(task):
            nonlocal save_called, saved_task
            save_called = True
            saved_task = task
        
        def on_cancel():
            nonlocal cancel_called
            cancel_called = True
        
        form = TaskForm(page=page, on_save=on_save, on_cancel=on_cancel)
        form.build()
        
        assert form.title_field is not None
        
        # Simular guardado
        form.title_field.value = "Tarea de prueba"
        if form._validate_and_save():
            task = form._build_task()
            if form.on_save:
                form.on_save(task)
        
        assert save_called is True
        assert saved_task is not None
        assert saved_task.title == "Tarea de prueba"
        
        # Simular cancelación
        if form.on_cancel:
            form.on_cancel()
        
        assert cancel_called is True
    
    def test_due_date_is_included_in_task(self, page: ft.Page):
        """Test: fecha de vencimiento se incluye en la tarea"""
        form = TaskForm(page=page)
        form.build()
        
        assert form.title_field is not None
        
        form.title_field.value = "Tarea con fecha"
        test_date = date.today() + timedelta(days=7)
        form.selected_date = test_date
        
        task = form._build_task()
        
        assert task.due_date == test_date
    
    def test_theme_colors_applied(self, page: ft.Page):
        """Test: colores del tema oscuro con rojo se aplican"""
        form = TaskForm(page=page)
        container = form.build()
        assert form.title_field is not None
        assert form.description_field is not None
        assert form.status_dropdown is not None
        assert form.urgent_checkbox is not None
        assert form.important_checkbox is not None
        
        # Verificar colores del contenedor
        assert container.bgcolor == ft.Colors.GREY_900
        assert container.border is not None
        
        # Verificar colores de los campos
        assert form.title_field.border_color == ft.Colors.RED_700
        assert form.title_field.focused_border_color == ft.Colors.RED_400
        assert form.description_field.border_color == ft.Colors.RED_700
        assert form.status_dropdown.border_color == ft.Colors.RED_700
        
        # Verificar colores de checkboxes
        assert form.urgent_checkbox.fill_color == ft.Colors.RED_700
        assert form.important_checkbox.fill_color == ft.Colors.RED_700


# Fixtures
@pytest.fixture
def page():
    """Fixture: página de Flet para tests"""
    from unittest.mock import Mock
    test_page = Mock(spec=ft.Page)
    test_page.theme_mode = ft.ThemeMode.DARK
    test_page.overlay = []
    test_page.controls = []
    return test_page


@pytest.fixture
def sample_task():
    """Fixture: tarea de ejemplo para tests"""
    return Task(
        id="task_1",
        title="Tarea de ejemplo",
        description="Descripción de ejemplo",
        status=TASK_STATUS_PENDING,
        urgent=True,
        important=False,
        due_date=date.today() + timedelta(days=3),
        tags=["python", "testing"],
        notes="Notas de ejemplo",
        subtasks=[
            Subtask(id="sub_1", task_id="task_1", title="Subtarea 1", completed=False),
            Subtask(id="sub_2", task_id="task_1", title="Subtarea 2", completed=True),
        ],
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )


# UI Demo para pruebas manuales
def main(page: ft.Page):
    """Demo UI para TaskForm con tema oscuro"""
    page.title = "TaskForm Demo"
    page.theme_mode = ft.ThemeMode.DARK
    page.theme = ft.Theme(color_scheme_seed=ft.Colors.RED_900)
    page.dark_theme = ft.Theme(
        color_scheme=ft.ColorScheme(
            primary=ft.Colors.RED_700,
            on_primary=ft.Colors.WHITE,
            secondary=ft.Colors.RED_900,
            surface=ft.Colors.GREY_800,
            on_surface=ft.Colors.WHITE,
        )
    )
    page.bgcolor = ft.Colors.GREY_900
    page.padding = 20
    
    def show_snackbar(message: str, color: str = ft.Colors.GREEN_400):
        """Muestra mensaje de confirmación"""
        snackbar = ft.SnackBar(
            content=ft.Text(message, color=ft.Colors.WHITE),
            bgcolor=color,
        )
        page.overlay.append(snackbar)
        snackbar.open = True
        page.update()
    
    def handle_save(task: Task):
        """Handler para guardar tarea"""
        print(f"Tarea guardada: {task.title}")
        print(f"  - Descripción: {task.description}")
        print(f"  - Estado: {task.status}")
        print(f"  - Urgente: {task.urgent}")
        print(f"  - Importante: {task.important}")
        print(f"  - Fecha: {task.due_date}")
        print(f"  - Tags: {task.tags}")
        print(f"  - Notas: {task.notes}")
        print(f"  - Subtareas: {len(task.subtasks)}")
        
        show_snackbar(f"✅ Tarea '{task.title}' guardada correctamente")
    
    def handle_cancel():
        """Handler para cancelar"""
        print("Formulario cancelado")
        show_snackbar("❌ Formulario cancelado", ft.Colors.ORANGE_400)
    
    # Tarea de ejemplo para modo editar
    sample_task = Task(
        id="task_1",
        title="Implementar autenticación",
        description="Agregar sistema de login con JWT",
        status=TASK_STATUS_IN_PROGRESS,
        urgent=True,
        important=True,
        due_date=date.today() + timedelta(days=5),
        tags=["backend", "security", "api"],
        notes="Revisar documentación de JWT",
        subtasks=[
            Subtask(id="1", task_id="task_1", title="Instalar librerías", completed=True),
            Subtask(id="2", task_id="task_1", title="Crear endpoints", completed=False),
            Subtask(id="3", task_id="task_1", title="Agregar tests", completed=False),
        ],
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    
    def switch_mode(e):
        """Cambia entre modo crear y editar"""
        page.controls.clear()
        
        if e.control.data == "create":
            page.add(
                ft.Column(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.FilledButton(
                                    "Modo Crear",
                                    icon=ft.Icons.ADD,
                                    data="create",
                                    on_click=switch_mode,
                                    style=ft.ButtonStyle(bgcolor=ft.Colors.RED_700),
                                ),
                                ft.OutlinedButton(
                                    "Modo Editar",
                                    icon=ft.Icons.EDIT,
                                    data="edit",
                                    on_click=switch_mode,
                                    style=ft.ButtonStyle(
                                        side=ft.BorderSide(2, ft.Colors.RED_700),
                                        color=ft.Colors.RED_700,
                                    ),
                                ),
                            ],
                            spacing=10,
                        ),
                        TaskForm(
                            page=page,
                            on_save=handle_save,
                            on_cancel=handle_cancel,
                        ).build(),
                    ],
                    spacing=20,
                    scroll=ft.ScrollMode.AUTO,
                )
            )
        else:
            page.add(
                ft.Column(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.OutlinedButton(
                                    "Modo Crear",
                                    icon=ft.Icons.ADD,
                                    data="create",
                                    on_click=switch_mode,
                                    style=ft.ButtonStyle(
                                        side=ft.BorderSide(2, ft.Colors.RED_700),
                                        color=ft.Colors.RED_700,
                                    ),
                                ),
                                ft.FilledButton(
                                    "Modo Editar",
                                    icon=ft.Icons.EDIT,
                                    data="edit",
                                    on_click=switch_mode,
                                    style=ft.ButtonStyle(bgcolor=ft.Colors.RED_700),
                                ),
                            ],
                            spacing=10,
                        ),
                        TaskForm(
                            page=page,
                            task=sample_task,
                            on_save=handle_save,
                            on_cancel=handle_cancel,
                        ).build(),
                    ],
                    spacing=20,
                    scroll=ft.ScrollMode.AUTO,
                )
            )
        
        page.update()
    
    # Iniciar en modo crear
    page.add(
        ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.FilledButton(
                            "Modo Crear",
                            icon=ft.Icons.ADD,
                            data="create",
                            on_click=switch_mode,
                            style=ft.ButtonStyle(bgcolor=ft.Colors.RED_700),
                        ),
                        ft.OutlinedButton(
                            "Modo Editar",
                            icon=ft.Icons.EDIT,
                            data="edit",
                            on_click=switch_mode,
                            style=ft.ButtonStyle(
                                side=ft.BorderSide(2, ft.Colors.RED_700),
                                color=ft.Colors.RED_700,
                            ),
                        ),
                    ],
                    spacing=10,
                ),
                TaskForm(
                    page=page,
                    on_save=handle_save,
                    on_cancel=handle_cancel,
                ).build(),
            ],
            spacing=20,
            scroll=ft.ScrollMode.AUTO,
        )
    )


if __name__ == "__main__":
    ft.run(main)
