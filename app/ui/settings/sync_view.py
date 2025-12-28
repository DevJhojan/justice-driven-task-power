"""
Vista de sincronización con Firebase.
"""
import flet as ft
import traceback

# Intentar importar pyperclip, si no está disponible usar método alternativo
try:
    import pyperclip
    HAS_PYPERCLIP = True
except ImportError:
    HAS_PYPERCLIP = False

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
        
        # Estado del resultado de sincronización
        self.last_sync_result = None  # {"type": "upload"/"download", "success": bool, "message": str, "error": str}
        self.sync_result_container = None
    
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
                        "Sincronizar en la nube",
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
            "Exportar",
            on_click=self._sync_to_firebase,
            icon=ft.Icons.UPLOAD,
            disabled=not is_logged_in,
            bgcolor=btn_bg_color,
            color=btn_text_color,
            expand=True
        )
        
        self.sync_down_button = ft.ElevatedButton(
            "Importar",
            on_click=self._sync_from_firebase,
            icon=ft.Icons.DOWNLOAD,
            disabled=not is_logged_in,
            bgcolor=btn_bg_color,
            color=btn_text_color,
            expand=True
        )
        
        # Construir lista de items
        items = [
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
        ]
        
        # Agregar contenedor de resultado si existe
        result_container = self._build_sync_result_container()
        if result_container.visible:
            items.append(result_container)
        
        # Agregar información
        items.append(
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
                        "• Exportar: envía tus datos locales a la nube\n"
                        "• Importar: trae los datos de la nube a tu dispositivo",
                        size=12,
                        color=ft.Colors.GREY
                    )
                ], spacing=8),
                padding=16,
                bgcolor=ft.Colors.SURFACE if is_dark else ft.Colors.WHITE,
                border_radius=12,
                border=ft.border.all(1, ft.Colors.OUTLINE)
            )
        )
        
        return ft.Column(items, spacing=16, scroll=ft.ScrollMode.AUTO, expand=True)
    
    def _build_sync_result_container(self) -> ft.Container:
        """Construye el contenedor para mostrar el resultado de la sincronización."""
        is_dark = self.page.theme_mode == ft.ThemeMode.DARK
        bg_color = ft.Colors.SURFACE if is_dark else ft.Colors.WHITE
        title_color = ft.Colors.RED_800 if not is_dark else ft.Colors.RED_400
        
        if not self.last_sync_result:
            # Si no hay resultado, retornar contenedor vacío pero ocupando espacio mínimo
            return ft.Container(
                content=ft.Column([]),
                padding=0,
                visible=False,
                height=0
            )
        
        result = self.last_sync_result
        is_success = result.get("success", False)
        message = result.get("message", "")
        error = result.get("error", "")
        sync_type = result.get("type", "upload")
        
        # Color y icono según el resultado
        if is_success:
            status_color = ft.Colors.GREEN
            status_icon = ft.Icons.CHECK_CIRCLE
            status_text = "✅ Éxito"
            title_text = f"{'Exportación' if sync_type == 'upload' else 'Importación'} - Éxito"
        else:
            status_color = ft.Colors.RED_700 if not is_dark else ft.Colors.RED_400
            status_icon = ft.Icons.ERROR
            status_text = "❌ Error"
            title_text = f"{'Exportación' if sync_type == 'upload' else 'Importación'} - Error"
        
        # Contenido del mensaje
        content_items = [
            ft.Row([
                ft.Icon(status_icon, color=status_color, size=24),
                ft.Text(
                    status_text,
                    size=16,
                    weight=ft.FontWeight.BOLD,
                    color=status_color
                )
            ], spacing=8),
            ft.Divider(height=10),
            ft.Text(
                message,
                size=14,
                color=ft.Colors.GREY if is_dark else ft.Colors.GREY_700
            )
        ]
        
        # Si hay error, mostrar el error completo y botón de copiar
        if not is_success and error:
            error_text = ft.Text(
                error,
                size=12,
                color=ft.Colors.RED_700 if not is_dark else ft.Colors.RED_400,
                selectable=True,
                font_family="monospace"
            )
            
            copy_button = ft.ElevatedButton(
                "Copiar Error",
                icon=ft.Icons.COPY,
                on_click=lambda e: self._copy_error(error),
                bgcolor=ft.Colors.RED_700 if not is_dark else ft.Colors.RED_600,
                color=ft.Colors.WHITE
            )
            
            content_items.extend([
                ft.Divider(height=10),
                ft.Text(
                    "Detalles del error:",
                    size=12,
                    weight=ft.FontWeight.BOLD,
                    color=status_color
                ),
                ft.Container(
                    content=error_text,
                    padding=12,
                    bgcolor=ft.Colors.BLACK if is_dark else ft.Colors.GREY_100,
                    border_radius=8,
                    border=ft.border.all(1, status_color)
                ),
                copy_button
            ])
        
        self.sync_result_container = ft.Container(
            content=ft.Column(content_items, spacing=12),
            padding=16,
            bgcolor=bg_color,
            border_radius=12,
            border=ft.border.all(2, status_color),
            visible=True
        )
        
        return self.sync_result_container
    
    def _copy_error(self, error_text: str):
        """Copia el error al portapapeles."""
        try:
            if HAS_PYPERCLIP:
                pyperclip.copy(error_text)
            else:
                # Usar métodos del sistema operativo
                import subprocess
                import sys
                if sys.platform == "linux":
                    try:
                        subprocess.run(["xclip", "-selection", "clipboard"], input=error_text.encode(), check=True)
                    except (subprocess.CalledProcessError, FileNotFoundError):
                        try:
                            subprocess.run(["xsel", "--clipboard", "--input"], input=error_text.encode(), check=True)
                        except (subprocess.CalledProcessError, FileNotFoundError):
                            raise Exception("No se encontró xclip ni xsel")
                elif sys.platform == "darwin":
                    subprocess.run(["pbcopy"], input=error_text.encode(), check=True)
                elif sys.platform == "win32":
                    subprocess.run(["clip"], input=error_text.encode(), check=True, shell=True)
                else:
                    raise Exception(f"Plataforma no soportada: {sys.platform}")
            
            self._show_snackbar("Error copiado al portapapeles", ft.Colors.GREEN)
        except Exception as ex:
            self._show_snackbar(f"No se pudo copiar el error: {str(ex)}", ft.Colors.RED)
    
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
            # Guardar resultado para mostrarlo en la UI
            self.last_sync_result = {
                "type": "upload",
                "success": result.get("success", False),
                "message": result.get("message", "Sincronización completada"),
                "error": "" if result.get("success") else result.get("message", "Error desconocido")
            }
            self._rebuild_ui()
        except Exception as ex:
            error_msg = str(ex)
            error_traceback = "".join(traceback.format_exception(type(ex), ex, ex.__traceback__))
            full_error = f"{error_msg}\n\n{error_traceback}"
            
            # Guardar resultado de error
            self.last_sync_result = {
                "type": "upload",
                "success": False,
                "message": "Error al sincronizar datos",
                "error": full_error
            }
            self._rebuild_ui()
    
    def _sync_from_firebase(self, e):
        """Sincroniza datos de Firebase a local."""
        if not self.firebase_sync_service:
            return
        
        try:
            result = self.firebase_sync_service.sync_from_firebase()
            # Guardar resultado para mostrarlo en la UI
            self.last_sync_result = {
                "type": "download",
                "success": result.get("success", False),
                "message": result.get("message", "Sincronización completada"),
                "error": "" if result.get("success") else result.get("message", "Error desconocido")
            }
            self._rebuild_ui()
        except Exception as ex:
            error_msg = str(ex)
            error_traceback = "".join(traceback.format_exception(type(ex), ex, ex.__traceback__))
            full_error = f"{error_msg}\n\n{error_traceback}"
            
            # Guardar resultado de error
            self.last_sync_result = {
                "type": "download",
                "success": False,
                "message": "Error al sincronizar datos",
                "error": full_error
            }
            self._rebuild_ui()
    
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

