# Consolidación de Scripts de Build - Documentación

## 📋 Resumen Ejecutivo

Se ha consolidado el proceso de build de Android en un **único script oficial**: `build_android.sh`

**Script eliminado:** `build_with_icon.sh`  
**Script oficial:** `build_android.sh`

## 🔍 Análisis de Scripts

### `build_with_icon.sh` (ELIMINADO)

#### ❌ Problemas Identificados:

1. **No lee `pyproject.toml`**:
   - Valores hardcodeados: `"TodoApp"`, `"Aplicación de gestión de tareas"`, `"Todo App"`
   - No respeta la configuración del proyecto
   - No usa la versión real del proyecto

2. **Solo construye APK**:
   - No genera AAB (Android App Bundle) necesario para Google Play Store
   - Funcionalidad limitada

3. **Menos robusto**:
   - No verifica existencia del entorno virtual antes de activarlo
   - Manejo de errores básico
   - No valida que los archivos se generaron correctamente

4. **Manejo de iconos básico**:
   - Requiere que el icono exista (falla si no está)
   - No verifica si ImageMagick está instalado antes de usar `convert`

#### ✅ Funcionalidades Útiles (ya integradas en `build_android.sh`):

- Manejo de iconos personalizados
- Conversión ICO a PNG
- Reemplazo de iconos en todas las resoluciones
- Reconstrucción del APK con iconos personalizados

### `build_android.sh` (SCRIPT OFICIAL)

#### ✅ Ventajas:

1. **Lee correctamente `pyproject.toml`**:
   - Extrae nombre del proyecto (`name`)
   - Extrae versión (`version`)
   - Extrae descripción (`description`)
   - Convierte el nombre a formato legible para display

2. **Construye tanto APK como AAB**:
   - APK para instalación directa
   - AAB para Google Play Store

3. **Robusto y completo**:
   - Verifica existencia del entorno virtual
   - Manejo de errores completo
   - Validación de archivos generados
   - Mensajes informativos con colores
   - Resumen final del build

4. **Manejo inteligente de iconos**:
   - Verifica si el icono existe (no falla si no está)
   - Verifica si ImageMagick está instalado
   - Maneja errores de conversión gracefully
   - Reemplaza iconos en todas las resoluciones necesarias

5. **Validaciones**:
   - Verifica que `pyproject.toml` existe
   - Valida que se pueden leer valores críticos (name, version)
   - Verifica que los archivos se generaron correctamente
   - Busca archivos en ubicaciones alternativas si no están donde se esperan

## 🔄 Cambios Realizados

### 1. Optimización de `build_android.sh`

#### Mejoras implementadas:

- **Validación mejorada de `pyproject.toml`**:
  - Ahora requiere que `pyproject.toml` exista (no usa valores por defecto)
  - Valida que se puedan leer valores críticos (`name`, `version`)
  - Mejor manejo de errores si falta información crítica

- **Limpieza de valores**:
  - Usa `tr -d ' '` para eliminar espacios en blanco de los valores extraídos
  - Mejor parsing de `pyproject.toml`

- **Mensajes mejorados**:
  - Muestra tanto el nombre "raw" como el nombre "display"
  - Mensajes más informativos sobre qué valores se están usando

### 2. Eliminación de `build_with_icon.sh`

- Script completamente eliminado
- Todas sus funcionalidades útiles ya estaban en `build_android.sh`

### 3. Actualización de Documentación

- **README.md** actualizado:
  - Eliminada referencia a `build_with_icon.sh`
  - Agregada documentación completa de `build_android.sh`
  - Explicación de archivos generados (APK y AAB)

## 📦 Configuración del Proyecto

### `pyproject.toml` - Valores Usados

El script `build_android.sh` lee los siguientes valores de `pyproject.toml`:

```toml
[project]
name = "justice-driven-task-power"        # → Usado como identificador
version = "0.1.5"                        # → Versión de la app
description = "conviértete en el héroe..." # → Descripción de la app
```

