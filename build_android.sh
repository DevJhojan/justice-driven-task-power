#!/bin/bash
# Script para construir APK y AAB (Android App Bundle) para Google Play
# Incluye inyección manual de wsgiref para soporte OAuth2 en Android
#
# Uso:
#   ./build_android.sh          # Construye APK y AAB (modo completo)
#   ./build_android.sh --apk    # Construye solo APK
#   ./build_android.sh --aab    # Construye solo AAB
#   ./build_android.sh --help   # Muestra esta ayuda

set -e

# Colores para output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Variables de control de build
BUILD_APK=false
BUILD_AAB=false
SHOW_HELP=false

# Función para mostrar ayuda
show_help() {
    cat << EOF
${BLUE}========================================${NC}
${BLUE}Script de Build para Android${NC}
${BLUE}========================================${NC}

${GREEN}Uso:${NC}
    ./build_android.sh [OPCIÓN]

${GREEN}Opciones:${NC}
    --apk          Construye únicamente el archivo APK (instalable en dispositivos)
    --aab          Construye únicamente el archivo AAB (para Google Play Store)
    --help, -h     Muestra esta ayuda

${GREEN}Modo por defecto:${NC}
    Si no se especifica ninguna opción, se construyen ambos artefactos (APK + AAB)

${GREEN}Ejemplos:${NC}
    ./build_android.sh              # Construye APK y AAB
    ./build_android.sh --apk        # Solo APK
    ./build_android.sh --aab        # Solo AAB

${GREEN}Notas:${NC}
    - El script lee la configuración desde pyproject.toml
    - Incluye automáticamente wsgiref para soporte OAuth2
    - Los assets y iconos se incluyen automáticamente
EOF
}

# Parsear argumentos de línea de comandos
parse_arguments() {
    local apk_count=0
    local aab_count=0
    
    for arg in "$@"; do
        case "$arg" in
            --apk)
                BUILD_APK=true
                apk_count=$((apk_count + 1))
                ;;
            --aab)
                BUILD_AAB=true
                aab_count=$((aab_count + 1))
                ;;
            --help|-h)
                SHOW_HELP=true
                ;;
            *)
                echo -e "${RED}Error: Flag desconocido: $arg${NC}" >&2
                echo -e "${YELLOW}Usa --help para ver las opciones disponibles${NC}" >&2
                exit 1
                ;;
        esac
    done
    
    # Si se muestra ayuda, salir después de mostrarla
    if [ "$SHOW_HELP" = true ]; then
        show_help
        exit 0
    fi
    
    # Si se pasaron ambos flags, es un error
    if [ "$apk_count" -gt 0 ] && [ "$aab_count" -gt 0 ]; then
        echo -e "${RED}Error: Los flags --apk y --aab son mutuamente excluyentes${NC}" >&2
        echo -e "${YELLOW}Usa --help para ver las opciones disponibles${NC}" >&2
        exit 1
    fi
    
    # Si no se pasó ningún flag, construir ambos (modo completo)
    if [ "$apk_count" -eq 0 ] && [ "$aab_count" -eq 0 ]; then
        BUILD_APK=true
        BUILD_AAB=true
    fi
}

# Función para mostrar información del build
show_build_info() {
    echo -e "${BLUE}========================================${NC}"
    if [ "$BUILD_APK" = true ] && [ "$BUILD_AAB" = true ]; then
        echo -e "${BLUE}Construyendo APK y AAB para Android${NC}"
        echo -e "${BLUE}Modo: ${GREEN}Completo${NC}${BLUE} (APK + AAB)${NC}"
    elif [ "$BUILD_APK" = true ]; then
        echo -e "${BLUE}Construyendo APK para Android${NC}"
        echo -e "${BLUE}Modo: ${GREEN}Solo APK${NC}"
    elif [ "$BUILD_AAB" = true ]; then
        echo -e "${BLUE}Construyendo AAB para Google Play${NC}"
        echo -e "${BLUE}Modo: ${GREEN}Solo AAB${NC}"
    fi
    echo -e "${BLUE}========================================${NC}"
}

