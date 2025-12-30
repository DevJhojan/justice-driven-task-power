#!/bin/bash

# Script de build para Android
# Genera APK para cualquier Android y AAB para Google Play Store
# Incluye sistema de versionado automático

set -e  # Salir si hay algún error

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Archivos de configuración
PYPROJECT_TOML="pyproject.toml"
FLET_TOML="flet.toml"
VERSION_CODE_FILE=".version_code.txt"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Cambiar al directorio del script
cd "$SCRIPT_DIR"

# Función para mostrar ayuda
show_help() {
    echo -e "${CYAN}Script de Build para Android${NC}"
    echo ""
    echo "Uso: $0 [opciones]"
    echo ""
    echo "Opciones:"
    echo "  --apk        Genera solo el archivo APK (para cualquier Android)"
    echo "  --aab        Genera solo el archivo AAB (para Google Play Store)"
    echo "  --both       Genera tanto APK como AAB (por defecto)"
    echo "  --help, -h   Muestra esta ayuda"
    echo ""
    echo "Ejemplos:"
    echo "  $0              # Genera APK y AAB"
    echo "  $0 --apk        # Genera solo APK"
    echo "  $0 --aab        # Genera solo AAB"
    echo "  $0 --both       # Genera APK y AAB"
    exit 0
}

