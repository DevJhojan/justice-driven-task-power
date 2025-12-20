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

# Función para incluir assets en el APK
include_assets() {
    if [ -d "assets" ] && [ -d "build/flutter" ]; then
        echo -e "${BLUE}Incluyendo assets en el build...${NC}"
        
        # Crear directorio de assets en Flutter si no existe
        mkdir -p build/flutter/assets
        
        # Copiar todos los archivos de assets
        if [ "$(ls -A assets 2>/dev/null)" ]; then
            echo -e "${BLUE}Copiando archivos de assets...${NC}"
            cp -r assets/* build/flutter/assets/ 2>/dev/null || true
            
            # Contar archivos copiados
            ASSET_COUNT=$(find build/flutter/assets -type f 2>/dev/null | wc -l)
            if [ "$ASSET_COUNT" -gt 0 ]; then
                echo -e "${GREEN}✓ ${ASSET_COUNT} archivo(s) de assets copiado(s)${NC}"
                
                # Listar archivos copiados
                find build/flutter/assets -type f | while read file; do
                    echo -e "  ${GREEN}  - $(basename "$file")${NC}"
                done
                
                # Actualizar pubspec.yaml para incluir los assets
                PUBSPEC_FILE="build/flutter/pubspec.yaml"
                if [ -f "$PUBSPEC_FILE" ]; then
                    echo -e "${BLUE}Actualizando pubspec.yaml para incluir assets...${NC}"
                    
                    # Primero, corregir cualquier formato incorrecto (assets fuera de la sección)
                    if grep -q "^  - app/" "$PUBSPEC_FILE" || grep -q "^  - assets/" "$PUBSPEC_FILE"; then
                        echo -e "${YELLOW}  Corrigiendo formato incorrecto en pubspec.yaml...${NC}"
                        python3 << 'PYTHON_FIX'
import re
import sys

pubspec_file = "build/flutter/pubspec.yaml"
try:
    with open(pubspec_file, 'r') as f:
        content = f.read()
    
    # Encontrar todas las líneas de assets (bien y mal ubicadas)
    all_assets = []
    lines = content.split('\n')
    new_lines = []
    in_flutter = False
    in_assets = False
    
    for line in lines:
        if line.strip() == "flutter:":
            in_flutter = True
            new_lines.append(line)
        elif in_flutter and line.strip() == "assets:":
            in_assets = True
            new_lines.append(line)
        elif in_assets:
            if line.strip().startswith("- "):
                # Asset dentro de la sección, agregarlo a la lista
                asset = line.strip()[2:].strip()
                if asset not in all_assets:
                    all_assets.append(asset)
            elif line.strip() == "" or line.strip().startswith("#"):
                new_lines.append(line)
            else:
                # Fin de la sección assets
                in_assets = False
                # Agregar todos los assets ordenados
                for asset in sorted(set(all_assets)):
                    new_lines.append(f"    - {asset}")
                new_lines.append(line)
        elif in_flutter and line.strip().startswith("- ") and (line.strip().startswith("- app/") or line.strip().startswith("- assets/")):
            # Asset mal ubicado, agregarlo a la lista pero no a new_lines
            asset = line.strip()[2:].strip()
            if asset not in all_assets:
                all_assets.append(asset)
        else:
            new_lines.append(line)
    
    # Si quedaron assets sin agregar, agregarlos a la sección assets
    if all_assets and not in_assets:
        for i, line in enumerate(new_lines):
            if line.strip() == "assets:":
                # Encontrar dónde termina la lista de assets
                j = i + 1
                while j < len(new_lines) and (new_lines[j].strip().startswith("- ") or new_lines[j].strip() == ""):
                    j += 1
                # Insertar los assets faltantes
                for asset in sorted(set(all_assets)):
                    asset_line = f"    - {asset}"
                    if asset_line not in new_lines[i+1:j]:
                        new_lines.insert(j, asset_line)
                        j += 1
                break
    
    with open(pubspec_file, 'w') as f:
        f.write('\n'.join(new_lines))
    
    print("✓ Formato corregido")
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
PYTHON_FIX
                    fi
                    
                    # Obtener lista de archivos de assets de la carpeta assets/
                    NEW_ASSET_FILES=$(find build/flutter/assets -type f -printf "assets/%P\n" | sort)
                    
                    # Extraer todos los assets actuales del pubspec.yaml
                    EXISTING_ASSETS=$(grep "^    - " "$PUBSPEC_FILE" | sed 's/^[[:space:]]*-[[:space:]]*//' | sort)
                    
                    # Agregar nuevos assets si no existen
                    for asset in $NEW_ASSET_FILES; do
                        if [ -n "$asset" ] && ! echo "$EXISTING_ASSETS" | grep -q "^$asset$"; then
                            # Encontrar la línea "assets:" y agregar después
                            ASSETS_LINE=$(grep -n "^  assets:" "$PUBSPEC_FILE" | head -1 | cut -d: -f1)
                            if [ -n "$ASSETS_LINE" ]; then
                                # Encontrar la última línea de asset
                                LAST_ASSET_LINE=$ASSETS_LINE
                                LINE_NUM=$((ASSETS_LINE + 1))
                                TOTAL_LINES=$(wc -l < "$PUBSPEC_FILE")
                                
                                while [ "$LINE_NUM" -le "$TOTAL_LINES" ]; do
                                    LINE_CONTENT=$(sed -n "${LINE_NUM}p" "$PUBSPEC_FILE")
                                    if echo "$LINE_CONTENT" | grep -q "^    - "; then
                                        LAST_ASSET_LINE=$LINE_NUM
                                    elif [[ ! "$LINE_CONTENT" =~ ^[[:space:]]*$ ]] && [[ ! "$LINE_CONTENT" =~ ^[[:space:]]*# ]]; then
                                        break
                                    fi
                                    LINE_NUM=$((LINE_NUM + 1))
                                done
                                
                                sed -i "${LAST_ASSET_LINE}a\    - $asset" "$PUBSPEC_FILE"
                            fi
                        fi
                    done
                    
                    echo -e "${GREEN}✓ pubspec.yaml actualizado con assets${NC}"
                else
                    echo -e "${YELLOW}Advertencia: No se encontró pubspec.yaml${NC}"
                fi
            else
                echo -e "${YELLOW}Advertencia: No se encontraron archivos en assets para copiar${NC}"
            fi
        else
            echo -e "${YELLOW}Advertencia: El directorio assets está vacío${NC}"
        fi
    else
        echo -e "${YELLOW}Advertencia: No se encontró el directorio assets o build/flutter${NC}"
    fi
}

# Verificar que pyproject.toml existe y tiene las dependencias
echo -e "${BLUE}Verificando pyproject.toml...${NC}"
if [ -f "pyproject.toml" ]; then
    if ! grep -q "gspread" pyproject.toml; then
        echo -e "${RED}Error: pyproject.toml no contiene gspread${NC}"
        exit 1
    fi
    if grep -q "google-api-python-client" pyproject.toml; then
        echo -e "${GREEN}✓ pyproject.toml contiene gspread y dependencias de Google Sheets${NC}"
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
    if ! grep -q "gspread" requirements.txt; then
        echo -e "${RED}Error: requirements.txt no contiene gspread${NC}"
        exit 1
    fi
    if ! grep -q "google-api-python-client" requirements.txt; then
        echo -e "${RED}Error: requirements.txt no contiene dependencias de Google Sheets${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓ requirements.txt contiene gspread y dependencias de Google Sheets${NC}"
    
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
# Flet usa main.py como punto de entrada por defecto, que importa desde app.main
echo -e "${BLUE}Ejecutando: flet build apk${NC}"
echo -e "${BLUE}  Punto de entrada: main.py${NC}"
echo -e "${BLUE}  Flet detectará automáticamente requirements.txt o pyproject.toml${NC}"

# Asegurar que requirements.txt existe y está actualizado
if [ -f "requirements.txt" ]; then
    echo -e "${BLUE}  Usando requirements.txt para dependencias${NC}"
    # Verificar que todas las dependencias de pyproject.toml estén en requirements.txt
    if grep -q "google-api-python-client" requirements.txt && \
       grep -q "google-auth-httplib2" requirements.txt && \
       grep -q "google-auth-oauthlib" requirements.txt; then
        echo -e "${GREEN}  ✓ requirements.txt contiene todas las dependencias necesarias${NC}"
    else
        echo -e "${YELLOW}  ⚠ Advertencia: requirements.txt puede estar incompleto${NC}"
    fi
else
    echo -e "${BLUE}  Usando pyproject.toml para dependencias${NC}"
fi

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
    ARCHITECTURES_FOUND=0
    
    # Verificar en site-packages (Flet empaqueta las dependencias en subdirectorios por arquitectura)
    # Las arquitecturas comunes son: arm64-v8a, armeabi-v7a, x86, x86_64
    if [ -d "build/site-packages" ]; then
        # Verificar cada arquitectura individualmente
        for arch in arm64-v8a armeabi-v7a x86 x86_64; do
            arch_dir="build/site-packages/$arch"
            if [ -d "$arch_dir" ]; then
                # Verificar paquetes específicos de Google en esta arquitectura
                PACKAGES_FOUND=0
                if [ -d "$arch_dir/google" ] && [ -d "$arch_dir/googleapiclient" ]; then
                    PACKAGES_FOUND=$((PACKAGES_FOUND + 1))
                fi
                if [ -d "$arch_dir/google_auth_oauthlib" ] || [ -f "$arch_dir/google_auth_oauthlib.py" ] || ls "$arch_dir"/google_auth_oauthlib* 1> /dev/null 2>&1; then
                    PACKAGES_FOUND=$((PACKAGES_FOUND + 1))
                fi
                if [ -d "$arch_dir/google_auth_httplib2" ] || [ -f "$arch_dir/google_auth_httplib2.py" ] || ls "$arch_dir"/google_auth_httplib2* 1> /dev/null 2>&1; then
                    PACKAGES_FOUND=$((PACKAGES_FOUND + 1))
                fi
                if ls "$arch_dir"/google_api_python_client* 1> /dev/null 2>&1; then
                    PACKAGES_FOUND=$((PACKAGES_FOUND + 1))
                fi
                
                if [ "$PACKAGES_FOUND" -ge 2 ]; then
                    ARCHITECTURES_FOUND=$((ARCHITECTURES_FOUND + 1))
                    echo -e "  ${GREEN}✓ Arquitectura ${arch}: ${PACKAGES_FOUND} paquetes de Google encontrados${NC}"
                    DEPENDENCIES_FOUND=true
                fi
            fi
        done
        
        # También verificar en el nivel raíz (por si Flet las empaqueta allí)
        if [ -d "build/site-packages/google" ] || [ -d "build/site-packages/googleapiclient" ]; then
            echo -e "  ${GREEN}✓ Dependencias también encontradas en nivel raíz de site-packages${NC}"
            DEPENDENCIES_FOUND=true
        fi
    fi
    
    # También verificar en python_packages si existe
    if [ -d "build/flutter/python_packages" ]; then
        if ls build/flutter/python_packages/google* 1> /dev/null 2>&1; then
            echo -e "  ${GREEN}✓ Dependencias de Google también detectadas en python_packages${NC}"
            DEPENDENCIES_FOUND=true
        fi
    fi
    
    # Verificar en el app.zip (donde Flet empaqueta el código Python)
    if [ -f "build/flutter/app/app.zip" ]; then
        # Verificar sin extraer (más rápido)
        if unzip -l build/flutter/app/app.zip 2>/dev/null | grep -qi "google" | head -1 | grep -q .; then
            echo -e "  ${GREEN}✓ Referencias a Google encontradas en app.zip${NC}"
            DEPENDENCIES_FOUND=true
        fi
    fi
    
    # Mostrar resumen
    if [ "$DEPENDENCIES_FOUND" = true ]; then
        if [ "$ARCHITECTURES_FOUND" -gt 0 ]; then
            echo -e "${GREEN}✓ Dependencias de Google verificadas correctamente en ${ARCHITECTURES_FOUND} arquitectura(s)${NC}"
        else
            echo -e "${GREEN}✓ Dependencias de Google verificadas correctamente en el build${NC}"
        fi
    else
        # Solo mostrar advertencia si realmente no se encontraron
        echo -e "${YELLOW}⚠ ADVERTENCIA: Dependencias de Google no encontradas en ubicaciones esperadas${NC}"
        echo -e "${YELLOW}  Verificando configuración...${NC}"
        if grep -q "gspread" pyproject.toml 2>/dev/null && grep -q "google-api-python-client" pyproject.toml 2>/dev/null; then
            echo -e "${GREEN}  ✓ pyproject.toml contiene gspread y las dependencias${NC}"
        fi
        if [ -f "requirements.txt" ] && grep -q "gspread" requirements.txt 2>/dev/null && grep -q "google-api-python-client" requirements.txt 2>/dev/null; then
            echo -e "${GREEN}  ✓ requirements.txt contiene gspread y las dependencias${NC}"
        fi
        echo -e "${BLUE}  ℹ Flet debería empaquetarlas automáticamente durante el build${NC}"
        echo -e "${BLUE}  ℹ Si la app funciona correctamente, las dependencias están incluidas${NC}"
    fi
    
    # Incluir assets en el build ANTES de reconstruir
    include_assets
    
    # Verificar y corregir pubspec.yaml después de incluir assets
    PUBSPEC_FILE="build/flutter/pubspec.yaml"
    if [ -f "$PUBSPEC_FILE" ]; then
        # Verificar si hay líneas de assets fuera de la sección assets:
        if grep -q "^  - app/" "$PUBSPEC_FILE" || grep -q "^  - assets/" "$PUBSPEC_FILE"; then
            echo -e "${YELLOW}Corrigiendo formato de pubspec.yaml...${NC}"
            # Corregir el formato moviendo las líneas mal ubicadas dentro de assets:
            python3 << 'PYTHON_SCRIPT'
import re
import sys

pubspec_file = "build/flutter/pubspec.yaml"
try:
    with open(pubspec_file, 'r') as f:
        lines = f.readlines()
    
    new_lines = []
    in_flutter = False
    in_assets = False
    assets_items = []
    misplaced_assets = []
    
    for i, line in enumerate(lines):
        if line.strip() == "flutter:":
            in_flutter = True
            new_lines.append(line)
        elif in_flutter and line.strip() == "assets:":
            in_assets = True
            new_lines.append(line)
        elif in_assets:
            if line.strip().startswith("- "):
                assets_items.append(line)
            elif line.strip() == "" or line.strip().startswith("#"):
                new_lines.append(line)
            else:
                # Fin de la sección assets
                in_assets = False
                # Agregar todos los assets
                for asset_line in assets_items:
                    new_lines.append(asset_line)
                assets_items = []
                new_lines.append(line)
        elif in_flutter and line.strip().startswith("- ") and (line.strip().startswith("- app/") or line.strip().startswith("- assets/")):
            # Assets mal ubicados, guardarlos para agregarlos después
            misplaced_assets.append(line)
            # No agregar esta línea aquí
        else:
            new_lines.append(line)
    
    # Si quedaron assets mal ubicados, agregarlos a la sección assets
    if misplaced_assets:
        # Buscar la sección assets y agregar los assets mal ubicados
        for i, line in enumerate(new_lines):
            if line.strip() == "assets:":
                # Encontrar el final de la lista de assets
                j = i + 1
                while j < len(new_lines) and (new_lines[j].strip().startswith("- ") or new_lines[j].strip() == ""):
                    j += 1
                # Insertar los assets mal ubicados
                for asset_line in misplaced_assets:
                    if asset_line not in new_lines[i+1:j]:
                        new_lines.insert(j, asset_line)
                        j += 1
                break
    
    with open(pubspec_file, 'w') as f:
        f.writelines(new_lines)
    
    print("✓ pubspec.yaml corregido")
except Exception as e:
    print(f"Error corrigiendo pubspec.yaml: {e}")
    sys.exit(1)
PYTHON_SCRIPT
        fi
    fi
    
    # Reemplazar iconos personalizados (solo modifica recursos, no afecta dependencias)
    replace_icons
    
    # IMPORTANTE: Reconstruir el APK para incluir los assets
    # Aunque esto puede ser costoso, es necesario para que los assets estén disponibles en el APK
    if [ -d "build/flutter/assets" ] && [ "$(ls -A build/flutter/assets 2>/dev/null)" ]; then
        echo -e "${BLUE}Reconstruyendo APK con assets incluidos...${NC}"
        
        # Verificar nuevamente el pubspec.yaml antes de reconstruir
        if [ -f "$PUBSPEC_FILE" ]; then
            # Verificar sintaxis YAML básica
            if grep -q "^  - app/" "$PUBSPEC_FILE" || grep -q "^  - assets/" "$PUBSPEC_FILE"; then
                echo -e "${RED}Error: pubspec.yaml tiene formato incorrecto. Corrigiendo...${NC}"
                # Ejecutar el script de corrección nuevamente
                python3 << 'PYTHON_SCRIPT'
import re

pubspec_file = "build/flutter/pubspec.yaml"
with open(pubspec_file, 'r') as f:
    content = f.read()

# Patrón para encontrar la sección flutter y assets
pattern = r'(flutter:\s+assets:\s+)(.*?)(\s+uses-material-design:)'
match = re.search(pattern, content, re.DOTALL)

if match:
    assets_section = match.group(2)
    # Extraer todos los assets (incluyendo los mal ubicados)
    all_assets = re.findall(r'^\s*-\s+(app/.*?|assets/.*?)$', content, re.MULTILINE)
    # Crear nueva sección de assets ordenada
    new_assets = '\n'.join([f'    - {asset}' for asset in sorted(set(all_assets))])
    # Reemplazar
    new_content = content[:match.start()] + match.group(1) + new_assets + '\n' + match.group(3) + content[match.end():]
    # Eliminar líneas de assets fuera de la sección
    lines = new_content.split('\n')
    new_lines = []
    in_assets = False
    for line in lines:
        if 'assets:' in line:
            in_assets = True
            new_lines.append(line)
        elif in_assets and line.strip().startswith('uses-material-design:'):
            in_assets = False
            new_lines.append(line)
        elif not in_assets and (line.strip().startswith('- app/') or line.strip().startswith('- assets/')):
            # Omitir assets fuera de la sección
            continue
        else:
            new_lines.append(line)
    
    with open(pubspec_file, 'w') as f:
        f.write('\n'.join(new_lines))
    print("✓ pubspec.yaml corregido")
PYTHON_SCRIPT
            fi
        fi
        
        cd build/flutter
        flutter pub get > /dev/null 2>&1 || true
        cd ../..
        
        # Reconstruir el APK con los assets
        flet build apk \
            --project "$PROJECT_NAME" \
            --description "$PROJECT_DESCRIPTION" \
            --product "$PROJECT_NAME"
        
        # Después de reconstruir, verificar y corregir nuevamente si es necesario
        if [ -f "$PUBSPEC_FILE" ]; then
            include_assets
        fi
        
        echo -e "${GREEN}✓ APK reconstruido con assets incluidos${NC}"
    fi
    
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
            # Buscar en todas las subcarpetas de arquitectura
            GOOGLE_COUNT_AFTER=$(find build/site-packages -type d \( -name "google*" -o -name "*google*" \) 2>/dev/null | grep -E "(google|googleapiclient|google_auth)" | wc -l)
            if [ "$GOOGLE_COUNT_AFTER" -gt 0 ]; then
                echo -e "${GREEN}✓ Dependencias de Google verificadas después de reconstrucción${NC}"
                DEPENDENCIES_AFTER_RECONSTRUCT=true
            else
                # Verificar también en app.zip
                if [ -f "build/flutter/app/app.zip" ]; then
                    TEMP_DIR=$(mktemp -d)
                    unzip -q build/flutter/app/app.zip -d "$TEMP_DIR" 2>/dev/null || true
                    if find "$TEMP_DIR" -type d -name "google*" 2>/dev/null | grep -q .; then
                        echo -e "${GREEN}✓ Dependencias de Google encontradas en app.zip después de reconstrucción${NC}"
                        DEPENDENCIES_AFTER_RECONSTRUCT=true
                    fi
                    rm -rf "$TEMP_DIR"
                fi
                
                if [ "$DEPENDENCIES_AFTER_RECONSTRUCT" = false ]; then
                    echo -e "${YELLOW}⚠ ADVERTENCIA: Dependencias de Google no encontradas en ubicaciones esperadas${NC}"
                    echo -e "${YELLOW}  Esto puede ser normal si Flet las empaqueta de otra manera${NC}"
                    echo -e "${BLUE}  ℹ Las dependencias están configuradas correctamente, Flet debería incluirlas${NC}"
                fi
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

# Asegurar que los assets estén incluidos antes de construir el AAB
include_assets

# Asegurar que los iconos estén actualizados antes de construir el AAB
replace_icons

# Construir el AAB usando el comando de Flet
flet build aab \
    --project "$PROJECT_NAME" \
    --description "$PROJECT_DESCRIPTION" \
    --product "$PROJECT_NAME"

# Asegurar que los assets estén incluidos después del build (por si Flet regeneró la estructura)
include_assets

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