# Leer información del proyecto desde pyproject.toml
read_project_info() {
    if [ -f "pyproject.toml" ]; then
        PROJECT_NAME_RAW=$(grep -E "^name\s*=" pyproject.toml | sed 's/.*= *"\(.*\)".*/\1/' | head -1 | tr -d ' ')
        PROJECT_NAME=$(echo "$PROJECT_NAME_RAW" | sed 's/-/ /g' | sed 's/\b\(.\)/\u\1/g')
        PROJECT_DESCRIPTION=$(grep -E "^description\s*=" pyproject.toml | sed 's/.*= *"\(.*\)".*/\1/' | head -1 | tr -d ' ')
        PROJECT_VERSION=$(grep -E "^version\s*=" pyproject.toml | sed 's/.*= *"\(.*\)".*/\1/' | head -1 | tr -d ' ')
        
        if [ -z "$PROJECT_NAME_RAW" ]; then
            echo -e "${RED}Error: No se pudo leer 'name' desde pyproject.toml${NC}"
            exit 1
        fi
        
        if [ -z "$PROJECT_VERSION" ]; then
            echo -e "${RED}Error: No se pudo leer 'version' desde pyproject.toml${NC}"
            exit 1
        fi
        
        if [ -z "$PROJECT_DESCRIPTION" ]; then
            PROJECT_DESCRIPTION="Aplicación móvil desarrollada con Flet"
            echo -e "${YELLOW}Advertencia: 'description' no encontrada en pyproject.toml, usando valor por defecto${NC}"
        fi
        
        echo -e "${BLUE}Información del proyecto (desde pyproject.toml):${NC}"
        echo -e "  Nombre: ${GREEN}$PROJECT_NAME${NC}"
        echo -e "  Versión: ${GREEN}$PROJECT_VERSION${NC}"
        echo -e "  Descripción: ${GREEN}$PROJECT_DESCRIPTION${NC}"
    else
        echo -e "${RED}Error: pyproject.toml no encontrado${NC}"
        exit 1
    fi
}

# Función para inyectar wsgiref manualmente
inject_wsgiref() {
    echo -e "${BLUE}Inyectando wsgiref manualmente...${NC}"
    
    # Verificar que existe build/python/site-packages
    if [ ! -d "build/python/site-packages" ]; then
        echo -e "${YELLOW}Advertencia: build/python/site-packages no existe aún. Se creará después del primer build.${NC}"
        return 0
    fi
    
    # Obtener la ruta de wsgiref usando Python
    WSGIREF_PATH=$(python3 -c "import wsgiref; import os; print(os.path.dirname(wsgiref.__file__))" 2>/dev/null || echo "")
    
    if [ -z "$WSGIREF_PATH" ]; then
        echo -e "${YELLOW}Advertencia: No se pudo encontrar wsgiref en el sistema. Intentando ubicación estándar...${NC}"
        # Intentar ubicaciones estándar
        for path in "/usr/lib/python3"*"/wsgiref" "/usr/local/lib/python3"*"/wsgiref" "$HOME/.local/lib/python3"*"/wsgiref"; do
            if [ -d "$path" ]; then
                WSGIREF_PATH="$path"
                break
            fi
        done
    fi
    
    if [ -z "$WSGIREF_PATH" ] || [ ! -d "$WSGIREF_PATH" ]; then
        echo -e "${RED}Error: No se pudo encontrar wsgiref en el sistema${NC}"
        echo -e "${YELLOW}wsgiref debería estar disponible en la biblioteca estándar de Python${NC}"
        return 1
    fi
    
    echo -e "${BLUE}  Ruta de wsgiref encontrada: $WSGIREF_PATH${NC}"
    
    # Copiar wsgiref a build/python/site-packages
    TARGET_DIR="build/python/site-packages/wsgiref"
    
    if [ -d "$TARGET_DIR" ]; then
        echo -e "${BLUE}  Eliminando wsgiref existente en build...${NC}"
        rm -rf "$TARGET_DIR"
    fi
    
    echo -e "${BLUE}  Copiando wsgiref a build/python/site-packages/...${NC}"
    cp -r "$WSGIREF_PATH" "$TARGET_DIR"
    
    # Verificar que se copió correctamente
    if [ -d "$TARGET_DIR" ] && [ -f "$TARGET_DIR/__init__.py" ]; then
        echo -e "${GREEN}  ✓ wsgiref inyectado correctamente${NC}"
        
        # Contar archivos copiados
        FILE_COUNT=$(find "$TARGET_DIR" -type f | wc -l)
        echo -e "${GREEN}  ✓ $FILE_COUNT archivo(s) copiado(s)${NC}"
        return 0
    else
        echo -e "${RED}  ✗ Error al copiar wsgiref${NC}"
        return 1
    fi
}

