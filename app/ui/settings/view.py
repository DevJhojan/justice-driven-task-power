"""
Vista de configuración.
"""
import flet as ft

from app.data.database import get_db
from app.services.user_settings_service import UserSettingsService
from app.services.firebase_sync_service import FirebaseSyncService


class SettingsView:
    """Vista de configuración de la aplicación."""
    
    def __init__(self, page: ft.Page, on_name_changed: callable = None,
                 firebase_sync_service: FirebaseSyncService = None):
        """
        Inicializa la vista de configuración.
        
        Args:
            page: Página de Flet.
            on_name_changed: Callback a ejecutar cuando se cambia el nombre del usuario.
            firebase_sync_service: Servicio de sincronización con Firebase.
        """
        self.page = page
        self.on_name_changed = on_name_changed
        db = get_db()
        self.user_settings_service = UserSettingsService(db)
        self.user_name_field = None
        self.firebase_sync_service = firebase_sync_service
        
    
    def build_ui(self) -> ft.Container:
        """
        Construye la interfaz de usuario de configuración.
        
        Returns:
            Container con la vista de configuración.
        """
        # Toggle para modo oscuro/claro
        is_dark = self.page.theme_mode == ft.ThemeMode.DARK
        theme_switch = ft.Switch(
            label="Modo oscuro",
            value=is_dark,
            on_change=self._toggle_theme
        )
        
        # Campo para el nombre del usuario
        user_name = self.user_settings_service.get_user_name()
        is_dark = self.page.theme_mode == ft.ThemeMode.DARK
        icon_color = ft.Colors.RED_700 if not is_dark else ft.Colors.RED_500
        
        self.user_name_field = ft.TextField(
            label="Nombre de usuario",
            hint_text="Ingresa tu nombre",
            value=user_name,
            on_submit=self._save_user_name,
            suffix=ft.IconButton(
                icon=ft.Icons.SAVE,
                on_click=self._save_user_name,
                tooltip="Guardar nombre",
                icon_color=icon_color
            )
        )
        
        # Información de la aplicación
        app_info = ft.Container(
            content=ft.Column(
                [
                    ft.Text(
                        "⚙️ Configuración",
                        size=24,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.RED_700 if not is_dark else ft.Colors.RED_500
                    ),
                    ft.Divider(),
                    ft.Text("Usuario", size=16, weight=ft.FontWeight.BOLD,
                           color=ft.Colors.RED_800 if not is_dark else ft.Colors.RED_400),
                    self.user_name_field,
                    ft.Divider(),
                    ft.Text("Tema", size=16, weight=ft.FontWeight.BOLD,
                           color=ft.Colors.RED_800 if not is_dark else ft.Colors.RED_400),
                    theme_switch,
                    ft.Divider(),
                    self._build_firebase_section(),
                    ft.Divider(),
                    ft.Text(
                        "Aplicación de Productividad",
                        size=14,
                        weight=ft.FontWeight.BOLD
                    ),
                    ft.Text(
                        "Versión 1.0.0",
                        size=12,
                        color=ft.Colors.GREY
                    ),
                    ft.Text(
                        "Gestiona tus tareas, hábitos y metas",
                        size=12,
                        color=ft.Colors.GREY
                    )
                ],
                spacing=16,
                scroll=ft.ScrollMode.AUTO,
                expand=True
            ),
            padding=16,
            expand=True
        )
        
        # Vista principal
        return ft.Container(
            content=app_info,
            expand=True
        )
    
    def _save_user_name(self, e):
        """Guarda el nombre del usuario."""
        if self.user_name_field:
            name = self.user_name_field.value.strip()
            if name:
                self.user_settings_service.set_user_name(name)
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text("Nombre guardado correctamente"),
                    bgcolor=ft.Colors.GREEN
                )
                self.page.snack_bar.open = True
                self.page.update()
                # Notificar que el nombre cambió
                if self.on_name_changed:
                    self.on_name_changed()
    
    def _build_firebase_section(self) -> ft.Column:
        """Construye la sección de sincronización con Firebase."""
        is_dark = self.page.theme_mode == ft.ThemeMode.DARK
        btn_bg_color = ft.Colors.RED_700 if not is_dark else ft.Colors.RED_600
        btn_text_color = ft.Colors.WHITE
        
        # Estado de conexión
        is_logged_in = False
        status_text = "No conectado"
        status_color = ft.Colors.GREY
        
        if self.firebase_sync_service:
            is_logged_in = self.firebase_sync_service.is_logged_in()
            status_text = "Conectado" if is_logged_in else "No conectado"
            status_color = ft.Colors.GREEN if is_logged_in else ft.Colors.GREY
        
        status_display = ft.Text(
            status_text,
            size=12,
            color=status_color,
            weight=ft.FontWeight.BOLD
        )
        
        # Botón para abrir la página de sincronización
        sync_button = ft.ElevatedButton(
            "Abrir Sincronización Firebase",
            on_click=self._open_sync_view,
            icon=ft.Icons.SYNC,
            bgcolor=btn_bg_color,
            color=btn_text_color,
            expand=True
        )
        
        if self.firebase_sync_service is None:
            return ft.Column([
                ft.Text("Sincronización Firebase", size=16, weight=ft.FontWeight.BOLD,
                       color=ft.Colors.RED_800 if not is_dark else ft.Colors.RED_400),
                ft.Text(
                    "Firebase no está disponible. Instala pyrebase4.",
                    size=12,
                    color=ft.Colors.GREY
                )
            ], spacing=8)
        
        return ft.Column([
            ft.Text("Sincronización Firebase", size=16, weight=ft.FontWeight.BOLD,
                   color=ft.Colors.RED_800 if not is_dark else ft.Colors.RED_400),
            status_display,
            ft.Text(
                "Gestiona la sincronización de tus datos con Firebase",
                size=12,
                color=ft.Colors.GREY
            ),
            sync_button
        ], spacing=12)
    
    def _open_sync_view(self, e):
        """Abre la vista de sincronización de Firebase."""
        self.page.go("/firebase-sync")
    
    def _toggle_theme(self, e):
        """Alterna entre modo oscuro y claro."""
        self.page.theme_mode = (
            ft.ThemeMode.DARK if self.page.theme_mode == ft.ThemeMode.LIGHT
            else ft.ThemeMode.LIGHT
        )
        self.page.update()

