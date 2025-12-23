"""
Módulo para la gestión de subtareas.
"""
import flet as ft
from datetime import datetime
from app.services.task_service import TaskService


def toggle_subtask(task_service: TaskService, subtask_id: int):
    """Cambia el estado de completado de una subtarea."""
    task_service.toggle_subtask_complete(subtask_id)


def delete_subtask(task_service: TaskService, subtask_id: int):
    """Elimina una subtarea."""
    task_service.delete_subtask(subtask_id)


def save_subtask(
    page: ft.Page,
    task_service: TaskService,
    is_editing: bool,
    editing_subtask,
    editing_subtask_task_id: int,
    title: str,
    description: str,
    deadline_str: str
) -> bool:
    """
    Guarda una subtarea (crear o actualizar).
    
    Args:
        page: Página de Flet.
        task_service: Servicio para gestionar tareas.
        is_editing: Si es edición o creación.
        editing_subtask: Subtarea a editar (si es edición).
        editing_subtask_task_id: ID de la tarea padre.
        title: Título de la subtarea.
        description: Descripción de la subtarea.
        deadline_str: Fecha límite como string.
    
    Returns:
        True si se guardó correctamente, False en caso contrario.
    """
    if not title or not title.strip():
        return False
    
    # Validar y parsear fecha límite
    deadline = None
    if deadline_str.strip():
        try:
            # Intentar parsear diferentes formatos
            formats = [
                "%Y-%m-%d %H:%M",
                "%Y-%m-%d",
                "%d/%m/%Y %H:%M",
                "%d/%m/%Y"
            ]
            parsed = False
            for fmt in formats:
                try:
                    deadline = datetime.strptime(deadline_str.strip(), fmt)
                    parsed = True
                    break
                except ValueError:
                    continue
            
            if not parsed:
                page.snack_bar = ft.SnackBar(
                    content=ft.Text("Formato de fecha inválido. Use YYYY-MM-DD HH:MM"),
                    bgcolor=ft.Colors.RED
                )
                page.snack_bar.open = True
                page.update()
                return False
        except Exception as ex:
            page.snack_bar = ft.SnackBar(
                content=ft.Text(f"Error al parsear fecha: {str(ex)}"),
                bgcolor=ft.Colors.RED
            )
            page.snack_bar.open = True
            page.update()
            return False
    
    try:
        if is_editing:
            # Actualizar subtarea existente
            editing_subtask.title = title.strip()
            editing_subtask.description = description.strip()
            editing_subtask.deadline = deadline
            task_service.update_subtask(editing_subtask)
        else:
            # Crear nueva subtarea
            if editing_subtask_task_id:
                task_service.create_subtask(
                    editing_subtask_task_id,
                    title.strip(),
                    description.strip(),
                    deadline
                )
            else:
                page.snack_bar = ft.SnackBar(
                    content=ft.Text("Error: No se encontró la tarea padre"),
                    bgcolor=ft.Colors.RED
                )
                page.snack_bar.open = True
                page.update()
                return False
        
        return True
    except Exception as ex:
        page.snack_bar = ft.SnackBar(
            content=ft.Text(f"Error: {str(ex)}"),
            bgcolor=ft.Colors.RED
        )
        page.snack_bar.open = True
        page.update()
        return False

