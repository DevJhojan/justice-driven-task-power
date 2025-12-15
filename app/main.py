"""
Punto de entrada principal de la aplicación de tareas.
"""
import sys
import os
from pathlib import Path

# Agregar el directorio raíz al PYTHONPATH para que las importaciones funcionen
# tanto ejecutando como módulo como directamente
root_dir = Path(__file__).parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

# Configurar flags del WebView para evitar el warning de WebGL por software
os.environ["FLET_WEBVIEW_FLAGS"] = "--enable-unsafe-swiftshader"

import flet as ft
from app.ui.home_view import HomeView
from app.services.settings_service import SettingsService, apply_theme_to_page


def main(page: ft.Page):
    """
    Función principal de la aplicación.
    
    Args:
        page: Página de Flet.
    """
    # Configuración de la página
    page.title = "Aplicación de Tareas"
    page.padding = 0
    page.spacing = 0

    # Solicitar permisos de almacenamiento en Android al iniciar
    if page.platform == ft.PagePlatform.ANDROID or page.platform == ft.PagePlatform.IOS:
        # En Android/iOS, intentar acceder al almacenamiento para solicitar permisos
        # Esto se hace automáticamente cuando usamos FilePicker, pero podemos
        # forzar la solicitud creando un FilePicker temporal
        try:
            temp_picker = ft.FilePicker()
            page.overlay.append(temp_picker)
            # Intentar acceder al almacenamiento para activar la solicitud de permisos
            # (El permiso real se solicitará cuando el usuario use importar/exportar)
            page.update()
        except Exception:
            pass  # Si falla, no es crítico, los permisos se pedirán al usar FilePicker

    # Cargar ajustes de apariencia desde SQLite y aplicarlos
    settings_service = SettingsService()
    app_settings = settings_service.get_settings()
    apply_theme_to_page(page, app_settings)
    
    # Configuración para móvil
    page.horizontal_alignment = ft.CrossAxisAlignment.STRETCH
    page.vertical_alignment = ft.MainAxisAlignment.START
    
    # Inicializar la vista principal
    HomeView(page)


if __name__ == "__main__":
    # Ejecutar la aplicación
    # Recomendado para desarrollo en escritorio: ventana nativa Flet
    # (evita problemas del navegador / portal de archivos).
    #
    # Para móvil (APK/AAB) el build de Flet gestionará internamente el WebView.
    ft.app(target=main, view=ft.AppView.FLET_APP, assets_dir="assets")

