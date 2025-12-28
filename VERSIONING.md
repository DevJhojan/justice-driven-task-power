# Sistema de Versionado Automático

Este documento explica cómo funciona el sistema de versionado automático para builds de Android.

## 🎯 Características

- ✅ **Versionado automático**: No requiere edición manual antes de cada build
- ✅ **versionCode incremental**: Se incrementa automáticamente en cada build
- ✅ **versionName semántico**: Basado en la versión del proyecto (MAJOR.MINOR.PATCH)
- ✅ **Persistente**: El versionCode se guarda en `.version_code.txt`
- ✅ **Compatible con Google Play**: Cumple con todos los requisitos

## 📋 Fuente de Versión

El sistema lee la versión base desde (en orden de prioridad):

1. **pyproject.toml** - Sección `[project]` → `version`
2. **flet.toml** - Sección `[app]` → `version`
3. **Variable de entorno** - `APP_VERSION` (override opcional)
4. **Valor por defecto** - `1.0.0` si no se encuentra ninguna

### Ejemplo en pyproject.toml

```toml
[project]
name = "justice-driven-task-power"
version = "1.4.2"  # ← Esta es la versión base
```

## 🔢 Cálculo de versionCode

### Primera vez (sin archivo `.version_code.txt`)

El versionCode se calcula desde la versión base:

```
versionCode = MAJOR * 10000 + MINOR * 100 + PATCH
```

**Ejemplo:**
- Versión: `1.4.2`
- versionCode: `1 * 10000 + 4 * 100 + 2 = 10402`

### Builds subsecuentes

El versionCode se incrementa automáticamente:

```
versionCode = último_versionCode + 1
```

**Ejemplo:**
- Build 1: `10402`
- Build 2: `10403`
- Build 3: `10404`
- ...

### Protección contra conflictos

Si el versionCode calculado desde la versión es mayor que el almacenado+1, se usa el calculado:

```
versionCode = max(último_versionCode + 1, calculado_desde_versión)
```

Esto asegura que:
- ✅ El versionCode nunca disminuya
- ✅ Respete la versión base si cambias de 1.0.0 a 2.0.0
- ✅ Sea siempre incremental

## 📁 Archivos del Sistema

### `.version_code.txt`

Archivo que almacena el último versionCode usado. Se crea automáticamente y se actualiza en cada build.

**Contenido:**
```
10402
```

**Ubicación:** Raíz del proyecto

**Git:** ❌ No debe ser commiteado (ya está en `.gitignore`)

### `flet.toml`

Archivo de configuración de Flet que se genera/actualiza automáticamente con las versiones.

**Contenido ejemplo:**
```toml
[app]
name = "justice-driven-task-power"
version = "1.4.2"
package = "com.flet.justice_driven_task_power"

[android]
min_sdk = 21
target_sdk = 34
compile_sdk = 34
version_code = 10402
version_name = "1.4.2"
```

**Ubicación:** Raíz del proyecto

**Git:** ❌ No debe ser commiteado (ya está en `.gitignore`)

## 🚀 Uso

El versionado se aplica automáticamente cuando ejecutas el build:

```bash
# El script automáticamente:
# 1. Lee la versión desde pyproject.toml
# 2. Calcula/incrementa el versionCode
# 3. Actualiza flet.toml
# 4. Ejecuta el build con las versiones correctas

./build_android.sh --apk
# Building version 1.4.2 (code 10402)

./build_android.sh --aab
# Building version 1.4.2 (code 10403)
```

## 🔄 Actualizar la Versión Base

Para cambiar la versión de la aplicación:

1. **Edita `pyproject.toml`:**
   ```toml
   [project]
   version = "1.5.0"  # Nueva versión
   ```

2. **Ejecuta el build:**
   ```bash
   ./build_android.sh
   ```

3. **El sistema automáticamente:**
   - Lee la nueva versión: `1.5.0`
   - Calcula el nuevo versionCode base: `10500`
   - Usa el mayor entre `10500` y `último_versionCode + 1`
   - Actualiza `flet.toml` con las nuevas versiones

## ✅ Validaciones

El sistema valida automáticamente:

- ✅ **versionName**: Debe seguir formato `MAJOR.MINOR.PATCH`
- ✅ **versionCode**: Debe ser numérico y mayor a 0
- ✅ **versionCode**: No puede exceder 2147483647 (límite de Android)
- ✅ **versionCode**: Nunca disminuye

Si alguna validación falla, el build se detiene con un mensaje de error claro.

## 📊 Ejemplo de Flujo Completo

### Build 1 (versión 1.0.0)

```bash
$ ./build_android.sh --apk

[INFO] Versión base: 1.0.0
[INFO] Inicializando versionCode: 10000 (desde versión 1.0.0)
[SUCCESS] versionCode: 10000
[INFO] Building version 1.0.0 (code 10000)
```

**Resultado:**
- `.version_code.txt` → `10000`
- `flet.toml` → `version_code = 10000`, `version_name = "1.0.0"`

### Build 2 (misma versión 1.0.0)

```bash
$ ./build_android.sh --apk

[INFO] Versión base: 1.0.0
[INFO] Incrementando versionCode desde archivo: 10000 -> 10001
[SUCCESS] versionCode: 10001
[INFO] Building version 1.0.0 (code 10001)
```

**Resultado:**
- `.version_code.txt` → `10001`
- `flet.toml` → `version_code = 10001`, `version_name = "1.0.0"`

### Build 3 (actualizar a versión 1.4.2)

1. Editar `pyproject.toml`:
   ```toml
   version = "1.4.2"
   ```

2. Ejecutar build:
   ```bash
   $ ./build_android.sh --apk
   
   [INFO] Versión base: 1.4.2
   [INFO] Usando versionCode calculado desde versión: 10402
   [SUCCESS] versionCode: 10402
   [INFO] Building version 1.4.2 (code 10402)
   ```

**Resultado:**
- `.version_code.txt` → `10402`
- `flet.toml` → `version_code = 10402`, `version_name = "1.4.2"`

## 🔧 Override Manual (Opcional)

Si necesitas forzar un versionCode específico, puedes editar `.version_code.txt` manualmente:

```bash
echo "10500" > .version_code.txt
./build_android.sh --apk
# El próximo build usará 10501
```

**⚠️ Advertencia:** Solo haz esto si sabes lo que estás haciendo. El sistema está diseñado para funcionar automáticamente.

## 🐛 Solución de Problemas

### Error: "Formato de versión inválido"

**Causa:** La versión en `pyproject.toml` no sigue el formato `MAJOR.MINOR.PATCH`

**Solución:**
```toml
# ❌ Incorrecto
version = "1.4"
version = "v1.4.2"
version = "1.4.2-beta"

# ✅ Correcto
version = "1.4.2"
```

### Error: "versionCode debe ser mayor a 0"

**Causa:** El archivo `.version_code.txt` está corrupto o tiene un valor inválido

**Solución:**
```bash
# Eliminar el archivo corrupto
rm .version_code.txt

# El sistema lo regenerará en el próximo build
./build_android.sh
```

### El versionCode no se incrementa

**Causa:** El archivo `.version_code.txt` no tiene permisos de escritura

**Solución:**
```bash
chmod 644 .version_code.txt
```

## 📚 Referencias

- [Android Versioning](https://developer.android.com/studio/publish/versioning)
- [Semantic Versioning](https://semver.org/)
- [Flet Build Configuration](https://docs.flet.dev/)

