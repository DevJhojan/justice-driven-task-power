"""
Parche de compatibilidad para collections.MutableMapping.
Este archivo debe ejecutarse ANTES de cualquier otra importación.

Se ejecuta automáticamente cuando Python inicia si está en el PYTHONPATH.
"""
# Aplicar el parche inmediatamente, sin importar nada primero
import sys

# Hook de importación para interceptar importaciones de 'collections'
_original_import = __builtins__.__import__ if isinstance(__builtins__, dict) else __builtins__['__import__']

def _patched_import(name, globals=None, locals=None, fromlist=(), level=0):
    """Hook que aplica el parche cuando se importa collections."""
    # Aplicar parche ANTES de importar
    if name == 'collections' or (fromlist and 'collections' in fromlist):
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
        except:
            pass
    
    # Importar normalmente
    return _original_import(name, globals, locals, fromlist, level)

# Aplicar el hook
if isinstance(__builtins__, dict):
    __builtins__['__import__'] = _patched_import
else:
    __builtins__.__import__ = _patched_import

# También aplicar el parche directamente si collections ya está importado
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
except:
    pass

