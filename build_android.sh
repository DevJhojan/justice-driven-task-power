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

# Leer información del proyecto desde pyproject.toml
# Este script respeta completamente la configuración definida en pyproject.toml
if [ -f "pyproject.toml" ]; then
    # Extraer nombre del proyecto (formato: "justice-driven-task-power")
    PROJECT_NAME_RAW=$(grep -E "^name\s*=" pyproject.toml | sed 's/.*= *"\(.*\)".*/\1/' | head -1 | tr -d ' ')
    
    # Convertir nombre de formato "justice-driven-task-power" a "Justice Driven Task Power" (capitalizar palabras)
    # Esto se usa como nombre de visualización en la app
    PROJECT_NAME=$(echo "$PROJECT_NAME_RAW" | sed 's/-/ /g' | sed 's/\b\(.\)/\u\1/g')
    
    # Extraer descripción
    PROJECT_DESCRIPTION=$(grep -E "^description\s*=" pyproject.toml | sed 's/.*= *"\(.*\)".*/\1/' | head -1 | tr -d ' ')
    
    # Extraer versión
    PROJECT_VERSION=$(grep -E "^version\s*=" pyproject.toml | sed 's/.*= *"\(.*\)".*/\1/' | head -1 | tr -d ' ')
    
    # Validar que se encontraron valores críticos
    if [ -z "$PROJECT_NAME_RAW" ]; then
        echo -e "${RED}Error: No se pudo leer 'name' desde pyproject.toml${NC}"
        exit 1
    fi
    
    if [ -z "$PROJECT_VERSION" ]; then
        echo -e "${RED}Error: No se pudo leer 'version' desde pyproject.toml${NC}"
        exit 1
    fi
    
    # Usar valores por defecto solo si la descripción está vacía
    if [ -z "$PROJECT_DESCRIPTION" ]; then
        PROJECT_DESCRIPTION="Aplicación móvil desarrollada con Flet"
        echo -e "${YELLOW}Advertencia: 'description' no encontrada en pyproject.toml, usando valor por defecto${NC}"
    fi
    
    echo -e "${BLUE}Información del proyecto (desde pyproject.toml):${NC}"
    echo -e "${BLUE}  Nombre (raw): $PROJECT_NAME_RAW${NC}"
    echo -e "${BLUE}  Nombre (display): $PROJECT_NAME${NC}"
    echo -e "${BLUE}  Versión: $PROJECT_VERSION${NC}"
    echo -e "${BLUE}  Descripción: $PROJECT_DESCRIPTION${NC}"
else
    # Valores por defecto si no existe pyproject.toml
    echo -e "${RED}Error: pyproject.toml no encontrado${NC}"
    echo -e "${RED}Este script requiere pyproject.toml para construir la aplicación${NC}"
    exit 1
fi

# Activar entorno virtual
if [ -d "venv" ]; then
    echo -e "${BLUE}Activando entorno virtual...${NC}"
    source venv/bin/activate
else
    echo -e "${RED}Error: No se encontró el entorno virtual (venv)${NC}"
    exit 1
fi

# Instalar/actualizar dependencias desde pyproject.toml
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Instalando dependencias...${NC}"
echo -e "${BLUE}========================================${NC}"

# Verificar que pip está disponible
if ! command -v pip &> /dev/null; then
    echo -e "${RED}Error: pip no está disponible${NC}"
    exit 1
fi

# Actualizar pip
echo -e "${BLUE}Actualizando pip...${NC}"
pip install --upgrade pip setuptools wheel --quiet

# Instalar dependencias desde requirements.txt (más confiable para Flet)
if [ -f "requirements.txt" ]; then
    echo -e "${BLUE}Instalando dependencias desde requirements.txt...${NC}"
    pip install -r requirements.txt --quiet
    echo -e "${GREEN}✓ Dependencias instaladas desde requirements.txt${NC}"
