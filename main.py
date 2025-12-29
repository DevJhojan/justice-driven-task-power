"""
Punto de entrada principal de la aplicación.
Este archivo permite ejecutar la aplicación desde el directorio raíz.
"""
import sys
import os
from pathlib import Path

# Agregar el directorio raíz al path para que los imports funcionen
sys.path.insert(0, str(Path(__file__).parent))

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
    
    # Importar y ejecutar la función main desde app.main
    logger.info("Importando app.main...")
    from app.main import main
    logger.info("app.main importado correctamente")
    
    import flet as ft
    logger.info("flet importado correctamente")
    
    if __name__ == "__main__":
        logger.info("Iniciando ft.app...")
        # Ejecutar la aplicación
        # Para desarrollo: ventana nativa Flet
        # Para producción Android: se construye con build_android.sh
        ft.app(
            target=main, 
            view=ft.AppView.FLET_APP, 
            assets_dir="assets"
        )
except Exception as e:
    logger.error(f"Error fatal al iniciar aplicación: {e}", exc_info=True)
    # Intentar mostrar error en consola
    print(f"ERROR FATAL: {e}")
    import traceback
    traceback.print_exc()
    # Re-lanzar para que Flet lo capture
    raise
