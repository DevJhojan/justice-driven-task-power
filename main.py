"""
Punto de entrada principal para el build del APK.
Este archivo importa y ejecuta la aplicación desde app.main

IMPORTANTE: Este archivo es usado por Flet para construir el APK.
Flet detectará automáticamente el modo de ejecución (móvil/desktop/web)
basado en el contexto, por lo que no especificamos 'view' explícitamente.
"""
from app.main import main
import flet as ft

if __name__ == "__main__":
    # Para el build del APK, Flet detectará automáticamente el modo móvil
    # No especificamos 'view' para que Flet lo determine automáticamente
    ft.app(
        target=main,
        assets_dir="assets"
    )