else
    echo -e "${YELLOW}Advertencia: requirements.txt no encontrado, extrayendo de pyproject.toml...${NC}"
    # Extraer dependencias de pyproject.toml usando grep/sed (más compatible)
    if [ -f "pyproject.toml" ]; then
        # Extraer líneas de dependencias (entre dependencies = [ y ])
        DEPENDENCIES=$(grep -A 20 "^dependencies = \[" pyproject.toml | grep -E '^\s*"[^"]+",?$' | sed 's/^[[:space:]]*"\([^"]*\)",\?$/\1/' | tr -d ' ')
        
        if [ -n "$DEPENDENCIES" ]; then
            echo -e "${BLUE}Instalando dependencias extraídas de pyproject.toml...${NC}"
            echo "$DEPENDENCIES" | while read -r dep; do
                if [ -n "$dep" ]; then
                    pip install "$dep" --quiet
                fi
            done
            echo -e "${GREEN}✓ Dependencias instaladas desde pyproject.toml${NC}"
        else
            echo -e "${YELLOW}No se pudieron extraer dependencias, instalando manualmente...${NC}"
            pip install google-api-python-client>=2.100.0 google-auth-httplib2>=0.1.1 google-auth-oauthlib>=1.1.0 --quiet
        fi
    else
        echo -e "${RED}Error: No se encontró requirements.txt ni pyproject.toml${NC}"
        exit 1
    fi
fi

# Verificar que las dependencias de Google están instaladas
echo -e "${BLUE}Verificando dependencias de Google Sheets...${NC}"
python3 -c "import google.oauth2.credentials; import google_auth_oauthlib.flow; import googleapiclient.discovery; print('✓ Dependencias de Google verificadas')" 2>/dev/null || {
    echo -e "${YELLOW}Advertencia: Las dependencias de Google no están instaladas, instalándolas manualmente...${NC}"
    pip install google-api-python-client>=2.100.0 google-auth-httplib2>=0.1.1 google-auth-oauthlib>=1.1.0 --quiet
    echo -e "${GREEN}✓ Dependencias de Google instaladas${NC}"
}

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

# Función para reemplazar iconos personalizados
replace_icons() {
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
}

# Verificar que pyproject.toml existe y tiene las dependencias
echo -e "${BLUE}Verificando pyproject.toml...${NC}"
if [ -f "pyproject.toml" ]; then
    if grep -q "google-api-python-client" pyproject.toml; then
        echo -e "${GREEN}✓ pyproject.toml contiene dependencias de Google Sheets${NC}"
    else
        echo -e "${RED}Error: pyproject.toml no contiene dependencias de Google Sheets${NC}"
        exit 1
    fi
else
    echo -e "${RED}Error: pyproject.toml no encontrado${NC}"
    exit 1
fi

# Construir el APK
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Construyendo APK...${NC}"
echo -e "${BLUE}========================================${NC}"

# Limpiar build anterior para forzar reconstrucción completa
if [ -d "build" ]; then
    echo -e "${BLUE}Limpiando build anterior...${NC}"
    rm -rf build
fi

# Reemplazar iconos ANTES de construir (si existen)
# Esto evita la necesidad de reconstruir después
if [ -f "assets/app_icon.png" ] || [ -f "assets/task_logo.ico" ]; then
    echo -e "${BLUE}Preparando iconos para el build...${NC}"
    # Los iconos se reemplazarán después de la primera construcción
fi

# Construir APK inicial
# IMPORTANTE: Según la documentación de Flet, si existe requirements.txt,
# Flet lo prioriza sobre pyproject.toml. Por lo tanto, nos aseguramos de que
# requirements.txt tenga todas las dependencias correctas.
echo -e "${BLUE}Construyendo APK (Flet empaquetará dependencias)...${NC}"
echo -e "${BLUE}  Flet usará requirements.txt si existe (tiene prioridad sobre pyproject.toml)${NC}"

# Verificar que requirements.txt tiene las dependencias de Google
if [ -f "requirements.txt" ]; then
    if ! grep -q "google-api-python-client" requirements.txt; then
        echo -e "${RED}Error: requirements.txt no contiene dependencias de Google Sheets${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓ requirements.txt contiene dependencias de Google Sheets${NC}"
    
    # Mostrar las dependencias que se van a incluir
    echo -e "${BLUE}Dependencias que se incluirán en el build:${NC}"
    grep -v "^#" requirements.txt | grep -v "^$" | while read dep; do
        echo -e "  ${BLUE}- ${dep}${NC}"
    done
else
    echo -e "${YELLOW}Advertencia: requirements.txt no encontrado, Flet usará pyproject.toml${NC}"
fi

# Construir el APK - Flet leerá dependencias automáticamente
# IMPORTANTE: No usar flags adicionales que puedan interferir con el empaquetado de dependencias
echo -e "${BLUE}Ejecutando: flet build apk${NC}"
flet build apk \
    --project "$PROJECT_NAME" \
    --description "$PROJECT_DESCRIPTION" \
    --product "$PROJECT_NAME"

