#!/bin/bash
# Script para construir APK y AAB (Android App Bundle) para Google Play
# Incluye inyección manual de wsgiref para soporte OAuth2 en Android

set -e

# Colores para output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Construyendo APK y AAB para Android${NC}"
echo -e "${BLUE}========================================${NC}"

# Leer información del proyecto desde pyproject.toml
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

# Verificar dependencias de Google antes de construir
verify_google_dependencies

# Paso 1: Empaquetado inicial sin bundle para generar estructura base
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Paso 1: Empaquetado inicial${NC}"
echo -e "${BLUE}========================================${NC}"

echo -e "${BLUE}Ejecutando: flet build apk${NC}"
echo -e "${BLUE}  Punto de entrada: main.py${NC}"
echo -e "${BLUE}  Flet detectará automáticamente requirements.txt o pyproject.toml${NC}"

flet build apk \
    --project "$PROJECT_NAME" \
    --description "$PROJECT_DESCRIPTION" \
    --product "$PROJECT_NAME"

# Esperar a que se cree la estructura de build
if [ -d "build/flutter" ]; then
    echo -e "${BLUE}Estructura de build generada${NC}"
else
    echo -e "${RED}Error: No se generó la estructura de build${NC}"
    exit 1
fi

# Paso 2: Inyección manual de wsgiref
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Paso 2: Inyección manual de wsgiref${NC}"
echo -e "${BLUE}========================================${NC}"

# Buscar en diferentes ubicaciones posibles de site-packages
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
    echo -e "${YELLOW}Advertencia: No se encontró build/python/site-packages${NC}"
    echo -e "${YELLOW}Intentando buscar en otras ubicaciones...${NC}"
    
    # Buscar recursivamente
    FOUND_SITE_PACKAGES=$(find build -type d -name "site-packages" 2>/dev/null | head -1)
    
    if [ -z "$FOUND_SITE_PACKAGES" ]; then
        echo -e "${YELLOW}Advertencia: No se encontró site-packages. wsgiref se inyectará después del build completo.${NC}"
    else
        echo -e "${BLUE}Encontrado site-packages en: $FOUND_SITE_PACKAGES${NC}"
    fi
fi

if [ -n "$FOUND_SITE_PACKAGES" ]; then
    # Modificar la función para usar la ruta encontrada
    OLD_BUILD_DIR="build/python/site-packages"
    export BUILD_SITE_PACKAGES="$FOUND_SITE_PACKAGES"
    
    # Obtener la ruta de wsgiref usando Python
    WSGIREF_PATH=$(python3 -c "import wsgiref; import os; print(os.path.dirname(wsgiref.__file__))" 2>/dev/null || echo "")
    
    if [ -z "$WSGIREF_PATH" ] || [ ! -d "$WSGIREF_PATH" ]; then
        echo -e "${YELLOW}Advertencia: No se pudo encontrar wsgiref usando Python${NC}"
        echo -e "${YELLOW}Intentando ubicaciones estándar...${NC}"
        
        # Intentar ubicaciones estándar
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
        echo -e "${BLUE}  Ruta de wsgiref encontrada: $WSGIREF_PATH${NC}"
        
        TARGET_DIR="$FOUND_SITE_PACKAGES/wsgiref"
        
        if [ -d "$TARGET_DIR" ]; then
            echo -e "${BLUE}  Eliminando wsgiref existente...${NC}"
            rm -rf "$TARGET_DIR"
        fi
        
        echo -e "${BLUE}  Copiando wsgiref a $TARGET_DIR...${NC}"
        cp -r "$WSGIREF_PATH" "$TARGET_DIR"
        
        if [ -d "$TARGET_DIR" ] && [ -f "$TARGET_DIR/__init__.py" ]; then
            FILE_COUNT=$(find "$TARGET_DIR" -type f | wc -l)
            echo -e "${GREEN}  ✓ wsgiref inyectado correctamente ($FILE_COUNT archivos)${NC}"
        else
            echo -e "${RED}  ✗ Error al copiar wsgiref${NC}"
        fi
    else
        echo -e "${RED}Error: No se pudo encontrar wsgiref en el sistema${NC}"
        echo -e "${YELLOW}wsgiref debería estar disponible en la biblioteca estándar de Python${NC}"
    fi
fi

# Incluir assets
include_assets

# Reemplazar iconos
replace_icons

# Paso 3: Finalización del build (reconstruir si es necesario)
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Paso 3: Finalización del build${NC}"
echo -e "${BLUE}========================================${NC}"

# Verificar si necesitamos reconstruir
if [ -f "assets/app_icon.png" ] && command -v convert &> /dev/null; then
    echo -e "${BLUE}Reconstruyendo APK con assets e iconos personalizados...${NC}"
    
    cd build/flutter
    flutter pub get > /dev/null 2>&1 || true
    cd ../..
    
    flet build apk \
        --project "$PROJECT_NAME" \
        --description "$PROJECT_DESCRIPTION" \
        --product "$PROJECT_NAME"
    
    # Inyectar wsgiref nuevamente después de reconstruir
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

# Construir AAB
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Construyendo AAB para Google Play${NC}"
echo -e "${BLUE}========================================${NC}"

include_assets
replace_icons

flet build aab \
    --project "$PROJECT_NAME" \
    --description "$PROJECT_DESCRIPTION" \
    --product "$PROJECT_NAME"

include_assets
replace_icons

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

echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}Build completado${NC}"
echo -e "${BLUE}========================================${NC}"
