"""
Componente modular para renderizar una tarjeta de tarea con botones de editar y eliminar.
"""

from __future__ import annotations

from typing import Callable, TYPE_CHECKING

import flet as ft
from app.logic.system_points import POINTS_BY_ACTION

if TYPE_CHECKING:
    from app.models.task import Task


class TaskCardView:
    """Componente para renderizar una tarjeta de tarea individual."""

    def __init__(self, on_edit: Callable, on_delete: Callable, on_task_updated: Callable = None, progress_service=None, rewards_view=None, page=None):
        """
        Inicializa el componente de tarjeta de tarea.

        Args:
            on_edit: Callback que se ejecuta al hacer clic en editar
            on_delete: Callback que se ejecuta al hacer clic en eliminar
            on_task_updated: Callback cuando la tarea se actualiza (opcional)
            progress_service: Servicio de progreso para sumar puntos (opcional)
            rewards_view: Vista de recompensas para actualizar (opcional)
            page: Referencia a la página de Flet (opcional)
        """
        self.on_edit = on_edit
        self.on_delete = on_delete
        self.on_task_updated = on_task_updated
        self.progress_service = progress_service
        self.rewards_view = rewards_view
        self.page = page
        self.expanded_tasks = set()  # Almacenar IDs de tareas expandidas
        self.subtasks_containers = {}  # Almacenar referencias a los containers de subtareas
        self.processed_transitions = {}  # Rastrear cambios de estado (incomp->comp) con timestamp
        self.task_card_refs = {}  # Almacenar referencias a las tarjetas de tareas para reconstruirlas

    def build(self, task: Task) -> ft.Card:
        """
        Construye y retorna la tarjeta de tarea.

        Args:
            task: Objeto SimpleTask con los datos de la tarea

        Returns:
            Card de Flet con la tarjeta renderizada
        """
        # Control para mostrar/ocultar subtareas
        subtasks_container = self._build_subtasks_container(task)

        # Mostrar checkbox solo si NO hay subtareas
        title_row = self._build_title_row(task)

        # Badge con el estado actual
        status_badge = self._build_status_badge(task)

        # Botones pequeños alineados a la derecha
        action_buttons = ft.Row(
            controls=[
                ft.IconButton(
                    ft.Icons.EDIT,
                    tooltip="Editar",
                    icon_size=18,
                    on_click=lambda _, t=task: self.on_edit(t),
                ),
                ft.IconButton(
                    ft.Icons.DELETE,
                    tooltip="Eliminar",
                    icon_size=18,
                    icon_color=ft.Colors.RED,
                    on_click=lambda _, t=task: self.on_delete(t),
                ),
            ],
            spacing=0,
        )

        return ft.Card(
            content=ft.Container(
                padding=12,
                content=ft.Column(
                    controls=[
                        ft.Row(
                            controls=[
                                title_row,
                                self._build_points_badge(task),
                                status_badge,
                                action_buttons,
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            vertical_alignment=ft.CrossAxisAlignment.START,
                        ),
                        subtasks_container,
                    ],
                    spacing=4,
                ),
            )
        )

    def _build_title_row(self, task: Task) -> ft.Control:
        """Construye la fila del título con checkbox si no hay subtareas."""
        if task.subtasks:
            # Si hay subtareas, mostrar título y estado basado en progreso
            status_text = self._get_status_text(task)
            return ft.Column(
                controls=[
                    ft.Text(
                        task.title,
                        size=16,
                        weight=ft.FontWeight.W_600,
                    ),
                    ft.Text(
                        task.description or "Sin descripción",
                        size=12,
                        color=ft.Colors.GREY_700,
                    ),
                    ft.Text(
                        status_text,
                        size=11,
                        color=ft.Colors.BLUE_ACCENT,
                        weight=ft.FontWeight.W_500,
                    ),
                ],
                expand=True,
                spacing=4,
            )
        else:
            # Si NO hay subtareas, mostrar checkbox + título (manual)
            return ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Checkbox(
                                value=task.status == "completada",
                                on_change=lambda e: self._on_task_checkbox_changed(task, e),
                            ),
                            ft.Text(
                                task.title,
                                size=16,
                                weight=ft.FontWeight.W_600,
                                color=ft.Colors.GREY_600
                                if task.status == "completada"
                                else ft.Colors.WHITE,
                            ),
                        ],
                        spacing=6,
                    ),
                    ft.Text(
                        task.description or "Sin descripción",
                        size=12,
                        color=ft.Colors.GREY_700,
                    ),
                ],
                expand=True,
                spacing=4,
            )

    def _build_subtasks_container(self, task: Task) -> ft.Container:
        """Construye el contenedor de subtareas visible directamente."""
        if not task.subtasks:
            return ft.Container(height=0)  # Container vacío si no hay subtareas

        is_expanded = task.id in self.expanded_tasks
        
        subtasks_list = ft.Column(spacing=4, visible=is_expanded)
        
        # Guardar referencia para poder actualizarla después
        self.subtasks_containers[task.id] = subtasks_list

        for subtask in task.subtasks:
            subtasks_list.controls.append(
                ft.Container(
                    padding=ft.padding.only(left=12),
                    content=ft.Row(
                        controls=[
                            ft.Checkbox(
                                value=subtask.completed,
                                on_change=lambda e, st=subtask, t=task: self._on_subtask_checkbox_changed(st, t, e),
                            ),
                            ft.Text(
                                subtask.title,
                                size=12,
                                color=ft.Colors.GREY_600
                                if subtask.completed
                                else ft.Colors.WHITE,
                            ),
                        ],
                        spacing=6,
                    ),
                )
            )

        toggle_btn = ft.TextButton(
            "Subtareas",
            on_click=lambda _: self._toggle_subtasks(task),
            style=ft.ButtonStyle(color=ft.Colors.WHITE)
        )

        return ft.Container(
            content=ft.Column(
                controls=[
                    toggle_btn,
                    subtasks_list,
                ],
                spacing=4,
            )
        )

    def _toggle_subtasks(self, task: Task):
        """Alterna la visibilidad de las subtareas."""
        if task.id in self.expanded_tasks:
            self.expanded_tasks.remove(task.id)
        else:
            self.expanded_tasks.add(task.id)
        
        # Actualizar la visibilidad del container
        if task.id in self.subtasks_containers:
            self.subtasks_containers[task.id].visible = task.id in self.expanded_tasks
    
    def _get_status_text(self, task: Task) -> str:
        """Retorna el texto del estado de la tarea basado en subtareas."""
        if not task.subtasks:
            return ""
        
        completed_count = sum(1 for st in task.subtasks if st.completed)
        total_count = len(task.subtasks)
        
        return f"{completed_count}/{total_count} completadas - {task.status}"
    
    def _on_task_checkbox_changed(self, task: Task, e):
        """Maneja el cambio del checkbox de la tarea (sin subtareas)."""
        from app.utils.task_helper import TASK_STATUS_COMPLETED, TASK_STATUS_PENDING
        
        if e.control.value:
            task.status = TASK_STATUS_COMPLETED
        else:
            task.status = TASK_STATUS_PENDING
        
        if self.on_task_updated:
            self.on_task_updated(task)
    
    def _build_status_badge(self, task: Task) -> ft.Container:
        """Construye un badge con el estado de la tarea con color según el estado."""
        status_color = self._get_status_color(task.status)
        status_label = self._get_status_label(task.status)
        
        return ft.Container(
            content=ft.Text(
                status_label,
                size=12,
                weight=ft.FontWeight.W_600,
                color=ft.Colors.BLACK,
            ),
            bgcolor=status_color,
            padding=ft.padding.symmetric(horizontal=12, vertical=6),
            border_radius=12,
        )

    def _build_points_badge(self, task: Task) -> ft.Container:
        """Muestra cuántos puntos otorga esta tarea (tarea + subtareas)."""
        base_points = POINTS_BY_ACTION.get("task_completed", 0.0)
        subtask_points = 0.0
        if task.subtasks:
            subtask_points = len(task.subtasks) * POINTS_BY_ACTION.get("subtask_completed", 0.0)
        total_points = base_points + subtask_points

        return ft.Container(
            content=ft.Text(
                f"{total_points:.2f} pts",
                size=12,
                weight=ft.FontWeight.W_600,
                color=ft.Colors.WHITE,
            ),
            bgcolor=ft.Colors.BLUE_GREY_700,
            padding=ft.padding.symmetric(horizontal=10, vertical=6),
            border_radius=12,
            tooltip="Puntos que otorga esta tarea (incluye subtareas)",
        )
    
    def _get_status_color(self, status: str) -> str:
        """Retorna el color según el estado de la tarea."""
        if status == "pendiente":
            return ft.Colors.AMBER
        elif status == "en_progreso":
            return ft.Colors.LIGHT_BLUE
        elif status == "completada":
            return ft.Colors.LIGHT_GREEN
        else:
            return ft.Colors.GREY_400
    
    def _get_status_label(self, status: str) -> str:
        """Retorna el label a mostrar según el estado."""
        if status == "pendiente":
            return "Pendiente"
        elif status == "en_progreso":
            return "En progreso"
        elif status == "completada":
            return "Completada"
        else:
            return status
    
    def _on_subtask_checkbox_changed(self, subtask, task: Task, e):
        """Maneja el cambio del checkbox de una subtarea."""
        try:
            # El estado actual antes del toggle
            current_value = e.control.value
            model_state = subtask.completed
            
            print(f"\n{'='*70}")
            print(f"[TaskCardView] 🔔 EVENTO ON_CHANGE DISPARADO")
            print(f"  Subtarea: {subtask.title}")
            print(f"  ID Subtarea: {subtask.id}")
            print(f"  Valor Control (UI): {current_value}")
            print(f"  Estado Modelo (BD): {model_state}")
            print(f"  ¿Coinciden?: {current_value == model_state}")
            print(f"{'='*70}")
            
            # Verificar si el evento es por inicialización
            # Si el valor del control es igual al del modelo, es probablemente un evento spurious
            if current_value == model_state:
                print(f"  ⚠️  IGNORANDO - Evento espurio de inicialización detectado")
                print(f"  Razón: El valor del control ({current_value}) coincide con el estado del modelo ({model_state})")
                print(f"  Esto indica que el checkbox se está renderizando por primera vez\n")
                return
            
            # Si llegamos aquí, es un cambio real del usuario
            print(f"  ✓ Cambio real detectado - Procesando...\n")
            
            # Detectar si la subtarea está siendo completada
            was_completed = subtask.completed
            subtask.toggle_completed()
            is_now_completed = subtask.completed
            
            print(f"  📊 Transición de estado:")
            print(f"     Antes: {was_completed} → Después: {is_now_completed}")
            
            # Crear una clave única basada en el timestamp del cambio
            transition_key = f"{task.id}_{subtask.id}_{subtask.updated_at.isoformat()}"
            print(f"  🔑 Clave transición: {transition_key}")
            
            # Actualizar el estado de la tarea basado en sus subtareas
            task.update_status_from_subtasks()
            print(f"  📋 Estado de tarea padre actualizado: {task.status}")
            
            # Forzar actualización del checkbox ANTES de guardar
            e.control.value = is_now_completed
            
            # Actualizar el contenedor del checkbox
            try:
                if hasattr(e.control, 'parent'):
                    e.control.parent.update()
                    print(f"  ♻️  Contenedor padre actualizado visualmente")
            except Exception as parent_error:
                print(f"  ⚠️  No se pudo actualizar contenedor padre: {parent_error}")
            
            # Guardar cambios en la base de datos
            if self.on_task_updated:
                self.on_task_updated(task)
                print(f"  💾 Cambios guardados en la base de datos")
            
            # Si la subtarea acaba de completarse, sumar puntos (evitar duplicados con timestamp)
            if not was_completed and is_now_completed:
                print(f"  ⭐ Subtarea completada: sumando puntos...")
                # Verificar si este cambio específico ya fue procesado
                if transition_key not in self.processed_transitions:
                    print(f"    ✅ Puntos sumados por PRIMERA VEZ")
                    self.processed_transitions[transition_key] = True
                    # Ejecutar suma de puntos de forma asincrónica
                    if self.progress_service and self.page:
                        self.page.run_task(self._async_add_points_for_subtask, subtask, task)
                else:
                    print(f"    ⏭️  Puntos ya procesados para esta transición - IGNORANDO DUPLICADO")
                    print(f"    Transition key ya en registro: {list(self.processed_transitions.keys())[-1]}")
            elif was_completed and not is_now_completed:
                print(f"  ↩️  Subtarea desmarcada")
            
            # Actualizar toda la página para reflejar cambios visuales
            try:
                if self.page:
                    self.page.update()
                    print(f"  🔄 Página actualizada")
            except Exception as page_error:
                print(f"  ⚠️  Error actualizando página: {page_error}")
            
            print(f"  ✓ Evento procesado correctamente\n")
            
        except Exception as ex:
            print(f"\n[TaskCardView] ❌ ERROR EN CHECKBOX HANDLER: {ex}")
            import traceback
            traceback.print_exc()
            print()
    
    async def _async_add_points_for_subtask(self, subtask, task: Task):
        """Añade puntos al usuario por completar una subtarea."""
        try:
            print(f"[TaskCardView] Añadiendo puntos por completar subtarea: {subtask.title}")
            
            # Añadir puntos usando ProgressService con persistencia
            stats = await self.progress_service.add_points("subtask_completed")
            print(f"[TaskCardView] Stats actualizados: Puntos={stats['points']:.2f}, Nivel={stats['level']}")
            
            # Actualizar PointsAndLevelsView si está disponible
            if self.rewards_view:
                current_points = stats.get("points", 0.0)
                current_level = stats.get("level", "Nadie")
                
                print(f"[TaskCardView] Actualizando PointsAndLevelsView - Puntos: {current_points:.2f}, Nivel: {current_level}")
                self.rewards_view.set_user_points(current_points)
                self.rewards_view.set_user_level(current_level)
                self.rewards_view.update_progress_from_stats(stats)
                
                # Mostrar notificación si hubo subida de nivel
                if stats.get("level_up", False):
                    old_level = stats.get("old_level", "")
                    print(f"[TaskCardView] 🎉 ¡NIVEL SUBIDO! {old_level} → {current_level}")
            
            print(f"✓ Puntos añadidos por completar subtarea: {subtask.title}")
        except Exception as e:
            print(f"[TaskCardView] Error añadiendo puntos por subtarea: {str(e)}")
            import traceback
            traceback.print_exc()
