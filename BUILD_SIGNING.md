# Guía de Firmado de APK y AAB

Esta guía explica cómo configurar y usar el sistema de firmado para builds de Android.

## 📋 Requisitos Previos

1. **Java JDK** instalado (para `keytool` y `jarsigner`)
   ```bash
   # Ubuntu/Debian
   sudo apt-get install openjdk-17-jdk
   
   # Fedora
   sudo dnf install java-17-openjdk-devel
   ```

2. **Keystore** creado (ver sección siguiente)

## 🔐 Crear el Keystore

### Opción 1: Usar el script automatizado (Recomendado)

```bash
./create_keystore.sh
```

El script te guiará paso a paso para crear el keystore.

### Opción 2: Crear manualmente

```bash
# Crear directorio
mkdir -p android/keystore

# Crear keystore
keytool -genkey -v \
  -keystore android/keystore/justice_task_power.jks \
  -alias justice_task_power \
  -keyalg RSA \
  -keysize 2048 \
  -validity 10000 \
  -storepass TU_KEYSTORE_PASSWORD \
  -keypass TU_KEY_PASSWORD
```

## ⚙️ Configurar Credenciales

### Paso 1: Crear archivo .env

```bash
cp .env.example .env
```

### Paso 2: Editar .env con tus credenciales

```bash
KEYSTORE_PATH=android/keystore/justice_task_power.jks
KEYSTORE_PASSWORD=tu_contraseña_keystore
KEY_ALIAS=justice_task_power
KEY_PASSWORD=tu_contraseña_key
```

**⚠️ IMPORTANTE:**
- El archivo `.env` NO debe ser commiteado al repositorio
- Guarda estas credenciales de forma segura
- Sin el keystore y las contraseñas, NO podrás actualizar tu app en Google Play

### Alternativa: Variables de Entorno del Sistema

También puedes configurar las variables directamente:

```bash
export KEYSTORE_PATH=android/keystore/justice_task_power.jks
export KEYSTORE_PASSWORD=tu_contraseña_keystore
export KEY_ALIAS=justice_task_power
export KEY_PASSWORD=tu_contraseña_key
```

## 🚀 Uso del Build con Firmado

El firmado se aplica automáticamente cuando ejecutas el script de build:

```bash
# Generar APK firmado
./build_android.sh --apk

# Generar AAB firmado
./build_android.sh --aab

# Generar ambos (APK y AAB) firmados
./build_android.sh
```

### Proceso Automático

1. ✅ Validación del keystore
2. ✅ Validación de credenciales
3. ✅ Build del artefacto (APK/AAB)
4. ✅ Firmado automático
5. ✅ Verificación del firmado
6. ✅ Archivo final listo para uso

## 📦 Archivos Generados

Los archivos firmados se generan en:

- **APK firmado**: `build/apk/justice-driven-task-power.apk`
- **AAB firmado**: `build/aab/justice-driven-task-power.aab`

## ✅ Verificación del Firmado

El script verifica automáticamente el firmado usando:

1. **jarsigner verify** (verificación principal)
2. **apksigner verify** (verificación adicional, si está disponible)

### Verificación Manual

```bash
# Verificar APK
jarsigner -verify -verbose -certs build/apk/justice-driven-task-power.apk

# Verificar AAB
jarsigner -verify -verbose -certs build/aab/justice-driven-task-power.aab
```

## 🔧 Solución de Problemas

### Error: "Keystore no encontrado"

**Solución:**
1. Verifica que el keystore existe en la ruta especificada
2. Revisa `KEYSTORE_PATH` en tu archivo `.env`
3. Crea el keystore con `./create_keystore.sh`

### Error: "Faltan variables de entorno"

**Solución:**
1. Crea el archivo `.env` desde `.env.example`
2. Completa todas las variables requeridas
3. O configura las variables de entorno del sistema

### Error: "alias incorrecto"

**Solución:**
1. Verifica que `KEY_ALIAS` coincida con el alias del keystore
2. Lista los alias disponibles:
   ```bash
   keytool -list -v -keystore android/keystore/justice_task_power.jks \
     -storepass TU_KEYSTORE_PASSWORD
   ```

### Error: "Error en el firmado: verificación falló"

**Solución:**
1. Verifica que las contraseñas sean correctas
2. Asegúrate de que el keystore no esté corrupto
3. Intenta regenerar el keystore si el problema persiste

## 🔒 Seguridad

### Buenas Prácticas

1. ✅ **Nunca commitees** el keystore (`.jks`) al repositorio
2. ✅ **Nunca commitees** el archivo `.env` con credenciales
3. ✅ **Guarda un backup seguro** del keystore y las contraseñas
4. ✅ **Usa contraseñas fuertes** para el keystore
5. ✅ **Mantén el keystore en un lugar seguro** (no en el proyecto)

### Backup del Keystore

```bash
# Crear backup
cp android/keystore/justice_task_power.jks \
   ~/backups/justice_task_power_backup_$(date +%Y%m%d).jks

# Guardar también las contraseñas en un gestor de contraseñas seguro
```

## 📚 Referencias

- [Android App Signing](https://developer.android.com/studio/publish/app-signing)
- [Keytool Documentation](https://docs.oracle.com/javase/8/docs/technotes/tools/unix/keytool.html)
- [Jarsigner Documentation](https://docs.oracle.com/javase/8/docs/technotes/tools/unix/jarsigner.html)

