"""
Funciones auxiliares para manejo de archivos y rutas
Gestiona rutas, directorios y archivos de la aplicación
"""

from pathlib import Path
from typing import Optional
import os


def get_project_root() -> Path:
    """
    Obtiene la ruta raíz del proyecto
    
    Returns:
        Path object apuntando a la raíz del proyecto
        
    Ejemplo:
        >>> root = get_project_root()
        >>> print(root)
        /home/devjdtp/Proyectos/App_movil_real_live
    """
    # Navegar desde este archivo hasta la raíz del proyecto
    # helpers/files.py -> utils/helpers/files.py -> app/utils/helpers/files.py -> App_movil_real_live/
    current_file = Path(__file__).resolve()
    # Subir 3 niveles: helpers -> utils -> app -> raíz
    return current_file.parent.parent.parent.parent


def get_asset_path(filename: str) -> Path:
    """
    Obtiene la ruta completa de un archivo en la carpeta assets
    
    Args:
        filename: Nombre del archivo en assets
        
    Returns:
        Path object con la ruta completa al archivo
        
    Ejemplo:
        >>> icon_path = get_asset_path("app_icon.png")
        >>> print(icon_path)
        /path/to/project/assets/app_icon.png
    """
    project_root = get_project_root()
    return project_root / "assets" / filename


def get_database_path(filename: str = "app.db") -> Path:
    """
    Obtiene la ruta completa de un archivo de base de datos
    
    Args:
        filename: Nombre del archivo de base de datos (default: "app.db")
        
    Returns:
        Path object con la ruta completa al archivo de base de datos
        
    Ejemplo:
        >>> db_path = get_database_path()
        >>> print(db_path)
        /path/to/project/database/app.db
    """
    project_root = get_project_root()
    return project_root / "database" / filename


def ensure_directory_exists(directory_path: str | Path) -> bool:
    """
    Asegura que un directorio existe, creándolo si es necesario
    
    Args:
        directory_path: Ruta del directorio a crear/verificar
        
    Returns:
        True si el directorio existe o se creó exitosamente, False en caso contrario
        
    Ejemplo:
        >>> ensure_directory_exists("database/backups")
        True
    """
    try:
        path = Path(directory_path)
        path.mkdir(parents=True, exist_ok=True)
        return True
    except (OSError, PermissionError):
        return False


def file_exists(file_path: str | Path) -> bool:
    """
    Verifica si un archivo existe
    
    Args:
        file_path: Ruta del archivo a verificar
        
    Returns:
        True si el archivo existe, False en caso contrario
        
    Ejemplo:
        >>> if file_exists("assets/app_icon.png"):
        ...     print("El archivo existe")
    """
    return Path(file_path).is_file()


def directory_exists(directory_path: str | Path) -> bool:
    """
    Verifica si un directorio existe
    
    Args:
        directory_path: Ruta del directorio a verificar
        
    Returns:
        True si el directorio existe, False en caso contrario
    """
    return Path(directory_path).is_dir()


def get_file_size(file_path: str | Path) -> Optional[int]:
    """
    Obtiene el tamaño de un archivo en bytes
    
    Args:
        file_path: Ruta del archivo
        
    Returns:
        Tamaño del archivo en bytes, o None si no existe
        
    Ejemplo:
        >>> size = get_file_size("assets/app_icon.png")
        >>> print(f"Tamaño: {size} bytes")
    """
    path = Path(file_path)
    if path.is_file():
        return path.stat().st_size
    return None


def get_file_extension(filename: str) -> str:
    """
    Obtiene la extensión de un archivo
    
    Args:
        filename: Nombre del archivo
        
    Returns:
        Extensión del archivo (sin el punto) o cadena vacía si no tiene
        
    Ejemplo:
        >>> get_file_extension("imagen.png")
        'png'
        >>> get_file_extension("archivo")
        ''
    """
    return Path(filename).suffix.lstrip('.')


def is_image_file(filename: str) -> bool:
    """
    Verifica si un archivo es una imagen según su extensión
    
    Args:
        filename: Nombre del archivo
        
    Returns:
        True si es una imagen, False en caso contrario
        
    Ejemplo:
        >>> is_image_file("foto.png")
        True
        >>> is_image_file("documento.pdf")
        False
    """
    image_extensions = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp', 'svg', 'ico'}
    extension = get_file_extension(filename).lower()
    return extension in image_extensions


