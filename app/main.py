"""
Punto de entrada principal de la aplicación.
Este archivo configura el entorno y ejecuta la aplicación desde app.app.
"""
import sys
import os
from pathlib import Path
import glob

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
            socket_dir = current_file.parent.parent
        
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

def get_app_base_path():
    """
    Obtiene la ruta base de la aplicación.
    Detecta si estamos en modo empaquetado (Flet) o en desarrollo.
    
    Returns:
        Path: Ruta base de la aplicación
    """
    # Detectar si estamos en modo empaquetado de Flet
    # Flet establece FLET_APP_STORAGE_DATA cuando está empaquetado
    flet_app_dir = os.getenv("FLET_APP_STORAGE_DATA")
    
    # Si estamos empaquetados, __file__ apunta al directorio de la app empaquetada
    # que normalmente es algo como: /home/user/.local/share/com.flet.app-name/flet/app
    current_file = Path(__file__).resolve()
    
    # Verificar si estamos en un directorio de Flet empaquetado
    # Los directorios de Flet suelen contener "flet/app" en la ruta
    if flet_app_dir or "flet/app" in str(current_file) or ".local/share/com.flet" in str(current_file):
        # En modo empaquetado, la app está en el directorio donde está __file__
        # Los assets están en el mismo directorio o en un subdirectorio relativo
        # Flet copia los assets al directorio de la app
        app_dir = current_file.parent.parent  # app/main.py -> app/ -> raíz de la app empaquetada
        # Verificar si assets está en la raíz de la app empaquetada
        if (app_dir / "assets").exists():
            return app_dir
        # Si no, intentar en el directorio actual
        if (current_file.parent.parent / "assets").exists():
            return current_file.parent.parent
        # Fallback: usar el directorio donde está __file__
        return current_file.parent.parent
    else:
        # En modo desarrollo, usar la ruta del proyecto
        return current_file.parent.parent

# Obtener la ruta base de la aplicación
app_base = get_app_base_path()

# Agregar el directorio raíz del proyecto al path para que los imports funcionen
sys.path.insert(0, str(app_base))

# Configurar logging básico para depuración en Android
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

try:
    # Limpiar sockets antiguos antes de iniciar
    cleanup_old_sockets()
    
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
        # Obtener la ruta de assets (funciona tanto en desarrollo como empaquetado)
        assets_path = app_base / "assets"
        logger.info(f"Assets path: {assets_path}")
        logger.info(f"Assets exists: {assets_path.exists()}")
        
        # Si assets no existe en la ruta calculada, intentar rutas alternativas
        if not assets_path.exists():
            # Intentar en el directorio actual
            alt_path = Path(__file__).parent.parent / "assets"
            if alt_path.exists():
                assets_path = alt_path
                logger.info(f"Using alternative assets path: {assets_path}")
            else:
                # En modo empaquetado, Flet puede copiar assets a otro lugar
                # Intentar usar ruta relativa
                assets_path = Path("assets")
                logger.info(f"Using relative assets path: {assets_path}")
        
        # Usar ft.run() en lugar de ft.app() (ft.app() está deprecado desde Flet 0.70.0)
        # ft.run() requiere main como primer argumento posicional
        ft.run(
            main, 
            view=ft.AppView.FLET_APP, 
            assets_dir=str(assets_path) if assets_path.exists() else None
        )
except Exception as e:
    logger.error(f"Error fatal al iniciar aplicación: {e}", exc_info=True)
    # Intentar mostrar error en consola
    print(f"ERROR FATAL: {e}")
    import traceback
    traceback.print_exc()
    # Re-lanzar para que Flet lo capture
    raise
