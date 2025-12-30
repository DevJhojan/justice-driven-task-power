"""
Punto de entrada principal de la aplicación.
Este archivo configura el entorno y ejecuta la aplicación desde app.app.
"""
import sys
import os
from pathlib import Path

# Agregar el directorio raíz del proyecto al path para que los imports funcionen
# __file__ está en app/main.py, así que necesitamos ir dos niveles arriba
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Configurar logging básico para depuración en Android
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

try:
    logger.info("Iniciando aplicación...")
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Working directory: {os.getcwd()}")
    logger.info(f"Python path: {sys.path[:3]}...")
    
    # Importar y ejecutar la función main desde app.app
    logger.info("Importando app.app...")
    from app.app import main
    logger.info("app.app importado correctamente")
    
    import flet as ft
    logger.info("flet importado correctamente")
    
    if __name__ == "__main__":
        logger.info("Iniciando ft.app...")
        # Ejecutar la aplicación
        # Para desarrollo: ventana nativa Flet
        # Para producción Android: se construye con build_android.sh
        # Obtener la ruta absoluta de assets desde la raíz del proyecto
        assets_path = project_root / "assets"
        ft.app(
            target=main, 
            view=ft.AppView.FLET_APP, 
            assets_dir=str(assets_path)
        )
except Exception as e:
    logger.error(f"Error fatal al iniciar aplicación: {e}", exc_info=True)
    # Intentar mostrar error en consola
    print(f"ERROR FATAL: {e}")
    import traceback
    traceback.print_exc()
    # Re-lanzar para que Flet lo capture
    raise
