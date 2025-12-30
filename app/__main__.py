"""
Punto de entrada cuando se ejecuta el paquete app como módulo.
Permite ejecutar con: python -m app
Este archivo es necesario para que Flet pueda ejecutar el paquete app.
Cuando Flet ejecuta 'python -m app', Python busca este archivo.
"""
import sys
import os
from pathlib import Path
import glob

# Agregar el directorio raíz del proyecto al path para que los imports funcionen
# Cuando se ejecuta como módulo, __file__ está en app/__main__.py
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def cleanup_old_sockets():
    """
    Limpia sockets antiguos de Flet que pueden causar conflictos.
    Esto previene errores de 'SocketException: Write failed' cuando hay
    sockets rotos de ejecuciones anteriores.
    """
    try:
        # Obtener el directorio de la app empaquetada
        flet_app_dir = os.getenv("FLET_APP_STORAGE_DATA")
        current_file = Path(__file__).resolve()
        
        # Determinar el directorio donde están los sockets
        if flet_app_dir or "flet/app" in str(current_file) or ".local/share/com.flet" in str(current_file):
            # En modo empaquetado, los sockets están en el directorio de la app
            app_dir = current_file.parent.parent
            socket_dir = app_dir
        else:
            # En desarrollo, buscar en el directorio actual
            socket_dir = project_root
        
        # Buscar y eliminar sockets antiguos
        socket_patterns = [
            str(socket_dir / "*.sock"),
            str(socket_dir / "flet_*.sock"),
            str(socket_dir / "stdout_*.sock"),
        ]
        
        sockets_cleaned = 0
        for pattern in socket_patterns:
            for socket_file in glob.glob(pattern):
                try:
                    socket_path = Path(socket_file)
                    if socket_path.is_socket():
                        # Verificar si el socket está realmente en uso
                        # Si no podemos conectarnos, probablemente está roto
                        socket_path.unlink()
                        sockets_cleaned += 1
                except (OSError, PermissionError) as e:
                    # Ignorar errores al eliminar sockets (pueden estar en uso)
                    pass
        
        if sockets_cleaned > 0:
            # Usar print en lugar de logger porque puede llamarse antes de configurar logging
            print(f"Limpieza: {sockets_cleaned} socket(s) antiguo(s) eliminado(s)")
    except Exception as e:
        # No fallar si la limpieza de sockets falla
        pass

# Configurar logging básico para depuración
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Limpiar sockets antiguos antes de iniciar (después de configurar logging)
cleanup_old_sockets()

try:
    logger.info("Iniciando aplicación desde __main__...")
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Working directory: {os.getcwd()}")
    logger.info(f"Python path: {sys.path[:3]}...")
    
    # Importar y ejecutar la función main desde app.app
    logger.info("Importando app.app...")
    from app.app import main
    logger.info("app.app importado correctamente")
    
    import flet as ft
    logger.info("flet importado correctamente")
    
    # Obtener la ruta de assets (funciona tanto en desarrollo como empaquetado)
    # Usar la misma lógica que en app/main.py
    flet_app_dir = os.getenv("FLET_APP_STORAGE_DATA")
    current_file = Path(__file__).resolve()
    
    if flet_app_dir or "flet/app" in str(current_file) or ".local/share/com.flet" in str(current_file):
        app_dir = current_file.parent.parent
        if (app_dir / "assets").exists():
            assets_path = app_dir / "assets"
        elif (current_file.parent.parent / "assets").exists():
            assets_path = current_file.parent.parent / "assets"
        else:
            assets_path = current_file.parent.parent / "assets"
    else:
        assets_path = project_root / "assets"
    
    logger.info(f"Assets path: {assets_path}")
    logger.info(f"Assets exists: {assets_path.exists()}")
    
    # Si assets no existe, intentar rutas alternativas
    if not assets_path.exists():
        alt_path = project_root / "assets"
        if alt_path.exists():
            assets_path = alt_path
            logger.info(f"Using alternative assets path: {assets_path}")
        else:
            assets_path = Path("assets")
            logger.info(f"Using relative assets path: {assets_path}")
    
    logger.info("Iniciando ft.run...")
    # Usar ft.run() en lugar de ft.app() (ft.app() está deprecado desde Flet 0.70.0)
    # ft.run() requiere main como primer argumento posicional
    ft.run(
        main, 
        view=ft.AppView.FLET_APP, 
        assets_dir=str(assets_path) if assets_path.exists() else None
    )
except Exception as e:
    logger.error(f"Error fatal al iniciar aplicación: {e}", exc_info=True)
    print(f"ERROR FATAL: {e}")
    import traceback
    traceback.print_exc()
    raise

