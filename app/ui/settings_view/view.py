"""
Vista principal de configuración - Orquesta todos los módulos.
"""
import flet as ft
from app.services.settings_service import SettingsService
from app.services.sync_service import SyncService

from .utils import get_app_version, copy_to_clipboard
from .appearance import (
    build_appearance_section,
    toggle_theme,
    build_accent_color_dialog,
    select_accent_color,
    close_accent_dialog
)
from .firebase_auth import (
    build_firebase_sync_section,
    get_error_copy_button
)
from .firebase_forms import show_auth_page
from .firebase_sync import (
    show_sync_direction_page,
    show_sync_loading_page,
    show_sync_results_page
)


class SettingsView:
    """Vista dedicada para gestionar la configuración de la aplicación."""
    
    def __init__(
        self,
        page: ft.Page,
        settings_service: SettingsService,
        sync_service: SyncService,
        firebase_auth_service,
        firebase_sync_service,
        firebase_available: bool,
        firebase_import_error: str = "",
        on_go_back: callable = None,
        on_rebuild_tasks: callable = None,
        on_rebuild_habits: callable = None
    ):
        """
        Inicializa la vista de configuración.
        
        Args:
            page: Página de Flet.
            settings_service: Servicio de configuración.
            sync_service: Servicio de sincronización.
            firebase_auth_service: Servicio de autenticación Firebase.
            firebase_sync_service: Servicio de sincronización Firebase.
            firebase_available: Si Firebase está disponible.
            firebase_import_error: Mensaje de error de importación de Firebase.
            on_go_back: Callback para volver a la vista anterior.
            on_rebuild_tasks: Callback para reconstruir vista de tareas.
            on_rebuild_habits: Callback para reconstruir vista de hábitos.
        """
        self.page = page
        self.settings_service = settings_service
        self.sync_service = sync_service
        self.firebase_auth_service = firebase_auth_service
        self.firebase_sync_service = firebase_sync_service
        self.firebase_available = firebase_available
        self.firebase_import_error = firebase_import_error
        self.on_go_back = on_go_back
        self.on_rebuild_tasks = on_rebuild_tasks
        self.on_rebuild_habits = on_rebuild_habits
        
        # Diálogo para seleccionar matiz (paleta de colores)
        self.accent_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(""),
            content=ft.Container(),
            actions=[],
        )
        if self.accent_dialog not in self.page.overlay:
            self.page.overlay.append(self.accent_dialog)
    
    def build_ui(self) -> ft.Container:
        """
        Construye la interfaz de usuario de configuración.
        
        Returns:
            Container con la vista completa de configuración.
        """
        is_dark = self.page.theme_mode == ft.ThemeMode.DARK
        bgcolor = ft.Colors.BLACK if is_dark else ft.Colors.GREY_50

        scheme = self.page.theme.color_scheme if self.page.theme else None
        preview_color = scheme.primary if scheme and scheme.primary else ft.Colors.RED_600

        # Construir secciones
        appearance_section = build_appearance_section(
            self.page,
            self.settings_service,
            lambda e: self._handle_toggle_theme(),
            lambda e: self._handle_open_accent_dialog()
        )
        
        firebase_section = build_firebase_sync_section(
            self.page,
            self.sync_service,
            self.firebase_auth_service,
            preview_color,
            is_dark,
            lambda e: self._handle_show_login(),
            lambda e: self._handle_show_register(),
            lambda e: self._handle_start_sync(),
            lambda e: self._handle_logout(),
            self.firebase_available
        )
        
        error_button = get_error_copy_button(
            self.page,
            preview_color,
            is_dark,
            self.firebase_available,
            self.firebase_import_error,
            lambda error: copy_to_clipboard(self.page, error, "✓ Error copiado al portapapeles")
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
                    *appearance_section,

                    ft.Divider(),

                    # Sección Firebase
                    *firebase_section,

                    ft.Divider(),

                    # Sección Información de la aplicación
                    ft.Text(
                        "Información de la aplicación",
                        size=18,
                        weight=ft.FontWeight.BOLD,
                        color=preview_color
                    ),
                    ft.Text(
                        "Información sobre la versión y el estado de la aplicación.",
                        size=14,
                        color=ft.Colors.GREY_600
                    ),
                    ft.Container(
                        content=ft.Row(
                            [
                                ft.Icon(
                                    ft.Icons.INFO_OUTLINE,
                                    color=preview_color,
                                    size=20
                                ),
                                ft.Column(
                                    [
                                        ft.Text(
                                            "Versión",
                                            size=12,
                                            color=ft.Colors.GREY_600 if not is_dark else ft.Colors.GREY_400,
                                            weight=ft.FontWeight.BOLD
                                        ),
                                        ft.Text(
                                            get_app_version(),
                                            size=16,
                                            color=preview_color,
                                            weight=ft.FontWeight.BOLD
                                        )
                                    ],
                                    spacing=4
                                )
                            ],
                            spacing=12,
                            alignment=ft.MainAxisAlignment.START
                        ),
                        padding=ft.padding.symmetric(vertical=8, horizontal=0)
                    ),
                    
                    # Botón discreto para copiar error (solo si hay error de Firebase)
                    *error_button
                ],
                spacing=16,
                expand=True,
                scroll=ft.ScrollMode.AUTO,
            ),
            padding=20,
            expand=True
        )

        return settings_content
    
    def _handle_toggle_theme(self):
        """Maneja el cambio de tema."""
        toggle_theme(
            self.page,
            self.settings_service,
            self._rebuild_current_view
        )
    
    def _handle_open_accent_dialog(self):
        """Maneja la apertura del diálogo de colores."""
        build_accent_color_dialog(
            self.page,
            self.settings_service,
            self.accent_dialog,
            lambda value: self._handle_select_accent_color(value)
        )
    
    def _handle_select_accent_color(self, value: str):
        """Maneja la selección de un color de acento."""
        from app.services.settings_service import apply_theme_to_page
        
        select_accent_color(
            self.page,
            self.settings_service,
            value,
            self._rebuild_current_view,
            self.accent_dialog
        )
    
    def _rebuild_current_view(self):
        """Reconstruye la vista actual después de cambios de tema/color."""
        # Esta función será llamada por home_view para reconstruir la vista
        if self.on_rebuild_tasks:
            self.on_rebuild_tasks()
        if self.on_rebuild_habits:
            self.on_rebuild_habits()
        # También reconstruir la vista de configuración si es necesario
        if hasattr(self, '_on_rebuild_settings'):
            self._on_rebuild_settings()
    
    def set_rebuild_settings_callback(self, callback: callable):
        """Establece el callback para reconstruir la vista de configuración."""
        self._on_rebuild_settings = callback
    
    def _handle_show_login(self):
        """Maneja la solicitud de mostrar login."""
        show_auth_page(
            self.page,
            self.sync_service,
            self.firebase_auth_service,
            mode="login",
            on_go_back=self.on_go_back,
            on_success=self._rebuild_current_view
        )
    
    def _handle_show_register(self):
        """Maneja la solicitud de mostrar registro."""
        show_auth_page(
            self.page,
            self.sync_service,
            self.firebase_auth_service,
            mode="register",
            on_go_back=self.on_go_back,
            on_success=self._rebuild_current_view
        )
    
    def _handle_logout(self):
        """Maneja el cierre de sesión."""
        try:
            if self.firebase_auth_service:
                self.firebase_auth_service.logout()
            
            # Limpiar configuración de sincronización
            self.sync_service.clear_sync_settings()
            
            # Mostrar mensaje
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text("✓ Sesión cerrada"),
                bgcolor=ft.Colors.GREEN,
                duration=2000
            )
            self.page.snack_bar.open = True
            
            # Reconstruir vista
            self._rebuild_current_view()
            
        except Exception as ex:
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"Error al cerrar sesión: {str(ex)}"),
                bgcolor=ft.Colors.RED,
                duration=3000
            )
            self.page.snack_bar.open = True
        finally:
            self.page.update()
    
    def _handle_start_sync(self):
        """Maneja el inicio de la sincronización."""
        if not self.firebase_sync_service:
            show_sync_results_page(
                self.page,
                False,
                None,
                "Firebase no está disponible",
                self.on_go_back
            )
            return
        
        # Verificar autenticación
        if not self.firebase_auth_service or not self.firebase_auth_service.is_authenticated():
            show_sync_results_page(
                self.page,
                False,
                None,
                "Debes iniciar sesión primero para sincronizar",
                self.on_go_back
            )
            return
        
        # Mostrar página de selección de dirección
        show_sync_direction_page(
            self.page,
            self.firebase_sync_service,
            self.firebase_auth_service,
            self.on_go_back,
            self.on_rebuild_tasks,
            self.on_rebuild_habits
        )

