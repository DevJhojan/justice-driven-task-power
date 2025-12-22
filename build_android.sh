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
    
    print_info "Ejecutando: flet build apk"
    print_info "Flet detectará automáticamente las dependencias de pyproject.toml o requirements.txt"
    print_info "Flet debería usar el icono de: assets/app_icon.png (según pyproject.toml)"
    flet build apk
    
    # Reemplazar iconos personalizados después del build inicial
    # Esto asegura que los iconos estén en todas las resoluciones necesarias
    replace_icons
    
    # Si se reemplazaron iconos, reconstruir el APK para aplicar los cambios
    if [ -f "assets/app_icon.png" ] && command -v convert &> /dev/null && [ -d "build/flutter/android/app/src/main/res" ]; then
        print_info "Reconstruyendo APK con iconos personalizados..."
        cd build/flutter
        
        # Limpiar build anterior para asegurar que se usen los nuevos iconos
        flutter clean 2>/dev/null || true
        
        # Reconstruir el APK
        if flutter build apk --release 2>&1 | tee /tmp/flutter_build.log; then
            print_success "APK reconstruido exitosamente con iconos personalizados"
        else
            print_warning "Error al reconstruir APK. Verificando si el APK original existe..."
        fi
        
        cd ../..
        
        # Copiar el APK reconstruido si existe
        if [ -f "build/flutter/build/app/outputs/flutter-apk/app-release.apk" ]; then
            mkdir -p build/apk
            cp build/flutter/build/app/outputs/flutter-apk/app-release.apk build/apk/app-release.apk
            print_success "APK con iconos personalizados copiado a build/apk/app-release.apk"
        elif [ -f "build/apk/app-release.apk" ]; then
            print_info "APK original encontrado en build/apk/app-release.apk"
        fi
    else
        print_info "Usando APK generado por Flet (iconos pueden ser los por defecto si Flet no los detectó)"
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
    
    print_info "Ejecutando: flet build aab"
    print_info "Flet detectará automáticamente las dependencias de pyproject.toml o requirements.txt"
    print_info "Flet debería usar el icono de: assets/app_icon.png (según pyproject.toml)"
    flet build aab
    
    # Reemplazar iconos personalizados después del build inicial
    # Esto asegura que los iconos estén en todas las resoluciones necesarias
    replace_icons
    
    # Si se reemplazaron iconos, reconstruir el AAB para aplicar los cambios
    if [ -f "assets/app_icon.png" ] && command -v convert &> /dev/null && [ -d "build/flutter/android/app/src/main/res" ]; then
        print_info "Reconstruyendo AAB con iconos personalizados..."
        cd build/flutter
        
        # Limpiar build anterior para asegurar que se usen los nuevos iconos
        flutter clean 2>/dev/null || true
        
        # Reconstruir el AAB
        if flutter build appbundle --release 2>&1 | tee /tmp/flutter_build.log; then
            print_success "AAB reconstruido exitosamente con iconos personalizados"
        else
            print_warning "Error al reconstruir AAB. Verificando si el AAB original existe..."
        fi
        
        cd ../..
        
        # Copiar el AAB reconstruido si existe
        if [ -f "build/flutter/build/app/outputs/bundle/release/app-release.aab" ]; then
            mkdir -p build/aab
            cp build/flutter/build/app/outputs/bundle/release/app-release.aab build/aab/app-release.aab
            print_success "AAB con iconos personalizados copiado a build/aab/app-release.aab"
        elif [ -f "build/aab/app-release.aab" ]; then
            print_info "AAB original encontrado en build/aab/app-release.aab"
        fi
    else
        print_info "Usando AAB generado por Flet (iconos pueden ser los por defecto si Flet no los detectó)"
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

