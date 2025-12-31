"""
Tests para helpers/files.py
"""
import pytest
from pathlib import Path
import tempfile
import os
from app.utils.helpers.files import (
    get_project_root,
    get_asset_path,
    get_database_path,
    get_config_path,
    ensure_directory_exists,
    ensure_assets_directory,
    ensure_database_directory,
    file_exists,
    directory_exists,
    get_file_size,
    get_file_extension,
    get_file_name_without_extension,
    is_image_file,
    join_paths,
    get_relative_path,
    create_backup_path,
    list_files_in_directory,
    normalize_path,
)


class TestFiles:
    """Tests para funciones de files"""
    
    def test_get_project_root(self):
        """Test obtener raíz del proyecto"""
        root = get_project_root()
        assert isinstance(root, Path)
        assert root.exists()
        assert root.is_dir()
    
    def test_get_asset_path(self):
        """Test obtener ruta de asset"""
        path = get_asset_path("test.png")
        assert isinstance(path, Path)
        assert "assets" in str(path)
        assert path.name == "test.png"
    
    def test_get_database_path(self):
        """Test obtener ruta de base de datos"""
        path = get_database_path("test.db")
        assert isinstance(path, Path)
        assert "database" in str(path)
        assert path.name == "test.db"
    
    def test_get_database_path_default(self):
        """Test obtener ruta de BD con nombre por defecto"""
        path = get_database_path()
        assert path.name == "app.db"
    
    def test_get_config_path(self):
        """Test obtener ruta de configuración"""
        path = get_config_path("test.json")
        assert isinstance(path, Path)
        assert "config" in str(path)
        assert path.name == "test.json"
    
    def test_ensure_directory_exists(self):
        """Test asegurar que directorio existe"""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_dir = Path(tmpdir) / "test_subdir"
            assert not test_dir.exists()
            
            result = ensure_directory_exists(test_dir)
            assert result == True
            assert test_dir.exists()
            assert test_dir.is_dir()
    
    def test_ensure_directory_exists_already_exists(self):
        """Test ensure_directory_exists cuando ya existe"""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_dir = Path(tmpdir) / "existing_dir"
            test_dir.mkdir()
            
            result = ensure_directory_exists(test_dir)
            assert result == True
            assert test_dir.exists()
    
    def test_ensure_assets_directory(self):
        """Test asegurar directorio assets"""
        result = ensure_assets_directory()
        assert result == True
        
        root = get_project_root()
        assets_dir = root / "assets"
        assert assets_dir.exists()
    
    def test_ensure_database_directory(self):
        """Test asegurar directorio database"""
        result = ensure_database_directory()
        assert result == True
        
        root = get_project_root()
        db_dir = root / "database"
        assert db_dir.exists()
    
    def test_file_exists(self):
        """Test verificar si archivo existe"""
        with tempfile.NamedTemporaryFile(delete=False) as tmpfile:
            tmp_path = Path(tmpfile.name)
            assert file_exists(tmp_path) == True
            assert file_exists(Path("nonexistent.txt")) == False
            os.unlink(tmp_path)
    
    def test_directory_exists(self):
        """Test verificar si directorio existe"""
        with tempfile.TemporaryDirectory() as tmpdir:
            assert directory_exists(Path(tmpdir)) == True
            assert directory_exists(Path("nonexistent_dir")) == False
    
    def test_get_file_size(self):
        """Test obtener tamaño de archivo"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmpfile:
            tmpfile.write("test content")
            tmp_path = Path(tmpfile.name)
            
            size = get_file_size(tmp_path)
            assert size is not None
            assert size > 0
            
            os.unlink(tmp_path)
    
    def test_get_file_size_nonexistent(self):
        """Test obtener tamaño de archivo inexistente"""
        size = get_file_size(Path("nonexistent.txt"))
        assert size is None
    
    def test_get_file_extension(self):
        """Test obtener extensión de archivo"""
        assert get_file_extension("test.txt") == ".txt"
        assert get_file_extension("test.PNG") == ".png"
        assert get_file_extension("test") == ""
        assert get_file_extension("test.file.ext") == ".ext"
    
    def test_get_file_name_without_extension(self):
        """Test obtener nombre sin extensión"""
        assert get_file_name_without_extension("test.txt") == "test"
        assert get_file_name_without_extension("test.file.txt") == "test.file"
        assert get_file_name_without_extension("test") == "test"
    
    def test_is_image_file(self):
        """Test verificar si es archivo de imagen"""
        assert is_image_file("test.png") == True
        assert is_image_file("test.jpg") == True
        assert is_image_file("test.JPEG") == True
        assert is_image_file("test.gif") == True
        assert is_image_file("test.txt") == False
        assert is_image_file("test") == False
    
    def test_join_paths(self):
        """Test unir rutas"""
        result = join_paths("path", "to", "file.txt")
        assert isinstance(result, Path)
        assert "path" in str(result)
        assert "file.txt" in str(result)
    
    def test_get_relative_path(self):
        """Test obtener ruta relativa"""
        root = get_project_root()
        test_file = root / "test" / "test_file.py"
        
        relative = get_relative_path(test_file, root)
        assert "test" in relative
        assert "test_file.py" in relative
    
    def test_create_backup_path(self):
        """Test crear ruta de backup"""
        original = Path("test.txt")
        backup = create_backup_path(original)
        
        assert backup.name == "test_backup.txt"
        assert backup.parent == original.parent
    
    def test_create_backup_path_custom_suffix(self):
        """Test crear ruta de backup con sufijo personalizado"""
        original = Path("test.txt")
        backup = create_backup_path(original, suffix="_old")
        
        assert backup.name == "test_old.txt"
    
    def test_list_files_in_directory(self):
        """Test listar archivos en directorio"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Crear archivos de prueba
            (Path(tmpdir) / "file1.txt").touch()
            (Path(tmpdir) / "file2.txt").touch()
            (Path(tmpdir) / "subdir").mkdir()
            
            files = list_files_in_directory(tmpdir, "*.txt")
            assert len(files) == 2
            assert all(f.suffix == ".txt" for f in files)
    
    def test_normalize_path(self):
        """Test normalizar ruta"""
        path = Path("test/../other/file.txt")
        normalized = normalize_path(path)
        
        assert isinstance(normalized, Path)
        assert normalized.is_absolute()

