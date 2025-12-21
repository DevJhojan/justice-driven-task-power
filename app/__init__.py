# Paquete de la aplicación

# Importar compatibilidad de collections ANTES de cualquier otra importación
# Esto asegura que el parche se aplique antes de que las dependencias lo necesiten
from app import collections_compat  # noqa: F401
