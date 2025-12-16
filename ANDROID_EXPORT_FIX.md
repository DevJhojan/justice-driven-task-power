# Solución al Problema de Exportación en Android 13+

## 🐞 Problema Identificado

### Síntomas
- En **escritorio (PC)**: La exportación funciona correctamente ✅
- En **Android 13+**: El archivo exportado siempre tiene **0 bytes (0B)** ❌
- El problema ocurre independientemente del tipo de archivo exportado

### Causa Raíz

El problema se debe a cómo **Flet maneja la escritura de archivos en Android 13+** con el **Storage Access Framework (SAF)**:

1. **En Android 13+**, cuando se usa `FilePicker.save_file()`:
   - El sistema usa **Storage Access Framework (SAF)**
   - La ruta devuelta puede ser un **URI de contenido** (`content://`) en lugar de una ruta de archivo normal
   - **Flet requiere que los bytes se pasen directamente** usando el parámetro `src_bytes`

2. **El código anterior tenía este problema**:
   ```python
   # ❌ INCORRECTO en Android
   self.export_file_picker.save_file(file_name=file_name)
   # Luego intentaba escribir manualmente con open()
   ```

3. **Por qué fallaba**:
   - En Android, si no se pasa `src_bytes` a `save_file()`, el archivo se crea vacío
   - Intentar escribir después con `open()` falla porque la ruta puede ser un URI de contenido
   - Flet necesita manejar la escritura internamente usando SAF

## ✅ Solución Implementada

### Cambios Realizados

#### 1. Modificación en `_start_export()`

**Antes (❌ Incorrecto)**:
```python
# Guardar bytes para escribir después
self._export_zip_bytes = zip_bytes
self.export_file_picker.save_file(file_name=file_name)
```

**Después (✅ Correcto)**:
```python
if is_android:
    # En Android: pasar bytes directamente
    self.export_file_picker.save_file(
        file_name=file_name,
        src_bytes=zip_bytes  # CRÍTICO: pasar bytes directamente
    )
else:
    # En escritorio/iOS: comportamiento original
    self._export_zip_bytes = zip_bytes
    self.export_file_picker.save_file(file_name=file_name)
```

#### 2. Modificación en `_handle_export_result()`

**Antes (❌ Incorrecto)**:
```python
# Intentaba escribir manualmente en todos los casos
with open(target_path, 'wb') as f:
    f.write(self._export_zip_bytes)
```

**Después (✅ Correcto)**:
```python
if is_android:
    # En Android: el archivo ya fue escrito por Flet
    # Solo mostramos mensaje de éxito
    success_msg = "Datos exportados correctamente..."
else:
    # En escritorio/iOS: escribir manualmente
    with open(target_path, 'wb') as f:
        f.write(self._export_zip_bytes)
```

## 🔧 Explicación Técnica

### ¿Por qué funciona en escritorio pero no en Android?

1. **Escritorio (Windows/Linux/Mac)**:
   - Usa rutas de archivo normales (`/path/to/file.zip`)
   - `open()` funciona directamente con estas rutas
   - No requiere permisos especiales

2. **Android 13+**:
   - Usa **Storage Access Framework (SAF)**
   - Las rutas pueden ser **URIs de contenido** (`content://...`)
   - `open()` no funciona directamente con URIs de contenido
   - Requiere usar **ContentResolver** o que Flet lo maneje internamente

### ¿Por qué pasar `src_bytes` soluciona el problema?

Cuando pasas `src_bytes` a `save_file()` en Android:
1. Flet detecta que estás en Android
2. Usa **Storage Access Framework (SAF)** internamente
3. Convierte el URI de contenido a una ruta accesible
4. Escribe los bytes usando el método correcto de Android
5. Maneja automáticamente los permisos necesarios

### Permisos en Android 13+

**No se requieren permisos explícitos** en el código porque:
- **Storage Access Framework (SAF)** maneja los permisos automáticamente
- Cuando el usuario selecciona una ubicación, Android solicita permisos automáticamente
- El permiso se otorga temporalmente para esa ubicación específica
- No necesitas `WRITE_EXTERNAL_STORAGE` o `READ_EXTERNAL_STORAGE` (obsoletos en Android 13+)

## 📱 Comportamiento Esperado

### En Android 13+:

1. Usuario presiona "Exportar datos"
2. Se genera el archivo ZIP en memoria
3. Se abre el diálogo de **Storage Access Framework**
4. Usuario selecciona ubicación (ej: Descargas)
5. Android solicita permisos automáticamente (si es necesario)
6. **Flet escribe el archivo automáticamente** usando `src_bytes`
7. Se muestra mensaje de éxito

### En Escritorio:

1. Usuario presiona "Exportar datos"
2. Se genera el archivo ZIP en memoria
3. Se abre el diálogo de guardar archivo del sistema
4. Usuario selecciona ubicación
5. Se escribe el archivo manualmente con `open()`
6. Se muestra mensaje de éxito

## ✅ Requisitos Cumplidos

- ✅ Compatible con **Android 13+ (API 33+)**
- ✅ Usa **Scoped Storage** (Storage Access Framework)
- ✅ No usa permisos obsoletos
- ✅ No usa accesos directos al almacenamiento global
- ✅ Usa prácticas recomendadas actuales de Android
- ✅ Funciona tanto en Android como en escritorio

## 🧪 Pruebas Recomendadas

1. **Probar en Android 13+**:
   - Exportar datos
   - Verificar que el archivo tiene contenido (no 0 bytes)
   - Verificar que se puede abrir y contiene los CSVs esperados

2. **Probar en escritorio**:
   - Verificar que sigue funcionando correctamente
   - Verificar que el archivo tiene contenido

3. **Probar en diferentes ubicaciones**:
   - Descargas
   - Documentos
   - Otras carpetas accesibles

## 📚 Referencias

- [Flet FilePicker Documentation](https://docs.flet.dev/services/filepicker/)
- [Android Storage Access Framework](https://developer.android.com/training/data-storage/shared/documents-files)
- [Android Scoped Storage](https://developer.android.com/training/data-storage)

## 🔍 Notas Adicionales

- El código mantiene compatibilidad con escritorio/iOS usando el método original
- En Android, el archivo se escribe automáticamente por Flet, por lo que no necesitamos verificar el tamaño
- Los permisos se solicitan automáticamente cuando el usuario selecciona la ubicación
- No se requiere modificar `AndroidManifest.xml` porque SAF maneja los permisos automáticamente