**Conversión de nombre:**
- `name` raw: `"justice-driven-task-power"` → Usado como identificador interno
- `name` display: `"Justice Driven Task Power"` → Usado como nombre de visualización

## 🛠️ Uso del Script

### Comando básico:

```bash
./build_android.sh
```

### Requisitos previos:

1. **Entorno virtual activado** o el script lo activará automáticamente
2. **Android SDK** configurado (variable `ANDROID_HOME`)
3. **Flet** instalado en el entorno virtual
4. **ImageMagick** (opcional, para manejo de iconos personalizados)

### Proceso de build:

1. ✅ Lee configuración de `pyproject.toml`
2. ✅ Activa entorno virtual
3. ✅ Verifica/convierte icono personalizado (si existe)
4. ✅ Construye APK inicial
5. ✅ Reemplaza iconos personalizados
6. ✅ Reconstruye APK con iconos
7. ✅ Construye AAB para Google Play Store
8. ✅ Verifica que ambos archivos se generaron
9. ✅ Muestra resumen final

### Archivos generados:

- **APK**: `build/apk/app-release.apk` - Para instalación directa
- **AAB**: `build/aab/app-release.aab` - Para Google Play Store

## ✅ Beneficios de la Consolidación

1. **Un solo punto de verdad**:
   - Un solo script para mantener
   - Un solo lugar donde buscar problemas
   - Menos confusión sobre qué script usar

2. **Consistencia**:
   - Siempre usa la configuración de `pyproject.toml`
   - Build reproducible y consistente
   - Mismo comportamiento en todos los entornos

3. **Mantenibilidad**:
   - Código más fácil de mantener
   - Menos duplicación
   - Mejor documentación

4. **Funcionalidad completa**:
   - Construye tanto APK como AAB
   - Manejo completo de iconos
   - Validaciones robustas

## 🔍 Comparación Final

| Característica | `build_with_icon.sh` ❌ | `build_android.sh` ✅ |
|---------------|------------------------|----------------------|
| Lee `pyproject.toml` | ❌ No | ✅ Sí |
| Construye APK | ✅ Sí | ✅ Sí |
| Construye AAB | ❌ No | ✅ Sí |
| Manejo de iconos | ✅ Básico | ✅ Completo |
| Validaciones | ❌ Básicas | ✅ Robustas |
| Manejo de errores | ❌ Básico | ✅ Completo |
| Mensajes informativos | ❌ Básicos | ✅ Detallados |
| Resumen final | ❌ No | ✅ Sí |

## 📝 Notas Técnicas

### Identificador de la Aplicación

El identificador de la aplicación Android se genera automáticamente por Flet basándose en:
- El nombre del proyecto (`name` en `pyproject.toml`)
- El formato es: `com.flet.<nombre-proyecto>`

Ejemplo:
- `name = "justice-driven-task-power"` → `com.flet.justice_driven_task_power`

### Versión de la Aplicación

La versión se toma directamente de `pyproject.toml`:
- `version = "0.1.5"` → Versión de la app: `0.1.5`

### Iconos Personalizados

El script maneja iconos de forma inteligente:
- Si existe `assets/task_logo.ico`, lo convierte a PNG
- Si existe `assets/app_icon.png`, lo usa directamente
- Si no existe ninguno, usa el icono por defecto de Flet
- Reemplaza iconos en todas las resoluciones necesarias:
  - mipmap: mdpi, hdpi, xhdpi, xxhdpi, xxxhdpi
  - drawable: Para adaptive icons

## 🎯 Resultado Final

✅ **Un solo script oficial**: `build_android.sh`  
✅ **Compatible con `pyproject.toml`**: Lee toda la configuración correctamente  
✅ **Build completo**: Genera tanto APK como AAB  
✅ **Robusto**: Validaciones y manejo de errores completo  
✅ **Mantenible**: Código limpio y bien documentado  

## 📚 Referencias

- [Flet Build Documentation](https://docs.flet.dev/)
- [Android App Bundle](https://developer.android.com/guide/app-bundle)
- [Python Packaging (pyproject.toml)](https://peps.python.org/pep-0621/)