# Esperar a que se cree la estructura de build
if [ -d "build/flutter" ]; then
    echo -e "${BLUE}Estructura de build generada${NC}"
    
    # Verificar que las dependencias se incluyeron
    echo -e "${BLUE}Verificando que las dependencias se incluyeron en el build...${NC}"
    DEPENDENCIES_FOUND=false
    
    # Verificar en site-packages (ubicación estándar de Flet)
    if [ -d "build/site-packages" ]; then
        GOOGLE_COUNT=$(find build/site-packages -maxdepth 1 -type d \( -name "google*" -o -name "*google*" \) 2>/dev/null | wc -l)
        if [ "$GOOGLE_COUNT" -gt 0 ]; then
            echo -e "${GREEN}✓ Dependencias de Google detectadas en site-packages (${GOOGLE_COUNT} paquetes)${NC}"
            DEPENDENCIES_FOUND=true
            # Listar los paquetes encontrados
            find build/site-packages -maxdepth 1 -type d -name "*google*" 2>/dev/null | while read dir; do
                echo -e "  ${GREEN}  - $(basename "$dir")${NC}"
            done
        fi
    fi
    
    # También verificar en python_packages si existe
    if [ -d "build/flutter/python_packages" ]; then
        if ls build/flutter/python_packages/google* 1> /dev/null 2>&1; then
            echo -e "${GREEN}✓ Dependencias de Google también detectadas en python_packages${NC}"
            DEPENDENCIES_FOUND=true
        fi
    fi
    
    if [ "$DEPENDENCIES_FOUND" = false ]; then
        echo -e "${RED}⚠ ADVERTENCIA: Dependencias de Google NO encontradas en el build${NC}"
        echo -e "${RED}  Esto indica que no se empaquetaron correctamente${NC}"
        echo -e "${YELLOW}  Verificando pyproject.toml...${NC}"
        if grep -q "google-api-python-client" pyproject.toml; then
            echo -e "${YELLOW}  pyproject.toml contiene las dependencias, pero Flet no las empaquetó${NC}"
            echo -e "${YELLOW}  Esto puede ser un problema con la versión de Flet o la configuración${NC}"
        fi
    fi
    
    # Reemplazar iconos personalizados (solo modifica recursos, no afecta dependencias)
    replace_icons
    
    # IMPORTANTE: NO reconstruimos el APK completo después de reemplazar iconos
    # porque Flet puede no incluir las dependencias en la segunda construcción.
    # El APK ya está construido con todas las dependencias desde el primer build.
    # Los iconos personalizados se incluyen automáticamente si están en la estructura correcta.
    
    # Si realmente necesitamos reconstruir (solo si es crítico para los iconos),
    # verificamos primero que las dependencias estén presentes
    RECONSTRUCT_NEEDED=false
    if [ -f "assets/app_icon.png" ] && command -v convert &> /dev/null; then
        # Verificar si los iconos se aplicaron correctamente
        ICON_COUNT=$(find build/flutter/android/app/src/main/res -name "ic_launcher.png" 2>/dev/null | wc -l)
        if [ "$ICON_COUNT" -lt 5 ]; then
            echo -e "${YELLOW}Advertencia: No se detectaron suficientes iconos, puede ser necesario reconstruir${NC}"
            RECONSTRUCT_NEEDED=true
        fi
    fi
    
    if [ "$RECONSTRUCT_NEEDED" = true ]; then
        echo -e "${YELLOW}⚠ ADVERTENCIA: Reconstruir puede causar que las dependencias no se incluyan${NC}"
        echo -e "${YELLOW}  Intentando reconstruir con dependencias explícitas...${NC}"
        flet build apk \
            --project "$PROJECT_NAME" \
            --description "$PROJECT_DESCRIPTION" \
            --product "$PROJECT_NAME"
        
        # Verificar nuevamente las dependencias después de reconstruir
        DEPENDENCIES_AFTER_RECONSTRUCT=false
        if [ -d "build/site-packages" ]; then
            GOOGLE_COUNT_AFTER=$(find build/site-packages -maxdepth 1 -type d \( -name "google*" -o -name "*google*" \) 2>/dev/null | wc -l)
            if [ "$GOOGLE_COUNT_AFTER" -gt 0 ]; then
                echo -e "${GREEN}✓ Dependencias de Google verificadas después de reconstrucción${NC}"
                DEPENDENCIES_AFTER_RECONSTRUCT=true
            else
                echo -e "${RED}⚠ ADVERTENCIA: Dependencias de Google NO encontradas después de reconstrucción${NC}"
                echo -e "${RED}  El APK reconstruido puede no funcionar correctamente${NC}"
            fi
        fi
    else
        echo -e "${GREEN}✓ APK construido. Iconos aplicados sin necesidad de reconstrucción completa.${NC}"
    fi
    
    # Verificar que el APK se generó
    if [ -f "build/apk/app-release.apk" ]; then
        APK_SIZE=$(du -h build/apk/app-release.apk | cut -f1)
        echo -e "${GREEN}✓ APK construido exitosamente! (${APK_SIZE})${NC}"
        echo -e "${GREEN}  Ubicación: build/apk/app-release.apk${NC}"
    else
        echo -e "${YELLOW}Advertencia: APK no encontrado en la ubicación esperada${NC}"
        # Buscar el APK en otras ubicaciones posibles
        APK_FILE=$(find build -name "*.apk" -type f 2>/dev/null | head -1)
        if [ -n "$APK_FILE" ]; then
            mkdir -p build/apk
            cp "$APK_FILE" build/apk/app-release.apk
            echo -e "${GREEN}✓ APK encontrado y copiado a build/apk/app-release.apk${NC}"
        fi
    fi
