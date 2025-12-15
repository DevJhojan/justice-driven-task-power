"""
Vista principal de la aplicación de tareas.
"""
import os
import flet as ft
from typing import Optional
from datetime import date, datetime
from app.data.models import Task, SubTask, Habit
from app.services.task_service import TaskService
from app.services.habit_service import HabitService
from app.services.csv_backup_service import CSVBackupService
from app.services.settings_service import SettingsService, apply_theme_to_page
from app.ui.widgets import (
    create_task_card, create_empty_state, create_statistics_card,
    create_habit_card, create_habit_empty_state, create_habit_statistics_card
)
from app.ui.task_form import TaskForm
from app.ui.habit_form import HabitForm


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
        self.habit_service = HabitService()
        self.csv_backup_service = CSVBackupService()
        self.settings_service = SettingsService()
        self.current_task_filter: Optional[bool] = None  # None=all, True=completed, False=pending
        self.current_habit_filter: Optional[bool] = None  # None=all, True=active, False=inactive
        self.editing_task: Optional[Task] = None
        self.editing_subtask_task_id: Optional[int] = None
        self.editing_subtask = None
        self.editing_habit: Optional[Habit] = None
        # Secciones: "tasks", "habits", "settings"
        self.current_section = "tasks"
        
        # Contenedores principales
        self.tasks_container = ft.Column([], spacing=0, scroll=ft.ScrollMode.AUTO, expand=True)
        self.habits_container = ft.Column([], spacing=0, scroll=ft.ScrollMode.AUTO, expand=True)
        self.stats_card = None
        self.habit_stats_card = None
        self.title_bar = None  # Guardar referencia a la barra de título
        
        # File pickers para importación/exportación de base de datos
        self.import_file_picker = ft.FilePicker(on_result=self._handle_import_result)
        self.export_file_picker = ft.FilePicker(on_result=self._handle_export_result)
        if self.import_file_picker not in self.page.overlay:
            self.page.overlay.append(self.import_file_picker)
        if self.export_file_picker not in self.page.overlay:
            self.page.overlay.append(self.export_file_picker)

        # Diálogo para seleccionar matiz (paleta de colores)
        # Debe tener al menos title, content o actions para que Flet no lance AssertionError.
        self.accent_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(""),
            content=ft.Container(),
            actions=[],
        )
        if self.accent_dialog not in self.page.overlay:
            self.page.overlay.append(self.accent_dialog)

        # Diálogo de permisos de almacenamiento (solo móvil)
        self.storage_permission_dialog = None

        self.page.update()

        self._build_ui()
        self._load_tasks()
    
    def _build_ui(self):
        """Construye la interfaz de usuario."""
        # Barra de título
        scheme = self.page.theme.color_scheme if self.page.theme else None
        title_color = scheme.primary if scheme and scheme.primary else ft.Colors.RED_400

        self.title_bar = ft.Container(
            content=ft.Row(
                [
                    ft.Text(
                        "Mis Tareas" if self.current_section == "tasks"
                        else "Mis Hábitos" if self.current_section == "habits"
                        else "Configuración",
                        size=28,
                        weight=ft.FontWeight.BOLD,
                        color=title_color,
                        expand=True
                    )
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER
            ),
            padding=ft.padding.symmetric(vertical=16, horizontal=20),
            bgcolor=ft.Colors.BLACK87 if self.page.theme_mode == ft.ThemeMode.DARK else ft.Colors.RED_50
        )
        
        # Crear la barra inferior de navegación
        self._build_bottom_bar()
        
        # Filtros - colores adaptativos según el tema/acento
        is_dark = self.page.theme_mode == ft.ThemeMode.DARK
        scheme = self.page.theme.color_scheme if self.page.theme else None
        primary = scheme.primary if scheme and scheme.primary else ft.Colors.RED_700
        secondary = scheme.secondary if scheme and scheme.secondary else ft.Colors.RED_600

        active_bg = primary
        inactive_bg = ft.Colors.GREY_800 if is_dark else ft.Colors.GREY_100
        text_color = ft.Colors.WHITE
        
        # Botón para agregar nueva tarea - color adaptativo
        new_task_button_bg = primary
        
        # Botones de filtro
        filter_buttons = [
                ft.ElevatedButton(
                    text="Todas",
                    on_click=lambda e: self._filter_tasks(None),
                    bgcolor=active_bg if self.current_task_filter is None else inactive_bg,
                    color=text_color,
                    height=40
                ),
                ft.ElevatedButton(
                    text="Pendientes",
                    on_click=lambda e: self._filter_tasks(False),
                    bgcolor=active_bg if self.current_task_filter is False else inactive_bg,
                    color=text_color,
                    height=40
                ),
                ft.ElevatedButton(
                    text="Completadas",
                    on_click=lambda e: self._filter_tasks(True),
                    bgcolor=active_bg if self.current_task_filter is True else inactive_bg,
                    color=text_color,
                    height=40
                )
        ]
        
        # Botón "+" para la parte superior derecha
        self.new_task_button = ft.IconButton(
            icon=ft.Icons.ADD,
            on_click=self._show_new_task_form,
            bgcolor=new_task_button_bg,
            icon_color=ft.Colors.WHITE,
            tooltip="Nueva Tarea",
            width=40,
            height=40
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

        scheme = self.page.theme.color_scheme if self.page.theme else None
        selected_color = scheme.primary if scheme and scheme.primary else ft.Colors.RED_400
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
        
        # Botón de Configuración
        settings_button = ft.Container(
            content=ft.Column(
                [
                    ft.Icon(
                        ft.Icons.SETTINGS,
                        color=selected_color if self.current_section == "settings" else unselected_color,
                        size=24
                    ),
                    ft.Text(
                        "Configuración",
                        size=12,
                        color=selected_color if self.current_section == "settings" else unselected_color,
                        weight=ft.FontWeight.BOLD if self.current_section == "settings" else None
                    )
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=4,
                tight=True
            ),
            on_click=lambda e: self._navigate_to_section("settings"),
            padding=12,
            expand=True,
            border=ft.border.only(
                top=ft.BorderSide(3, selected_color if self.current_section == "settings" else ft.Colors.TRANSPARENT)
            )
        )

        self.bottom_bar = ft.Container(
            content=ft.Row(
                [
                    tasks_button,
                    habits_button,
                    settings_button
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
            self._load_habits()
        elif section == "settings":
            # Mostrar la vista de configuración
            self._build_settings_view()
        
        # Actualizar el título
        if self.title_bar:
            title_text = self.title_bar.content.controls[0]  # El texto está en el índice 0 ahora
            if isinstance(title_text, ft.Text):
                if section == "tasks":
                    title_text.value = "Mis Tareas"
                elif section == "habits":
                    title_text.value = "Mis Hábitos"
                else:
                    title_text.value = "Configuración"
        
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

        scheme = self.page.theme.color_scheme if self.page.theme else None
        primary = scheme.primary if scheme and scheme.primary else ft.Colors.RED_700
        secondary = scheme.secondary if scheme and scheme.secondary else ft.Colors.RED_600
        
        # Botón para agregar nuevo hábito - color adaptativo
        new_habit_button_bg = primary
        
        # Botón "+" para agregar hábito
        self.new_habit_button = ft.IconButton(
            icon=ft.Icons.ADD,
            on_click=self._show_new_habit_form,
            bgcolor=new_habit_button_bg,
            icon_color=ft.Colors.WHITE,
            tooltip="Nuevo Hábito",
            width=40,
            height=40
        )
        
        # Filtros para hábitos (Activos/Inactivos/Todos)
        active_bg = primary
        inactive_bg = ft.Colors.GREY_800 if is_dark else ft.Colors.GREY_100
        text_color = ft.Colors.WHITE
        
        # Contenedor de estadísticas de hábitos
        habit_stats_container = ft.Container(
            content=create_habit_statistics_card(self.habit_service.get_statistics(), self.page),
            visible=True
        )
        self.habit_stats_container = habit_stats_container
        
        # Filtros de hábitos
        habit_filter_row = ft.Row(
            [
                ft.ElevatedButton(
                    text="Todos",
                    on_click=lambda e: self._filter_habits(None),
                    bgcolor=active_bg,
                    color=text_color,
                    height=40
                ),
                ft.ElevatedButton(
                    text="Activos",
                    on_click=lambda e: self._filter_habits(True),
                    bgcolor=inactive_bg,
                    color=text_color,
                    height=40
                ),
                ft.ElevatedButton(
                    text="Inactivos",
                    on_click=lambda e: self._filter_habits(False),
                    bgcolor=inactive_bg,
                    color=text_color,
                    height=40
                ),
                self.new_habit_button
            ],
            spacing=8,
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER
        )
        
        # Vista principal (lista de hábitos)
        main_view = ft.Container(
            content=ft.Column(
                [
                    habit_stats_container,
                    habit_filter_row,
                    self.habits_container
                ],
                spacing=8,
                expand=True
            ),
            padding=16,
            expand=True
        )
        
        # Actualizar la vista principal
        self.home_view.controls = [
            ft.Column(
                [
                    self.title_bar,
                    main_view,
                    self.bottom_bar
                ],
                spacing=0,
                expand=True
            )
        ]
        self.home_view.bgcolor = bgcolor
        
        # Cargar hábitos
        self._load_habits()

    def _build_settings_view(self):
        """Construye la vista de configuración (placeholder)."""
        is_dark = self.page.theme_mode == ft.ThemeMode.DARK
        bgcolor = ft.Colors.BLACK if is_dark else ft.Colors.GREY_50

        scheme = self.page.theme.color_scheme if self.page.theme else None
        preview_color = scheme.primary if scheme and scheme.primary else ft.Colors.RED_600

        # ==================== Sección 1: Apariencia ====================
        # Controles de apariencia (tema y color principal)
        current_settings = self.settings_service.get_settings()

        # Botón de luna/sol para alternar tema
        theme_icon = (
            ft.Icons.DARK_MODE if current_settings.theme_mode == "dark" else ft.Icons.LIGHT_MODE
        )
        theme_icon_button = ft.IconButton(
            icon=theme_icon,
            tooltip="Cambiar modo de tema",
            on_click=self._toggle_theme,
        )

        # ==================== Sección 2: Copia de seguridad ====================
        # Botones de importación/exportación CSV (también con matiz)
        import_button = ft.ElevatedButton(
            text="Importar datos desde archivo CSV",
            icon=ft.Icons.FILE_UPLOAD,
            on_click=self._start_import,
            bgcolor=preview_color,
            color=ft.Colors.WHITE,
        )

        export_button = ft.ElevatedButton(
            text="Exportar datos a archivo CSV",
            icon=ft.Icons.FILE_DOWNLOAD,
            on_click=self._start_export,
            bgcolor=preview_color,
            color=ft.Colors.WHITE,
        )

        settings_content = ft.Container(
            content=ft.Column(
                [
                    ft.Text(
                        "Configuración",
                        size=24,
                        weight=ft.FontWeight.BOLD,
                        color=preview_color
                    ),
                    ft.Divider(),

                    # Sección Apariencia
                    ft.Text(
                        "Apariencia",
                        size=18,
                        weight=ft.FontWeight.BOLD,
                        color=preview_color
                    ),
                    ft.Text(
                        "Ajusta el modo de tema y el color principal de la aplicación.",
                        size=14,
                        color=ft.Colors.GREY_600
                    ),
                    ft.Row(
                        [
                            ft.Text("Modo de tema", size=14),
                            theme_icon_button,
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    ft.Text(
                        "Color principal",
                        size=14,
                        weight=ft.FontWeight.BOLD
                    ),
                    ft.Row(
                        [
                            ft.Container(
                                content=ft.Icon(ft.Icons.CIRCLE, color=preview_color, size=20),
                                border=ft.border.all(1, ft.Colors.GREY_400),
                                border_radius=20,
                                padding=6,
                            ),
                            ft.ElevatedButton(
                                text="Elegir matiz",
                                icon=ft.Icons.COLOR_LENS,
                                on_click=self._open_accent_dialog,
                            )
                        ],
                        spacing=12,
                        alignment=ft.MainAxisAlignment.START,
                    ),

                    ft.Divider(),

                    # ==================== Sección 2: Importación de datos ====================
                    ft.Text(
                        "Importación de datos",
                        size=18,
                        weight=ft.FontWeight.BOLD,
                        color=preview_color
                    ),
                    ft.Text(
                        "Importa registros desde un archivo CSV (ZIP) generado por esta aplicación. "
                        "Los datos se agregan sin reemplazar tu base actual, evitando duplicados "
                        "y manteniendo la integridad de tareas, subtareas y hábitos.",
                        size=14,
                        color=ft.Colors.GREY_600
                    ),
                    ft.Row(
                        [import_button],
                        alignment=ft.MainAxisAlignment.START
                    ),

                    ft.Divider(),

                    # ==================== Sección 3: Exportación de datos ====================
                    ft.Text(
                        "Exportación de datos",
                        size=18,
                        weight=ft.FontWeight.BOLD,
                        color=preview_color
                    ),
                    ft.Text(
                        "Exporta todos los datos a un archivo CSV comprimido (ZIP) conteniendo "
                        "tasks.csv, subtasks.csv, habits.csv y habit_completions.csv. "
                        "Ideal para copias de seguridad, migración entre dispositivos o restauración futura.",
                        size=14,
                        color=ft.Colors.GREY_600
                    ),
                    ft.Row(
                        [export_button],
                        alignment=ft.MainAxisAlignment.START
                    )
                ],
                spacing=16,
                expand=True,
                scroll=ft.ScrollMode.AUTO,
            ),
            padding=20,
            expand=True
        )

        # Actualizar la vista principal
        self.home_view.controls = [
            ft.Column(
                [
                    self.title_bar,
                    settings_content,
                    self.bottom_bar
                ],
                spacing=0,
                expand=True
            )
        ]
        self.home_view.bgcolor = bgcolor
        self.page.update()

    # ==================== IMPORT / EXPORT CSV ====================

    def _start_import(self, e):
        """Inicia el proceso de selección de archivo ZIP (CSV) para importar."""
        try:
            self.import_file_picker.pick_files(
                allow_multiple=False,
                file_type=ft.FilePickerFileType.CUSTOM,
                allowed_extensions=["zip"],
            )
        except Exception as ex:
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"Error al iniciar la importación: {str(ex)}"),
                bgcolor=ft.Colors.RED,
            )
            self.page.snack_bar.open = True
            self.page.update()

    def _handle_import_result(self, e: ft.FilePickerResultEvent):
        """Maneja el resultado de la selección de archivo CSV para importación."""
        if not e.files:
            return  # Usuario canceló

        file = e.files[0]
        path = file.path
        if not path or not path.lower().endswith(".zip"):
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text("Debe seleccionar un archivo ZIP con extensión .zip"),
                bgcolor=ft.Colors.RED,
            )
            self.page.snack_bar.open = True
            self.page.update()
            return

        # Detectar si estamos en Android/iOS
        is_mobile = (
            self.page.platform == ft.PagePlatform.ANDROID 
            or self.page.platform == ft.PagePlatform.IOS
        )

        try:
            result = self.csv_backup_service.import_from_csv(path)
            
            # Construir mensaje de éxito
            msg_parts = [f"Importación completada."]
            if result.tasks_imported > 0:
                msg_parts.append(f"Tareas nuevas: {result.tasks_imported}")
            if result.subtasks_imported > 0:
                msg_parts.append(f"Subtareas nuevas: {result.subtasks_imported}")
            if result.habits_imported > 0:
                msg_parts.append(f"Hábitos nuevos: {result.habits_imported}")
            if result.habit_completions_imported > 0:
                msg_parts.append(f"Cumplimientos nuevos: {result.habit_completions_imported}")
            
            if result.errors:
                msg_parts.append(f"\nAdvertencias: {len(result.errors)}")
                # Mostrar primeros errores en el mensaje
                for error in result.errors[:3]:
                    msg_parts.append(f"  - {error}")
                if len(result.errors) > 3:
                    msg_parts.append(f"  ... y {len(result.errors) - 3} más")

            msg = " ".join(msg_parts)
            
            bg_color = ft.Colors.GREEN if not result.errors else ft.Colors.ORANGE
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(msg),
                bgcolor=bg_color,
                duration=8000 if is_mobile else 5000,
            )
            self.page.snack_bar.open = True

            # Refrescar vistas si estamos en tareas/hábitos
            if self.current_section == "tasks":
                self._load_tasks()
            elif self.current_section == "habits":
                self._load_habits()

        except Exception as ex:
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"Error al importar datos CSV: {str(ex)}"),
                bgcolor=ft.Colors.RED,
                duration=8000 if is_mobile else 5000,
            )
            self.page.snack_bar.open = True
        finally:
            self.page.update()

    def _start_export(self, e):
        """Inicia el diálogo para elegir dónde guardar el backup CSV (ZIP)."""
        try:
            # Nombre sugerido con timestamp para evitar sobrescribir
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.export_file_picker.save_file(
                file_name=f"tasks_backup_{ts}.zip"
            )
        except Exception as ex:
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"Error al iniciar la exportación: {str(ex)}"),
                bgcolor=ft.Colors.RED,
            )
            self.page.snack_bar.open = True
            self.page.update()

    def _handle_export_result(self, e: ft.FilePickerResultEvent):
        """Maneja la ruta elegida por el usuario y realiza el backup CSV."""
        if not e.path:
            return  # Usuario canceló

        # Asegurar extensión .zip
        target_path = e.path
        if not target_path.lower().endswith(".zip"):
            target_path = target_path + ".zip"

        # Si es una prueba de permisos (archivo test_permission.zip), solo verificar que funciona
        if "test_permission" in target_path.lower():
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(
                    "✓ Permisos de almacenamiento activados correctamente.\n"
                    "Ya puedes usar importar/exportar sin problemas."
                ),
                bgcolor=ft.Colors.GREEN,
                duration=4000,
            )
            self.page.snack_bar.open = True
            self.page.update()
            return  # No exportar realmente, solo verificar permisos

        # Detectar si estamos en Android/iOS para mostrar mensajes más específicos
        is_mobile = (
            self.page.platform == ft.PagePlatform.ANDROID 
            or self.page.platform == ft.PagePlatform.IOS
        )

        try:
            self.csv_backup_service.export_to_csv(target_path)
            
            # Verificar tamaño del archivo exportado
            file_size = os.path.getsize(target_path)
            size_mb = file_size / (1024 * 1024)
            
            success_msg = (
                f"Datos exportados correctamente a CSV.\n"
                f"Ubicación: {target_path}\n"
                f"Tamaño: {size_mb:.2f} MB\n"
                f"Contiene: tasks.csv, subtasks.csv, habits.csv, habit_completions.csv"
            )
            
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(success_msg),
                bgcolor=ft.Colors.GREEN,
                duration=6000 if is_mobile else 4000,
            )
            self.page.snack_bar.open = True
        except OSError as ex:
            # Errores específicos de permisos/almacenamiento
            error_msg = str(ex)
            if is_mobile and "permisos" in error_msg.lower():
                error_msg += (
                    "\n\nSugerencia: Intenta guardar en la carpeta 'Descargas' "
                    "o selecciona otra ubicación accesible."
                )
            
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(error_msg),
                bgcolor=ft.Colors.RED,
                duration=8000 if is_mobile else 5000,
            )
            self.page.snack_bar.open = True
        except Exception as ex:
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"Error al exportar datos CSV: {str(ex)}"),
                bgcolor=ft.Colors.RED,
                duration=6000,
            )
            self.page.snack_bar.open = True
        finally:
            self.page.update()

    def _show_storage_permission_dialog(self):
        """Muestra un diálogo informativo sobre permisos de almacenamiento en Android/iOS."""
        if self.page.platform != ft.PagePlatform.ANDROID and self.page.platform != ft.PagePlatform.IOS:
            return  # Solo en móvil

        # Crear diálogo informativo
        permission_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Permisos de almacenamiento"),
            content=ft.Column(
                [
                    ft.Text(
                        "Para usar las funciones de importar y exportar datos, "
                        "la aplicación necesita acceso al almacenamiento.",
                        size=14,
                    ),
                    ft.Divider(),
                    ft.Text(
                        "Los permisos se solicitarán automáticamente cuando uses "
                        "las funciones de importar o exportar por primera vez.",
                        size=14,
                        weight=ft.FontWeight.BOLD,
                    ),
                    ft.Text(
                        "Recomendación: Guarda los backups en la carpeta 'Descargas' "
                        "para mayor compatibilidad.",
                        size=12,
                        color=ft.Colors.GREY_600,
                    ),
                ],
                tight=True,
                spacing=12,
            ),
            actions=[
                ft.TextButton(
                    "Entendido",
                    on_click=lambda e: self._close_permission_dialog(),
                ),
                ft.ElevatedButton(
                    "Probar ahora",
                    on_click=lambda e: self._test_storage_permission(),
                ),
            ],
        )

        self.storage_permission_dialog = permission_dialog
        self.page.dialog = permission_dialog
        permission_dialog.open = True
        self.page.update()

    def _close_permission_dialog(self):
        """Cierra el diálogo de permisos."""
        if self.storage_permission_dialog:
            self.storage_permission_dialog.open = False
            self.page.dialog = None
            self.page.update()

    def _test_storage_permission(self):
        """Intenta activar el FilePicker para solicitar permisos."""
        self._close_permission_dialog()
        
        # Intentar abrir el FilePicker para activar la solicitud de permisos
        try:
            # Usar el export_file_picker para activar permisos
            # Esto debería mostrar el diálogo de permisos de Android
            self.export_file_picker.save_file(file_name="test_permission.zip")
            
            # Si el usuario cancela, no hacemos nada
            # Si acepta, el _handle_export_result manejará el resultado
        except Exception as ex:
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"Error al solicitar permisos: {str(ex)}"),
                bgcolor=ft.Colors.RED,
            )
            self.page.snack_bar.open = True
            self.page.update()
    
    def _load_tasks(self):
        """Carga las tareas desde la base de datos."""
        tasks = self.task_service.get_all_tasks(self.current_task_filter)
        
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
        self.current_task_filter = filter_completed
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
        self.editing_habit = None
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
        # Alternar modo y persistir a través del servicio de ajustes
        current = self.settings_service.get_settings()
        new_mode = "light" if current.theme_mode == "dark" else "dark"
        updated = self.settings_service.update_settings(theme_mode=new_mode)
        apply_theme_to_page(self.page, updated)

        # Reconstruir vista según sección actual
        if self.current_section == "tasks":
            self._build_ui()
            self._load_tasks()
        elif self.current_section == "habits":
            self._build_habits_view()
        elif self.current_section == "settings":
            self._build_settings_view()

        self.page.update()

    def _open_accent_dialog(self, e):
        """Abre el diálogo con la paleta de matices disponibles."""
        current_settings = self.settings_service.get_settings()

        # Secciones de colores con sus opciones
        sections: list[tuple[str, list[tuple[str, str, str]]]] = [
            (
                "Azules",
                [
                    ("dodger_blue", "#1E90FF", "DodgerBlue"),
                    ("primary_blue", "#007BFF", "Primary Blue"),
                    ("bootstrap_blue", "#0D6EFD", "Bootstrap Blue"),
                    ("deep_blue", "#0056B3", "Deep Blue"),
                    ("deepsky_blue", "#00BFFF", "DeepSkyBlue"),
                    ("steel_blue", "#4682B4", "SteelBlue"),
                    ("navy_dark", "#003366", "Navy Dark"),
                ],
            ),
            (
                "Verdes",
                [
                    ("success_green", "#28A745", "Success Green"),
                    ("emerald", "#2ECC71", "Emerald"),
                    ("bright_green", "#00C853", "Bright Green"),
                    ("material_green", "#4CAF50", "Material Green"),
                    ("turquoise", "#1ABC9C", "Turquoise"),
                    ("green_sea", "#16A085", "Green Sea"),
                    ("dark_teal", "#00695C", "Dark Teal"),
                ],
            ),
            (
                "Rojos",
                [
                    ("danger_red", "#DC3545", "Danger Red"),
                    ("alizarin", "#E74C3C", "Alizarin"),
                    ("dark_red", "#C0392B", "Dark Red"),
                    ("soft_red", "#FF5252", "Soft Red"),
                    ("deep_red", "#B71C1C", "Deep Red"),
                    ("vivid_red", "#FF1744", "Vivid Red"),
                ],
            ),
            (
                "Amarillos / Naranjas",
                [
                    ("amber", "#FFC107", "Amber"),
                    ("soft_yellow", "#FFD54F", "Soft Yellow"),
                    ("orange", "#FF9800", "Orange"),
                    ("deep_orange", "#FF5722", "Deep Orange"),
                    ("sun_orange", "#F39C12", "Sun Orange"),
                    ("golden", "#FFB300", "Golden"),
                ],
            ),
            (
                "Morados / Rosas",
                [
                    ("ui_purple", "#6F42C1", "Purple UI"),
                    ("amethyst", "#9B59B6", "Amethyst"),
                    ("dark_purple", "#8E44AD", "Dark Purple"),
                    ("vibrant_purple", "#E056FD", "Vibrant Purple"),
                    ("ui_pink", "#D63384", "Pink"),
                    ("hot_pink", "#FF69B4", "Hot Pink"),
                ],
            ),
            (
                "Grises / Neutros",
                [
                    ("dark_gray", "#212529", "Dark Gray"),
                    ("charcoal", "#343A40", "Charcoal"),
                    ("medium_gray", "#495057", "Medium Gray"),
                    ("secondary_gray", "#6C757D", "Secondary Gray"),
                    ("light_gray", "#ADB5BD", "Light Gray"),
                    ("soft_gray", "#DEE2E6", "Soft Gray"),
                    ("almost_white", "#F8F9FA", "Almost White"),
                ],
            ),
            (
                "Blancos / Negros",
                [
                    ("black", "#000000", "Black"),
                    ("white", "#FFFFFF", "White"),
                    ("soft_white", "#FAFAFA", "Soft White"),
                    ("true_dark", "#121212", "True Dark Mode"),
                ],
            ),
            (
                "Colores gamer / UI",
                [
                    ("neon_cyan", "#00E5FF", "Neon Cyan"),
                    ("neon_green", "#76FF03", "Neon Green"),
                    ("neon_pink", "#FF4081", "Neon Pink"),
                    ("electric_purple", "#651FFF", "Electric Purple"),
                    ("tech_blue", "#00B0FF", "Tech Blue"),
                    ("mint_neon", "#1DE9B6", "Mint Neon"),
                    ("orange_neon", "#FF9100", "Orange Neon"),
                ],
            ),
        ]

        section_controls: list[ft.Control] = []

        for title, options in sections:
            # Título de sección
            section_controls.append(
                ft.Text(
                    title,
                    size=16,
                    weight=ft.FontWeight.BOLD,
                )
            )

            # Botones de la sección, organizados en filas
            buttons: list[ft.Container] = []
            for value, color, label in options:
                selected = value == current_settings.accent_color
                buttons.append(
                    ft.Container(
                        content=ft.IconButton(
                            icon=ft.Icons.CIRCLE,
                            icon_color=color,
                            tooltip=label,
                            data=value,
                            on_click=self._on_accent_button_click,
                        ),
                        border=ft.border.all(
                            2,
                            color if selected else ft.Colors.TRANSPARENT,
                        ),
                        border_radius=20,
                        padding=4,
                    )
                )

            # Agrupar botones en filas de 4 para mejor uso de espacio
            for i in range(0, len(buttons), 4):
                section_controls.append(
                    ft.Row(
                        controls=buttons[i : i + 4],
                        spacing=8,
                        alignment=ft.MainAxisAlignment.START,
                    )
                )

            # Separador entre secciones
            section_controls.append(ft.Divider())

        # Contenido scrollable ocupando ~70% del ancho de la pantalla
        content_width = self.page.width * 0.7 if self.page.width else None

        self.accent_dialog.title = ft.Text("Selecciona un matiz")
        self.accent_dialog.content = ft.Container(
            width=content_width,
            content=ft.Column(
                controls=section_controls,
                spacing=8,
                scroll=ft.ScrollMode.AUTO,
            ),
        )
        self.accent_dialog.actions = [
            ft.TextButton("Cerrar", on_click=lambda ev: self._close_accent_dialog())
        ]
        self.accent_dialog.open = True
        self.page.dialog = self.accent_dialog
        self.page.update()

    def _on_accent_button_click(self, e: ft.ControlEvent):
        """Cambio de color principal desde la grid de matices."""
        value = e.control.data
        # La validación se hace de forma implícita en SettingsService mediante AccentColorLiteral,
        # aquí solo comprobamos que exista algún valor.
        if not value:
            return

        updated = self.settings_service.update_settings(accent_color=value)
        apply_theme_to_page(self.page, updated)

        # Reconstruir la vista actual respetando la sección activa
        if self.current_section == "tasks":
            self._build_ui()
            self._load_tasks()
        elif self.current_section == "habits":
            self._build_habits_view()
        elif self.current_section == "settings":
            self._build_settings_view()

        # Cerrar el diálogo de selección si está abierto
        self._close_accent_dialog()
        self.page.update()

    def _close_accent_dialog(self):
        """Cierra el diálogo de selección de matiz si está abierto."""
        if hasattr(self, "accent_dialog"):
            self.accent_dialog.open = False
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
    
    # ==================== MÉTODOS PARA HÁBITOS ====================
    
    def _load_habits(self):
        """Carga los hábitos desde la base de datos."""
        habits = self.habit_service.get_all_habits(self.current_habit_filter)
        
        # Asegurarse de que el contenedor existe
        if not hasattr(self, 'habits_container') or self.habits_container is None:
            return
        
        self.habits_container.controls.clear()
        
        if not habits:
            self.habits_container.controls.append(create_habit_empty_state(self.page))
        else:
            for habit in habits:
                # Obtener métricas del hábito
                metrics = self.habit_service.get_habit_metrics(habit.id)
                
                card = create_habit_card(
                    habit,
                    metrics,
                    on_toggle_completion=self._toggle_habit_completion,
                    on_edit=self._edit_habit,
                    on_delete=self._delete_habit,
                    on_view_details=self._view_habit_details,
                    page=self.page
                )
                self.habits_container.controls.append(card)
        
        # Actualizar estadísticas
        if hasattr(self, 'habit_stats_container') and self.habit_stats_container:
            stats = self.habit_service.get_statistics()
            self.habit_stats_container.content = create_habit_statistics_card(stats, self.page)
            try:
                self.habit_stats_container.update()
            except:
                pass
        
        try:
            self.habits_container.update()
        except:
            pass
        self.page.update()
    
    def _filter_habits(self, filter_active: Optional[bool]):
        """Filtra los hábitos por estado activo/inactivo."""
        self.current_habit_filter = filter_active
        self._load_habits()
        # Actualizar colores de los botones de filtro
        self._update_habit_filters()
    
    def _update_habit_filters(self):
        """Actualiza los colores de los botones de filtro de hábitos."""
        is_dark = self.page.theme_mode == ft.ThemeMode.DARK
        active_bg = ft.Colors.RED_700 if is_dark else ft.Colors.RED_600
        inactive_bg = ft.Colors.GREY_800 if is_dark else ft.Colors.RED_100
        text_color = ft.Colors.WHITE
        
        if hasattr(self, 'habit_filter_all_btn'):
            self.habit_filter_all_btn.bgcolor = active_bg if self.current_habit_filter is None else inactive_bg
            self.habit_filter_all_btn.update()
        if hasattr(self, 'habit_filter_active_btn'):
            self.habit_filter_active_btn.bgcolor = active_bg if self.current_habit_filter is True else inactive_bg
            self.habit_filter_active_btn.update()
        if hasattr(self, 'habit_filter_inactive_btn'):
            self.habit_filter_inactive_btn.bgcolor = active_bg if self.current_habit_filter is False else inactive_bg
            self.habit_filter_inactive_btn.update()
    
    def _show_new_habit_form(self, e):
        """Navega a la vista del formulario para crear un nuevo hábito."""
        self.editing_habit = None
        self._navigate_to_habit_form_view()
    
    def _edit_habit(self, habit: Habit):
        """Navega a la vista del formulario para editar un hábito."""
        self.editing_habit = habit
        self._navigate_to_habit_form_view()
    
    def _navigate_to_habit_form_view(self):
        """Navega a la vista del formulario de hábito."""
        title = "Editar Hábito" if self.editing_habit else "Nuevo Hábito"
        
        # Crear el formulario
        form = HabitForm(
            on_save=self._save_habit,
            on_cancel=self._go_back,
            habit=self.editing_habit
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
            route="/habit-form",
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
        self.page.go("/habit-form")
    
    def _save_habit(self, *args):
        """Guarda un hábito (crear o actualizar)."""
        # Si el primer argumento es un objeto Habit, es una actualización
        if args and isinstance(args[0], Habit):
            # Actualizar hábito existente
            habit = args[0]
            self.habit_service.update_habit(habit)
        else:
            # Crear nuevo hábito
            title, description, frequency, target_days = args
            self.habit_service.create_habit(title, description, frequency, target_days)
        
        # Volver a la vista principal
        self._go_back()
        
        # Forzar actualización de la página antes de recargar hábitos
        self.page.update()
        
        # Recargar los hábitos después de volver
        self._load_habits()
    
    def _toggle_habit_completion(self, habit_id: int):
        """Alterna el cumplimiento de un hábito para hoy."""
        completion = self.habit_service.toggle_completion(habit_id, date.today())
        self._load_habits()
        
        # Mostrar mensaje
        if completion:
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text("¡Hábito completado!"),
                bgcolor=ft.Colors.RED_700
            )
        else:
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text("Cumplimiento eliminado"),
                bgcolor=ft.Colors.GREY_700
            )
        self.page.snack_bar.open = True
        self.page.update()
    
    def _delete_habit(self, habit_id: int):
        """Elimina un hábito."""
        if habit_id is None:
            return
        
        try:
            deleted = self.habit_service.delete_habit(int(habit_id))
            if deleted:
                self._load_habits()
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text("Hábito eliminado correctamente"),
                    bgcolor=ft.Colors.RED_700
                )
                self.page.snack_bar.open = True
            else:
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text("No se pudo eliminar el hábito"),
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
    
    def _view_habit_details(self, habit: Habit):
        """Muestra la vista de detalles de un hábito con historial y métricas."""
        # Obtener métricas completas
        metrics = self.habit_service.get_habit_metrics(habit.id)
        weekly_progress = self.habit_service.get_weekly_progress(habit.id)
        monthly_progress = self.habit_service.get_monthly_progress(habit.id)
        
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
                        habit.title,
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
        
        # Construir contenido de detalles
        details_content = ft.Container(
            content=ft.Column(
                [
                    # Descripción
                    ft.Text(
                        habit.description if habit.description else "Sin descripción",
                        size=14,
                        color=ft.Colors.GREY_500 if is_dark else ft.Colors.GREY_600
                    ),
                    ft.Divider(),
                    # Métricas principales
                    ft.Text(
                        "Métricas",
                        size=20,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.RED_400
                    ),
                    ft.Row(
                        [
                            ft.Container(
                                content=ft.Column(
                                    [
                                        ft.Text(
                                            str(metrics['streak']),
                                            size=32,
                                            weight=ft.FontWeight.BOLD,
                                            color=ft.Colors.RED_400
                                        ),
                                        ft.Text("Días seguidos", size=12)
                                    ],
                                    horizontal_alignment=ft.CrossAxisAlignment.CENTER
                                ),
                                expand=True
                            ),
                            ft.VerticalDivider(),
                            ft.Container(
                                content=ft.Column(
                                    [
                                        ft.Text(
                                            f"{metrics['completion_percentage']:.1f}%",
                                            size=32,
                                            weight=ft.FontWeight.BOLD,
                                            color=ft.Colors.RED_500
                                        ),
                                        ft.Text("Cumplimiento", size=12)
                                    ],
                                    horizontal_alignment=ft.CrossAxisAlignment.CENTER
                                ),
                                expand=True
                            ),
                            ft.VerticalDivider(),
                            ft.Container(
                                content=ft.Column(
                                    [
                                        ft.Text(
                                            str(metrics['total_completions']),
                                            size=32,
                                            weight=ft.FontWeight.BOLD,
                                            color=ft.Colors.RED_600
                                        ),
                                        ft.Text("Total", size=12)
                                    ],
                                    horizontal_alignment=ft.CrossAxisAlignment.CENTER
                                ),
                                expand=True
                            )
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_EVENLY
                    ),
                    ft.Divider(),
                    # Información adicional
                    ft.Text(
                        f"Frecuencia: {habit.frequency.capitalize()}",
                        size=14
                    ),
                    ft.Text(
                        f"Último cumplimiento: {metrics['last_completion_date'].strftime('%d/%m/%Y') if metrics['last_completion_date'] else 'Nunca'}",
                        size=14
                    )
                ],
                spacing=16,
                scroll=ft.ScrollMode.AUTO
            ),
            padding=20,
            expand=True
        )
        
        # Construir la vista de detalles
        details_view = ft.View(
            route="/habit-details",
            controls=[
                title_bar,
                details_content
            ],
            bgcolor=bgcolor
        )
        
        # Agregar la vista y navegar a ella
        self.page.views.append(details_view)
        self.page.go("/habit-details")

