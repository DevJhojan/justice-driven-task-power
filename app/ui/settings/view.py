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
        self._firebase_login_visible = False  # Controla si el formulario de login está visible
        self.firebase_email_field = None
        self.firebase_password_field = None
        
    
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
        title_color = ft.Colors.RED_800 if not is_dark else ft.Colors.RED_400
        
        if self.firebase_sync_service is None:
            return ft.Column([
                ft.Text("Sincronizar en la nube", size=16, weight=ft.FontWeight.BOLD,
                       color=title_color),
                ft.Text(
                    "Firebase no está disponible. Instala pyrebase4.",
                    size=12,
                    color=ft.Colors.GREY
                )
            ], spacing=8)
        
        # Estado de conexión
        is_logged_in = self.firebase_sync_service.is_logged_in()
        firebase_email = self.user_settings_service.get_firebase_email() if is_logged_in else None
        
        # Botón para sincronizar (mostrar/ocultar formulario)
        sync_button_text = "Sincronizar" if not is_logged_in else "Sincronizado"
        sync_button = ft.ElevatedButton(
            sync_button_text,
            on_click=self._toggle_firebase_sync,
            icon=ft.Icons.SYNC if not is_logged_in else ft.Icons.CHECK_CIRCLE,
            bgcolor=btn_bg_color,
            color=btn_text_color,
            expand=True
        )
        
        # Estado de conexión
        if is_logged_in:
            status_display = ft.Text(
                f"✅ Conectado como: {firebase_email or 'Usuario'}",
                size=12,
                color=ft.Colors.GREEN,
                weight=ft.FontWeight.BOLD
            )
        else:
            status_display = ft.Text(
                "❌ No conectado",
                size=12,
                color=ft.Colors.GREY,
                weight=ft.FontWeight.BOLD
            )
        
        # Formulario de login (solo visible si no está logueado y _firebase_login_visible es True)
        login_form = None
        if not is_logged_in and self._firebase_login_visible:
            # Crear campos si no existen
            if self.firebase_email_field is None:
                self.firebase_email_field = ft.TextField(
                    label="Email",
                    hint_text="tu@email.com",
                    expand=True
                )
            if self.firebase_password_field is None:
                self.firebase_password_field = ft.TextField(
                    label="Contraseña",
                    hint_text="••••••••",
                    password=True,
                    can_reveal_password=True,
                    expand=True
                )
            
            login_form = ft.Container(
                content=ft.Column([
                    ft.Text(
                        "Iniciar sesión en Firebase",
                        size=14,
                        weight=ft.FontWeight.BOLD,
                        color=title_color
                    ),
                    self.firebase_email_field,
                    self.firebase_password_field,
                    ft.Row([
                        ft.ElevatedButton(
                            "Iniciar sesión",
                            on_click=self._firebase_login,
                            bgcolor=btn_bg_color,
                            color=btn_text_color,
                            expand=True
                        ),
                        ft.ElevatedButton(
                            "Registrar",
                            on_click=self._firebase_register,
                            bgcolor=btn_bg_color,
                            color=btn_text_color,
                            expand=True
                        ),
                    ], spacing=8)
                ], spacing=12),
                padding=12,
                bgcolor=ft.Colors.SURFACE if is_dark else ft.Colors.GREY_100,
                border_radius=8,
                border=ft.border.all(1, ft.Colors.OUTLINE),
                margin=ft.margin.only(top=8)
            )
        
        # Botón de cerrar sesión (solo si está logueado)
        logout_button = None
        if is_logged_in:
            logout_button = ft.ElevatedButton(
                "Cerrar sesión",
                on_click=self._firebase_logout,
                bgcolor=ft.Colors.RED,
                color=ft.Colors.WHITE,
                expand=True,
                icon=ft.Icons.LOGOUT
            )
        
        # Construir la columna
        items = [
            ft.Text("Sincronizar en la nube", size=16, weight=ft.FontWeight.BOLD,
                   color=title_color),
            status_display,
            sync_button
        ]
        
        if login_form:
            items.append(login_form)
        
        if logout_button:
            items.append(logout_button)
        
        return ft.Column(items, spacing=12)
    
    def _toggle_firebase_sync(self, e):
        """Muestra u oculta el formulario de sincronización de Firebase."""
        if not self.firebase_sync_service:
            return
        
        # Si ya está logueado, no hacer nada
        if self.firebase_sync_service.is_logged_in():
            return
        
        # Alternar visibilidad del formulario
        self._firebase_login_visible = not self._firebase_login_visible
        # Reconstruir la UI
        if hasattr(self.page, '_home_view_ref'):
            home_view = self.page._home_view_ref
            home_view._build_ui()
        else:
            self.page.update()
    
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
                # Sincronizar automáticamente después del login
                try:
                    sync_result = self.firebase_sync_service.sync_to_firebase()
                    if sync_result.get("success"):
                        self._show_snackbar("✅ Login exitoso. Sincronización activada", ft.Colors.GREEN)
                    else:
                        self._show_snackbar(f"⚠️ Login exitoso. Advertencia: {sync_result.get('message', '')}", ft.Colors.ORANGE)
                except Exception as sync_ex:
                    self._show_snackbar(f"⚠️ Login exitoso. Error en sincronización: {str(sync_ex)}", ft.Colors.ORANGE)
                
                # Ocultar formulario y limpiar campos
                self._firebase_login_visible = False
                if self.firebase_email_field:
                    self.firebase_email_field.value = ""
                if self.firebase_password_field:
                    self.firebase_password_field.value = ""
                
                # Reconstruir UI
                if hasattr(self.page, '_home_view_ref'):
                    home_view = self.page._home_view_ref
                    home_view._build_ui()
                else:
                    self.page.update()
            else:
                self._show_snackbar("❌ Error al iniciar sesión. Verifica tus credenciales.", ft.Colors.RED)
        except Exception as ex:
            error_msg = str(ex)
            if "INVALID_PASSWORD" in error_msg or "EMAIL_NOT_FOUND" in error_msg:
                self._show_snackbar("❌ Credenciales incorrectas", ft.Colors.RED)
            elif "INVALID_EMAIL" in error_msg:
                self._show_snackbar("❌ Email inválido", ft.Colors.RED)
            else:
                self._show_snackbar(f"❌ Error: {error_msg}", ft.Colors.RED)
    
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
            self._show_snackbar("❌ La contraseña debe tener al menos 6 caracteres", ft.Colors.RED)
            return
        
        try:
            success = self.firebase_sync_service.register(email, password)
            if success:
                # Sincronizar automáticamente después del registro
                try:
                    sync_result = self.firebase_sync_service.sync_to_firebase()
                    if sync_result.get("success"):
                        self._show_snackbar("✅ Registro exitoso. Sincronización activada", ft.Colors.GREEN)
                    else:
                        self._show_snackbar(f"⚠️ Registro exitoso. Advertencia: {sync_result.get('message', '')}", ft.Colors.ORANGE)
                except Exception as sync_ex:
                    self._show_snackbar(f"⚠️ Registro exitoso. Error en sincronización: {str(sync_ex)}", ft.Colors.ORANGE)
                
                # Ocultar formulario y limpiar campos
                self._firebase_login_visible = False
                if self.firebase_email_field:
                    self.firebase_email_field.value = ""
                if self.firebase_password_field:
                    self.firebase_password_field.value = ""
                
                # Reconstruir UI
                if hasattr(self.page, '_home_view_ref'):
                    home_view = self.page._home_view_ref
                    home_view._build_ui()
                else:
                    self.page.update()
            else:
                self._show_snackbar("❌ Error al registrar usuario", ft.Colors.RED)
        except Exception as ex:
            error_msg = str(ex)
            if "EMAIL_EXISTS" in error_msg:
                self._show_snackbar("❌ El email ya está registrado", ft.Colors.RED)
            elif "INVALID_EMAIL" in error_msg:
                self._show_snackbar("❌ Email inválido", ft.Colors.RED)
            elif "WEAK_PASSWORD" in error_msg:
                self._show_snackbar("❌ La contraseña es muy débil", ft.Colors.RED)
            else:
                self._show_snackbar(f"❌ Error: {error_msg}", ft.Colors.RED)
    
    def _firebase_logout(self, e):
        """Cierra sesión en Firebase."""
        if self.firebase_sync_service:
            self.firebase_sync_service.logout()
            self._show_snackbar("Sesión cerrada", ft.Colors.GREEN)
            # Reconstruir UI
            if hasattr(self.page, '_home_view_ref'):
                home_view = self.page._home_view_ref
                home_view._build_ui()
            else:
                self.page.update()
    
    def _show_snackbar(self, message: str, color: ft.Colors = ft.Colors.BLUE):
        """Muestra un mensaje snackbar."""
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(message),
            bgcolor=color
        )
        self.page.snack_bar.open = True
        self.page.update()
    
    def _open_sync_view(self, e):
        """Abre la vista de sincronización de Firebase."""
        self.page.go("/firebase-sync")
    
    def _toggle_theme(self, e):
        """Alterna entre modo oscuro y claro."""
        new_theme_mode = (
            ft.ThemeMode.DARK if self.page.theme_mode == ft.ThemeMode.LIGHT
            else ft.ThemeMode.LIGHT
        )
        self.page.theme_mode = new_theme_mode
        
        # Guardar el tema en la base de datos
        theme_str = "dark" if new_theme_mode == ft.ThemeMode.DARK else "light"
        self.user_settings_service.set_theme(theme_str)
        
        self.page.update()

