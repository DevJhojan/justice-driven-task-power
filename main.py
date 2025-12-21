"""
Punto de entrada principal para el build del APK.
Este archivo importa y ejecuta la aplicación desde app.main

IMPORTANTE: Este archivo es usado por Flet para construir el APK.
Flet detectará automáticamente el modo de ejecución (móvil/desktop/web)
basado en el contexto, por lo que no especificamos 'view' explícitamente.
"""
# Parche de compatibilidad para Python 3.10+
# collections.MutableMapping fue movido a collections.abc.MutableMapping
# pero algunas dependencias antiguas (como pyrebase4) aún lo usan
try:
    import collections.abc
    import collections
    if not hasattr(collections, 'MutableMapping'):
        collections.MutableMapping = collections.abc.MutableMapping
    if not hasattr(collections, 'Mapping'):
        collections.Mapping = collections.abc.Mapping
    if not hasattr(collections, 'Sequence'):
        collections.Sequence = collections.abc.Sequence
    if not hasattr(collections, 'Iterable'):
        collections.Iterable = collections.abc.Iterable
except ImportError:
    pass

from app.main import main
import flet as ft

if __name__ == "__main__":
    # Para el build del APK, Flet detectará automáticamente el modo móvil
    # No especificamos 'view' para que Flet lo determine automáticamente
    ft.app(
        target=main,
        assets_dir="assets"
    )
