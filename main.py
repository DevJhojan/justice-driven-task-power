"""
Punto de entrada principal para el build del APK.
Este archivo importa y ejecuta la aplicación desde app.main

IMPORTANTE: Este archivo es usado por Flet para construir el APK.
Flet detectará automáticamente el modo de ejecución (móvil/desktop/web)
basado en el contexto, por lo que no especificamos 'view' explícitamente.
"""
# CRÍTICO: Aplicar parche de collections ANTES de cualquier otra cosa
# Intentar importar el parche desde el archivo raíz primero
try:
    import collections_patch  # noqa: F401
except ImportError:
    pass

# CRÍTICO: Hook de importación para interceptar TODAS las importaciones de collections
# Esto se ejecuta ANTES de que cualquier código importe collections
import sys

# Guardar la función de importación original
_original_import = __builtins__.__import__ if hasattr(__builtins__, '__import__') else __builtins__['__import__']

def _patched_import(name, globals=None, locals=None, fromlist=(), level=0):
    """Hook que aplica el parche cuando se importa collections."""
    # Solo interceptar importaciones de 'collections', no otras
    is_collections_import = (name == 'collections') or (fromlist and 'collections' in fromlist)
    
    if is_collections_import:
        try:
            # Importar collections usando la función original para evitar recursión
            collections_module = _original_import('collections', globals, locals, fromlist, level)
            
            # Aplicar parche solo si no está ya aplicado
            if not hasattr(collections_module, 'MutableMapping'):
                import collections.abc
                collections_module.MutableMapping = collections.abc.MutableMapping
                collections_module.Mapping = collections.abc.Mapping
                collections_module.Sequence = collections.abc.Sequence
                collections_module.Iterable = collections.abc.Iterable
                collections_module.Callable = collections.abc.Callable
                collections_module.Iterator = collections.abc.Iterator
            
            return collections_module
        except (ImportError, AttributeError, KeyError):
            # Si falla, importar normalmente
            return _original_import(name, globals, locals, fromlist, level)
    
    # Para todas las demás importaciones, usar la función original
    return _original_import(name, globals, locals, fromlist, level)

# Aplicar el hook ANTES de cualquier importación
if isinstance(__builtins__, dict):
    __builtins__['__import__'] = _patched_import
else:
    __builtins__.__import__ = _patched_import

# También aplicar el parche directamente si collections ya está importado
try:
    import collections.abc
    if 'collections' in sys.modules:
        collections = sys.modules['collections']
        if not hasattr(collections, 'MutableMapping'):
            collections.MutableMapping = collections.abc.MutableMapping
        if not hasattr(collections, 'Mapping'):
            collections.Mapping = collections.abc.Mapping
        if not hasattr(collections, 'Sequence'):
            collections.Sequence = collections.abc.Sequence
        if not hasattr(collections, 'Iterable'):
            collections.Iterable = collections.abc.Iterable
except (ImportError, AttributeError, KeyError):
    pass

# También importar el módulo de compatibilidad para doble seguridad
try:
    import app.collections_compat  # noqa: F401
except ImportError:
    pass

# CRÍTICO: Importar requests explícitamente para que Flet lo empaquete en el APK
# Esto asegura que la dependencia se detecte y se incluya en el build
try:
    import requests  # noqa: F401
except ImportError:
    # Si requests no está disponible, la app funcionará en modo offline
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
