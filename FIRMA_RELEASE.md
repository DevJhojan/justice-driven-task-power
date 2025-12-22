# Configuración de Firma de Release para Android

Este documento explica cómo configurar la firma de release para subir tu aplicación a Google Play Console.

## Problema

Si intentas subir un APK o AAB a Google Play Console y recibes el error:
> "Subiste un APK o un Android App Bundle que se firmaron en el modo de depuración. Debes firmarlos en el modo de lanzamiento."

Esto significa que tu aplicación está siendo firmada con la clave de debug en lugar de una clave de release.

## Solución

### Paso 1: Crear el Keystore

Ejecuta el script para crear el keystore de firma:

```bash
./create_keystore.sh
```

Este script te pedirá:
- **Alias de la clave**: Nombre identificador de la clave (por defecto: `upload`)
- **Contraseña del keystore**: Contraseña para proteger el archivo keystore
- **Contraseña de la clave**: Contraseña para la clave específica (puede ser la misma)
- **Información personal**: Nombre, organización, ciudad, etc.

**⚠️ IMPORTANTE**: Guarda estas credenciales en un lugar seguro. Las necesitarás para:
- Todas las actualizaciones futuras de tu aplicación
- Si pierdes estas credenciales, NO podrás actualizar tu app en Google Play

### Paso 2: Verificar que se crearon los archivos

Después de ejecutar el script, deberías tener:

- `build/flutter/android/app/upload-keystore.jks` - El archivo keystore
- `build/flutter/android/key.properties` - Archivo con las credenciales

### Paso 3: Construir la aplicación en modo release

Ahora puedes construir tu aplicación normalmente:

```bash
./build_android.sh --aab
```

O para construir ambos (APK y AAB):

```bash
./build_android.sh
```

La aplicación ahora se firmará automáticamente con tu keystore de release.

## Archivos generados

- `build/apk/app-release.apk` - APK firmado en modo release
- `build/aab/app-release.aab` - AAB firmado en modo release (para Google Play)

## Seguridad

- ✅ El archivo `key.properties` está en `.gitignore` y NO se subirá a git
- ✅ El archivo `upload-keystore.jks` está en `.gitignore` y NO se subirá a git
- ⚠️ **NUNCA** compartas estos archivos ni las contraseñas públicamente
- ⚠️ Haz una copia de seguridad segura del keystore y las credenciales

## Solución de problemas

### Error: "keytool no está instalado"

Instala Java JDK:
```bash
sudo apt-get install openjdk-17-jdk
```

### Error: "No se encuentra el keystore"

Asegúrate de haber ejecutado `./create_keystore.sh` primero.

### La app sigue firmándose en modo debug

1. Verifica que `build/flutter/android/key.properties` existe
2. Verifica que `build/flutter/android/app/upload-keystore.jks` existe
3. Limpia el build anterior: `cd build/flutter && flutter clean && cd ../..`
4. Vuelve a construir: `./build_android.sh`

## Verificar la firma

Para verificar que tu APK/AAB está firmado correctamente:

```bash
# Para APK
jarsigner -verify -verbose -certs build/apk/app-release.apk

# Para AAB (requiere bundletool)
# Primero extrae el APK del AAB y luego verifica
```

O usa:
```bash
keytool -printcert -jarfile build/apk/app-release.apk
```

## Actualizaciones futuras

Para futuras versiones de tu aplicación, simplemente:
1. Actualiza la versión en `pyproject.toml`
2. Ejecuta `./build_android.sh --aab`
3. Sube el nuevo AAB a Google Play Console

**No necesitas crear un nuevo keystore** - usa siempre el mismo que creaste inicialmente.

