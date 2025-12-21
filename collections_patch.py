"""
Parche de compatibilidad para collections.MutableMapping.
Este archivo se ejecuta automáticamente cuando Python inicia si está en el PYTHONPATH.

Para que funcione durante el build de Flet, este archivo debe estar en el directorio raíz
y debe ejecutarse ANTES de que cualquier dependencia se importe.
"""
# Aplicar parche inmediatamente
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
    if not hasattr(collections, 'Callable'):
        collections.Callable = collections.abc.Callable
    if not hasattr(collections, 'Iterator'):
        collections.Iterator = collections.abc.Iterator
except (ImportError, AttributeError):
    pass

