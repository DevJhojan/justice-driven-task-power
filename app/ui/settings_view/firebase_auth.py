"""
Módulo para la autenticación con Firebase.
"""
import flet as ft
from app.services.sync_service import SyncService
from .utils import copy_to_clipboard


def build_firebase_auth_section(
    page: ft.Page,
    sync_service: SyncService,
    firebase_auth_service,
    preview_color,
    is_dark: bool,
    on_login_click: callable,
    on_register_click: callable,
    on_sync_click: callable,
    on_logout_click: callable
) -> ft.Column:
    """
    Construye la sección de autenticación y sincronización con Firebase.
    
    Args:
        page: Página de Flet.
        sync_service: Servicio de sincronización.
        firebase_auth_service: Servicio de autenticación Firebase.
        preview_color: Color principal de la aplicación.
        is_dark: Si el tema es oscuro.
        on_login_click: Callback para iniciar sesión.
        on_register_click: Callback para registrarse.
        on_sync_click: Callback para sincronizar.
        on_logout_click: Callback para cerrar sesión.
    
    Returns:
        Column con la sección de autenticación.
    """
    sync_settings = sync_service.get_sync_settings()
    is_authenticated = sync_settings.is_authenticated
    
    if is_authenticated:
        # Usuario autenticado: mostrar información y botón de sincronización
        user_email = sync_settings.email or "Usuario"
        
        sync_button = ft.ElevatedButton(
            text="Sincronizar",
            icon=ft.Icons.CLOUD_SYNC,
            on_click=on_sync_click,
            bgcolor=preview_color,
            color=ft.Colors.WHITE,
        )
        
        logout_button = ft.OutlinedButton(
            text="Cerrar sesión",
            icon=ft.Icons.LOGOUT,
            on_click=on_logout_click,
            style=ft.ButtonStyle(color=ft.Colors.RED)
        )
        
        return ft.Column(
            [
                ft.Text(
                    f"✓ Conectado como: {user_email}",
                    size=14,
                    color=ft.Colors.GREEN if not is_dark else ft.Colors.GREEN_300,
                    weight=ft.FontWeight.BOLD
                ),
                ft.Text(
                    "Tus datos se guardan localmente y se sincronizan en la nube cuando lo solicites.",
                    size=12,
                    color=ft.Colors.GREY_600 if not is_dark else ft.Colors.GREY_400
                ),
                ft.Row(
                    [sync_button, logout_button],
                    spacing=8,
                    alignment=ft.MainAxisAlignment.START
                )
            ],
            spacing=8
        )
    else:
        # Usuario no autenticado: mostrar botones de login y registro
        login_button = ft.ElevatedButton(
            text="Iniciar sesión",
            icon=ft.Icons.LOGIN,
            on_click=on_login_click,
            bgcolor=preview_color,
            color=ft.Colors.WHITE,
        )
        
        register_button = ft.OutlinedButton(
            text="Registrarse",
            icon=ft.Icons.PERSON_ADD,
            on_click=on_register_click,
            style=ft.ButtonStyle(color=preview_color)
        )
        
        return ft.Column(
            [
                ft.Row(
                    [login_button, register_button],
                    spacing=8,
                    alignment=ft.MainAxisAlignment.START
                ),
                ft.Text(
                    "Crea una cuenta o inicia sesión para sincronizar tus datos en la nube.",
                    size=12,
                    color=ft.Colors.GREY_600 if not is_dark else ft.Colors.GREY_400,
                    italic=True
                )
            ],
            spacing=8
        )


def build_firebase_sync_section(
    page: ft.Page,
    sync_service: SyncService,
    firebase_auth_service,
    preview_color,
    is_dark: bool,
    on_login_click: callable,
    on_register_click: callable,
    on_sync_click: callable,
    on_logout_click: callable,
    firebase_available: bool
) -> list:
    """
    Construye la sección de autenticación y sincronización con Firebase.
    Retorna una lista de widgets. Si hay error, retorna lista vacía (no muestra nada).
    
    Args:
        page: Página de Flet.
        sync_service: Servicio de sincronización.
        firebase_auth_service: Servicio de autenticación Firebase.
        preview_color: Color principal de la aplicación.
        is_dark: Si el tema es oscuro.
        on_login_click: Callback para iniciar sesión.
        on_register_click: Callback para registrarse.
        on_sync_click: Callback para sincronizar.
        on_logout_click: Callback para cerrar sesión.
        firebase_available: Si Firebase está disponible.
    
    Returns:
        Lista de controles para la sección de Firebase.
    """
    if not firebase_available or not firebase_auth_service:
        # Si hay error, NO mostrar la sección de autenticación
        return []
    
    # Si Firebase está disponible, mostrar la sección completa
    return [
        ft.Text(
            "Autenticación y Sincronización",
            size=18,
            weight=ft.FontWeight.BOLD,
            color=preview_color
        ),
        ft.Text(
            "Autentícate con Firebase para sincronizar tus datos en la nube. "
            "Tus datos se guardan localmente y se sincronizan cuando lo solicites.",
            size=14,
            color=ft.Colors.GREY_600
        ),
        build_firebase_auth_section(
            page,
            sync_service,
            firebase_auth_service,
            preview_color,
            is_dark,
            on_login_click,
            on_register_click,
            on_sync_click,
            on_logout_click
        ),
    ]


def get_error_copy_button(
    page: ft.Page,
    preview_color,
    is_dark: bool,
    firebase_available: bool,
    firebase_import_error: str = "",
    on_copy_error: callable = None
) -> list:
    """
    Retorna un botón discreto para copiar el error si Firebase no está disponible.
    Si Firebase está disponible, retorna lista vacía.
    
    Args:
        page: Página de Flet.
        preview_color: Color principal de la aplicación.
        is_dark: Si el tema es oscuro.
        firebase_available: Si Firebase está disponible.
        firebase_import_error: Mensaje de error de importación de Firebase.
        on_copy_error: Callback para copiar error (opcional).
    
    Returns:
        Lista con el botón de copiar error o lista vacía.
    """
    if firebase_available:
        return []
    
    # Construir el mensaje de error completo
    error_msg = (
        "Firebase no está disponible porque el módulo 'requests' no se empaquetó correctamente en el APK.\n\n"
        "Solución:\n"
        "1. Reconstruye el APK ejecutando:\n"
        "   ./build_android.sh --apk\n\n"
        "2. Verifica que requests>=2.31.0 esté en:\n"
        "   - requirements.txt\n"
        "   - pyproject.toml (sección dependencies)\n\n"
        "3. Asegúrate de que main.py importa requests explícitamente."
    )
    
    full_error = f"{error_msg}\n\nError técnico: {firebase_import_error}" if firebase_import_error else error_msg
    
    # Retornar un botón discreto al final
    return [
        ft.Container(
            content=ft.Row(
                [
                    ft.IconButton(
                        icon=ft.Icons.CONTENT_COPY,
                        tooltip="Copiar información de error",
                        icon_size=16,
                        on_click=lambda e: (on_copy_error(full_error) if on_copy_error else copy_to_clipboard(page, full_error, "✓ Error copiado al portapapeles")),
                        style=ft.ButtonStyle(
                            color=ft.Colors.GREY_600 if not is_dark else ft.Colors.GREY_400,
                        )
                    ),
                ],
                alignment=ft.MainAxisAlignment.END,
            ),
            padding=ft.padding.only(top=8),
        )
    ]