# Función para verificar dependencias de Google
verify_google_dependencies() {
    echo -e "${BLUE}Verificando dependencias de Google...${NC}"
    
    # Verificar en pyproject.toml
    if grep -q "google-api-python-client" pyproject.toml && \
       grep -q "google-auth-oauthlib" pyproject.toml; then
        echo -e "${GREEN}  ✓ Dependencias de Google encontradas en pyproject.toml${NC}"
    else
        echo -e "${YELLOW}  ⚠ ADVERTENCIA: Dependencias de Google NO encontradas en pyproject.toml${NC}"
        echo -e "${YELLOW}    Esto puede causar problemas con la sincronización de Google Sheets${NC}"
    fi
    
    # Verificar en requirements.txt si existe
    if [ -f "requirements.txt" ]; then
        if grep -q "google-api-python-client" requirements.txt && \
           grep -q "google-auth-oauthlib" requirements.txt; then
            echo -e "${GREEN}  ✓ Dependencias de Google encontradas en requirements.txt${NC}"
        else
            echo -e "${YELLOW}  ⚠ ADVERTENCIA: Dependencias de Google NO encontradas en requirements.txt${NC}"
        fi
    fi
}

# Función para incluir assets
include_assets() {
    if [ -d "assets" ] && [ -d "build/flutter" ]; then
        echo -e "${BLUE}Incluyendo assets en el build...${NC}"
        
        mkdir -p build/flutter/assets
        
        if [ "$(ls -A assets 2>/dev/null)" ]; then
            echo -e "${BLUE}Copiando archivos de assets...${NC}"
            cp -r assets/* build/flutter/assets/ 2>/dev/null || true
            
            ASSET_COUNT=$(find build/flutter/assets -type f 2>/dev/null | wc -l)
            if [ "$ASSET_COUNT" -gt 0 ]; then
                echo -e "${GREEN}✓ ${ASSET_COUNT} archivo(s) de assets copiado(s)${NC}"
                
                PUBSPEC_FILE="build/flutter/pubspec.yaml"
                if [ -f "$PUBSPEC_FILE" ]; then
                    echo -e "${BLUE}Actualizando pubspec.yaml para incluir assets...${NC}"
                    
                    python3 - <<EOF
import yaml
from pathlib import Path

pubspec_path = Path("$PUBSPEC_FILE")
assets_dir = Path("build/flutter/assets")

with open(pubspec_path, 'r') as f:
    pubspec = yaml.safe_load(f)

if 'flutter' not in pubspec:
    pubspec['flutter'] = {}
if 'assets' not in pubspec['flutter']:
    pubspec['flutter']['assets'] = []

existing_assets = [item for item in pubspec['flutter']['assets'] if isinstance(item, str) and item.startswith('app/')]

for asset_file in assets_dir.rglob('*'):
    if asset_file.is_file():
        relative_path = f"assets/{asset_file.relative_to(assets_dir)}"
        if relative_path not in existing_assets:
            existing_assets.append(relative_path)

pubspec['flutter']['assets'] = sorted(list(set(existing_assets)))

with open(pubspec_path, 'w') as f:
    yaml.dump(pubspec, f, sort_keys=False, indent=2)
EOF
                    echo -e "${GREEN}✓ pubspec.yaml actualizado con assets${NC}"
                fi
            fi
        fi
    fi
}

# Función para reemplazar iconos
replace_icons() {
    if [ -f "assets/app_icon.png" ] && command -v convert &> /dev/null; then
        echo -e "${BLUE}Reemplazando iconos personalizados...${NC}"
        
        ICON_SIZES=(
            "48:mdpi"
            "72:hdpi"
            "96:xhdpi"
            "144:xxhdpi"
            "192:xxxhdpi"
        )
        
        FOREGROUND_SIZES=(
            "108:mdpi"
            "162:hdpi"
            "216:xhdpi"
            "324:xxhdpi"
            "432:xxxhdpi"
        )
        
        for size_info in "${ICON_SIZES[@]}"; do
            size=$(echo $size_info | cut -d: -f1)
            density=$(echo $size_info | cut -d: -f2)
            target_dir="build/flutter/android/app/src/main/res/mipmap-${density}"
            
            if [ -d "$target_dir" ]; then
                convert assets/app_icon.png -resize ${size}x${size} "$target_dir/ic_launcher.png" 2>/dev/null && \
                echo -e "${GREEN}  ✓ Icono ${size}x${size} en mipmap-${density}${NC}" || true
            fi
        done
        
        for size_info in "${FOREGROUND_SIZES[@]}"; do
            size=$(echo $size_info | cut -d: -f1)
            density=$(echo $size_info | cut -d: -f2)
            target_dir="build/flutter/android/app/src/main/res/drawable-${density}"
            
            if [ -d "$target_dir" ]; then
                convert assets/app_icon.png -resize ${size}x${size} "$target_dir/ic_launcher_foreground.png" 2>/dev/null && \
                echo -e "${GREEN}  ✓ Icono foreground ${size}x${size} en drawable-${density}${NC}" || true
            fi
        done
    fi
}

# Función para construir APK
build_apk() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}Construyendo APK${NC}"
    echo -e "${BLUE}========================================${NC}"
    
    # Paso 1: Empaquetado inicial
    echo -e "${BLUE}Paso 1: Empaquetado inicial${NC}"
    echo -e "${BLUE}Ejecutando: flet build apk${NC}"
    echo -e "${BLUE}  Punto de entrada: main.py${NC}"
    echo -e "${BLUE}  Flet detectará automáticamente requirements.txt o pyproject.toml${NC}"
    
    flet build apk \
        --project "$PROJECT_NAME" \
        --description "$PROJECT_DESCRIPTION" \
        --product "$PROJECT_NAME"
    
    # Esperar a que se cree la estructura de build
    if [ ! -d "build/flutter" ]; then
        echo -e "${RED}Error: No se generó la estructura de build${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✓ Estructura de build generada${NC}"
    
    # Paso 2: Inyección de wsgiref
    echo -e "${BLUE}Paso 2: Inyección manual de wsgiref${NC}"
    
    SITE_PACKAGES_DIRS=(
        "build/python/site-packages"
        "build/flutter/python/site-packages"
        "build/app/python/site-packages"
    )
    
    FOUND_SITE_PACKAGES=""
    for dir in "${SITE_PACKAGES_DIRS[@]}"; do
        if [ -d "$dir" ]; then
            FOUND_SITE_PACKAGES="$dir"
            echo -e "${BLUE}Encontrado site-packages en: $dir${NC}"
            break
        fi
    done
    
    if [ -z "$FOUND_SITE_PACKAGES" ]; then
        FOUND_SITE_PACKAGES=$(find build -type d -name "site-packages" 2>/dev/null | head -1)
        if [ -z "$FOUND_SITE_PACKAGES" ]; then
            echo -e "${YELLOW}Advertencia: No se encontró site-packages. wsgiref se inyectará después del build completo.${NC}"
        else
            echo -e "${BLUE}Encontrado site-packages en: $FOUND_SITE_PACKAGES${NC}"
        fi
    fi
    
    if [ -n "$FOUND_SITE_PACKAGES" ]; then
        WSGIREF_PATH=$(python3 -c "import wsgiref; import os; print(os.path.dirname(wsgiref.__file__))" 2>/dev/null || echo "")
        
        if [ -z "$WSGIREF_PATH" ] || [ ! -d "$WSGIREF_PATH" ]; then
            PYTHON_VERSION=$(python3 --version | grep -oP '\d+\.\d+' | head -1)
            for base_path in "/usr/lib/python${PYTHON_VERSION}" "/usr/local/lib/python${PYTHON_VERSION}" "$HOME/.local/lib/python${PYTHON_VERSION}"; do
                test_path="${base_path}/wsgiref"
                if [ -d "$test_path" ]; then
                    WSGIREF_PATH="$test_path"
                    break
                fi
            done
        fi
        
        if [ -n "$WSGIREF_PATH" ] && [ -d "$WSGIREF_PATH" ]; then
            TARGET_DIR="$FOUND_SITE_PACKAGES/wsgiref"
            if [ -d "$TARGET_DIR" ]; then
                rm -rf "$TARGET_DIR"
            fi
            cp -r "$WSGIREF_PATH" "$TARGET_DIR"
            if [ -d "$TARGET_DIR" ] && [ -f "$TARGET_DIR/__init__.py" ]; then
                FILE_COUNT=$(find "$TARGET_DIR" -type f | wc -l)
                echo -e "${GREEN}  ✓ wsgiref inyectado correctamente ($FILE_COUNT archivos)${NC}"
            fi
        fi
    fi
    
    # Paso 3: Incluir assets e iconos
    include_assets
    replace_icons
    
    # Paso 4: Reconstruir si es necesario
    if [ -f "assets/app_icon.png" ] && command -v convert &> /dev/null; then
        echo -e "${BLUE}Paso 3: Reconstruyendo APK con assets e iconos personalizados...${NC}"
        
        cd build/flutter
        flutter pub get > /dev/null 2>&1 || true
        cd ../..
        
        flet build apk \
            --project "$PROJECT_NAME" \
            --description "$PROJECT_DESCRIPTION" \
            --product "$PROJECT_NAME"
        
        # Re-inyectar wsgiref después de reconstruir
        if [ -n "$FOUND_SITE_PACKAGES" ] && [ -d "$FOUND_SITE_PACKAGES" ] && [ -n "$WSGIREF_PATH" ] && [ -d "$WSGIREF_PATH" ]; then
            TARGET_DIR="$FOUND_SITE_PACKAGES/wsgiref"
            if [ -d "$TARGET_DIR" ]; then
                rm -rf "$TARGET_DIR"
            fi
            cp -r "$WSGIREF_PATH" "$TARGET_DIR"
            echo -e "${GREEN}  ✓ wsgiref re-inyectado después de reconstrucción${NC}"
        fi
        
        include_assets
    fi
    
    # Verificar que el APK se generó
    if [ -f "build/apk/app-release.apk" ]; then
        APK_SIZE=$(du -h build/apk/app-release.apk | cut -f1)
        echo -e "${GREEN}✓ APK generado exitosamente: build/apk/app-release.apk (${APK_SIZE})${NC}"
    else
        echo -e "${YELLOW}⚠ Advertencia: No se encontró el APK en build/apk/app-release.apk${NC}"
    fi
}

# Función para construir AAB
build_aab() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}Construyendo AAB para Google Play${NC}"
    echo -e "${BLUE}========================================${NC}"
    
    # Si no existe la estructura de build, construir APK primero para generarla
    if [ ! -d "build/flutter" ]; then
        echo -e "${YELLOW}Advertencia: No existe estructura de build. Construyendo APK inicial para generarla...${NC}"
        flet build apk \
            --project "$PROJECT_NAME" \
            --description "$PROJECT_DESCRIPTION" \
            --product "$PROJECT_NAME"
    fi
    
    # Incluir assets e iconos
    include_assets
    replace_icons
    
    # Construir AAB
    echo -e "${BLUE}Ejecutando: flet build aab${NC}"
    flet build aab \
        --project "$PROJECT_NAME" \
        --description "$PROJECT_DESCRIPTION" \
        --product "$PROJECT_NAME"
    
    # Re-incluir assets e iconos después del build
    include_assets
    replace_icons
    
    # Reconstruir si hay iconos personalizados
    if [ -f "assets/app_icon.png" ] && command -v convert &> /dev/null; then
        echo -e "${BLUE}Reconstruyendo AAB con iconos personalizados...${NC}"
        flet build aab \
            --project "$PROJECT_NAME" \
            --description "$PROJECT_DESCRIPTION" \
            --product "$PROJECT_NAME"
    fi
    
    # Verificar que el AAB se generó
    if [ -f "build/aab/app-release.aab" ]; then
        AAB_SIZE=$(du -h build/aab/app-release.aab | cut -f1)
        echo -e "${GREEN}✓ AAB generado exitosamente: build/aab/app-release.aab (${AAB_SIZE})${NC}"
    else
        echo -e "${YELLOW}⚠ Advertencia: No se encontró el AAB en build/aab/app-release.aab${NC}"
    fi
}

# ==================== MAIN ====================

# Parsear argumentos
parse_arguments "$@"

# Mostrar información del build
show_build_info

# Leer información del proyecto
read_project_info

# Verificar dependencias de Google
verify_google_dependencies

# Construir según los flags
if [ "$BUILD_APK" = true ]; then
    build_apk
fi

if [ "$BUILD_AAB" = true ]; then
    build_aab
fi

# Mensaje final
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}Build completado${NC}"
echo -e "${BLUE}========================================${NC}"

if [ "$BUILD_APK" = true ] && [ "$BUILD_AAB" = true ]; then
    echo -e "${GREEN}Artefactos generados:${NC}"
    [ -f "build/apk/app-release.apk" ] && echo -e "  ${GREEN}✓${NC} APK: build/apk/app-release.apk"
    [ -f "build/aab/app-release.aab" ] && echo -e "  ${GREEN}✓${NC} AAB: build/aab/app-release.aab"
elif [ "$BUILD_APK" = true ]; then
    [ -f "build/apk/app-release.apk" ] && echo -e "${GREEN}APK generado: build/apk/app-release.apk${NC}"
elif [ "$BUILD_AAB" = true ]; then
    [ -f "build/aab/app-release.aab" ] && echo -e "${GREEN}AAB generado: build/aab/app-release.aab${NC}"
fi
