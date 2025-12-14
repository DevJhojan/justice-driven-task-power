#!/bin/bash
# Script para construir APK y AAB (Android App Bundle) para Google Play

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

# Activar entorno virtual
if [ -d "venv" ]; then
    echo -e "${BLUE}Activando entorno virtual...${NC}"
    source venv/bin/activate
else
    echo -e "${RED}Error: No se encontró el entorno virtual (venv)${NC}"
    exit 1
fi

# Configurar variables de entorno
export ANDROID_HOME=${ANDROID_HOME:-$HOME/Android/Sdk}
export PATH=$PATH:$ANDROID_HOME/tools:$ANDROID_HOME/platform-tools

echo -e "${BLUE}ANDROID_HOME: $ANDROID_HOME${NC}"

# Verificar que el icono existe
if [ ! -f "assets/task_logo.ico" ]; then
    echo -e "${YELLOW}Advertencia: assets/task_logo.ico no encontrado, se usará el icono por defecto${NC}"
else
    # Convertir ICO a PNG si es necesario
    if [ ! -f "assets/app_icon.png" ] || [ "assets/task_logo.ico" -nt "assets/app_icon.png" ]; then
        echo -e "${BLUE}Convirtiendo icono ICO a PNG...${NC}"
        if command -v convert &> /dev/null; then
            convert assets/task_logo.ico -resize 512x512 assets/app_icon.png
            echo -e "${GREEN}✓ Icono convertido${NC}"
        else
            echo -e "${YELLOW}Advertencia: ImageMagick no está instalado, se usará el icono por defecto${NC}"
        fi
    fi
fi

# Limpiar builds anteriores si existen
if [ -d "build" ]; then
    echo -e "${BLUE}Limpiando builds anteriores...${NC}"
    rm -rf build/flutter
fi

# Construir el APK
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Construyendo APK...${NC}"
echo -e "${BLUE}========================================${NC}"

flet build apk \
    --project "TodoApp" \
    --description "Aplicación de gestión de tareas" \
    --product "Todo App" \
    --module-name main

# Esperar a que se cree la estructura de build
if [ -d "build/flutter" ]; then
    echo -e "${BLUE}Estructura de build generada${NC}"
    
    # Reemplazar iconos si existe app_icon.png
    if [ -f "assets/app_icon.png" ] && command -v convert &> /dev/null; then
        echo -e "${BLUE}Reemplazando iconos personalizados...${NC}"
        
        # Reemplazar iconos en todas las resoluciones
        for size in mdpi:48 hdpi:72 xhdpi:96 xxhdpi:144 xxxhdpi:192; do
            dir=$(echo $size | cut -d: -f1)
            px=$(echo $size | cut -d: -f2)
            mipmap_dir="build/flutter/android/app/src/main/res/mipmap-$dir"
            
            if [ -d "$mipmap_dir" ]; then
                convert assets/app_icon.png -resize ${px}x${px} "$mipmap_dir/ic_launcher.png" 2>/dev/null || true
                echo -e "  ${GREEN}✓${NC} Icono ${px}x${px} en mipmap-$dir"
            fi
        done
        
        # Reemplazar iconos foreground para adaptive icons
        for size in mdpi:108 hdpi:162 xhdpi:216 xxhdpi:324 xxxhdpi:432; do
            dir=$(echo $size | cut -d: -f1)
            px=$(echo $size | cut -d: -f2)
            drawable_dir="build/flutter/android/app/src/main/res/drawable-$dir"
            
            if [ -d "$drawable_dir" ]; then
                convert assets/app_icon.png -resize ${px}x${px} "$drawable_dir/ic_launcher_foreground.png" 2>/dev/null || true
                echo -e "  ${GREEN}✓${NC} Icono foreground ${px}x${px} en drawable-$dir"
            fi
        done
    fi
    
    # Reconstruir el APK con los iconos personalizados
    echo -e "${BLUE}Reconstruyendo APK con iconos personalizados...${NC}"
    flet build apk \
        --project "TodoApp" \
        --description "Aplicación de gestión de tareas" \
        --product "Todo App" \
        --module-name main
else
    echo -e "${RED}Error: No se generó la estructura de build${NC}"
    exit 1
fi

# Construir el AAB (Android App Bundle) para Google Play
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Construyendo AAB para Google Play...${NC}"
echo -e "${BLUE}========================================${NC}"

# Navegar al directorio de Flutter y construir el AAB
cd build/flutter

# Construir el AAB
if [ -f "android/gradlew" ]; then
    cd android
    ./gradlew bundleRelease
    cd ..
    
    # Buscar el AAB generado
    AAB_FILE=$(find android/app/build/outputs/bundle/release -name "*.aab" 2>/dev/null | head -1)
    
    if [ -n "$AAB_FILE" ]; then
        # Copiar el AAB al directorio build
        mkdir -p ../../build/aab
        cp "$AAB_FILE" ../../build/aab/app-release.aab
        echo -e "${GREEN}✓ AAB construido exitosamente!${NC}"
        echo -e "${GREEN}  Ubicación: build/aab/app-release.aab${NC}"
    else
        echo -e "${RED}Error: No se encontró el archivo AAB generado${NC}"
        exit 1
    fi
else
    echo -e "${RED}Error: No se encontró gradlew en build/flutter/android${NC}"
    exit 1
fi

cd ../..

# Verificar que los archivos se generaron correctamente
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Resumen de builds:${NC}"
echo -e "${BLUE}========================================${NC}"

if [ -f "build/apk/app-release.apk" ]; then
    APK_SIZE=$(du -h build/apk/app-release.apk | cut -f1)
    echo -e "${GREEN}✓ APK: build/apk/app-release.apk (${APK_SIZE})${NC}"
else
    echo -e "${RED}✗ APK no encontrado${NC}"
fi

if [ -f "build/aab/app-release.aab" ]; then
    AAB_SIZE=$(du -h build/aab/app-release.aab | cut -f1)
    echo -e "${GREEN}✓ AAB: build/aab/app-release.aab (${AAB_SIZE})${NC}"
else
    echo -e "${RED}✗ AAB no encontrado${NC}"
fi

echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}Build completado!${NC}"
echo -e "${BLUE}========================================${NC}"

