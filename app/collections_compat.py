"""
Módulo de compatibilidad para Python 3.10+.
Parchea collections para mantener compatibilidad con dependencias antiguas.

Este módulo debe importarse ANTES de cualquier otra importación que use collections.MutableMapping.
Se ejecuta automáticamente cuando se importa el paquete 'app'.
"""
# CRÍTICO: Aplicar el parche ANTES de cualquier otra importación
# Esto debe ejecutarse lo más temprano posible en el proceso de inicio

def _patch_collections():
    """Aplica el parche de compatibilidad a collections."""
    try:
        import collections.abc
        import collections
        
        # Solo aplicar el parche si no existe (evitar sobrescribir si ya está parcheado)
        if not hasattr(collections, 'MutableMapping'):
            collections.MutableMapping = collections.abc.MutableMapping
        if not hasattr(collections, 'Mapping'):
            collections.Mapping = collections.abc.Mapping
        if not hasattr(collections, 'Sequence'):
            collections.Sequence = collections.abc.Sequence
        if not hasattr(collections, 'Iterable'):
            collections.Iterable = collections.abc.Iterable
        if not hasattr(collections, 'Callable'):
            collections.Callable = collections.abc.Callable
        if not hasattr(collections, 'Iterator'):
            collections.Iterator = collections.abc.Iterator
    except (ImportError, AttributeError):
        pass

# Ejecutar el parche inmediatamente al importar este módulo
_patch_collections()

# También aplicar el parche si collections ya está en sys.modules
# (por si acaso se importó antes de este módulo)
try:
    import sys
    if 'collections' in sys.modules:
        _patch_collections()
except (ImportError, AttributeError):
    pass