else
    echo -e "${RED}Error: No se generó la estructura de build${NC}"
    exit 1
fi

# Construir el AAB (Android App Bundle) para Google Play
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Construyendo AAB para Google Play...${NC}"
echo -e "${BLUE}========================================${NC}"

# Asegurar que los iconos estén actualizados antes de construir el AAB
replace_icons

# Construir el AAB usando el comando de Flet
flet build aab \
    --project "$PROJECT_NAME" \
    --description "$PROJECT_DESCRIPTION" \
    --product "$PROJECT_NAME"

# Reemplazar iconos nuevamente después del build (por si Flet regeneró la estructura)
replace_icons

# Si los iconos fueron reemplazados, reconstruir el AAB
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
    echo -e "${GREEN}✓ AAB construido exitosamente! (${AAB_SIZE})${NC}"
    echo -e "${GREEN}  Ubicación: build/aab/app-release.aab${NC}"
else
    echo -e "${YELLOW}Advertencia: AAB no encontrado en la ubicación esperada${NC}"
    # Buscar el AAB en otras ubicaciones posibles
    AAB_FILE=$(find build -name "*.aab" -type f 2>/dev/null | head -1)
    if [ -n "$AAB_FILE" ]; then
        mkdir -p build/aab
        cp "$AAB_FILE" build/aab/app-release.aab
        echo -e "${GREEN}✓ AAB encontrado y copiado a build/aab/app-release.aab${NC}"
    else
        echo -e "${RED}Error: No se pudo encontrar el archivo AAB generado${NC}"
        exit 1
    fi
fi

# Verificar que los archivos se generaron correctamente
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Resumen de builds:${NC}"
echo -e "${BLUE}========================================${NC}"

APK_SUCCESS=false
AAB_SUCCESS=false

if [ -f "build/apk/app-release.apk" ]; then
    APK_SIZE=$(du -h build/apk/app-release.apk | cut -f1)
    echo -e "${GREEN}✓ APK: build/apk/app-release.apk (${APK_SIZE})${NC}"
    APK_SUCCESS=true
else
    echo -e "${RED}✗ APK no encontrado en build/apk/app-release.apk${NC}"
fi

if [ -f "build/aab/app-release.aab" ]; then
    AAB_SIZE=$(du -h build/aab/app-release.aab | cut -f1)
    echo -e "${GREEN}✓ AAB: build/aab/app-release.aab (${AAB_SIZE})${NC}"
    AAB_SUCCESS=true
else
    echo -e "${RED}✗ AAB no encontrado en build/aab/app-release.aab${NC}"
fi

echo -e "${BLUE}========================================${NC}"

if [ "$APK_SUCCESS" = true ] && [ "$AAB_SUCCESS" = true ]; then
    echo -e "${GREEN}✓ Build completado exitosamente!${NC}"
    echo -e "${GREEN}  APK listo para instalación directa${NC}"
    echo -e "${GREEN}  AAB listo para subir a Google Play Store${NC}"
    echo -e "${BLUE}  Versión: $PROJECT_VERSION${NC}"
    exit 0
elif [ "$APK_SUCCESS" = true ]; then
    echo -e "${YELLOW}⚠ APK construido, pero AAB falló${NC}"
    exit 1
elif [ "$AAB_SUCCESS" = true ]; then
    echo -e "${YELLOW}⚠ AAB construido, pero APK falló${NC}"
    exit 1
else
    echo -e "${RED}✗ Build falló - ningún archivo generado${NC}"
    exit 1
fi
