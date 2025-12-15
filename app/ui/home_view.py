"""
Vista principal de la aplicación de tareas.
"""
import flet as ft
from typing import Optional
from app.data.models import Task, SubTask
from app.services.task_service import TaskService
from app.ui.widgets import create_task_card, create_empty_state, create_statistics_card
from app.ui.task_form import TaskForm


class HomeView:
    """Vista principal de la aplicación."""
    
    def __init__(self, page: ft.Page):
        """
        Inicializa la vista principal.
        
        Args:
            page: Página de Flet.
        """
        self.page = page
        self.task_service = TaskService()
        self.current_filter: Optional[bool] = None
        self.editing_task: Optional[Task] = None
        self.editing_subtask_task_id: Optional[int] = None
        self.editing_subtask = None
        self.current_section = "tasks"  # "tasks" o "habits"
        
        # Contenedores principales
        self.tasks_container = ft.Column([], spacing=0, scroll=ft.ScrollMode.AUTO, expand=True)
        self.stats_card = None
        self.title_bar = None  # Guardar referencia a la barra de título
        
        self._build_ui()
        self._load_tasks()
    
    def _build_ui(self):
        """Construye la interfaz de usuario."""
        # Botón para cambiar tema
        # Determinar el icono inicial según el tema actual
        initial_icon = ft.Icons.DARK_MODE if self.page.theme_mode == ft.ThemeMode.LIGHT else ft.Icons.LIGHT_MODE
        initial_tooltip = "Cambiar a tema oscuro" if self.page.theme_mode == ft.ThemeMode.LIGHT else "Cambiar a tema claro"
        
        self.theme_button = ft.IconButton(
            icon=initial_icon,
            tooltip=initial_tooltip,
            on_click=self._toggle_theme,
            icon_color=ft.Colors.RED_400
        )
        
        # Barra de título
        self.title_bar = ft.Container(
            content=ft.Row(
                [
                    ft.Text(
                        "Mis Tareas" if self.current_section == "tasks" else "Mis Hábitos",
                        size=28,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.RED_400,
                        expand=True
                    ),
                    self.theme_button
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER
            ),
            padding=ft.padding.symmetric(vertical=16, horizontal=20),
            bgcolor=ft.Colors.BLACK87 if self.page.theme_mode == ft.ThemeMode.DARK else ft.Colors.RED_50
        )
        
        # Crear la barra inferior de navegación
        self._build_bottom_bar()
        
        # Filtros - colores adaptativos según el tema
        is_dark = self.page.theme_mode == ft.ThemeMode.DARK
        active_bg = ft.Colors.RED_700 if is_dark else ft.Colors.RED_600
        inactive_bg = ft.Colors.GREY_800 if is_dark else ft.Colors.RED_100
        text_color = ft.Colors.WHITE
        
        # Botón para agregar nueva tarea - color adaptativo
        new_task_button_bg = ft.Colors.RED_700 if is_dark else ft.Colors.RED_600
        
        # Botones de filtro
        filter_buttons = [
            ft.ElevatedButton(
                text="Todas",
                on_click=lambda e: self._filter_tasks(None),
                bgcolor=active_bg if self.current_filter is None else inactive_bg,
                color=text_color,
                height=40
            ),
            ft.ElevatedButton(
                text="Pendientes",
                on_click=lambda e: self._filter_tasks(False),
                bgcolor=active_bg if self.current_filter is False else inactive_bg,
                color=text_color,
                height=40
            ),
            ft.ElevatedButton(
                text="Completadas",
                on_click=lambda e: self._filter_tasks(True),
                bgcolor=active_bg if self.current_filter is True else inactive_bg,
                color=text_color,
                height=40
            )
        ]
        
        # Botón "+ Nueva Tarea" para la parte superior derecha
        self.new_task_button = ft.ElevatedButton(
            icon=ft.Icons.ADD,
            text="Nueva Tarea",
            on_click=self._show_new_task_form,
            bgcolor=new_task_button_bg,
            color=ft.Colors.WHITE,
            height=40,
            tooltip="Crear nueva tarea"
        )
        
        # Fila de filtros con botón de nueva tarea a la derecha
        filter_row = ft.Row(
            [
                ft.Row(
                    filter_buttons,
                    spacing=8,
                    scroll=ft.ScrollMode.AUTO,
                    expand=True
                ),
                self.new_task_button
            ],
            spacing=8,
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER
        )
        
        # Contenedor de estadísticas
        stats_container = ft.Container(
            content=create_statistics_card(self.task_service.get_statistics(), self.page),
            visible=True
        )
        self.stats_container = stats_container
        
        # Vista principal (lista de tareas)
        main_view = ft.Container(
            content=ft.Column(
                [
                    stats_container,
                    filter_row,
                    self.tasks_container
                ],
                spacing=8,
                expand=True
            ),
            padding=16,
            expand=True
        )
        
        # Guardar referencia a la vista principal
        self.home_view = ft.View(
            route="/",
            controls=[
                ft.Column(
                    [
                        self.title_bar,
                        main_view,
                        self.bottom_bar
                    ],
                    spacing=0,
                    expand=True
                )
            ],
            bgcolor=ft.Colors.BLACK if self.page.theme_mode == ft.ThemeMode.DARK else ft.Colors.GREY_50
        )
        
        # Configurar las vistas de la página
        self.page.views.clear()
        self.page.views.append(self.home_view)
        self.page.go("/")
        self.page.update()
    
    def _build_bottom_bar(self):
        """Construye la barra inferior de navegación."""
        is_dark = self.page.theme_mode == ft.ThemeMode.DARK
        bgcolor = ft.Colors.BLACK87 if is_dark else ft.Colors.WHITE
        selected_color = ft.Colors.RED_400
        unselected_color = ft.Colors.GREY_500 if is_dark else ft.Colors.GREY_600
        
        # Botón de Mis Tareas
        tasks_button = ft.Container(
            content=ft.Column(
                [
                    ft.Icon(
                        ft.Icons.TASK_ALT if self.current_section == "tasks" else ft.Icons.TASK,
                        color=selected_color if self.current_section == "tasks" else unselected_color,
                        size=24
                    ),
                    ft.Text(
                        "Mis Tareas",
                        size=12,
                        color=selected_color if self.current_section == "tasks" else unselected_color,
                        weight=ft.FontWeight.BOLD if self.current_section == "tasks" else None
                    )
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=4,
                tight=True
            ),
            on_click=lambda e: self._navigate_to_section("tasks"),
            padding=12,
            expand=True,
            border=ft.border.only(
                top=ft.BorderSide(3, selected_color if self.current_section == "tasks" else ft.Colors.TRANSPARENT)
            )
        )
        
        # Botón de Mis Hábitos
        habits_button = ft.Container(
            content=ft.Column(
                [
                    ft.Icon(
                        ft.Icons.CALENDAR_VIEW_DAY if self.current_section == "habits" else ft.Icons.CALENDAR_VIEW_WEEK,
                        color=selected_color if self.current_section == "habits" else unselected_color,
                        size=24
                    ),
                    ft.Text(
                        "Mis Hábitos",
                        size=12,
                        color=selected_color if self.current_section == "habits" else unselected_color,
                        weight=ft.FontWeight.BOLD if self.current_section == "habits" else None
                    )
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=4,
                tight=True
            ),
            on_click=lambda e: self._navigate_to_section("habits"),
            padding=12,
            expand=True,
            border=ft.border.only(
                top=ft.BorderSide(3, selected_color if self.current_section == "habits" else ft.Colors.TRANSPARENT)
            )
        )
        
        self.bottom_bar = ft.Container(
            content=ft.Row(
                [
                    tasks_button,
                    habits_button
                ],
                alignment=ft.MainAxisAlignment.SPACE_AROUND,
                spacing=0
            ),
            bgcolor=bgcolor,
            border=ft.border.only(
                top=ft.BorderSide(1, ft.Colors.GREY_800 if is_dark else ft.Colors.GREY_300)
            ),
            padding=0
        )
    
    def _navigate_to_section(self, section: str):
        """Navega a una sección específica."""
        self.current_section = section
        
        if section == "tasks":
            # Mostrar la vista de tareas
            self._build_ui()
            self._load_tasks()
        elif section == "habits":
            # Mostrar la vista de hábitos
            self._build_habits_view()
        
        # Actualizar el título
        if self.title_bar:
            title_text = self.title_bar.content.controls[0]  # El texto está en el índice 0 ahora
            if isinstance(title_text, ft.Text):
                title_text.value = "Mis Tareas" if section == "tasks" else "Mis Hábitos"
        
        # Actualizar la barra inferior
        self._build_bottom_bar()
        # Actualizar la barra en la vista
        if self.home_view and len(self.home_view.controls) > 0:
            column = self.home_view.controls[0]
            if isinstance(column, ft.Column) and len(column.controls) > 2:
                column.controls[2] = self.bottom_bar
        
        self.page.update()
    
    def _build_habits_view(self):
        """Construye la vista de hábitos."""
        is_dark = self.page.theme_mode == ft.ThemeMode.DARK
        bgcolor = ft.Colors.BLACK if is_dark else ft.Colors.GREY_50
        
        # Vista básica de hábitos (por ahora solo un placeholder)
        habits_content = ft.Container(
            content=ft.Column(
                [
                    ft.Text(
                        "Mis Hábitos",
                        size=24,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.RED_400
                    ),
                    ft.Divider(),
                    ft.Container(
                        content=ft.Column(
                            [
                                ft.Icon(
                                    ft.Icons.CALENDAR_VIEW_WEEK,
                                    size=64,
                                    color=ft.Colors.GREY_500
                                ),
                                ft.Text(
                                    "Próximamente",
                                    size=18,
                                    color=ft.Colors.GREY_500,
                                    weight=ft.FontWeight.BOLD
                                ),
                                ft.Text(
                                    "La funcionalidad de hábitos estará disponible pronto",
                                    size=14,
                                    color=ft.Colors.GREY_600,
                                    text_align=ft.TextAlign.CENTER
                                )
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=16
                        ),
                        padding=40,
                        alignment=ft.alignment.center
                    )
                ],
                spacing=16,
                expand=True
            ),
            padding=20,
            expand=True
        )
        
        # Actualizar la vista principal
        self.home_view.controls = [
            ft.Column(
                [
                    self.title_bar,
                    habits_content,
                    self.bottom_bar
                ],
                spacing=0,
                expand=True
            )
        ]
        # Sin botón de nueva tarea en hábitos por ahora (ya no hay FAB)
        self.home_view.bgcolor = bgcolor
    
    def _load_tasks(self):
        """Carga las tareas desde la base de datos."""
        tasks = self.task_service.get_all_tasks(self.current_filter)
        
        # Asegurarse de que el contenedor existe
        if not hasattr(self, 'tasks_container') or self.tasks_container is None:
            return
        
        self.tasks_container.controls.clear()
        
        if not tasks:
            self.tasks_container.controls.append(create_empty_state(self.page))
        else:
            for task in tasks:
                card = create_task_card(
                    task,
                    on_toggle=self._toggle_task,
                    on_edit=self._edit_task,
                    on_delete=self._delete_task,
                    on_toggle_subtask=self._toggle_subtask,
                    on_add_subtask=self._show_add_subtask_dialog,
                    on_delete_subtask=self._delete_subtask,
                    on_edit_subtask=self._edit_subtask,
                    page=self.page
                )
                self.tasks_container.controls.append(card)
        
        # Actualizar estadísticas
        if hasattr(self, 'stats_container') and self.stats_container:
            stats = self.task_service.get_statistics()
            self.stats_container.content = create_statistics_card(stats, self.page)
            try:
                self.stats_container.update()
            except:
                pass
        
        try:
            self.tasks_container.update()
        except:
            pass
        self.page.update()
    
    def _filter_tasks(self, filter_completed: Optional[bool]):
        """Filtra las tareas por estado."""
        self.current_filter = filter_completed
        self._load_tasks()
        self._rebuild_filters()
    
    def _rebuild_filters(self):
        """Reconstruye los botones de filtro con los colores correctos."""
        # Esta función se puede mejorar para actualizar los colores dinámicamente
        self._load_tasks()
    
    def _show_new_task_form(self, e):
        """Navega a la vista del formulario para crear una nueva tarea."""
        self.editing_task = None
        self._navigate_to_form_view()
    
    def _edit_task(self, task: Task):
        """Navega a la vista del formulario para editar una tarea."""
        self.editing_task = task
        self._navigate_to_form_view()
    
    def _navigate_to_form_view(self):
        """Navega a la vista del formulario."""
        title = "Editar Tarea" if self.editing_task else "Nueva Tarea"
        
        # Crear el formulario
        form = TaskForm(
            on_save=self._save_task,
            on_cancel=self._go_back,
            task=self.editing_task
        )
        
        # Detectar el tema actual
        is_dark = self.page.theme_mode == ft.ThemeMode.DARK
        bgcolor = ft.Colors.BLACK if is_dark else ft.Colors.GREY_50
        
        # Crear la barra de título con botón de volver
        back_button = ft.IconButton(
            icon=ft.Icons.ARROW_BACK,
            on_click=lambda e: self._go_back(),
            icon_color=ft.Colors.RED_400,
            tooltip="Volver"
        )
        
        title_bar = ft.Container(
            content=ft.Row(
                [
                    back_button,
                    ft.Text(
                        title,
                        size=24,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.RED_400,
                        expand=True
                    )
                ],
                alignment=ft.MainAxisAlignment.START,
                vertical_alignment=ft.CrossAxisAlignment.CENTER
            ),
            padding=ft.padding.symmetric(vertical=16, horizontal=20),
            bgcolor=ft.Colors.BLACK87 if is_dark else ft.Colors.RED_50
        )
        
        # Construir la vista del formulario
        form_view = ft.View(
            route="/form",
            controls=[
                title_bar,
                ft.Container(
                    content=form.build(),
                    expand=True,
                    padding=20
                )
            ],
            bgcolor=bgcolor
        )
        
        # Agregar la vista y navegar a ella
        self.page.views.append(form_view)
        self.page.go("/form")
    
    def _go_back(self):
        """Vuelve a la vista principal."""
        self.editing_task = None
        # Remover la última vista (el formulario)
        if len(self.page.views) > 1:
            self.page.views.pop()
        # Navegar a la vista principal
        if self.page.views:
            self.page.go(self.page.views[-1].route)
        else:
            self.page.go("/")
        self.page.update()
    
    def _save_task(self, *args):
        """Guarda una tarea (crear o actualizar)."""
        # Si el primer argumento es un objeto Task, es una actualización
        if args and isinstance(args[0], Task):
            # Actualizar tarea existente
            task = args[0]
            self.task_service.update_task(task)
        else:
            # Crear nueva tarea
            title, description, priority = args
            self.task_service.create_task(title, description, priority)
        
        # Volver a la vista principal
        self._go_back()
        
        # Forzar actualización de la página antes de recargar tareas
        self.page.update()
        
        # Recargar las tareas después de volver
        # El contenedor debería estar disponible ya que no se reconstruye la UI
        self._load_tasks()
    
    def _toggle_task(self, task_id: int):
        """Cambia el estado de completado de una tarea."""
        self.task_service.toggle_task_complete(task_id)
        self._load_tasks()
    
    def _delete_task(self, task_id: int):
        """Elimina una tarea."""
        if task_id is None:
            return
        
        # Eliminar directamente primero para verificar que funciona
        try:
            deleted = self.task_service.delete_task(int(task_id))
            if deleted:
                self._load_tasks()
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text("Tarea eliminada correctamente"),
                    bgcolor=ft.Colors.RED_700
                )
                self.page.snack_bar.open = True
            else:
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text("No se pudo eliminar la tarea"),
                    bgcolor=ft.Colors.RED
                )
                self.page.snack_bar.open = True
        except Exception as ex:
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"Error: {str(ex)}"),
                bgcolor=ft.Colors.RED
            )
            self.page.snack_bar.open = True
        
        self.page.update()
    
    def _toggle_theme(self, e):
        """Cambia entre tema claro y oscuro."""
        if self.page.theme_mode == ft.ThemeMode.LIGHT:
            self.page.theme_mode = ft.ThemeMode.DARK
            self.page.bgcolor = ft.Colors.BLACK
            self.theme_button.icon = ft.Icons.LIGHT_MODE
            self.theme_button.tooltip = "Cambiar a tema claro"
            # Actualizar botón de nueva tarea
            if hasattr(self, 'new_task_button') and self.new_task_button:
                self.new_task_button.bgcolor = ft.Colors.RED_700
            # Actualizar barra de título
            if self.title_bar:
                self.title_bar.bgcolor = ft.Colors.BLACK87
            # Colores para vistas
            view_bgcolor = ft.Colors.BLACK
            title_bar_bgcolor = ft.Colors.BLACK87
        else:
            self.page.theme_mode = ft.ThemeMode.LIGHT
            self.page.bgcolor = ft.Colors.GREY_50
            self.theme_button.icon = ft.Icons.DARK_MODE
            self.theme_button.tooltip = "Cambiar a tema oscuro"
            # Actualizar botón de nueva tarea
            if hasattr(self, 'new_task_button') and self.new_task_button:
                self.new_task_button.bgcolor = ft.Colors.RED_600
            # Actualizar barra de título
            if self.title_bar:
                self.title_bar.bgcolor = ft.Colors.RED_50
            # Colores para vistas
            view_bgcolor = ft.Colors.GREY_50
            title_bar_bgcolor = ft.Colors.RED_50
        
        # Reconstruir la vista principal para aplicar todos los cambios
        self._build_ui()
        
        # Actualizar todas las vistas abiertas (incluyendo el formulario si está abierto)
        for view in self.page.views:
            view.bgcolor = view_bgcolor
            # Actualizar la barra de título de cada vista si existe
            if view.controls and len(view.controls) > 0:
                first_control = view.controls[0]
                if isinstance(first_control, ft.Container):
                    first_control.bgcolor = title_bar_bgcolor
        
        # Actualizar la barra inferior con los nuevos colores
        self._build_bottom_bar()
        # Actualizar la barra en la vista
        if self.home_view and len(self.home_view.controls) > 0:
            column = self.home_view.controls[0]
            if isinstance(column, ft.Column) and len(column.controls) > 2:
                column.controls[2] = self.bottom_bar
        
        # Recargar las tareas para actualizar los colores adaptativos
        # Solo si el contenedor está en la página
        if hasattr(self, 'tasks_container') and self.tasks_container and hasattr(self.tasks_container, '_page') and self.tasks_container._page is not None:
            self._load_tasks()
        self.page.update()
    
    def _toggle_subtask(self, subtask_id: int):
        """Cambia el estado de completado de una subtarea."""
        self.task_service.toggle_subtask_complete(subtask_id)
        self._load_tasks()
    
    def _delete_subtask(self, subtask_id: int):
        """Elimina una subtarea."""
        self.task_service.delete_subtask(subtask_id)
        self._load_tasks()
    
    def _show_add_subtask_dialog(self, task_id: int):
        """Navega a la vista del formulario para agregar una subtarea."""
        # Guardar el task_id para usarlo al guardar
        self.editing_subtask_task_id = task_id
        self.editing_subtask = None
        self._navigate_to_subtask_form_view()
    
    def _edit_subtask(self, subtask):
        """Navega a la vista del formulario para editar una subtarea."""
        # Guardar la subtarea y el task_id para usarlos al guardar
        self.editing_subtask = subtask
        self.editing_subtask_task_id = subtask.task_id
        self._navigate_to_subtask_form_view()
    
    def _navigate_to_subtask_form_view(self):
        """Navega a la vista del formulario de subtarea."""
        from datetime import datetime
        
        # Determinar si es edición o creación
        is_editing = self.editing_subtask is not None
        
        # Crear campos del formulario con valores iniciales si es edición
        subtask_title_field = ft.TextField(
            label="Título de la subtarea",
            hint_text="Ingresa el título de la subtarea",
            autofocus=True,
            expand=True,
            value=self.editing_subtask.title if is_editing else ""
        )
        
        subtask_description_field = ft.TextField(
            label="Descripción",
            hint_text="Ingresa una descripción (opcional)",
            multiline=True,
            min_lines=3,
            max_lines=5,
            expand=True,
            value=self.editing_subtask.description if is_editing and self.editing_subtask.description else ""
        )
        
        # Formatear fecha límite si existe
        deadline_value = ""
        if is_editing and self.editing_subtask.deadline:
            try:
                deadline_value = self.editing_subtask.deadline.strftime("%Y-%m-%d %H:%M")
            except:
                deadline_value = ""
        
        subtask_deadline_field = ft.TextField(
            label="Fecha límite",
            hint_text="YYYY-MM-DD HH:MM (opcional)",
            expand=True,
            helper_text="Formato: 2024-12-31 23:59",
            value=deadline_value
        )
        
        # Detectar el tema actual
        is_dark = self.page.theme_mode == ft.ThemeMode.DARK
        bgcolor = ft.Colors.BLACK if is_dark else ft.Colors.GREY_50
        title_bar_bgcolor = ft.Colors.BLACK87 if is_dark else ft.Colors.RED_50
        
        def save_subtask(e):
            title = subtask_title_field.value
            description = subtask_description_field.value or ""
            deadline_str = subtask_deadline_field.value or ""
            
            if not title or not title.strip():
                subtask_title_field.error_text = "El título es obligatorio"
                subtask_title_field.update()
                return
            
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
                        subtask_deadline_field.error_text = "Formato inválido. Use YYYY-MM-DD HH:MM"
                        subtask_deadline_field.update()
                        return
                except Exception as ex:
                    subtask_deadline_field.error_text = f"Error al parsear fecha: {str(ex)}"
                    subtask_deadline_field.update()
                    return
            
            try:
                if is_editing:
                    # Actualizar subtarea existente
                    self.editing_subtask.title = title.strip()
                    self.editing_subtask.description = description.strip()
                    self.editing_subtask.deadline = deadline
                    self.task_service.update_subtask(self.editing_subtask)
                else:
                    # Crear nueva subtarea
                    task_id = getattr(self, 'editing_subtask_task_id', None)
                    if task_id:
                        self.task_service.create_subtask(
                            task_id, 
                            title.strip(), 
                            description.strip(),
                            deadline
                        )
                    else:
                        # Mostrar error en la página en lugar de actualizar el campo
                        self.page.snack_bar = ft.SnackBar(
                            content=ft.Text("Error: No se encontró la tarea padre"),
                            bgcolor=ft.Colors.RED
                        )
                        self.page.snack_bar.open = True
                        self.page.update()
                        return
                
                self._go_back()
                self._load_tasks()
            except Exception as ex:
                # Mostrar error en la página en lugar de actualizar el campo
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text(f"Error: {str(ex)}"),
                    bgcolor=ft.Colors.RED
                )
                self.page.snack_bar.open = True
                self.page.update()
        
        # Crear la barra de título con botón de volver
        back_button = ft.IconButton(
            icon=ft.Icons.ARROW_BACK,
            on_click=lambda e: self._go_back(),
            icon_color=ft.Colors.RED_400,
            tooltip="Volver"
        )
        
        title_bar = ft.Container(
            content=ft.Row(
                [
                    back_button,
                    ft.Text(
                        "Editar Subtarea" if is_editing else "Nueva Subtarea",
                        size=24,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.RED_400,
                        expand=True
                    )
                ],
                alignment=ft.MainAxisAlignment.START,
                vertical_alignment=ft.CrossAxisAlignment.CENTER
            ),
            padding=ft.padding.symmetric(vertical=16, horizontal=20),
            bgcolor=title_bar_bgcolor
        )
        
        # Botones de acción
        save_button = ft.ElevatedButton(
            text="Guardar",
            icon=ft.Icons.SAVE,
            on_click=save_subtask,
            color=ft.Colors.WHITE,
            bgcolor=ft.Colors.RED_700,
            expand=True
        )
        
        cancel_button = ft.OutlinedButton(
            text="Cancelar",
            icon=ft.Icons.CANCEL,
            on_click=lambda e: self._go_back(),
            expand=True
        )
        
        # Construir la vista del formulario
        form_view = ft.View(
            route="/subtask-form",
            controls=[
                title_bar,
                ft.Container(
                    content=ft.Column(
                        [
                            subtask_title_field,
                            subtask_description_field,
                            subtask_deadline_field,
                            ft.Row(
                                [
                                    save_button,
                                    cancel_button
                                ],
                                spacing=8,
                                alignment=ft.MainAxisAlignment.END
                            )
                        ],
                        spacing=16,
                        expand=True,
                        scroll=ft.ScrollMode.AUTO
                    ),
                    expand=True,
                    padding=20
                )
            ],
            bgcolor=bgcolor
        )
        
        # Agregar la vista y navegar a ella
        self.page.views.append(form_view)
        self.page.go("/subtask-form")

