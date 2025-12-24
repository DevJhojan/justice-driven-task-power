"""
Utilidades y funciones auxiliares para SettingsView.
"""
import flet as ft
from pathlib import Path


def get_app_version() -> str:
    """
    Obtiene la versión de la aplicación desde pyproject.toml.
    
    Returns:
        Versión de la aplicación o "Desconocida" si no se puede obtener.
    """
    try:
        # Buscar pyproject.toml desde el directorio actual
        current_path = Path(__file__)
        root_dir = current_path.parent.parent.parent.parent
        pyproject_path = root_dir / 'pyproject.toml'
        
        if pyproject_path.exists():
            with open(pyproject_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip().startswith('version'):
                        # Extraer la versión del formato: version = "0.2.5"
                        version = line.split('=')[1].strip().strip('"').strip("'")
                        return version
        
        return "Desconocida"
    except Exception:
        return "Desconocida"


def copy_to_clipboard(page: ft.Page, text: str, success_message: str = "✓ Copiado al portapapeles"):
    """
    Copia texto al portapapeles y muestra un mensaje de confirmación.
    
    Args:
        page: Página de Flet.
        text: Texto a copiar.
        success_message: Mensaje de éxito a mostrar.
    """
    try:
        if not text:
            return
        
        page.set_clipboard(text)
        
        # Mostrar confirmación
        page.snack_bar = ft.SnackBar(
            content=ft.Text(success_message),
            bgcolor=ft.Colors.GREEN,
            duration=2000
        )
        page.snack_bar.open = True
        page.update()
    except Exception as ex:
        # Si falla, mostrar error
        page.snack_bar = ft.SnackBar(
            content=ft.Text(f"No se pudo copiar: {str(ex)}"),
            bgcolor=ft.Colors.RED,
            duration=3000
        )
        page.snack_bar.open = True
        page.update()

