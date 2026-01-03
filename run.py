import sys
import flet as ft
from pathlib import Path
from app.main import main
import asyncio
import logging

project_root = Path(__file__).parent
sys.path.append(str(project_root))

# Suprimir errores de conexión al cerrar la aplicación
logging.getLogger("flet_core").setLevel(logging.ERROR)


if __name__ == "__main__":
    try:
        ft.run(main)
    except (ConnectionResetError, asyncio.CancelledError):
        # Ignorar errores de cierre de conexión
        pass