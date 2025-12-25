"""
Módulo para la sincronización con Firebase.
"""
import flet as ft
from .utils import copy_to_clipboard


def show_sync_direction_page(
    page: ft.Page,
    firebase_sync_service,
    firebase_auth_service,
    on_go_back: callable,
    on_tasks_refresh: callable = None,
    on_habits_refresh: callable = None
):
    """
    Muestra una página para seleccionar la dirección de sincronización.
    
    Args:
        page: Página de Flet.
        firebase_sync_service: Servicio de sincronización Firebase.
        firebase_auth_service: Servicio de autenticación Firebase.
        on_go_back: Callback para volver.
        on_tasks_refresh: Callback para refrescar tareas después de descargar.
        on_habits_refresh: Callback para refrescar hábitos después de descargar.
    """
    is_dark = page.theme_mode == ft.ThemeMode.DARK
    scheme = page.theme.color_scheme if page.theme else None
    primary_color = scheme.primary if scheme and scheme.primary else ft.Colors.BLUE_700
    
    def upload_to_cloud(e):
        """Sube datos locales a Firebase."""
        show_sync_loading_page(page)
        try:
            result = firebase_sync_service.upload_to_cloud()
            show_sync_results_page(page, True, result, None, on_go_back)
        except Exception as ex:
            show_sync_results_page(page, False, None, str(ex), on_go_back)
    
    def download_from_cloud(e):
        """Descarga datos de Firebase al local."""
        show_sync_loading_page(page)
        try:
            result = firebase_sync_service.download_from_cloud()
            
            # Refrescar vistas si se descargaron datos
            if result.tasks_downloaded > 0 and on_tasks_refresh:
                on_tasks_refresh()
            if result.habits_downloaded > 0 and on_habits_refresh:
                on_habits_refresh()
            
            show_sync_results_page(page, True, result, None, on_go_back)
        except Exception as ex:
            show_sync_results_page(page, False, None, str(ex), on_go_back)
    
    # Botones de acción
    upload_button = ft.ElevatedButton(
        text="Subir datos locales a la nube",
        icon=ft.Icons.CLOUD_UPLOAD,
        on_click=upload_to_cloud,
        expand=True,
        height=60,
        bgcolor=ft.Colors.BLUE,
        color=ft.Colors.WHITE,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=10)
        )
    )
    
    download_button = ft.ElevatedButton(
        text="Descargar datos de la nube al local",
        icon=ft.Icons.CLOUD_DOWNLOAD,
        on_click=download_from_cloud,
        expand=True,
        height=60,
        bgcolor=ft.Colors.GREEN,
        color=ft.Colors.WHITE,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=10)
        )
    )
    
    # Construir la vista
    direction_view = ft.View(
        route="/sync-direction",
        appbar=ft.AppBar(
            title=ft.Text("Sincronización"),
            leading=ft.IconButton(
                icon=ft.Icons.ARROW_BACK,
                on_click=lambda e: on_go_back()
            ),
            bgcolor=primary_color
        ),
        padding=20,
        scroll=ft.ScrollMode.AUTO,
        controls=[
            ft.Container(
                content=ft.Column(
                    [
                        ft.Icon(
                            ft.Icons.SYNC,
                            size=64,
                            color=primary_color
                        ),
                        ft.Text(
                            "Selecciona la dirección de sincronización",
                            size=22,
                            weight=ft.FontWeight.BOLD,
                            text_align=ft.TextAlign.CENTER
                        ),
                        ft.Divider(height=30),
                        ft.Container(
                            content=ft.Column(
                                [
                                    ft.Row(
                                        [
                                            ft.Icon(ft.Icons.PHONE_ANDROID, size=32, color=ft.Colors.BLUE),
                                            ft.Column(
                                                [
                                                    ft.Text(
                                                        "Datos locales",
                                                        size=16,
                                                        weight=ft.FontWeight.BOLD
                                                    ),
                                                    ft.Text(
                                                        "Tareas y hábitos guardados en tu dispositivo",
                                                        size=12,
                                                        color=ft.Colors.GREY_600 if not is_dark else ft.Colors.GREY_400
                                                    )
                                                ],
                                                spacing=5
                                            )
                                        ],
                                        spacing=15
                                    ),
                                    ft.Divider(height=20),
                                    ft.Row(
                                        [
                                            ft.Icon(ft.Icons.CLOUD, size=32, color=ft.Colors.GREEN),
                                            ft.Column(
                                                [
                                                    ft.Text(
                                                        "Datos en la nube",
                                                        size=16,
                                                        weight=ft.FontWeight.BOLD
                                                    ),
                                                    ft.Text(
                                                        "Tareas y hábitos guardados en Firebase",
                                                        size=12,
                                                        color=ft.Colors.GREY_600 if not is_dark else ft.Colors.GREY_400
                                                    )
                                                ],
                                                spacing=5
                                            )
                                        ],
                                        spacing=15
                                    )
                                ],
                                spacing=10
                            ),
                            padding=20,
                            bgcolor=ft.Colors.BLUE_50 if not is_dark else ft.Colors.BLUE_900,
                            border_radius=10,
                            border=ft.border.all(1, ft.Colors.BLUE_200 if not is_dark else ft.Colors.BLUE_700)
                        ),
                        ft.Divider(height=30),
                        ft.Text(
                            "¿Qué deseas hacer?",
                            size=18,
                            weight=ft.FontWeight.BOLD,
                            text_align=ft.TextAlign.CENTER
                        ),
                        upload_button,
                        download_button,
                        ft.Divider(height=20),
                        ft.Container(
                            content=ft.Row(
                                [
                                    ft.Icon(ft.Icons.INFO_OUTLINE, size=20, color=ft.Colors.ORANGE),
                                    ft.Container(
                                        content=ft.Text(
                                            "Subir: Respalda tus datos locales en Firebase.\n"
                                            "Descargar: Trae datos de Firebase a tu dispositivo.",
                                            size=12,
                                            color=ft.Colors.GREY_600 if not is_dark else ft.Colors.GREY_400
                                        ),
                                        expand=True
                                    )
                                ],
                                spacing=10
                            ),
                            padding=15,
                            bgcolor=ft.Colors.ORANGE_50 if not is_dark else ft.Colors.ORANGE_900,
                            border_radius=10
                        )
                    ],
                    spacing=20,
                    horizontal_alignment=ft.CrossAxisAlignment.STRETCH
                ),
                padding=20,
                border_radius=10,
                bgcolor=ft.Colors.GREY_900 if is_dark else ft.Colors.GREY_100
            )
        ]
    )
    
    page.views.append(direction_view)
    page.go("/sync-direction")
    page.update()


