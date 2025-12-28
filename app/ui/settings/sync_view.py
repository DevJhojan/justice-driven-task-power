"""
Vista de sincronización con Firebase.
"""
import flet as ft

from app.services.firebase_sync_service import FirebaseSyncService


class FirebaseSyncView:
    """Vista de sincronización con Firebase."""
    
    def __init__(self, page: ft.Page, firebase_sync_service: FirebaseSyncService = None):
        """
        Inicializa la vista de sincronización.
        
        Args:
            page: Página de Flet.
            firebase_sync_service: Servicio de sincronización con Firebase.
        """
        self.page = page
        self.firebase_sync_service = firebase_sync_service
        
        # Campos de Firebase
        self.firebase_email_field = None
        self.firebase_password_field = None
        self.firebase_status_text = None
        self.login_button = None
        self.register_button = None
        self.logout_button = None
        self.sync_up_button = None
        self.sync_down_button = None
    
    def build_view(self) -> ft.View:
        """
        Construye la vista completa de sincronización.
        
        Returns:
            View con la interfaz de sincronización.
        """
        is_dark = self.page.theme_mode == ft.ThemeMode.DARK
        bg_color = ft.Colors.BLACK if is_dark else ft.Colors.WHITE
        title_color = ft.Colors.RED_700 if not is_dark else ft.Colors.RED_500
        icon_color = ft.Colors.RED_700 if not is_dark else ft.Colors.RED_500
        
        # Header con botón de volver y título
        header = ft.Container(
            content=ft.Row(
                [
                    ft.IconButton(
                        icon=ft.Icons.ARROW_BACK,
                        on_click=self._cancel,
                        icon_color=icon_color,
                        tooltip="Volver"
                    ),
                    ft.Text(
                        "Sincronización Firebase",
                        size=20,
                        weight=ft.FontWeight.BOLD,
                        color=title_color
                    ),
                ],
                spacing=8,
                alignment=ft.MainAxisAlignment.START
            ),
            padding=16,
            bgcolor=ft.Colors.SURFACE if is_dark else ft.Colors.WHITE,
            border=ft.border.only(
                bottom=ft.border.BorderSide(1, ft.Colors.OUTLINE)
            )
        )
        
        # Contenido principal con scroll
        content = ft.Container(
            content=self._build_sync_content(),
            padding=16,
            expand=True
        )
        
        # Crear la vista
        return ft.View(
            route="/firebase-sync",
            controls=[
                ft.Column(
                    [header, content],
                    spacing=0,
                    expand=True
                )
            ],
            bgcolor=bg_color
        )
    
    def _build_sync_content(self) -> ft.Column:
        """Construye el contenido de sincronización."""
        if self.firebase_sync_service is None:
            is_dark = self.page.theme_mode == ft.ThemeMode.DARK
            return ft.Column([
                ft.Text(
                    "Firebase no está disponible",
                    size=18,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.RED_800 if not is_dark else ft.Colors.RED_400
                ),
                ft.Text(
                    "Para usar la sincronización con Firebase, instala pyrebase4:",
                    size=14,
                    color=ft.Colors.GREY
                ),
                ft.Text(
                    "pip install pyrebase4",
                    size=12,
                    color=ft.Colors.GREY,
                    font_family="monospace"
                )
            ], spacing=16, scroll=ft.ScrollMode.AUTO, expand=True)
        
        is_logged_in = self.firebase_sync_service.is_logged_in()
        
        # Campos de autenticación
        self.firebase_email_field = ft.TextField(
            label="Email",
            hint_text="tu@email.com",
            disabled=is_logged_in,
            expand=True
        )
        
        self.firebase_password_field = ft.TextField(
            label="Contraseña",
            hint_text="••••••••",
            password=True,
            can_reveal_password=True,
            disabled=is_logged_in,
            expand=True
        )
        
        self.firebase_status_text = ft.Text(
            "No conectado" if not is_logged_in else "Conectado",
            size=14,
            weight=ft.FontWeight.BOLD,
            color=ft.Colors.GREEN if is_logged_in else ft.Colors.GREY
        )
        
        is_dark = self.page.theme_mode == ft.ThemeMode.DARK
        btn_bg_color = ft.Colors.RED_700 if not is_dark else ft.Colors.RED_600
        btn_text_color = ft.Colors.WHITE
        
        # Botones de autenticación
        self.login_button = ft.ElevatedButton(
            "Iniciar sesión",
            on_click=self._firebase_login,
            disabled=is_logged_in,
            bgcolor=btn_bg_color,
            color=btn_text_color,
            expand=True
        )
        
        self.register_button = ft.ElevatedButton(
            "Registrar",
            on_click=self._firebase_register,
            disabled=is_logged_in,
            bgcolor=btn_bg_color,
            color=btn_text_color,
            expand=True
        )
        
        self.logout_button = ft.ElevatedButton(
            "Cerrar sesión",
            on_click=self._firebase_logout,
            bgcolor=ft.Colors.RED,
            color=ft.Colors.WHITE,
            disabled=not is_logged_in,
            expand=True
        )
        
        # Botones de sincronización
        self.sync_up_button = ft.ElevatedButton(
            "Subir a Firebase",
            on_click=self._sync_to_firebase,
            icon=ft.Icons.UPLOAD,
            disabled=not is_logged_in,
            bgcolor=btn_bg_color,
            color=btn_text_color,
            expand=True
        )
        
        self.sync_down_button = ft.ElevatedButton(
            "Descargar de Firebase",
            on_click=self._sync_from_firebase,
            icon=ft.Icons.DOWNLOAD,
            disabled=not is_logged_in,
            bgcolor=btn_bg_color,
            color=btn_text_color,
            expand=True
        )
        
        return ft.Column([
            ft.Container(
                content=ft.Column([
                    ft.Text(
                        "Estado de Conexión",
                        size=18,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.RED_800 if not is_dark else ft.Colors.RED_400
                    ),
                    self.firebase_status_text,
                    ft.Divider(height=20),
                ], spacing=12),
                padding=16,
                bgcolor=ft.Colors.SURFACE if is_dark else ft.Colors.WHITE,
                border_radius=12,
                border=ft.border.all(1, ft.Colors.OUTLINE)
            ),
            
            ft.Container(
                content=ft.Column([
                    ft.Text(
                        "Autenticación",
                        size=18,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.RED_800 if not is_dark else ft.Colors.RED_400
                    ),
                    self.firebase_email_field,
                    self.firebase_password_field,
                    ft.Row([self.login_button, self.register_button], spacing=8) if not is_logged_in else ft.Container(),
                    self.logout_button if is_logged_in else ft.Container(),
                ], spacing=12),
                padding=16,
                bgcolor=ft.Colors.SURFACE if is_dark else ft.Colors.WHITE,
                border_radius=12,
                border=ft.border.all(1, ft.Colors.OUTLINE)
            ),
            
            ft.Container(
                content=ft.Column([
                    ft.Text(
                        "Sincronización",
                        size=18,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.RED_800 if not is_dark else ft.Colors.RED_400
                    ),
                    ft.Text(
                        "Sincroniza tus datos locales con Firebase",
                        size=12,
                        color=ft.Colors.GREY
                    ),
                    self.sync_up_button,
                    self.sync_down_button,
                ], spacing=12),
                padding=16,
                bgcolor=ft.Colors.SURFACE if is_dark else ft.Colors.WHITE,
                border_radius=12,
                border=ft.border.all(1, ft.Colors.OUTLINE)
            ),
            
            ft.Container(
                content=ft.Column([
                    ft.Text(
                        "ℹ️ Información",
                        size=16,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.RED_800 if not is_dark else ft.Colors.RED_400
                    ),
                    ft.Text(
                        "• La sincronización es bidireccional\n"
                        "• Los datos se sincronizan de forma granular (solo campos modificados)\n"
                        "• Subir a Firebase: envía tus datos locales a la nube\n"
                        "• Descargar de Firebase: trae los datos de la nube a tu dispositivo",
                        size=12,
                        color=ft.Colors.GREY
                    )
                ], spacing=8),
                padding=16,
                bgcolor=ft.Colors.SURFACE if is_dark else ft.Colors.WHITE,
                border_radius=12,
                border=ft.border.all(1, ft.Colors.OUTLINE)
            ),
        ], spacing=16, scroll=ft.ScrollMode.AUTO, expand=True)
    
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
                self._show_snackbar("Sesión iniciada correctamente. Sincronizando datos...", ft.Colors.GREEN)
                # Sincronizar automáticamente después del login
                try:
                    sync_result = self.firebase_sync_service.sync_to_firebase()
                    if sync_result.get("success"):
                        self._show_snackbar(f"Login exitoso. {sync_result.get('message', 'Datos sincronizados')}", ft.Colors.GREEN)
                    else:
                        self._show_snackbar(f"Login exitoso. Advertencia: {sync_result.get('message', '')}", ft.Colors.ORANGE)
                except Exception as sync_ex:
                    self._show_snackbar(f"Login exitoso. Error en sincronización: {str(sync_ex)}", ft.Colors.ORANGE)
                # Reconstruir UI para reflejar el estado de login
                self._rebuild_ui()
            else:
                self._show_snackbar("Error al iniciar sesión. Verifica tus credenciales.", ft.Colors.RED)
        except Exception as ex:
            error_msg = str(ex)
            if "INVALID_PASSWORD" in error_msg or "EMAIL_NOT_FOUND" in error_msg:
                self._show_snackbar("Credenciales incorrectas", ft.Colors.RED)
            elif "INVALID_EMAIL" in error_msg:
                self._show_snackbar("Email inválido", ft.Colors.RED)
            else:
                self._show_snackbar(f"Error: {error_msg}", ft.Colors.RED)
    
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
                self._show_snackbar("Usuario registrado correctamente. Sincronizando datos...", ft.Colors.GREEN)
                # Sincronizar automáticamente después del registro
                try:
                    sync_result = self.firebase_sync_service.sync_to_firebase()
                    if sync_result.get("success"):
                        self._show_snackbar(f"Registro exitoso. {sync_result.get('message', 'Datos sincronizados')}", ft.Colors.GREEN)
                    else:
                        self._show_snackbar(f"Registro exitoso. Advertencia: {sync_result.get('message', '')}", ft.Colors.ORANGE)
                except Exception as sync_ex:
                    self._show_snackbar(f"Registro exitoso. Error en sincronización: {str(sync_ex)}", ft.Colors.ORANGE)
                # Reconstruir UI para reflejar el estado de login
                self._rebuild_ui()
            else:
                self._show_snackbar("Error al registrar usuario", ft.Colors.RED)
        except Exception as ex:
            error_msg = str(ex)
            if "EMAIL_EXISTS" in error_msg:
                self._show_snackbar("El email ya está registrado", ft.Colors.RED)
            elif "INVALID_EMAIL" in error_msg:
                self._show_snackbar("Email inválido", ft.Colors.RED)
            elif "WEAK_PASSWORD" in error_msg:
                self._show_snackbar("La contraseña es muy débil", ft.Colors.RED)
            else:
                self._show_snackbar(f"Error: {error_msg}", ft.Colors.RED)
    
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
        """Reconstruye la UI después de cambios en Firebase."""
        # Reconstruir la vista completa
        if self.page.route == "/firebase-sync":
            # Limpiar la vista actual
            if len(self.page.views) > 0:
                self.page.views.pop()
            # Crear nueva vista
            new_view = self.build_view()
            self.page.views.append(new_view)
            self.page.update()
    
    def _cancel(self, e):
        """Cancela y regresa a configuración."""
        self.page.go("/")
    
    def _show_snackbar(self, message: str, color: ft.Colors = ft.Colors.BLUE):
        """Muestra un mensaje snackbar."""
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(message),
            bgcolor=color
        )
        self.page.snack_bar.open = True
        self.page.update()

