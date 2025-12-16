# Solución: Persistencia de Datos en Android

## 🐞 Problema Identificado

Cada vez que se actualiza o reinstala la aplicación en Android, **todos los datos locales se borran**.

### Causa Raíz

La base de datos se estaba guardando en el directorio de la aplicación (`app_dir / 'tasks.db'`), que en Android:
- Se borra al **actualizar** la aplicación
- Se borra al **reinstalar** la aplicación
- No es un directorio persistente

## ✅ Solución Implementada

### Cambios en `app/data/database.py`

#### 1. Detección Automática de Android

El código ahora detecta automáticamente si está ejecutándose en Android usando la variable de entorno `FLET_APP_STORAGE_DATA`, que Flet establece automáticamente en Android.

```python
app_data_dir = os.getenv("FLET_APP_STORAGE_DATA")
```

#### 2. Uso de Directorio Persistente

En Android, la base de datos se guarda en:
- **Ubicación**: `FLET_APP_STORAGE_DATA/tasks.db`
- **Persistencia**: ✅ NO se borra al actualizar
- **Persistencia**: ❌ Se borra al desinstalar (comportamiento normal de Android)

#### 3. Migración Automática

Si existe una base de datos antigua en la ubicación anterior, se migra automáticamente a la nueva ubicación persistente la primera vez que se ejecuta la app actualizada.

## 📱 Comportamiento en Android

### Al Actualizar la Aplicación:

1. ✅ La base de datos en `FLET_APP_STORAGE_DATA` **NO se borra**
2. ✅ Los datos se mantienen intactos
3. ✅ La aplicación funciona con los datos existentes

### Al Reinstalar la Aplicación:

1. ❌ La base de datos se borra (comportamiento normal de Android)
2. ✅ Se crea una nueva base de datos vacía
3. ℹ️ **Recomendación**: Usar la función de exportar antes de desinstalar

### Migración Automática:

Si actualizas la app y existe una base de datos antigua:
1. ✅ Se detecta automáticamente
2. ✅ Se copia a la nueva ubicación persistente
3. ✅ Los datos se preservan

## 🔧 Detalles Técnicos

### Ubicación de la Base de Datos

**Antes (❌ Se borraba al actualizar):**
```
<app_dir>/tasks.db
```

**Ahora (✅ Persiste entre actualizaciones):**
```
FLET_APP_STORAGE_DATA/tasks.db
```

### Variable de Entorno `FLET_APP_STORAGE_DATA`

- **Establecida por**: Flet automáticamente en Android
- **Ubicación típica**: `/data/data/<package_name>/files` o similar
- **Persistencia**: Entre actualizaciones ✅
- **Persistencia**: Entre desinstalaciones ❌

### Migración Automática

La función `_migrate_old_database()`:
1. Verifica si existe una base de datos antigua
2. La copia a la nueva ubicación si no existe la nueva
3. Mantiene la antigua como respaldo
4. Maneja errores gracefully

## 📋 Verificación

### Cómo Verificar que Funciona:

1. **Instalar la app** en Android
2. **Crear algunas tareas/hábitos**
3. **Actualizar la app** (instalar nueva versión sin desinstalar)
4. **Verificar**: Los datos deben estar intactos ✅

### Si los Datos se Pierden:

Si después de actualizar los datos se pierden, puede ser porque:
1. La variable `FLET_APP_STORAGE_DATA` no está disponible
2. Hay problemas de permisos
3. El directorio no es escribible

En este caso, el código usa un fallback al directorio del proyecto (comportamiento anterior).

## 🛠️ Solución de Problemas

### Problema: Los datos aún se pierden

**Posibles causas:**
1. La variable `FLET_APP_STORAGE_DATA` no está disponible
2. Problemas de permisos en Android
3. El directorio no es accesible

**Solución:**
- Verificar que Flet esté actualizado a la versión más reciente
- Verificar permisos de almacenamiento en Android
- Revisar logs de la aplicación para ver errores

### Problema: Base de datos no se crea

**Posibles causas:**
1. Problemas de permisos
2. Espacio insuficiente
3. Directorio no accesible

**Solución:**
- Verificar permisos de almacenamiento
- Verificar espacio disponible
- Revisar logs de la aplicación

## 📚 Referencias

- [Flet Environment Variables](https://flet.dev/docs/reference/environment-variables/)
- [Android Data Storage](https://developer.android.com/training/data-storage)
- [Android App Data Persistence](https://developer.android.com/guide/topics/data/data-storage)

## ✅ Resultado Final

- ✅ Los datos **persisten entre actualizaciones** de la aplicación
- ✅ Migración automática de datos antiguos
- ✅ Compatible con escritorio (comportamiento original)
- ✅ Sin cambios necesarios en otros servicios
- ✅ Detección automática de Android

## 🔄 Próximos Pasos

1. **Probar la actualización**:
   - Instalar app con datos
   - Actualizar sin desinstalar
   - Verificar que los datos persisten

2. **Probar la migración**:
   - Si tienes una versión antigua con datos
   - Actualizar a esta versión
   - Verificar que los datos se migran automáticamente

3. **Recomendación para usuarios**:
   - Exportar datos antes de desinstalar (si quieren conservarlos)
   - Los datos persisten automáticamente entre actualizaciones
