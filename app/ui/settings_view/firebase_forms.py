"""
Módulo para formularios y páginas de Firebase (login, registro, sincronización).
"""
import flet as ft
from app.services.sync_service import SyncService
from .utils import copy_to_clipboard


def show_auth_page(
    page: ft.Page,
    sync_service: SyncService,
    firebase_auth_service,
    mode: str = "login",
    on_go_back: callable = None,
    on_success: callable = None
):
    """
    Muestra una página completa de autenticación (login o registro).
    
    Args:
        page: Página de Flet.
        sync_service: Servicio de sincronización.
        firebase_auth_service: Servicio de autenticación Firebase.
        mode: "login" o "register".
        on_go_back: Callback para volver.
        on_success: Callback cuando la autenticación es exitosa.
    """
    is_login = mode == "login"
    
    # Campos del formulario
    email_field = ft.TextField(
        label="Correo electrónico",
        hint_text="tu@email.com",
        autofocus=True,
        keyboard_type=ft.KeyboardType.EMAIL,
        expand=True
    )
    
    password_field = ft.TextField(
        label="Contraseña",
        hint_text="Mínimo 6 caracteres",
        password=True,
        can_reveal_password=True,
        expand=True
    )
    
    confirm_password_field = ft.TextField(
        label="Confirmar contraseña",
        hint_text="Repite la contraseña",
        password=True,
        can_reveal_password=True,
        expand=True,
        visible=not is_login  # Solo visible en modo registro
    )
    
    error_text = ft.Text("", color=ft.Colors.RED, size=12, selectable=True, weight=ft.FontWeight.W_500)
    loading_indicator = ft.ProgressRing(visible=False)
    
    # Botón para copiar el error al portapapeles
    copy_error_button = ft.IconButton(
        icon=ft.Icons.COPY,
        tooltip="Copiar error al portapapeles",
        icon_size=18,
        icon_color=ft.Colors.RED,
        on_click=lambda e: copy_to_clipboard(page, error_text.value, "✓ Error copiado al portapapeles")
    )
    
    # Contenedor del error (se mostrará cuando haya error)
    error_container = ft.Container(
        content=ft.Row(
            [
                ft.Container(
                    content=error_text,
                    expand=True,
                    padding=ft.padding.only(right=5)
                ),
                copy_error_button
            ],
            spacing=5,
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER
        ),
        visible=False,
        bgcolor=ft.Colors.RED_50 if page.theme_mode != ft.ThemeMode.DARK else ft.Colors.RED_900,
        padding=10,
        border_radius=5,
        border=ft.border.all(1, ft.Colors.RED_300 if page.theme_mode != ft.ThemeMode.DARK else ft.Colors.RED_700)
    )
    
    # Botón de submit (se define antes para poder usarlo en submit_auth)
    submit_button = ft.ElevatedButton(
        text="Iniciar sesión" if is_login else "Registrarse",
        icon=ft.Icons.LOGIN if is_login else ft.Icons.PERSON_ADD,
        expand=True,
        height=50
    )
    
    def submit_auth(e):
        """Procesa el inicio de sesión o registro."""
        email = email_field.value.strip()
        password = password_field.value
        confirm_password = confirm_password_field.value if not is_login else ""
        
        # Validaciones
        if not email:
            error_text.value = "El correo electrónico es requerido"
            error_container.visible = True
            error_text.update()
            error_container.update()
            return
        
        if not password:
            error_text.value = "La contraseña es requerida"
            error_container.visible = True
            error_text.update()
            error_container.update()
            return
        
        if not is_login:
            if len(password) < 6:
                error_text.value = "La contraseña debe tener al menos 6 caracteres"
                error_container.visible = True
                error_text.update()
                error_container.update()
                return
            
            if password != confirm_password:
                error_text.value = "Las contraseñas no coinciden"
                error_container.visible = True
                error_text.update()
                error_container.update()
                return
        
        # Mostrar indicador de carga
        error_container.visible = False
        loading_indicator.visible = True
        submit_button.disabled = True
        page.update()
        
        try:
            if not firebase_auth_service:
                raise RuntimeError("Firebase no está disponible")
            
            # Ejecutar login o registro
            if is_login:
                result = firebase_auth_service.login(email, password)
                success_message = f"✓ Sesión iniciada: {result.get('user', {}).get('email')}"
            else:
                result = firebase_auth_service.register(email, password)
                success_message = f"✓ Usuario registrado: {result.get('user', {}).get('email')}"
            
            # Guardar estado de sincronización
            user = result.get('user', {})
            sync_service.update_sync_settings(
                is_authenticated=True,
                email=user.get('email'),
                user_id=user.get('uid')
            )
            
            # Volver a configuración
            if on_go_back:
                on_go_back()
            
            # Mostrar éxito
            page.snack_bar = ft.SnackBar(
                content=ft.Text(success_message),
                bgcolor=ft.Colors.GREEN,
                duration=3000
            )
            page.snack_bar.open = True
            
            # Llamar callback de éxito
            if on_success:
                on_success()
            
        except ValueError as ve:
            error_text.value = str(ve)
            error_container.visible = True
            loading_indicator.visible = False
            submit_button.disabled = False
            error_text.update()
            error_container.update()
            page.update()
        except Exception as ex:
            error_text.value = f"Error: {str(ex)}"
            error_container.visible = True
            loading_indicator.visible = False
            submit_button.disabled = False
            error_text.update()
            error_container.update()
            page.update()
    
    # Asignar el handler al botón
    submit_button.on_click = submit_auth
    
    switch_button = ft.TextButton(
        text="¿No tienes cuenta? Regístrate" if is_login else "¿Ya tienes cuenta? Inicia sesión",
        on_click=lambda e: show_auth_page(page, sync_service, firebase_auth_service, "register" if is_login else "login", on_go_back, on_success)
    )
    
    # Construir la vista
    auth_view = ft.View(
        route="/auth",
        appbar=ft.AppBar(
            title=ft.Text("Iniciar sesión" if is_login else "Registrarse"),
            leading=ft.IconButton(
                icon=ft.Icons.ARROW_BACK,
                on_click=lambda e: on_go_back() if on_go_back else None
            ),
            bgcolor=page.theme.primary_color if page.theme else ft.Colors.BLUE_700
        ),
        padding=20,
        scroll=ft.ScrollMode.AUTO,
        controls=[
            ft.Container(
                content=ft.Column(
                    [
                        ft.Text(
                            "Inicia sesión para sincronizar tus datos" if is_login else "Crea una cuenta para sincronizar tus datos",
                            size=16,
                            weight=ft.FontWeight.BOLD,
                            text_align=ft.TextAlign.CENTER
                        ),
                        ft.Divider(height=20),
                        email_field,
                        password_field,
                        confirm_password_field,
                        error_container,
                        ft.Row(
                            [loading_indicator, submit_button],
                            spacing=10,
                            alignment=ft.MainAxisAlignment.CENTER
                        ),
                        ft.Divider(height=20),
                        switch_button
                    ],
                    spacing=15,
                    horizontal_alignment=ft.CrossAxisAlignment.STRETCH
                ),
                padding=20,
                border_radius=10,
                bgcolor=ft.Colors.GREY_900 if page.theme_mode == ft.ThemeMode.DARK else ft.Colors.GREY_100
            )
        ]
    )
    
    page.views.append(auth_view)
    page.go("/auth")
    page.update()

