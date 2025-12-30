"""
Punto de entrada para builds de Flet.
Este archivo redirige a app.app para mantener compatibilidad con Flet.
Flet busca app.py en la raíz, así que este archivo actúa como puente.
"""
import sys
from pathlib import Path

# Agregar raíz al path
sys.path.insert(0, str(Path(__file__).parent))

# Importar la función main desde app.app (que es donde está la lógica real)
from app.app import main

# Flet espera que app.py tenga una función main() disponible
# Exportar main para que Flet pueda encontrarla
__all__ = ['main']

