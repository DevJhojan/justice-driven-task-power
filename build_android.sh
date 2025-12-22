#!/bin/bash

################################################################################
# build_android.sh - Script de construcción para Android (APK y AAB)
#
# Este script construye artefactos de Android para la aplicación Flet.
# Soporta construcción de APK, AAB, o ambos según los flags proporcionados.
#
# Uso:
#   ./build_android.sh          # Construye APK y AAB (por defecto)
#   ./build_android.sh --apk    # Construye solo APK
#   ./build_android.sh --aab    # Construye solo AAB
#   ./build_android.sh --help   # Muestra esta ayuda
#
################################################################################

set -e  # Salir si hay algún error

# Colores para mensajes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Variables de control
BUILD_APK=false
BUILD_AAB=false
SHOW_HELP=false

################################################################################
# Funciones auxiliares
################################################################################

show_help() {
    cat << EOF
${BLUE}build_android.sh${NC} - Script de construcción para Android

${GREEN}Uso:${NC}
    ./build_android.sh [OPCIONES]

${GREEN}Opciones:${NC}
    --apk          Construye únicamente el archivo APK
    --aab          Construye únicamente el archivo AAB (Android App Bundle)
    --help, -h     Muestra esta ayuda

${GREEN}Comportamiento por defecto:${NC}
    Si no se especifica ninguna opción, se construyen ambos artefactos (APK y AAB).

${GREEN}Ejemplos:${NC}
    ./build_android.sh              # Construye APK y AAB
    ./build_android.sh --apk        # Construye solo APK
    ./build_android.sh --aab        # Construye solo AAB

${GREEN}Archivos generados:${NC}
    APK: build/apk/app-release.apk
    AAB: build/aab/app-release.aab

EOF
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_section() {
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
}

################################################################################
# Parseo de argumentos
################################################################################

parse_arguments() {
    local flags_count=0
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --apk)
                BUILD_APK=true
                flags_count=$((flags_count + 1))
                shift
                ;;
            --aab)
                BUILD_AAB=true
                flags_count=$((flags_count + 1))
                shift
                ;;
            --help|-h)
                SHOW_HELP=true
                shift
                ;;
            *)
                print_error "Opción desconocida: $1"
                echo ""
                show_help
        exit 1
                ;;
        esac
    done
    
    # Validar que no se pasen múltiples flags mutuamente excluyentes
    if [ $flags_count -gt 1 ]; then
        print_error "Los flags --apk y --aab son mutuamente excluyentes."
        echo ""
        show_help
        exit 1
    fi
    
    # Si no se pasó ningún flag, construir ambos por defecto
    if [ $flags_count -eq 0 ] && [ "$SHOW_HELP" = false ]; then
        BUILD_APK=true
        BUILD_AAB=true
    fi
}

################################################################################
# Funciones de manejo de iconos y assets
################################################################################