# Función para log con colores
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Función para leer versión desde pyproject.toml
read_version_from_pyproject() {
    if [ ! -f "$PYPROJECT_TOML" ]; then
        log_warning "No se encontró $PYPROJECT_TOML, buscando en $FLET_TOML"
        read_version_from_flet_toml
        return
    fi
    
    # Usar Python para parsear TOML de forma más robusta
    local version=""
    if command -v python3 &> /dev/null; then
        version=$(python3 <<'PYTHON_SCRIPT'
import re
try:
    with open('pyproject.toml', 'r') as f:
        content = f.read()
        # Buscar en la sección [project]
        # Patrón: [project] ... version = "1.0.0" o version = '1.0.0' o version = 1.0.0
        match = re.search(r'\[project\].*?^version\s*=\s*["\']?([0-9]+\.[0-9]+\.[0-9]+)["\']?', content, re.MULTILINE | re.DOTALL)
        if match:
            print(match.group(1))
except Exception:
    pass
PYTHON_SCRIPT
)
    fi
    
    # Si Python falla, usar método alternativo con sed
    if [ -z "$version" ] || [[ ! $version =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
        # Método alternativo: extraer línea de versión y limpiar
        local version_line=$(grep -A 20 "\[project\]" "$PYPROJECT_TOML" | grep -E "^version\s*=" | head -1)
        if [ -n "$version_line" ]; then
            # Extraer versión: remover espacios, comillas, y todo excepto números y puntos
            version=$(echo "$version_line" | sed -E 's/.*version[[:space:]]*=[[:space:]]*["'\'']?([0-9]+\.[0-9]+\.[0-9]+)["'\'']?.*/\1/' | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1)
        fi
    fi
    
    if [ -z "$version" ] || [[ ! $version =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
        log_warning "No se pudo leer versión de $PYPROJECT_TOML, buscando en $FLET_TOML"
        read_version_from_flet_toml
    else
        echo "$version"
    fi
}

# Función para leer versión desde flet.toml
read_version_from_flet_toml() {
    if [ ! -f "$FLET_TOML" ]; then
        log_warning "No se encontró $FLET_TOML, usando versión por defecto 1.0.0"
        echo "1.0.0"
        return
    fi
    
    # Usar Python para parsear TOML de forma más robusta
    local version=""
    if command -v python3 &> /dev/null; then
        version=$(python3 <<'PYTHON_SCRIPT'
import re
import sys
try:
    flet_toml = sys.argv[1] if len(sys.argv) > 1 else 'flet.toml'
    with open(flet_toml, 'r') as f:
        content = f.read()
        # Buscar versión en [app]
        match = re.search(r'\[app\].*?^version\s*=\s*["\']?([0-9]+\.[0-9]+\.[0-9]+)["\']?', content, re.MULTILINE | re.DOTALL)
        if match:
            print(match.group(1))
except Exception:
    pass
PYTHON_SCRIPT
"$FLET_TOML" 2>/dev/null)
    fi
    
    # Si Python falla, usar método alternativo
    if [ -z "$version" ] || [[ ! $version =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
        local version_line=$(grep -E "^version\s*=" "$FLET_TOML" | head -1)
        if [ -n "$version_line" ]; then
            version=$(echo "$version_line" | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1)
        fi
    fi
    
    if [ -z "$version" ] || [[ ! $version =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
        log_warning "No se pudo leer versión de $FLET_TOML, usando versión por defecto 1.0.0"
        echo "1.0.0"
    else
        echo "$version"
    fi
}

# Función para validar formato de versión (MAJOR.MINOR.PATCH)
validate_version_format() {
    local version=$1
    if [[ ! $version =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
        log_error "Formato de versión inválido: $version"
        log_error "Debe seguir el formato MAJOR.MINOR.PATCH (ej: 1.0.0)"
        exit 1
    fi
}

# Función para calcular versionCode desde versión
calculate_version_code() {
    local version=$1
    IFS='.' read -ra ADDR <<< "$version"
    local major=${ADDR[0]}
    local minor=${ADDR[1]}
    local patch=${ADDR[2]}
    
    # versionCode = MAJOR * 10000 + MINOR * 100 + PATCH
    echo $((major * 10000 + minor * 100 + patch))
}

# Función para obtener el siguiente versionCode
get_next_version_code() {
    local base_version=$1
    local calculated_code=$(calculate_version_code "$base_version")
    
    if [ ! -f "$VERSION_CODE_FILE" ]; then
        # Primera vez: usar el calculado
        log_info "Inicializando versionCode: $calculated_code (desde versión $base_version)"
        echo $calculated_code
        return
    fi
    
    local last_code=$(cat "$VERSION_CODE_FILE" | tr -d '[:space:]')
    
    # Validar que sea numérico
    if ! [[ "$last_code" =~ ^[0-9]+$ ]]; then
        log_warning "Archivo $VERSION_CODE_FILE contiene valor inválido, reinicializando"
        echo $calculated_code
        return
    fi
    
    # Validar que sea mayor a 0
    if [ "$last_code" -le 0 ]; then
        log_warning "versionCode inválido ($last_code), reinicializando"
        echo $calculated_code
        return
    fi
    
    local next_code=$((last_code + 1))
    
    # Usar el mayor entre next_code y calculated_code para respetar cambios de versión
    if [ $calculated_code -gt $next_code ]; then
        log_info "Usando versionCode calculado desde versión: $calculated_code"
        echo $calculated_code
    else
        log_info "Incrementando versionCode desde archivo: $last_code -> $next_code"
        echo $next_code
    fi
}

# Función para validar versionCode
validate_version_code() {
    local code=$1
    
    # Debe ser numérico y mayor a 0
    if ! [[ "$code" =~ ^[0-9]+$ ]] || [ "$code" -le 0 ]; then
        log_error "versionCode inválido: $code (debe ser un número mayor a 0)"
        exit 1
    fi
    
    # No puede exceder el límite de Android (2147483647)
    if [ "$code" -gt 2147483647 ]; then
        log_error "versionCode excede el límite de Android (2147483647): $code"
        exit 1
    fi
}

# Función para actualizar flet.toml con versiones
update_flet_toml() {
    local version=$1
    local version_code=$2
    
    log_info "Actualizando $FLET_TOML con versión $version (code $version_code)"
    
    # Si flet.toml no existe, crearlo con configuración básica
    if [ ! -f "$FLET_TOML" ]; then
        log_warning "$FLET_TOML no existe, creando uno nuevo"
        cat > "$FLET_TOML" <<EOF
# Configuración de Flet para builds de Android
# Generado automáticamente por build_android.sh

[app]
name = "justice-driven-task-power"
version = "$version"
package = "com.flet.justice_driven_task_power"
icon = "assets/app_icon.png"

[android]
min_sdk = 21
target_sdk = 34
compile_sdk = 34
version_code = $version_code
version_name = "$version"
EOF
    else
        # Crear un archivo temporal
        local temp_file=$(mktemp)
        
        # Leer el archivo línea por línea y actualizar
        local in_app_section=false
        local in_android_section=false
        
        while IFS= read -r line; do
            # Detectar secciones
            if [[ $line =~ ^\[app\] ]]; then
                in_app_section=true
                in_android_section=false
                echo "$line" >> "$temp_file"
                continue
            elif [[ $line =~ ^\[android\] ]]; then
                in_app_section=false
                in_android_section=true
                echo "$line" >> "$temp_file"
                continue
            elif [[ $line =~ ^\[ ]]; then
                in_app_section=false
                in_android_section=false
                echo "$line" >> "$temp_file"
                continue
            fi
            
            # Actualizar version en sección [app]
            if [ "$in_app_section" = true ] && [[ $line =~ ^version\s*= ]]; then
                echo "version = \"$version\"" >> "$temp_file"
                continue
            fi
            
            # Actualizar version_code en sección [android]
            if [ "$in_android_section" = true ] && [[ $line =~ ^version_code\s*= ]]; then
                echo "version_code = $version_code" >> "$temp_file"
                continue
            fi
            
            # Actualizar version_name en sección [android]
            if [ "$in_android_section" = true ] && [[ $line =~ ^version_name\s*= ]]; then
                echo "version_name = \"$version\"" >> "$temp_file"
                continue
            fi
            
            # Mantener línea original
            echo "$line" >> "$temp_file"
        done < "$FLET_TOML"
        
        # Reemplazar el archivo original
        mv "$temp_file" "$FLET_TOML"
    fi
}

# Función para guardar versionCode
save_version_code() {
    local code=$1
    echo "$code" > "$VERSION_CODE_FILE"
    log_success "versionCode guardado: $code"
}

# Función para verificar que Flet está instalado
check_flet() {
    if ! command -v flet &> /dev/null; then
        log_error "Flet no está instalado"
        log_info "Instala Flet con: pip install flet"
        exit 1
    fi
}

# Función para verificar keystore (solo para AAB)
check_keystore() {
    if [ ! -f "$FLET_TOML" ]; then
        log_warning "$FLET_TOML no existe, no se puede verificar keystore"
        return
    fi
    
    local keystore_path=$(grep -E "^keystore_path\s*=" "$FLET_TOML" | head -1 | sed -E 's/.*keystore_path\s*=\s*["\047]?([^"\047]+)["\047]?.*/\1/' | tr -d ' ')
    
    if [ -z "$keystore_path" ]; then
        log_warning "No se encontró keystore_path en $FLET_TOML"
        log_warning "El AAB se generará sin firmar (no recomendado para producción)"
        return
    fi
    
    if [ ! -f "$keystore_path" ]; then
        log_error "Keystore no encontrado: $keystore_path"
        log_error "El AAB necesita un keystore para firmarse"
        exit 1
    fi
    
    log_success "Keystore encontrado: $keystore_path"
}

# Función para encontrar archivos generados
find_built_files() {
    local build_type=$1  # "apk" o "aab"
    local files_found=0
    
    # Buscar en build/apk/ y build/aab/
    if [ -d "build/$build_type" ]; then
        while IFS= read -r file; do
            if [ -n "$file" ]; then
                log_success "Archivo generado: $file"
                files_found=$((files_found + 1))
            fi
        done < <(find "build/$build_type" -name "*.$build_type" -type f 2>/dev/null)
    fi
    
    # También buscar en el directorio raíz de build/
    if [ -d "build" ]; then
        while IFS= read -r file; do
            if [ -n "$file" ]; then
                log_success "Archivo generado: $file"
                files_found=$((files_found + 1))
            fi
        done < <(find "build" -maxdepth 1 -name "*.$build_type" -type f 2>/dev/null)
    fi
    
    if [ $files_found -eq 0 ]; then
        log_warning "No se encontraron archivos .$build_type generados"
        return 1
    fi
    
    return 0
}

# Función para construir APK
build_apk() {
    log_info "Generando APK para Android..."
    log_info "Building version $BASE_VERSION (code $VERSION_CODE)"
    
    if flet build apk; then
        log_success "APK generado exitosamente"
        find_built_files "apk"
    else
        log_error "Error al generar APK"
        exit 1
    fi
}

# Función para construir AAB
build_aab() {
    log_info "Generando AAB para Google Play Store..."
    log_info "Building version $BASE_VERSION (code $VERSION_CODE)"
    
    check_keystore
    
    if flet build aab; then
        log_success "AAB generado exitosamente"
        find_built_files "aab"
    else
        log_error "Error al generar AAB"
        exit 1
    fi
}

# Procesar argumentos
BUILD_APK=false
BUILD_AAB=false

if [ $# -eq 0 ]; then
    # Por defecto, construir ambos
    BUILD_APK=true
    BUILD_AAB=true
else
    case "$1" in
        --apk)
            BUILD_APK=true
            ;;
        --aab)
            BUILD_AAB=true
            ;;
        --both)
            BUILD_APK=true
            BUILD_AAB=true
            ;;
        --help|-h)
            show_help
            ;;
        *)
            log_error "Argumento inválido: $1"
            show_help
            ;;
    esac
fi

# Verificar que Flet está instalado
check_flet

# Leer versión base
log_info "Leyendo versión base..."
BASE_VERSION=$(read_version_from_pyproject)
validate_version_format "$BASE_VERSION"
log_success "Versión base: $BASE_VERSION"

# Obtener y validar versionCode
VERSION_CODE=$(get_next_version_code "$BASE_VERSION")
validate_version_code "$VERSION_CODE"

# Actualizar flet.toml
update_flet_toml "$BASE_VERSION" "$VERSION_CODE"

# Guardar versionCode para el próximo build
save_version_code "$VERSION_CODE"

echo ""
log_info "═══════════════════════════════════════════════════════════"
log_info "Iniciando build de Android"
log_info "Versión: $BASE_VERSION (code: $VERSION_CODE)"
log_info "═══════════════════════════════════════════════════════════"
echo ""

# Construir según las opciones
BUILD_SUCCESS=true

if [ "$BUILD_APK" = true ]; then
    echo ""
    build_apk
    echo ""
fi

if [ "$BUILD_AAB" = true ]; then
    echo ""
    build_aab
    echo ""
fi

# Resumen final
echo ""
log_info "═══════════════════════════════════════════════════════════"
log_success "Build completado exitosamente"
log_info "Versión: $BASE_VERSION (code: $VERSION_CODE)"
if [ "$BUILD_APK" = true ]; then
    log_info "✓ APK generado para instalación directa"
fi
if [ "$BUILD_AAB" = true ]; then
    log_info "✓ AAB generado para Google Play Store"
fi
log_info "═══════════════════════════════════════════════════════════"
echo ""

