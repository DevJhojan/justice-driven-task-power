"""
Punto de entrada principal para el build del APK.
Este archivo importa y ejecuta la aplicación desde app.main
"""
from app.main import main
import flet as ft

if __name__ == "__main__":
    ft.app(
        target=main,
        view=ft.AppView.FLET_APP,
        assets_dir="assets"
    )

