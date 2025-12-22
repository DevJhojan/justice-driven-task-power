#!/bin/bash
# Script para aplicar configuración de firma de release al build.gradle

set -e

# Obtener el directorio del script o usar el directorio actual
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR" || exit 1

BUILD_GRADLE="build/flutter/android/app/build.gradle"
KEY_PROPERTIES="build/flutter/android/key.properties"

if [ ! -f "$BUILD_GRADLE" ]; then
    echo "Error: build.gradle no encontrado en $BUILD_GRADLE"
    exit 1
fi

# Asegurar que key.properties existe
if [ ! -f "$KEY_PROPERTIES" ]; then
    echo "Creando key.properties..."
    mkdir -p "$(dirname "$KEY_PROPERTIES")"
    cat > "$KEY_PROPERTIES" << EOF
storePassword=upload
keyPassword=upload
keyAlias=upload
storeFile=app/upload-keystore.jks
EOF
fi

# Crear backup del build.gradle
cp "$BUILD_GRADLE" "${BUILD_GRADLE}.bak"

# Usar Python para modificar el build.gradle de forma segura
python3 << PYTHON_SCRIPT
import re
import sys
import os

# Usar el directorio de trabajo actual (ya configurado por cd arriba)
script_dir = os.getcwd()
build_gradle_path = os.path.join(script_dir, "build/flutter/android/app/build.gradle")

try:
    with open(build_gradle_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # 1. Agregar carga de key.properties después de flutterVersionName si no existe
    if 'def keystoreProperties' not in content:
        pattern = r'(def flutterVersionName = localProperties\.getProperty\([\'"]flutter\.versionName[\'"]\)\s+if \(flutterVersionName == null\) \{\s+flutterVersionName = [\'"]1\.0[\'"]\s+\})'
        replacement = r'''\1

// Cargar propiedades de la keystore para firma de release
def keystoreProperties = new Properties()
def keystorePropertiesFile = rootProject.file('key.properties')
if (keystorePropertiesFile.exists()) {
    keystorePropertiesFile.withReader('UTF-8') { reader ->
        keystoreProperties.load(reader)
    }
}'''
        content = re.sub(pattern, replacement, content)
    
    # 2. Agregar signingConfigs después de sourceSets si no existe
    if 'signingConfigs {' not in content:
        pattern = r'(sourceSets \{\s+main\.java\.srcDirs \+= [\'"]src/main/kotlin[\'"]\s+\})'
        replacement = r'''\1

    // Configuración de firma para release
    signingConfigs {
        release {
            if (keystorePropertiesFile.exists()) {
                keyAlias keystoreProperties['keyAlias']
                keyPassword keystoreProperties['keyPassword']
                def keystoreFile = keystoreProperties['storeFile']
                if (keystoreFile) {
                    // La ruta en key.properties es relativa al directorio android/
                    storeFile keystoreFile.startsWith('/') ? file(keystoreFile) : file("../${keystoreFile}")
                }
                storePassword keystoreProperties['storePassword']
            }
        }
    }'''
        content = re.sub(pattern, replacement, content)
    
    # 3. Cambiar signingConfig de debug a release en buildTypes
    content = re.sub(
        r'signingConfig signingConfigs\.debug',
        'signingConfig signingConfigs.release',
        content
    )
    
    # 4. Si no hay signingConfig en buildTypes release, agregarlo
    if 'buildTypes' in content and 'release' in content:
        # Buscar el bloque release y asegurar que tenga signingConfig
        pattern = r'(buildTypes \{\s+release \{[^}]*?)(\s+\})'
        def replace_buildtypes(match):
            release_block = match.group(1)
            closing = match.group(2)
            
            if 'signingConfig' not in release_block:
                # Agregar signingConfig antes del cierre
                return release_block + '\n            signingConfig signingConfigs.release' + closing
            return match.group(0)
        
        content = re.sub(pattern, replace_buildtypes, content, flags=re.DOTALL)
    
    # Escribir el contenido modificado
    if content != original_content:
        with open(build_gradle_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print("✓ Configuración de firma de release aplicada correctamente")
        sys.exit(0)
    else:
        # Verificar si ya está configurado correctamente
        if 'signingConfig signingConfigs.release' in content:
            print("✓ La configuración de firma de release ya está presente")
            sys.exit(0)
        else:
            print("⚠ No se pudo aplicar la configuración automáticamente")
            sys.exit(1)
            
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
PYTHON_SCRIPT

EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo "Configuración de firma de release aplicada exitosamente"
else
    echo "Error al aplicar configuración de firma"
    # Restaurar backup si hay error
    if [ -f "${BUILD_GRADLE}.bak" ]; then
        mv "${BUILD_GRADLE}.bak" "$BUILD_GRADLE"
    fi
    exit 1
fi

# Eliminar backup si todo salió bien
rm -f "${BUILD_GRADLE}.bak"