def join_paths(*paths: str | Path) -> Path:
    """
    Une múltiples rutas de forma segura
    
    Args:
        *paths: Rutas a unir
        
    Returns:
        Path object con las rutas unidas
        
    Ejemplo:
        >>> path = join_paths("app", "ui", "home_view.py")
        >>> print(path)
        app/ui/home_view.py
    """
    result = Path(paths[0])
    for path in paths[1:]:
        result = result / path
    return result


def get_relative_path(file_path: str | Path, from_directory: str | Path = None) -> str:
    """
    Obtiene la ruta relativa de un archivo desde un directorio base
    
    Args:
        file_path: Ruta del archivo
        from_directory: Directorio base (default: raíz del proyecto)
        
    Returns:
        Ruta relativa como string
        
    Ejemplo:
        >>> rel_path = get_relative_path("/project/app/main.py")
        'app/main.py'
    """
    file_path = Path(file_path).resolve()
    
    if from_directory is None:
        from_directory = get_project_root()
    else:
        from_directory = Path(from_directory).resolve()
    
    try:
        return str(file_path.relative_to(from_directory))
    except ValueError:
        # Si no es relativo, retornar la ruta absoluta
        return str(file_path)


def create_backup_path(original_path: str | Path, suffix: str = "_backup") -> Path:
    """
    Crea una ruta de respaldo para un archivo
    
    Args:
        original_path: Ruta del archivo original
        suffix: Sufijo para el archivo de respaldo (default: "_backup")
        
    Returns:
        Path object con la ruta del respaldo
        
    Ejemplo:
        >>> backup = create_backup_path("database/app.db")
        >>> print(backup)
        database/app_backup.db
    """
    path = Path(original_path)
    stem = path.stem
    suffix = path.suffix
    directory = path.parent
    
    backup_name = f"{stem}{suffix}{suffix}"
    return directory / backup_name


def get_config_path(filename: str = "config.json") -> Path:
    """
    Obtiene la ruta de un archivo de configuración
    
    Args:
        filename: Nombre del archivo de configuración
        
    Returns:
        Path object con la ruta al archivo de configuración
        
    Ejemplo:
        >>> config_path = get_config_path("settings.json")
    """
    project_root = get_project_root()
    return project_root / "config" / filename


def ensure_assets_directory() -> bool:
    """
    Asegura que el directorio assets existe
    
    Returns:
        True si el directorio existe o se creó exitosamente
    """
    project_root = get_project_root()
    assets_dir = project_root / "assets"
    return ensure_directory_exists(assets_dir)


def ensure_database_directory() -> bool:
    """
    Asegura que el directorio database existe
    
    Returns:
        True si el directorio existe o se creó exitosamente
    """
    project_root = get_project_root()
    database_dir = project_root / "database"
    return ensure_directory_exists(database_dir)


def list_files_in_directory(directory_path: str | Path, pattern: str = "*") -> list[Path]:
    """
    Lista todos los archivos en un directorio que coincidan con un patrón
    
    Args:
        directory_path: Ruta del directorio
        pattern: Patrón de búsqueda (default: "*" para todos)
        
    Returns:
        Lista de Path objects con los archivos encontrados
        
    Ejemplo:
        >>> images = list_files_in_directory("assets", "*.png")
        >>> for img in images:
        ...     print(img)
    """
    directory = Path(directory_path)
    if not directory.is_dir():
        return []
    
    return list(directory.glob(pattern))


def get_file_name_without_extension(file_path: str | Path) -> str:
    """
    Obtiene el nombre del archivo sin su extensión
    
    Args:
        file_path: Ruta del archivo
        
    Returns:
        Nombre del archivo sin extensión
        
    Ejemplo:
        >>> get_file_name_without_extension("imagen.png")
        'imagen'
    """
    return Path(file_path).stem


def normalize_path(path: str | Path) -> Path:
    """
    Normaliza una ruta (resuelve .., ., etc.)
    
    Args:
        path: Ruta a normalizar
        
    Returns:
        Path object normalizado
        
    Ejemplo:
        >>> normalize_path("app/../app/main.py")
        Path('app/main.py')
    """
    return Path(path).resolve()