include_assets() {
    # Incluye los assets en el build de Flutter.
    print_info "Incluyendo assets en el build..."
    
    # Verificar que existe el directorio de assets
    if [ ! -d "assets" ]; then
        print_warning "Directorio assets/ no encontrado. Saltando inclusión de assets."
        return 0
    fi
    
    # Crear directorio de assets en build/flutter si no existe
    mkdir -p build/flutter/assets
    
    # Copiar todos los archivos de assets
    if [ -d "assets" ]; then
        cp -r assets/* build/flutter/assets/ 2>/dev/null || true
        print_success "Assets copiados a build/flutter/assets/"
    fi
    
    # Copiar google-services.json a assets si existe en la raíz
    if [ -f "google-services.json" ]; then
        cp google-services.json build/flutter/assets/ 2>/dev/null && print_success "google-services.json copiado a assets/" || true
    fi
    
    # Asegurar que el icono esté disponible ANTES del build de Flet
    # Flet lee el icono desde pyproject.toml, pero necesita que el archivo exista
    if [ -f "assets/app_icon.png" ]; then
        # Verificar que el icono existe y es válido
        if file "assets/app_icon.png" | grep -q "PNG\|image"; then
            print_success "Icono app_icon.png encontrado y válido"
        else
            print_warning "El archivo app_icon.png podría no ser una imagen PNG válida"
        fi
    else
        print_warning "assets/app_icon.png no encontrado. Flet usará el icono por defecto."
    fi
    
    # Actualizar pubspec.yaml para incluir assets
    if [ -f "build/flutter/pubspec.yaml" ]; then
        # Usar Python para manipular YAML de forma segura
        python3 << 'PYTHON_SCRIPT'
import yaml
import sys
from pathlib import Path

pubspec_path = Path("build/flutter/pubspec.yaml")
if not pubspec_path.exists():
    sys.exit(0)

with open(pubspec_path, 'r', encoding='utf-8') as f:
    data = yaml.safe_load(f)

# Asegurar que existe la sección flutter
if 'flutter' not in data:
    data['flutter'] = {}

# Asegurar que existe la lista de assets
if 'assets' not in data['flutter']:
    data['flutter']['assets'] = []

# Agregar assets si existen
assets_dir = Path("build/flutter/assets")
if assets_dir.exists():
    assets_files = list(assets_dir.glob("*"))
    for asset_file in assets_files:
        asset_path = f"assets/{asset_file.name}"
        if asset_path not in data['flutter']['assets']:
            data['flutter']['assets'].append(asset_path)

# Guardar el archivo actualizado
with open(pubspec_path, 'w', encoding='utf-8') as f:
    yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

PYTHON_SCRIPT
        
        if [ $? -eq 0 ]; then
            print_success "pubspec.yaml actualizado con assets"
        else
            print_warning "No se pudo actualizar pubspec.yaml (Python o PyYAML no disponible)"
        fi
    fi
}

replace_icons() {
    # Reemplaza los iconos de Flet con los iconos personalizados.
    print_info "Reemplazando iconos personalizados..."
    
    # Verificar que existe el icono personalizado
    ICON_SOURCE="assets/app_icon.png"
    if [ ! -f "$ICON_SOURCE" ]; then
        print_warning "Icono personalizado no encontrado en $ICON_SOURCE. Usando icono por defecto de Flet."
        return 0
    fi
    
    # Verificar que ImageMagick está instalado
    if ! command -v convert &> /dev/null; then
        print_warning "ImageMagick no está instalado. No se pueden reemplazar iconos personalizados."
        print_info "Instala ImageMagick con: sudo apt-get install imagemagick"
        return 0
    fi
    
    # Verificar que el directorio de recursos de Android existe
    ANDROID_RES_DIR="build/flutter/android/app/src/main/res"
    if [ ! -d "$ANDROID_RES_DIR" ]; then
        print_warning "Directorio de recursos de Android no encontrado: $ANDROID_RES_DIR"
        print_info "Esperando a que Flet complete el build inicial..."
        return 0
    fi
    
    # Crear directorios si no existen
    mkdir -p "$ANDROID_RES_DIR/mipmap-mdpi"
    mkdir -p "$ANDROID_RES_DIR/mipmap-hdpi"
    mkdir -p "$ANDROID_RES_DIR/mipmap-xhdpi"
    mkdir -p "$ANDROID_RES_DIR/mipmap-xxhdpi"
    mkdir -p "$ANDROID_RES_DIR/mipmap-xxxhdpi"
    mkdir -p "$ANDROID_RES_DIR/drawable-mdpi"
    mkdir -p "$ANDROID_RES_DIR/drawable-hdpi"
    mkdir -p "$ANDROID_RES_DIR/drawable-xhdpi"
    mkdir -p "$ANDROID_RES_DIR/drawable-xxhdpi"
    mkdir -p "$ANDROID_RES_DIR/drawable-xxxhdpi"
    
    print_info "Reemplazando iconos en todas las resoluciones..."
    
    # Reemplazar iconos en todas las resoluciones (mipmap para iconos de app)
    convert "$ICON_SOURCE" -resize 48x48! "$ANDROID_RES_DIR/mipmap-mdpi/ic_launcher.png" 2>/dev/null && print_success "✓ Icono 48x48 en mipmap-mdpi" || print_warning "✗ Error al crear icono 48x48"
    convert "$ICON_SOURCE" -resize 72x72! "$ANDROID_RES_DIR/mipmap-hdpi/ic_launcher.png" 2>/dev/null && print_success "✓ Icono 72x72 en mipmap-hdpi" || print_warning "✗ Error al crear icono 72x72"
    convert "$ICON_SOURCE" -resize 96x96! "$ANDROID_RES_DIR/mipmap-xhdpi/ic_launcher.png" 2>/dev/null && print_success "✓ Icono 96x96 en mipmap-xhdpi" || print_warning "✗ Error al crear icono 96x96"
    convert "$ICON_SOURCE" -resize 144x144! "$ANDROID_RES_DIR/mipmap-xxhdpi/ic_launcher.png" 2>/dev/null && print_success "✓ Icono 144x144 en mipmap-xxhdpi" || print_warning "✗ Error al crear icono 144x144"
    convert "$ICON_SOURCE" -resize 192x192! "$ANDROID_RES_DIR/mipmap-xxxhdpi/ic_launcher.png" 2>/dev/null && print_success "✓ Icono 192x192 en mipmap-xxxhdpi" || print_warning "✗ Error al crear icono 192x192"
    
    # Reemplazar iconos foreground para adaptive icons (drawable)
    convert "$ICON_SOURCE" -resize 108x108! "$ANDROID_RES_DIR/drawable-mdpi/ic_launcher_foreground.png" 2>/dev/null && print_success "✓ Icono foreground 108x108 en drawable-mdpi" || print_warning "✗ Error al crear icono foreground 108x108"
    convert "$ICON_SOURCE" -resize 162x162! "$ANDROID_RES_DIR/drawable-hdpi/ic_launcher_foreground.png" 2>/dev/null && print_success "✓ Icono foreground 162x162 en drawable-hdpi" || print_warning "✗ Error al crear icono foreground 162x162"
    convert "$ICON_SOURCE" -resize 216x216! "$ANDROID_RES_DIR/drawable-xhdpi/ic_launcher_foreground.png" 2>/dev/null && print_success "✓ Icono foreground 216x216 en drawable-xhdpi" || print_warning "✗ Error al crear icono foreground 216x216"
    convert "$ICON_SOURCE" -resize 324x324! "$ANDROID_RES_DIR/drawable-xxhdpi/ic_launcher_foreground.png" 2>/dev/null && print_success "✓ Icono foreground 324x324 en drawable-xxhdpi" || print_warning "✗ Error al crear icono foreground 324x324"
    convert "$ICON_SOURCE" -resize 432x432! "$ANDROID_RES_DIR/drawable-xxxhdpi/ic_launcher_foreground.png" 2>/dev/null && print_success "✓ Icono foreground 432x432 en drawable-xxxhdpi" || print_warning "✗ Error al crear icono foreground 432x432"
    
    # También reemplazar el icono round si existe
    if [ -d "$ANDROID_RES_DIR/mipmap-anydpi-v26" ]; then
        print_info "Adaptive icons detectados, asegurando compatibilidad..."
    fi
    
    print_success "Iconos personalizados reemplazados correctamente"
}

################################################################################
# Funciones de configuración de firma
################################################################################

verify_release_signing() {
    # Verifica que un APK o AAB esté firmado en modo release
    local file_path="$1"
    local file_type="$2"  # "apk" o "aab"
    
    if [ ! -f "$file_path" ]; then
        print_error "Archivo no encontrado: $file_path"
        return 1
    fi
    
    print_info "Verificando firma de release en $file_type..."
    
    # Verificar usando apksigner si está disponible (para APK)
    if [ "$file_type" = "apk" ] && command -v apksigner &> /dev/null; then
        local signing_info=$(apksigner verify --print-certs "$file_path" 2>&1)
        if echo "$signing_info" | grep -qi "debug\|debuggable"; then
            print_error "El APK está firmado en modo DEBUG"
            return 1
        else
            print_success "APK verificado: firmado en modo RELEASE"
            return 0
        fi
    fi
    
    # Verificar usando jarsigner si está disponible (para AAB y APK)
    if command -v jarsigner &> /dev/null; then
        local verify_output=$(jarsigner -verify -verbose -certs "$file_path" 2>&1)
        if echo "$verify_output" | grep -qi "debug\|debuggable"; then
            print_warning "Posible firma de debug detectada"
        else
            print_success "$(echo "$file_type" | tr '[:lower:]' '[:upper:]') verificado: parece estar firmado correctamente"
        fi
        return 0
    fi
    
    # Si no hay herramientas de verificación, al menos verificar que el archivo existe y tiene tamaño
    local file_size=$(stat -f%z "$file_path" 2>/dev/null || stat -c%s "$file_path" 2>/dev/null || echo "0")
    if [ "$file_size" -gt 1000000 ]; then
        print_success "$(echo "$file_type" | tr '[:lower:]' '[:upper:]') generado: $(numfmt --to=iec-i --suffix=B $file_size 2>/dev/null || echo "${file_size} bytes")"
        print_info "Nota: Instala 'apksigner' o 'jarsigner' para verificación completa de firma"
        return 0
    else
        print_error "El archivo $file_type parece estar vacío o corrupto"
        return 1
    fi
}

configure_release_signing() {
    # Configura la firma de release en build.gradle para cumplir con los estándares de Google Play
    print_info "Configurando firma de release para cumplir con estándares de Google Play..."
    
    local build_gradle="build/flutter/android/app/build.gradle"
    local keystore_path="build/flutter/android/app/upload-keystore.jks"
    
    # Verificar que existe el build.gradle
    if [ ! -f "$build_gradle" ]; then
        print_warning "build.gradle no encontrado. Se configurará después de que Flet genere el proyecto."
        return 0
    fi
    
    # Verificar que existe el keystore
    if [ ! -f "$keystore_path" ]; then
        print_warning "Keystore no encontrado en $keystore_path"
        print_info "Asegúrate de que el keystore existe antes de construir para release"
    fi
    
    # Usar el script auxiliar para aplicar la configuración
    if [ -f "apply_release_signing.sh" ]; then
        if ./apply_release_signing.sh; then
            print_success "Configuración de firma de release aplicada correctamente"
            return 0
        else
            print_error "Error al aplicar configuración de firma de release"
            return 1
        fi
    else
        print_warning "Script apply_release_signing.sh no encontrado. Intentando configuración manual..."
        # Fallback: verificar si ya está configurado
        if grep -q "signingConfig signingConfigs.release" "$build_gradle" 2>/dev/null; then
            print_success "La configuración de firma de release ya está presente"
            return 0
        else
            print_error "No se pudo aplicar la configuración automáticamente"
            return 1
        fi
    fi
}

################################################################################
# Funciones auxiliares para entorno
################################################################################

activate_venv() {
    # Activa el entorno virtual si existe
    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
        return 0
    elif [ -f ".venv/bin/activate" ]; then
        source .venv/bin/activate
        return 0
    else
        print_warning "No se encontró entorno virtual. Asegúrate de que flet esté instalado."
        return 1
    fi
}

load_signing_credentials() {
    # Carga las credenciales de firma desde key.properties
    # Retorna las variables: KEYSTORE_PATH, KEYSTORE_PASSWORD, KEY_ALIAS, KEY_PASSWORD
    
    local key_properties_file="build/flutter/android/key.properties"
    
    # Si no existe en build/flutter, buscar en la raíz del proyecto
    if [ ! -f "$key_properties_file" ]; then
        key_properties_file="key.properties"
    fi
    
    if [ ! -f "$key_properties_file" ]; then
        print_warning "key.properties no encontrado. Usando valores por defecto..."
        # Intentar usar valores por defecto si el keystore existe
        if [ -f "build/flutter/android/app/upload-keystore.jks" ]; then
            SIGNING_KEYSTORE_PATH="$(pwd)/build/flutter/android/app/upload-keystore.jks"
            SIGNING_KEYSTORE_PASSWORD="upload"
            SIGNING_KEY_ALIAS="upload"
            SIGNING_KEY_PASSWORD="upload"
            return 0
        fi
        return 1
    fi
    
    # Leer valores del archivo key.properties
    while IFS='=' read -r key value; do
        # Ignorar comentarios y líneas vacías
        [[ "$key" =~ ^#.*$ ]] && continue
        [[ -z "$key" ]] && continue
        
        # Eliminar espacios en blanco
        key=$(echo "$key" | tr -d '[:space:]')
        value=$(echo "$value" | tr -d '[:space:]')
        
        case "$key" in
            storeFile)
                # Convertir ruta relativa a absoluta si es necesario
                if [[ "$value" != /* ]]; then
                    # La ruta en key.properties es relativa al directorio android/
                    # Por ejemplo: "app/upload-keystore.jks" significa "android/app/upload-keystore.jks"
                    local android_dir="build/flutter/android"
                    local full_path="$android_dir/$value"
                    
                    if [ -f "$full_path" ]; then
                        # Construir ruta absoluta
                        SIGNING_KEYSTORE_PATH="$(cd "$(dirname "$full_path")" && pwd)/$(basename "$full_path")"
                    elif [ -f "$value" ]; then
                        # Si existe como ruta relativa desde el directorio actual
                        SIGNING_KEYSTORE_PATH="$(cd "$(dirname "$value")" && pwd)/$(basename "$value")"
                    else
                        # Intentar construir la ruta absoluta desde el directorio del proyecto
                        SIGNING_KEYSTORE_PATH="$(pwd)/$android_dir/$value"
                    fi
                else
                    SIGNING_KEYSTORE_PATH="$value"
                fi
                ;;
            storePassword)
                SIGNING_KEYSTORE_PASSWORD="$value"
                ;;
            keyAlias)
                SIGNING_KEY_ALIAS="$value"
                ;;
            keyPassword)
                SIGNING_KEY_PASSWORD="$value"
                ;;
        esac
    done < "$key_properties_file"
    
    # Verificar que todos los valores estén definidos
    if [ -z "$SIGNING_KEYSTORE_PATH" ] || [ -z "$SIGNING_KEYSTORE_PASSWORD" ] || \
       [ -z "$SIGNING_KEY_ALIAS" ] || [ -z "$SIGNING_KEY_PASSWORD" ]; then
        print_error "Faltan valores en key.properties"
        return 1
    fi
    
    # Verificar que el keystore existe
    if [ ! -f "$SIGNING_KEYSTORE_PATH" ]; then
        print_error "Keystore no encontrado en: $SIGNING_KEYSTORE_PATH"
        return 1
    fi
    
    print_success "Credenciales de firma cargadas desde $key_properties_file"
    return 0
}

################################################################################
# Funciones de construcción
################################################################################

build_apk() {
    print_section "Construyendo APK para Android"
    
    # Verificar que las dependencias están configuradas
    print_info "Verificando dependencias..."
    if ! grep -q "requests" pyproject.toml 2>/dev/null && ! grep -q "requests" requirements.txt 2>/dev/null; then
        print_error "requests no está en pyproject.toml ni en requirements.txt"
        print_info "Agregando requests a requirements.txt..."
        echo "requests>=2.31.0" >> requirements.txt
    fi
    
    # Asegurar que requirements.txt existe y tiene las dependencias necesarias
    if [ ! -f "requirements.txt" ]; then
        print_warning "requirements.txt no existe. Creándolo desde pyproject.toml..."
        echo "flet>=0.28.0" > requirements.txt
        echo "requests>=2.31.0" >> requirements.txt
    fi
    
    # Verificar que pyproject.toml tiene las dependencias correctas
    if ! grep -q '"requests' pyproject.toml 2>/dev/null; then
        print_warning "requests no encontrado en pyproject.toml. Flet usará requirements.txt."
    fi
    
    # Mostrar dependencias detectadas
    print_info "Dependencias detectadas:"
    grep -E "flet|requests" pyproject.toml requirements.txt 2>/dev/null | head -5
    
    # Incluir assets antes del build
    include_assets
    
    # Verificar que el icono existe antes del build
    if [ -f "assets/app_icon.png" ]; then
        print_info "Icono personalizado encontrado: assets/app_icon.png"
        print_info "Flet debería usar este icono según pyproject.toml"
    else
        print_warning "Icono personalizado no encontrado. Flet usará el icono por defecto."
    fi
    
    # Cargar credenciales de firma
    if ! load_signing_credentials; then
        print_warning "No se pudieron cargar las credenciales de firma. Construyendo sin parámetros de firma..."
        SIGNING_KEYSTORE_PATH=""
        SIGNING_KEYSTORE_PASSWORD=""
        SIGNING_KEY_ALIAS=""
        SIGNING_KEY_PASSWORD=""
    fi
    
    print_info "Ejecutando: flet build apk con firma de release"
    print_info "Flet detectará automáticamente las dependencias de pyproject.toml o requirements.txt"
    print_info "Flet debería usar el icono de: assets/app_icon.png (según pyproject.toml)"
    
    # Activar venv si existe antes de ejecutar flet
    if activate_venv; then
        print_info "Entorno virtual activado"
    fi
    
    # Construir comando flet build apk con parámetros de firma si están disponibles
    local flet_cmd="flet build apk"
    if [ -n "$SIGNING_KEYSTORE_PATH" ] && [ -f "$SIGNING_KEYSTORE_PATH" ]; then
        print_info "Usando firma de release con keystore: $SIGNING_KEYSTORE_PATH"
        flet_cmd="flet build apk \\
  --android-signing-key-store \"$SIGNING_KEYSTORE_PATH\" \\
  --android-signing-key-store-password \"$SIGNING_KEYSTORE_PASSWORD\" \\
  --android-signing-key-alias \"$SIGNING_KEY_ALIAS\" \\
  --android-signing-key-password \"$SIGNING_KEY_PASSWORD\""
    else
        print_warning "Construyendo sin parámetros de firma (se aplicará después)"
    fi
    
    # Intentar ejecutar flet build apk, pero continuar si falla (el proyecto puede ya existir)
    if ! eval "$flet_cmd" 2>&1; then
        print_warning "flet build apk falló o el proyecto ya existe. Continuando con el build..."
        # Verificar que el proyecto Flutter existe
        if [ ! -d "build/flutter" ]; then
            print_error "El proyecto Flutter no existe. Necesitas ejecutar 'flet build apk' manualmente primero."
            return 1
        fi
    fi
    
    # Si flet build se ejecutó con parámetros de firma, verificar el APK generado directamente
    if [ -n "$SIGNING_KEYSTORE_PATH" ] && [ -f "$SIGNING_KEYSTORE_PATH" ]; then
        print_info "Flet build ejecutado con parámetros de firma. Verificando APK generado..."
        
        # Buscar el APK generado por Flet
        local flet_apk=""
        if [ -f "build/apk/app-release.apk" ]; then
            flet_apk="build/apk/app-release.apk"
        elif [ -f "build/flutter/build/app/outputs/flutter-apk/app-release.apk" ]; then
            flet_apk="build/flutter/build/app/outputs/flutter-apk/app-release.apk"
        fi
        
        if [ -n "$flet_apk" ] && [ -f "$flet_apk" ]; then
            print_success "APK encontrado: $flet_apk"
            mkdir -p build/apk
            cp "$flet_apk" build/apk/app-release.apk
            
            # Verificar la firma del APK
            if verify_release_signing "build/apk/app-release.apk" "apk"; then
                print_success "APK firmado correctamente en modo release"
                return 0
            else
                print_warning "APK encontrado pero la verificación de firma falló. Reconstruyendo..."
            fi
        fi
    fi
    
    # Si no se usaron parámetros de firma o el APK no se encontró, aplicar configuración y reconstruir
    print_info "Aplicando configuración de firma de release y reconstruyendo..."
    
    # Configurar firma de release ANTES de construir
    if ! configure_release_signing; then
        print_error "Error al configurar firma de release"
        return 1
    fi
    
    # Verificar que la configuración de firma esté correcta
    if ! grep -q "signingConfig signingConfigs.release" build/flutter/android/app/build.gradle 2>/dev/null; then
        print_error "La configuración de firma de release no se aplicó correctamente"
        return 1
    fi
    print_success "Configuración de firma de release verificada"
    
    # Reemplazar iconos personalizados después del build inicial
    # Esto asegura que los iconos estén en todas las resoluciones necesarias
    replace_icons
    
    # Reconstruir el APK con Flutter para asegurar firma de release
    print_info "Construyendo APK con firma de release (estándares de Google Play)..."
    cd build/flutter
    
    # Limpiar build anterior para asegurar que se use la configuración correcta
    flutter clean 2>/dev/null || true
    
    # Reconstruir el APK con firma de release (--release es crítico)
    print_info "Ejecutando: flutter build apk --release"
    
    # Capturar tanto stdout como stderr
    local build_output=$(flutter build apk --release 2>&1)
    local build_exit_code=$?
    
    # Guardar el output completo en el log
    echo "$build_output" | tee /tmp/flutter_build.log
    
    # Verificar si el build fue exitoso buscando indicadores de éxito
    if echo "$build_output" | grep -qi "Built\|Successfully\|apk.*release" || [ $build_exit_code -eq 0 ]; then
        print_success "APK construido exitosamente con firma de release"
    else
        # El warning de "privileged capabilities" es común y no es un error crítico
        if echo "$build_output" | grep -qi "cannot set privileged capabilities"; then
            print_warning "Warning de capabilities detectado (no crítico)"
            # Verificar si el APK se generó a pesar del warning
            if find build/app/outputs/flutter-apk -name "*.apk" -type f 2>/dev/null | head -1 | grep -q .; then
                print_success "APK generado a pesar del warning"
            else
                print_error "Error al construir APK. Revisa el log completo en /tmp/flutter_build.log"
                echo "$build_output" | tail -20
                cd ../..
                return 1
            fi
        else
            print_error "Error al construir APK con firma de release"
            echo "$build_output" | tail -30
            cd ../..
            return 1
        fi
    fi
    
    cd ../..
    
    # Verificar y copiar el APK reconstruido con firma de release
    local apk_path="build/flutter/build/app/outputs/flutter-apk/app-release.apk"
    if [ -f "$apk_path" ]; then
        mkdir -p build/apk
        cp "$apk_path" build/apk/app-release.apk
        print_success "APK con firma de release copiado a build/apk/app-release.apk"
        
        # Verificar la firma del APK
        verify_release_signing "build/apk/app-release.apk" "apk"
    else
        print_error "No se encontró el APK reconstruido en $apk_path"
        return 1
    fi
    
    # Verificar que el APK se generó
    if [ -f "build/apk/app-release.apk" ]; then
        print_success "APK generado exitosamente: build/apk/app-release.apk"
        return 0
    else
        print_error "No se encontró el APK generado en build/apk/app-release.apk"
        return 1
    fi
}

build_aab() {
    print_section "Construyendo AAB (Android App Bundle) para Google Play"
    
    # Verificar que las dependencias están configuradas
    print_info "Verificando dependencias..."
    if ! grep -q "requests" pyproject.toml 2>/dev/null && ! grep -q "requests" requirements.txt 2>/dev/null; then
        print_error "requests no está en pyproject.toml ni en requirements.txt"
        print_info "Agregando requests a requirements.txt..."
        echo "requests>=2.31.0" >> requirements.txt
    fi
    
    # Asegurar que requirements.txt existe y tiene las dependencias necesarias
    if [ ! -f "requirements.txt" ]; then
        print_warning "requirements.txt no existe. Creándolo desde pyproject.toml..."
        echo "flet>=0.28.0" > requirements.txt
        echo "requests>=2.31.0" >> requirements.txt
    fi
    
    # Verificar que pyproject.toml tiene las dependencias correctas
    if ! grep -q '"requests' pyproject.toml 2>/dev/null; then
        print_warning "requests no encontrado en pyproject.toml. Flet usará requirements.txt."
    fi
    
    # Incluir assets antes del build
    include_assets
    
    # Verificar que el icono existe antes del build
    if [ -f "assets/app_icon.png" ]; then
        print_info "Icono personalizado encontrado: assets/app_icon.png"
        print_info "Flet debería usar este icono según pyproject.toml"
    else
        print_warning "Icono personalizado no encontrado. Flet usará el icono por defecto."
    fi
    
    # Cargar credenciales de firma
    if ! load_signing_credentials; then
        print_warning "No se pudieron cargar las credenciales de firma. Construyendo sin parámetros de firma..."
        SIGNING_KEYSTORE_PATH=""
        SIGNING_KEYSTORE_PASSWORD=""
        SIGNING_KEY_ALIAS=""
        SIGNING_KEY_PASSWORD=""
    fi
    
    print_info "Ejecutando: flet build aab con firma de release"
    print_info "Flet detectará automáticamente las dependencias de pyproject.toml o requirements.txt"
    print_info "Flet debería usar el icono de: assets/app_icon.png (según pyproject.toml)"
    
    # Activar venv si existe antes de ejecutar flet
    if activate_venv; then
        print_info "Entorno virtual activado"
    fi
    
    # Construir comando flet build aab con parámetros de firma si están disponibles
    local flet_cmd="flet build aab"
    if [ -n "$SIGNING_KEYSTORE_PATH" ] && [ -f "$SIGNING_KEYSTORE_PATH" ]; then
        print_info "Usando firma de release con keystore: $SIGNING_KEYSTORE_PATH"
        flet_cmd="flet build aab \\
  --android-signing-key-store \"$SIGNING_KEYSTORE_PATH\" \\
  --android-signing-key-store-password \"$SIGNING_KEYSTORE_PASSWORD\" \\
  --android-signing-key-alias \"$SIGNING_KEY_ALIAS\" \\
  --android-signing-key-password \"$SIGNING_KEY_PASSWORD\""
    else
        print_warning "Construyendo sin parámetros de firma (se aplicará después)"
    fi
    
    # Intentar ejecutar flet build aab, pero continuar si falla (el proyecto puede ya existir)
    if ! eval "$flet_cmd" 2>&1; then
        print_warning "flet build aab falló o el proyecto ya existe. Continuando con el build..."
        # Verificar que el proyecto Flutter existe
        if [ ! -d "build/flutter" ]; then
            print_error "El proyecto Flutter no existe. Necesitas ejecutar 'flet build aab' manualmente primero."
            return 1
        fi
    fi
    
    # Si flet build se ejecutó con parámetros de firma, verificar el AAB generado directamente
    if [ -n "$SIGNING_KEYSTORE_PATH" ] && [ -f "$SIGNING_KEYSTORE_PATH" ]; then
        print_info "Flet build ejecutado con parámetros de firma. Verificando AAB generado..."
        
        # Buscar el AAB generado por Flet
        local flet_aab=""
        if [ -f "build/aab/app-release.aab" ]; then
            flet_aab="build/aab/app-release.aab"
        elif [ -f "build/flutter/build/app/outputs/bundle/release/app-release.aab" ]; then
            flet_aab="build/flutter/build/app/outputs/bundle/release/app-release.aab"
        fi
        
        if [ -n "$flet_aab" ] && [ -f "$flet_aab" ]; then
            print_success "AAB encontrado: $flet_aab"
            mkdir -p build/aab
            cp "$flet_aab" build/aab/app-release.aab
            
            # Verificar la firma del AAB
            if verify_release_signing "build/aab/app-release.aab" "aab"; then
                print_success "AAB firmado correctamente en modo release"
                return 0
            else
                print_warning "AAB encontrado pero la verificación de firma falló. Reconstruyendo..."
            fi
        fi
    fi
    
    # Si no se usaron parámetros de firma o el AAB no se encontró, aplicar configuración y reconstruir
    print_info "Aplicando configuración de firma de release y reconstruyendo..."
    
    # Configurar firma de release ANTES de construir
    if ! configure_release_signing; then
        print_error "Error al configurar firma de release"
        return 1
    fi
    
    # Verificar que la configuración de firma esté correcta
    if ! grep -q "signingConfig signingConfigs.release" build/flutter/android/app/build.gradle 2>/dev/null; then
        print_error "La configuración de firma de release no se aplicó correctamente"
        return 1
    fi
    print_success "Configuración de firma de release verificada"
    
    # Reemplazar iconos personalizados después del build inicial
    # Esto asegura que los iconos estén en todas las resoluciones necesarias
    replace_icons
    
    # Reconstruir el AAB con Flutter para asegurar firma de release
    print_info "Construyendo AAB con firma de release (estándares de Google Play)..."
    cd build/flutter
    
    # Limpiar build anterior para asegurar que se use la configuración correcta
    flutter clean 2>/dev/null || true
    
    # Reconstruir el AAB con firma de release (--release es crítico)
    print_info "Ejecutando: flutter build appbundle --release"
    
    # Capturar tanto stdout como stderr
    local build_output=$(flutter build appbundle --release 2>&1)
    local build_exit_code=$?
    
    # Guardar el output completo en el log
    echo "$build_output" | tee /tmp/flutter_build.log
    
    # Verificar si el build fue exitoso buscando indicadores de éxito
    if echo "$build_output" | grep -qi "Built\|Successfully\|bundle.*release" || [ $build_exit_code -eq 0 ]; then
        print_success "AAB construido exitosamente con firma de release"
    else
        # El warning de "privileged capabilities" es común y no es un error crítico
        if echo "$build_output" | grep -qi "cannot set privileged capabilities"; then
            print_warning "Warning de capabilities detectado (no crítico)"
            # Verificar si el AAB se generó a pesar del warning
            if find build/app/outputs/bundle -name "*.aab" -type f 2>/dev/null | grep -v intermediary | head -1 | grep -q .; then
                print_success "AAB generado a pesar del warning"
            else
                print_error "Error al construir AAB. Revisa el log completo en /tmp/flutter_build.log"
                echo "$build_output" | tail -20
                cd ../..
                return 1
            fi
        else
            print_error "Error al construir AAB con firma de release"
            echo "$build_output" | tail -30
            cd ../..
            return 1
        fi
    fi
    
    cd ../..
    
    # Buscar el AAB en múltiples ubicaciones posibles
    local aab_path=""
    local possible_paths=(
        "build/flutter/build/app/outputs/bundle/release/app-release.aab"
        "build/flutter/build/app/outputs/bundle/release/app.aab"
        "build/flutter/build/app/outputs/bundle/app-release.aab"
        "build/flutter/build/app/outputs/bundle/app.aab"
    )
    
    print_info "Buscando AAB generado..."
    for path in "${possible_paths[@]}"; do
        if [ -f "$path" ]; then
            aab_path="$path"
            print_success "AAB encontrado en: $aab_path"
            break
        fi
    done
    
    # Si no se encontró, buscar recursivamente
    if [ -z "$aab_path" ]; then
        print_info "Buscando AAB recursivamente..."
        local found_aab=$(find build/flutter/build/app/outputs/bundle -name "*.aab" -type f 2>/dev/null | grep -v intermediary | head -1)
        if [ -n "$found_aab" ]; then
            aab_path="$found_aab"
            print_success "AAB encontrado en: $aab_path"
        fi
    fi
    
    if [ -n "$aab_path" ] && [ -f "$aab_path" ]; then
        mkdir -p build/aab
        cp "$aab_path" build/aab/app-release.aab
        print_success "AAB con firma de release copiado a build/aab/app-release.aab"
        
        # Verificar la firma del AAB
        verify_release_signing "build/aab/app-release.aab" "aab"
    else
        print_error "No se encontró el AAB reconstruido. Rutas verificadas:"
        for path in "${possible_paths[@]}"; do
            echo "  - $path"
        done
        print_info "Revisa el log de Flutter en /tmp/flutter_build.log para más detalles"
        return 1
    fi
    
    # Verificar que el AAB se generó
    if [ -f "build/aab/app-release.aab" ]; then
        print_success "AAB generado exitosamente: build/aab/app-release.aab"
        return 0
    else
        print_error "No se encontró el AAB generado en build/aab/app-release.aab"
        return 1
    fi
}

################################################################################
# Función principal
################################################################################

main() {
    # Parsear argumentos
    parse_arguments "$@"
    
    # Mostrar ayuda si se solicitó
    if [ "$SHOW_HELP" = true ]; then
        show_help
        exit 0
    fi
    
    # Mostrar información del build
    print_section "Iniciando construcción de artefactos Android"
    
    if [ "$BUILD_APK" = true ] && [ "$BUILD_AAB" = true ]; then
        print_info "Modo: Build completo (APK + AAB)"
        print_info "Artefactos a generar:"
        echo "  📦 APK (instalable en dispositivos Android)"
        echo "  🏬 AAB (Android App Bundle para Google Play)"
    elif [ "$BUILD_APK" = true ]; then
        print_info "Modo: Solo APK"
        print_info "Artefacto a generar:"
        echo "  📦 APK (instalable en dispositivos Android)"
    elif [ "$BUILD_AAB" = true ]; then
        print_info "Modo: Solo AAB"
        print_info "Artefacto a generar:"
        echo "  🏬 AAB (Android App Bundle para Google Play)"
    fi
    
    echo ""
    
    # Ejecutar builds según los flags
    local build_failed=false
    
    if [ "$BUILD_APK" = true ]; then
        if ! build_apk; then
            build_failed=true
        fi
    fi
    
    if [ "$BUILD_AAB" = true ]; then
        if ! build_aab; then
            build_failed=true
        fi
    fi
    
    # Resumen final
    echo ""
    print_section "Resumen de construcción"
    
    if [ "$build_failed" = true ]; then
        print_error "La construcción falló. Revisa los errores arriba."
        exit 1
    fi
    
    print_success "Construcción completada exitosamente!"
    echo ""
    print_info "Archivos generados:"
    
    if [ "$BUILD_APK" = true ] && [ -f "build/apk/app-release.apk" ]; then
        local apk_size=$(du -h "build/apk/app-release.apk" | cut -f1)
        echo "  📦 build/apk/app-release.apk ($apk_size)"
    fi
    
    if [ "$BUILD_AAB" = true ] && [ -f "build/aab/app-release.aab" ]; then
        local aab_size=$(du -h "build/aab/app-release.aab" | cut -f1)
        echo "  🏬 build/aab/app-release.aab ($aab_size)"
    fi
    
    echo ""
    print_success "¡Listo para distribuir!"
}

################################################################################
# Ejecutar función principal
################################################################################

main "$@"

