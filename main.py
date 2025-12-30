"""
Punto de entrada principal para Flet builds.
Flet busca main.py en la raíz, así que este archivo redirige a app.main.
"""
import sys
from pathlib import Path

# Agregar raíz al path
sys.path.insert(0, str(Path(__file__).parent))

# Importar y ejecutar desde app.main
from app.main import *

