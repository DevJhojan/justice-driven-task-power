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
# Funciones de construcción
################################################################################

build_apk() {
    print_section "Construyendo APK para Android"
    
    print_info "Ejecutando: flet build apk"
    flet build apk
    
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
    
    print_info "Ejecutando: flet build aab"
    flet build aab
    
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

