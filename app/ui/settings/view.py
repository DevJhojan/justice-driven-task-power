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
        
        # Campos de Firebase
        self.firebase_email_field = None
        self.firebase_password_field = None
        self.firebase_status_text = None
    
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
        if self.firebase_sync_service is None:
            is_dark = self.page.theme_mode == ft.ThemeMode.DARK
            return ft.Column([
                ft.Text("Sincronización Firebase", size=16, weight=ft.FontWeight.BOLD,
                       color=ft.Colors.RED_800 if not is_dark else ft.Colors.RED_400),
                ft.Text(
                    "Firebase no está disponible. Instala pyrebase4.",
                    size=12,
                    color=ft.Colors.GREY
                )
            ], spacing=8)
        
        is_logged_in = self.firebase_sync_service.is_logged_in()
        
        self.firebase_email_field = ft.TextField(
            label="Email",
            hint_text="tu@email.com",
            disabled=is_logged_in
        )
        
        self.firebase_password_field = ft.TextField(
            label="Contraseña",
            hint_text="••••••••",
            password=True,
            can_reveal_password=True,
            disabled=is_logged_in
        )
        
        self.firebase_status_text = ft.Text(
            "No conectado" if not is_logged_in else "Conectado",
            size=12,
            color=ft.Colors.GREEN if is_logged_in else ft.Colors.GREY
        )
        
        is_dark = self.page.theme_mode == ft.ThemeMode.DARK
        btn_bg_color = ft.Colors.RED_700 if not is_dark else ft.Colors.RED_600
        btn_text_color = ft.Colors.WHITE
        
        login_button = ft.ElevatedButton(
            "Iniciar sesión",
            on_click=self._firebase_login,
            disabled=is_logged_in,
            bgcolor=btn_bg_color,
            color=btn_text_color
        )
        
        register_button = ft.TextButton(
            "Registrar",
            on_click=self._firebase_register,
            disabled=is_logged_in,
            style=ft.ButtonStyle(color=btn_bg_color)
        )
        
        logout_button = ft.ElevatedButton(
            "Cerrar sesión",
            on_click=self._firebase_logout,
            bgcolor=ft.Colors.RED,
            color=ft.Colors.WHITE,
            disabled=not is_logged_in
        )
        
        sync_up_button = ft.ElevatedButton(
            "Subir a Firebase",
            on_click=self._sync_to_firebase,
            icon=ft.Icons.UPLOAD,
            disabled=not is_logged_in,
            bgcolor=btn_bg_color,
            color=btn_text_color
        )
        
        sync_down_button = ft.ElevatedButton(
            "Descargar de Firebase",
            on_click=self._sync_from_firebase,
            icon=ft.Icons.DOWNLOAD,
            disabled=not is_logged_in,
            bgcolor=btn_bg_color,
            color=btn_text_color
        )
        
        return ft.Column([
            ft.Text("Sincronización Firebase", size=16, weight=ft.FontWeight.BOLD),
            self.firebase_status_text,
            self.firebase_email_field,
            self.firebase_password_field,
            ft.Row([login_button, register_button], spacing=8),
            logout_button,
            ft.Divider(height=20),
            sync_up_button,
            sync_down_button
        ], spacing=12)
    
    def _firebase_login(self, e):
        """Inicia sesión en Firebase."""
        if not self.firebase_sync_service or not self.firebase_email_field or not self.firebase_password_field:
            return
        
        email = self.firebase_email_field.value.strip()
        password = self.firebase_password_field.value.strip()
        
        if not email or not password:
            self._show_snackbar("Por favor completa email y contraseña", ft.Colors.RED)
            return
        
        try:
            success = self.firebase_sync_service.login(email, password)
            if success:
                self._show_snackbar("Sesión iniciada correctamente", ft.Colors.GREEN)
                self._rebuild_ui()
            else:
                self._show_snackbar("Error al iniciar sesión", ft.Colors.RED)
        except Exception as ex:
            self._show_snackbar(f"Error: {str(ex)}", ft.Colors.RED)
    
    def _firebase_register(self, e):
        """Registra un nuevo usuario en Firebase."""
        if not self.firebase_sync_service or not self.firebase_email_field or not self.firebase_password_field:
            return
        
        email = self.firebase_email_field.value.strip()
        password = self.firebase_password_field.value.strip()
        
        if not email or not password:
            self._show_snackbar("Por favor completa email y contraseña", ft.Colors.RED)
            return
        
        if len(password) < 6:
            self._show_snackbar("La contraseña debe tener al menos 6 caracteres", ft.Colors.RED)
            return
        
        try:
            success = self.firebase_sync_service.register(email, password)
            if success:
                self._show_snackbar("Usuario registrado correctamente", ft.Colors.GREEN)
                self._rebuild_ui()
            else:
                self._show_snackbar("Error al registrar usuario", ft.Colors.RED)
        except Exception as ex:
            self._show_snackbar(f"Error: {str(ex)}", ft.Colors.RED)
    
    def _firebase_logout(self, e):
        """Cierra sesión en Firebase."""
        if self.firebase_sync_service:
            self.firebase_sync_service.logout()
            self._show_snackbar("Sesión cerrada", ft.Colors.GREEN)
            self._rebuild_ui()
    
    def _sync_to_firebase(self, e):
        """Sincroniza datos locales a Firebase."""
        if not self.firebase_sync_service:
            return
        
        try:
            result = self.firebase_sync_service.sync_to_firebase()
            if result["success"]:
                self._show_snackbar(result["message"], ft.Colors.GREEN)
            else:
                self._show_snackbar(result["message"], ft.Colors.RED)
        except Exception as ex:
            self._show_snackbar(f"Error: {str(ex)}", ft.Colors.RED)
    
    def _sync_from_firebase(self, e):
        """Sincroniza datos de Firebase a local."""
        if not self.firebase_sync_service:
            return
        
        try:
            result = self.firebase_sync_service.sync_from_firebase()
            if result["success"]:
                self._show_snackbar(result["message"], ft.Colors.GREEN)
            else:
                self._show_snackbar(result["message"], ft.Colors.RED)
        except Exception as ex:
            self._show_snackbar(f"Error: {str(ex)}", ft.Colors.RED)
    
    def _rebuild_ui(self):
        """Reconstruye la UI de configuración."""
        # Esto se manejará desde home_view cuando se navegue de vuelta
        self.page.update()
    
    def _show_snackbar(self, message: str, color: ft.Colors = ft.Colors.BLUE):
        """Muestra un mensaje snackbar."""
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(message),
            bgcolor=color
        )
        self.page.snack_bar.open = True
        self.page.update()
    
    def _toggle_theme(self, e):
        """Alterna entre modo oscuro y claro."""
        self.page.theme_mode = (
            ft.ThemeMode.DARK if self.page.theme_mode == ft.ThemeMode.LIGHT
            else ft.ThemeMode.LIGHT
        )
        self.page.update()

