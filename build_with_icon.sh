#!/bin/bash
# Script para construir el APK con icono personalizado

set -e

# Colores para output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Construyendo APK con icono personalizado...${NC}"

# Activar entorno virtual
source venv/bin/activate

# Configurar variables de entorno
export ANDROID_HOME=$HOME/Android/Sdk
export PATH=$PATH:$ANDROID_HOME/tools:$ANDROID_HOME/platform-tools

# Verificar que el icono existe
if [ ! -f "assets/task_logo.ico" ]; then
    echo "Error: assets/task_logo.ico no encontrado"
    exit 1
fi

# Convertir ICO a PNG si es necesario
if [ ! -f "assets/app_icon.png" ]; then
    echo "Convirtiendo icono ICO a PNG..."
    convert assets/task_logo.ico -resize 512x512 assets/app_icon.png
fi

# Construir el APK
echo -e "${BLUE}Construyendo APK...${NC}"
flet build apk --project "TodoApp" --description "Aplicación de gestión de tareas" --product "Todo App"

# Esperar a que se cree la estructura de build
echo -e "${BLUE}Esperando a que se genere la estructura del build...${NC}"
sleep 2

# Reemplazar iconos en todas las resoluciones
echo -e "${BLUE}Reemplazando iconos...${NC}"
for size in mdpi:48 hdpi:72 xhdpi:96 xxhdpi:144 xxxhdpi:192; do
    dir=$(echo $size | cut -d: -f1)
    px=$(echo $size | cut -d: -f2)
    mipmap_dir="build/flutter/android/app/src/main/res/mipmap-$dir"
    
    if [ -d "$mipmap_dir" ]; then
        convert assets/app_icon.png -resize ${px}x${px} "$mipmap_dir/ic_launcher.png" 2>/dev/null || true
        echo "  ✓ Icono ${px}x${px} creado en mipmap-$dir"
    fi
done

# También reemplazar los iconos foreground para adaptive icons
for size in mdpi:108 hdpi:162 xhdpi:216 xxhdpi:324 xxxhdpi:432; do
    dir=$(echo $size | cut -d: -f1)
    px=$(echo $size | cut -d: -f2)
    drawable_dir="build/flutter/android/app/src/main/res/drawable-$dir"
    
    if [ -d "$drawable_dir" ]; then
        convert assets/app_icon.png -resize ${px}x${px} "$drawable_dir/ic_launcher_foreground.png" 2>/dev/null || true
        echo "  ✓ Icono foreground ${px}x${px} creado en drawable-$dir"
    fi
done

# Reconstruir el APK con los nuevos iconos usando flet build apk nuevamente
# (Flet detectará los cambios y reconstruirá)
echo -e "${BLUE}Reconstruyendo APK con iconos personalizados...${NC}"
flet build apk --project "TodoApp" --description "Aplicación de gestión de tareas" --product "Todo App"

echo -e "${GREEN}✓ APK construido exitosamente con icono personalizado!${NC}"
echo -e "${GREEN}  Ubicación: build/apk/app-release.apk${NC}"