def show_sync_loading_page(page: ft.Page):
    """Muestra una página de carga durante la sincronización."""
    is_dark = page.theme_mode == ft.ThemeMode.DARK
    scheme = page.theme.color_scheme if page.theme else None
    primary_color = scheme.primary if scheme and scheme.primary else ft.Colors.BLUE_700
    
    loading_view = ft.View(
        route="/sync-loading",
        appbar=ft.AppBar(
            title=ft.Text("Sincronizando..."),
            bgcolor=primary_color
        ),
        padding=20,
        controls=[
            ft.Container(
                content=ft.Column(
                    [
                        ft.ProgressRing(width=64, height=64),
                        ft.Divider(height=30),
                        ft.Text(
                            "Sincronizando datos con Firebase...",
                            size=18,
                            weight=ft.FontWeight.BOLD,
                            text_align=ft.TextAlign.CENTER
                        ),
                        ft.Text(
                            "Por favor espera",
                            size=14,
                            color=ft.Colors.GREY_600 if not is_dark else ft.Colors.GREY_400,
                            text_align=ft.TextAlign.CENTER
                        )
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=15
                ),
                padding=40,
                alignment=ft.alignment.center
            )
        ]
    )
    
    page.views.append(loading_view)
    page.go("/sync-loading")
    page.update()


def show_sync_results_page(
    page: ft.Page,
    success: bool,
    sync_result=None,
    error_message: str = None,
    on_go_back: callable = None
):
    """
    Muestra una página completa con los resultados de la sincronización.
    
    Args:
        page: Página de Flet.
        success: True si la sincronización fue exitosa.
        sync_result: Objeto SyncResult con los detalles de la sincronización.
        error_message: Mensaje de error si success=False.
        on_go_back: Callback para volver.
    """
    is_dark = page.theme_mode == ft.ThemeMode.DARK
    scheme = page.theme.color_scheme if page.theme else None
    primary_color = scheme.primary if scheme and scheme.primary else ft.Colors.BLUE_700
    
    # Remover la página de carga si existe
    if len(page.views) > 1 and page.views[-1].route == "/sync-loading":
        page.views.pop()
    
    # Contenido de la página
    content_controls = []
    
    if success and sync_result:
        # Página de éxito
        icon_color = ft.Colors.GREEN
        title_text = "✓ Sincronización completada"
        title_color = ft.Colors.GREEN
        
        # Estadísticas
        stats = []
        
        if sync_result.tasks_uploaded > 0:
            stats.append(ft.ListTile(
                leading=ft.Icon(ft.Icons.UPLOAD, color=ft.Colors.BLUE),
                title=ft.Text(f"Tareas subidas: {sync_result.tasks_uploaded}"),
                subtitle=ft.Text("Datos locales respaldados en Firebase")
            ))
        
        if sync_result.tasks_downloaded > 0:
            stats.append(ft.ListTile(
                leading=ft.Icon(ft.Icons.DOWNLOAD, color=ft.Colors.GREEN),
                title=ft.Text(f"Tareas descargadas: {sync_result.tasks_downloaded}"),
                subtitle=ft.Text("Datos remotos agregados localmente")
            ))
        
        if sync_result.habits_uploaded > 0:
            stats.append(ft.ListTile(
                leading=ft.Icon(ft.Icons.UPLOAD, color=ft.Colors.BLUE),
                title=ft.Text(f"Hábitos subidos: {sync_result.habits_uploaded}"),
                subtitle=ft.Text("Datos locales respaldados en Firebase")
            ))
        
        if sync_result.habits_downloaded > 0:
            stats.append(ft.ListTile(
                leading=ft.Icon(ft.Icons.DOWNLOAD, color=ft.Colors.GREEN),
                title=ft.Text(f"Hábitos descargados: {sync_result.habits_downloaded}"),
                subtitle=ft.Text("Datos remotos agregados localmente")
            ))
        
        if sync_result.deletions_uploaded > 0:
            stats.append(ft.ListTile(
                leading=ft.Icon(ft.Icons.DELETE, color=ft.Colors.ORANGE),
                title=ft.Text(f"Eliminaciones subidas: {sync_result.deletions_uploaded}"),
                subtitle=ft.Text("Eliminaciones locales sincronizadas en Firebase")
            ))
        
        if sync_result.deletions_downloaded > 0:
            stats.append(ft.ListTile(
                leading=ft.Icon(ft.Icons.DELETE, color=ft.Colors.RED),
                title=ft.Text(f"Eliminaciones aplicadas: {sync_result.deletions_downloaded}"),
                subtitle=ft.Text("Eliminaciones remotas aplicadas localmente")
            ))
        
        # Verificar si no hay cambios para sincronizar
        if hasattr(sync_result, 'no_changes') and sync_result.no_changes:
            stats = [
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Icon(
                                ft.Icons.CHECK_CIRCLE,
                                size=64,
                                color=ft.Colors.GREEN if not is_dark else ft.Colors.GREEN_300
                            ),
                            ft.Text(
                                "Los datos no han sido modificados",
                                size=20,
                                weight=ft.FontWeight.BOLD,
                                text_align=ft.TextAlign.CENTER
                            ),
                            ft.Text(
                                "No es necesario sincronizar.",
                                size=16,
                                text_align=ft.TextAlign.CENTER,
                                color=ft.Colors.GREY_600 if not is_dark else ft.Colors.GREY_400
                            ),
                            ft.Divider(height=20),
                            ft.Text(
                                "Todos los datos locales y remotos están sincronizados.",
                                size=14,
                                text_align=ft.TextAlign.CENTER,
                                color=ft.Colors.GREY_600 if not is_dark else ft.Colors.GREY_400
                            )
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=12
                    ),
                    padding=40,
                    alignment=ft.alignment.center
                )
            ]
        elif not stats:
            stats.append(ft.Text(
                "No hubo cambios que sincronizar. Los datos ya están actualizados.",
                size=14,
                color=ft.Colors.GREY_600 if not is_dark else ft.Colors.GREY_400,
                text_align=ft.TextAlign.CENTER
            ))
        
        # Mostrar elementos omitidos si los hay (y no es el caso de "no_changes")
        if not (hasattr(sync_result, 'no_changes') and sync_result.no_changes):
            if hasattr(sync_result, 'tasks_skipped') and sync_result.tasks_skipped > 0:
                stats.append(ft.Divider(height=10))
                stats.append(ft.ListTile(
                    leading=ft.Icon(ft.Icons.SKIP_NEXT, color=ft.Colors.GREY),
                    title=ft.Text(f"Tareas omitidas (sin cambios): {sync_result.tasks_skipped}"),
                    subtitle=ft.Text("Estas tareas no fueron modificadas localmente")
                ))
            
            if hasattr(sync_result, 'habits_skipped') and sync_result.habits_skipped > 0:
                stats.append(ft.ListTile(
                    leading=ft.Icon(ft.Icons.SKIP_NEXT, color=ft.Colors.GREY),
                    title=ft.Text(f"Hábitos omitidos (sin cambios): {sync_result.habits_skipped}"),
                    subtitle=ft.Text("Estos hábitos no fueron modificados localmente")
                ))
        
        content_controls.extend(stats)
        
        # Advertencias si las hay
        if sync_result.errors:
            content_controls.append(ft.Divider(height=20))
            content_controls.append(ft.Text(
                f"⚠ Advertencias ({len(sync_result.errors)}):",
                size=16,
                weight=ft.FontWeight.BOLD,
                color=ft.Colors.ORANGE
            ))
            
            for error in sync_result.errors:
                error_text = ft.Text(error, size=12, selectable=True)
                copy_button = ft.IconButton(
                    icon=ft.Icons.COPY,
                    tooltip="Copiar advertencia",
                    icon_size=18,
                    icon_color=ft.Colors.ORANGE,
                    on_click=lambda e, err=error: copy_to_clipboard(page, err, "✓ Advertencia copiada")
                )
                
                content_controls.append(
                    ft.Container(
                        content=ft.Row(
                            [
                                ft.Container(content=error_text, expand=True, padding=ft.padding.only(right=5)),
                                copy_button
                            ],
                            spacing=5,
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                        ),
                        padding=10,
                        bgcolor=ft.Colors.ORANGE_50 if not is_dark else ft.Colors.ORANGE_900,
                        border_radius=5,
                        border=ft.border.all(1, ft.Colors.ORANGE_300 if not is_dark else ft.Colors.ORANGE_700)
                    )
                )
    
    else:
        # Página de error
        icon_color = ft.Colors.RED
        title_text = "✗ Error en la sincronización"
        title_color = ft.Colors.RED
        
        error_msg = error_message or "Error desconocido durante la sincronización"
        if sync_result and sync_result.errors:
            error_msg = "\n".join(sync_result.errors)
        
        # Texto del error (seleccionable)
        error_text = ft.Text(
            error_msg,
            size=14,
            selectable=True,
            weight=ft.FontWeight.W_500
        )
        
        # Botón para copiar error
        copy_button = ft.IconButton(
            icon=ft.Icons.COPY,
            tooltip="Copiar error al portapapeles",
            icon_size=20,
            icon_color=ft.Colors.RED,
            on_click=lambda e: copy_to_clipboard(page, error_msg, "✓ Error copiado")
        )
        
        content_controls.append(
            ft.Container(
                content=ft.Column(
                    [
                        ft.Row(
                            [
                                ft.Container(content=error_text, expand=True, padding=ft.padding.only(right=5)),
                                copy_button
                            ],
                            spacing=5,
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                        )
                    ],
                    spacing=10
                ),
                padding=15,
                bgcolor=ft.Colors.RED_50 if not is_dark else ft.Colors.RED_900,
                border_radius=10,
                border=ft.border.all(2, ft.Colors.RED_300 if not is_dark else ft.Colors.RED_700)
            )
        )
    
    # Botón para volver
    back_button = ft.ElevatedButton(
        text="Volver",
        icon=ft.Icons.ARROW_BACK,
        on_click=lambda e: on_go_back() if on_go_back else None,
        expand=True,
        height=50,
        bgcolor=primary_color,
        color=ft.Colors.WHITE
    )
    
    # Construir la vista
    results_view = ft.View(
        route="/sync-results",
        appbar=ft.AppBar(
            title=ft.Text("Resultados de sincronización"),
            leading=ft.IconButton(
                icon=ft.Icons.ARROW_BACK,
                on_click=lambda e: on_go_back() if on_go_back else None
            ),
            bgcolor=primary_color
        ),
        padding=20,
        scroll=ft.ScrollMode.AUTO,
        controls=[
            ft.Container(
                content=ft.Column(
                    [
                        ft.Icon(
                            ft.Icons.CHECK_CIRCLE if success else ft.Icons.ERROR,
                            size=64,
                            color=icon_color
                        ),
                        ft.Text(
                            title_text,
                            size=24,
                            weight=ft.FontWeight.BOLD,
                            color=title_color,
                            text_align=ft.TextAlign.CENTER
                        ),
                        ft.Divider(height=30),
                        *content_controls,
                        ft.Divider(height=30),
                        back_button
                    ],
                    spacing=15,
                    horizontal_alignment=ft.CrossAxisAlignment.STRETCH
                ),
                padding=20,
                border_radius=10,
                bgcolor=ft.Colors.GREY_900 if is_dark else ft.Colors.GREY_100
            )
        ]
    )
    
    page.views.append(results_view)
    page.go("/sync-results")
    page.update()

