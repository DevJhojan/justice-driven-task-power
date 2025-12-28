"""
Punto de entrada principal de la aplicación.
"""
import sys
import warnings
from pathlib import Path

# Suprimir advertencias de pkg_resources (deprecation warning de gcloud/pyrebase4)
warnings.filterwarnings('ignore', category=UserWarning, module='pkg_resources')
warnings.filterwarnings('ignore', category=UserWarning, module='gcloud')

# Agregar el directorio raíz al PYTHONPATH
root_dir = Path(__file__).parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

import flet as ft
from app.ui.home_view import HomeView


def main(page: ft.Page):
    """
    Función principal de la aplicación.
    
    Args:
        page: Página de Flet.
    """
    # Configuración de la página
    page.title = "Productividad Personal"
    page.padding = 0
    page.spacing = 0
    
    # Configuración para móvil y escritorio
    page.horizontal_alignment = ft.CrossAxisAlignment.STRETCH
    page.vertical_alignment = ft.MainAxisAlignment.START
    
    # Inicializar la vista principal
    HomeView(page)


if __name__ == "__main__":
    # Ejecutar la aplicación
    # Para desarrollo: ventana nativa Flet
    # Para producción Android: se construye con build_android.sh
    ft.app(target=main, view=ft.AppView.FLET_APP, assets_dir="assets")

