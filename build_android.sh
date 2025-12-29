#!/bin/bash

################################################################################
# Script de Build para Android - Justice Driven Task Power
# 
# Este script genera builds Android (APK y/o AAB) para la aplicación Flet
# y los firma automáticamente usando un keystore configurado.
# 
# Requisitos:
#   - Keystore en android/keystore/justice_task_power.jks
#   - Variables de entorno configuradas (ver .env.example)
#   - Java JDK instalado (para jarsigner)
# 
# Uso:
#   ./build_android.sh           # Genera APK y AAB (ambos firmados)
#   ./build_android.sh --apk     # Genera solo APK (firmado)
#   ./build_android.sh --aab     # Genera solo AAB (firmado)
#   ./build_android.sh --help     # Muestra esta ayuda
# 
# Configuración:
#   - Crea el keystore: ./create_keystore.sh
#   - Configura credenciales: cp .env.example .env
#   - Ver BUILD_SIGNING.md para más detalles
#
################################################################################

# Desactivar set -e temporalmente para manejar errores de versionado
# set -e se reactivará después de las validaciones iniciales
set +e

# ============================================================================
# CONFIGURACIÓN
# ============================================================================

# Nombre de la aplicación (sin extensión)
APP_NAME="justice-driven-task-power"

# Rutas de iconos (en orden de prioridad)
ICON_PATHS=(
    "assets/app_icon.png"
    "assets/task_logo.ico"
)

# Directorios de salida
BUILD_DIR="build"
APK_DIR="${BUILD_DIR}/apk"
AAB_DIR="${BUILD_DIR}/aab"

# Configuración de keystore
KEYSTORE_DIR="android/keystore"
KEYSTORE_FILE="${KEYSTORE_DIR}/justice_task_power.jks"
ENV_FILE=".env"

# Configuración de versionado
VERSION_CODE_FILE=".version_code.txt"
PYPROJECT_FILE="pyproject.toml"
FLET_CONFIG_FILE="flet.toml"

# Colores para mensajes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ============================================================================
# FUNCIONES
# ============================================================================

# Función para imprimir mensajes con color
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Función para mostrar ayuda
show_help() {
    cat << EOF
Uso: $0 [OPCIÓN]

Opciones:
    --apk        Genera únicamente el archivo APK
    --aab        Genera únicamente el archivo AAB
    --help       Muestra esta ayuda

Si no se especifica ninguna opción, se generan ambos archivos (APK y AAB).

Ejemplos:
    $0              # Genera APK y AAB
    $0 --apk        # Genera solo APK
    $0 --aab        # Genera solo AAB
EOF
}

# Función para detectar y activar el entorno virtual
activate_venv() {
    # Buscar venv en ubicaciones comunes
    if [ -d "venv" ]; then
        if [ -z "$VIRTUAL_ENV" ]; then
            print_info "Activando entorno virtual: venv"
            source venv/bin/activate
        fi
    elif [ -d ".venv" ]; then
        if [ -z "$VIRTUAL_ENV" ]; then
            print_info "Activando entorno virtual: .venv"
            source .venv/bin/activate
        fi
    else
        print_warning "No se encontró entorno virtual. Usando Flet del sistema."
    fi
    
    # Asegurar que el PATH incluya el venv
    if [ -n "$VIRTUAL_ENV" ]; then
        export PATH="$VIRTUAL_ENV/bin:$PATH"
    fi
}

# Función para validar que Flet está instalado
check_flet() {
    # Intentar activar venv primero
    activate_venv
    
    if ! command -v flet &> /dev/null; then
        print_error "Flet no está instalado o no está en el PATH."
        print_info "Instala Flet con: pip install flet"
        print_info "O activa tu entorno virtual con: source venv/bin/activate"
        exit 1
    fi
    print_success "Flet encontrado: $(flet --version 2>&1 | head -n 1)"
}

# Función para encontrar y validar el icono
find_icon() {
    local icon_path=""
    
    for path in "${ICON_PATHS[@]}"; do
        if [ -f "$path" ]; then
            icon_path="$path"
            print_success "Icono encontrado: $icon_path" >&2
            break
        fi
    done
    
    if [ -z "$icon_path" ]; then
        print_error "No se encontró ningún icono válido."
        print_info "Buscando en las siguientes ubicaciones:"
        for path in "${ICON_PATHS[@]}"; do
            echo "  - $path"
        done
        exit 1
    fi
    
    # Verificar que el icono esté configurado en pyproject.toml
    if [ -f "pyproject.toml" ]; then
        if ! grep -q "icon.*=.*\"$icon_path\"" pyproject.toml; then
            print_warning "El icono no está configurado en pyproject.toml"
            print_info "Actualizando pyproject.toml con el icono encontrado..."
            
            # Actualizar o agregar la configuración del icono
            if grep -q "\[tool.flet\]" pyproject.toml; then
                # Si existe la sección, actualizar o agregar icon
                if grep -q "icon\s*=" pyproject.toml; then
                    # Reemplazar icono existente
                    sed -i "s|icon\s*=.*|icon = \"$icon_path\"|" pyproject.toml
                else
                    # Agregar icon después de [tool.flet]
                    sed -i "/\[tool.flet\]/a icon = \"$icon_path\"" pyproject.toml
                fi
            else
                # Agregar sección completa
                echo "" >> pyproject.toml
                echo "[tool.flet]" >> pyproject.toml
                echo "icon = \"$icon_path\"" >> pyproject.toml
            fi
            print_success "pyproject.toml actualizado con icono: $icon_path"
        fi
    fi
    
    echo "$icon_path"
}

# Función para limpiar builds anteriores
clean_builds() {
    if [ -d "$BUILD_DIR" ]; then
        print_info "Limpiando builds anteriores..."
        rm -rf "$BUILD_DIR"
        print_success "Builds anteriores eliminados"
    fi
}

# Función para crear directorios necesarios
create_directories() {
    mkdir -p "$APK_DIR" "$AAB_DIR"
}

# Función para leer versión base desde pyproject.toml
read_base_version() {
    local version=""
    
    # Usar variable de entorno como override (máxima prioridad)
    if [ -n "$APP_VERSION" ]; then
        version="$APP_VERSION"
        print_info "Usando versión desde variable de entorno: $version"
    fi
    
    # Intentar leer desde pyproject.toml
    if [ -z "$version" ] && [ -f "$PYPROJECT_FILE" ]; then
        # Buscar en [project] section (formato: version = "1.0.0")
        version=$(grep -E "^version\s*=" "$PYPROJECT_FILE" | head -n 1 | sed -E 's/.*version\s*=\s*["'\'']?([^"'\'']+)["'\'']?.*/\1/' | tr -d '[:space:]')
        
        # Si no está en [project], buscar en [tool.flet] o [tool.app]
        if [ -z "$version" ]; then
            version=$(awk '/\[tool\.flet\]/,/^\[/ {if (/^version\s*=/) {gsub(/["'\'']/, "", $0); gsub(/.*=/, "", $0); gsub(/^[ \t]+|[ \t]+$/, "", $0); print; exit}}' "$PYPROJECT_FILE")
        fi
        
        if [ -z "$version" ]; then
            version=$(awk '/\[tool\.app\]/,/^\[/ {if (/^version\s*=/) {gsub(/["'\'']/, "", $0); gsub(/.*=/, "", $0); gsub(/^[ \t]+|[ \t]+$/, "", $0); print; exit}}' "$PYPROJECT_FILE")
        fi
    fi
    
    # Intentar leer desde flet.toml si existe
    if [ -z "$version" ] && [ -f "$FLET_CONFIG_FILE" ]; then
        version=$(grep -E "^version\s*=" "$FLET_CONFIG_FILE" | head -n 1 | sed -E 's/.*version\s*=\s*["'\'']?([^"'\'']+)["'\'']?.*/\1/' | tr -d '[:space:]')
        
        if [ -z "$version" ]; then
            version=$(awk '/\[app\]/,/^\[/ {if (/^version\s*=/) {gsub(/["'\'']/, "", $0); gsub(/.*=/, "", $0); gsub(/^[ \t]+|[ \t]+$/, "", $0); print; exit}}' "$FLET_CONFIG_FILE")
        fi
    fi
    
    # Valor por defecto si no se encuentra
    if [ -z "$version" ]; then
        version="1.0.0"
        print_warning "No se encontró versión en configuración. Usando versión por defecto: $version"
    fi
    
    # Limpiar espacios y validar formato semántico (MAJOR.MINOR.PATCH)
    version=$(echo "$version" | tr -d '[:space:]')
    
    if ! echo "$version" | grep -qE '^[0-9]+\.[0-9]+\.[0-9]+$'; then
        print_error "Formato de versión inválido: $version"
        print_error "El formato debe ser MAJOR.MINOR.PATCH (ej: 1.4.2)"
        print_info "Verifica la versión en:"
        echo "  - $PYPROJECT_FILE (sección [project])"
        echo "  - $FLET_CONFIG_FILE (sección [app])"
        echo "  - Variable de entorno APP_VERSION"
        exit 1
    fi
    
    echo "$version"
}

# Función para leer o inicializar versionCode
get_version_code() {
    local base_version="$1"
    local version_code=1
    local calculated_code=1
    
    # Calcular versionCode desde la versión base
    # Formato: MAJOR * 10000 + MINOR * 100 + PATCH
    local major=$(echo "$base_version" | cut -d. -f1)
    local minor=$(echo "$base_version" | cut -d. -f2)
    local patch=$(echo "$base_version" | cut -d. -f3)
    
    # Asegurar que los valores sean numéricos
    major=${major:-1}
    minor=${minor:-0}
    patch=${patch:-0}
    
    calculated_code=$((major * 10000 + minor * 100 + patch))
    
    # Si el versionCode calculado es muy bajo, usar un valor mínimo
    if [ $calculated_code -lt 100 ]; then
        calculated_code=100
    fi
    
    # Leer versionCode desde archivo persistente
    if [ -f "$VERSION_CODE_FILE" ]; then
        local stored_code=$(cat "$VERSION_CODE_FILE" | tr -d '[:space:]')
        if [ -n "$stored_code" ] && [[ "$stored_code" =~ ^[0-9]+$ ]]; then
            # Usar el mayor entre el almacenado+1 y el calculado
            # Esto asegura que nunca disminuya y que respete la versión base
            local next_stored=$((stored_code + 1))
            if [ $next_stored -gt $calculated_code ]; then
                version_code=$next_stored
                print_info "Incrementando versionCode desde archivo: $stored_code -> $version_code" >&2
            else
                version_code=$calculated_code
                print_info "Usando versionCode calculado desde versión: $version_code" >&2
            fi
        else
            print_warning "Archivo de versionCode corrupto. Usando versión calculada." >&2
            version_code=$calculated_code
        fi
    else
        # Primera vez: usar el calculado desde la versión
        version_code=$calculated_code
        print_info "Inicializando versionCode: $version_code (desde versión $base_version)" >&2
    fi
    
    # Guardar el nuevo versionCode para el próximo build
    echo "$version_code" > "$VERSION_CODE_FILE"
    
    # Devolver solo el valor numérico (sin mensajes)
    echo "$version_code"
}

# Función para actualizar configuración de Flet con versiones, keystore e icono
update_flet_version_config() {
    local version_name="$1"
    local version_code="$2"
    
    print_info "Actualizando configuración de versión..."
    print_info "  versionName: $version_name"
    print_info "  versionCode: $version_code"
    
    # Obtener el icono (redirigir stderr para evitar mensajes en la salida)
    local icon_path=$(find_icon 2>/dev/null | tail -n 1)
    # Limpiar cualquier código de color ANSI que pueda haber quedado
    icon_path=$(echo "$icon_path" | sed 's/\x1b\[[0-9;]*m//g' | tr -d '\n\r' | sed 's/^[^a-zA-Z]*//' | sed 's/[^a-zA-Z0-9._/-]*$//')
    print_info "  Icono: $icon_path"
    
    # Convertir ruta del keystore a relativa si es absoluta (para flet.toml)
    local keystore_path_rel="$KEYSTORE_PATH"
    if [[ "$KEYSTORE_PATH" =~ ^/ ]]; then
        # Es absoluta, convertir a relativa desde el directorio del proyecto
        keystore_path_rel=$(realpath --relative-to="$(pwd)" "$KEYSTORE_PATH" 2>/dev/null || echo "$KEYSTORE_PATH")
    fi
    
    # Crear o actualizar flet.toml con la configuración de versión, keystore e icono
    if [ ! -f "$FLET_CONFIG_FILE" ]; then
        # Crear flet.toml básico
        cat > "$FLET_CONFIG_FILE" << EOF
# Configuración de Flet para builds de Android
# Generado automáticamente por build_android.sh
# Este archivo se actualiza automáticamente en cada build

[app]
name = "$APP_NAME"
version = "$version_name"
package = "com.flet.${APP_NAME//-/_}"
icon = "$icon_path"

[android]
min_sdk = 21
target_sdk = 34
compile_sdk = 34
version_code = $version_code
version_name = "$version_name"
keystore_path = "$keystore_path_rel"
keystore_password = "$KEYSTORE_PASSWORD"
key_alias = "$KEY_ALIAS"
key_password = "$KEY_PASSWORD"
EOF
        print_success "Archivo $FLET_CONFIG_FILE creado"
    else
        # Actualizar icono en [app]
        if grep -q "^\[app\]" "$FLET_CONFIG_FILE"; then
            if grep -q "^icon\s*=" "$FLET_CONFIG_FILE"; then
                # Usar awk para reemplazar de forma segura (más seguro que sed con caracteres especiales)
                awk -v icon_line="icon = \"$icon_path\"" '/^icon\s*=/ {print icon_line; next} {print}' "$FLET_CONFIG_FILE" > "${FLET_CONFIG_FILE}.tmp" && mv "${FLET_CONFIG_FILE}.tmp" "$FLET_CONFIG_FILE"
            else
                # Agregar icon después de [app] o después de package usando un método más seguro
                if grep -q "^package\s*=" "$FLET_CONFIG_FILE"; then
                    # Usar awk o perl para insertar de forma segura
                    awk -v icon_line="icon = \"$icon_path\"" '/^package\s*=/ {print; print icon_line; next} {print}' "$FLET_CONFIG_FILE" > "${FLET_CONFIG_FILE}.tmp" && mv "${FLET_CONFIG_FILE}.tmp" "$FLET_CONFIG_FILE"
                else
                    awk -v icon_line="icon = \"$icon_path\"" '/^\[app\]/ {print; print icon_line; next} {print}' "$FLET_CONFIG_FILE" > "${FLET_CONFIG_FILE}.tmp" && mv "${FLET_CONFIG_FILE}.tmp" "$FLET_CONFIG_FILE"
                fi
            fi
            
            # Actualizar version en [app]
            if grep -q "^version\s*=" "$FLET_CONFIG_FILE"; then
                sed -i "s|^version\s*=.*|version = \"$version_name\"|" "$FLET_CONFIG_FILE"
            else
                sed -i "/^\[app\]/a version = \"$version_name\"" "$FLET_CONFIG_FILE"
            fi
        else
            # Agregar sección [app] completa
            echo "" >> "$FLET_CONFIG_FILE"
            echo "[app]" >> "$FLET_CONFIG_FILE"
            echo "name = \"$APP_NAME\"" >> "$FLET_CONFIG_FILE"
            echo "version = \"$version_name\"" >> "$FLET_CONFIG_FILE"
            echo "package = \"com.flet.${APP_NAME//-/_}\"" >> "$FLET_CONFIG_FILE"
            echo "icon = \"$icon_path\"" >> "$FLET_CONFIG_FILE"
        fi
        
        # Actualizar version_code en [android]
        if grep -q "^\[android\]" "$FLET_CONFIG_FILE"; then
            # Actualizar o agregar version_code
            if grep -q "^version_code\s*=" "$FLET_CONFIG_FILE"; then
                sed -i "s|^version_code\s*=.*|version_code = $version_code|" "$FLET_CONFIG_FILE"
            else
                # Agregar después de [android]
                sed -i "/^\[android\]/a version_code = $version_code" "$FLET_CONFIG_FILE"
            fi
            
            # Actualizar o agregar version_name
            if grep -q "^version_name\s*=" "$FLET_CONFIG_FILE"; then
                sed -i "s|^version_name\s*=.*|version_name = \"$version_name\"|" "$FLET_CONFIG_FILE"
            else
                # Agregar después de version_code o [android]
                if grep -q "^version_code" "$FLET_CONFIG_FILE"; then
                    sed -i "/^version_code/a version_name = \"$version_name\"" "$FLET_CONFIG_FILE"
                else
                    sed -i "/^\[android\]/a version_name = \"$version_name\"" "$FLET_CONFIG_FILE"
                fi
            fi
            
            # Actualizar o agregar configuración del keystore
            if grep -q "^keystore_path\s*=" "$FLET_CONFIG_FILE"; then
                sed -i "s|^keystore_path\s*=.*|keystore_path = \"$keystore_path_rel\"|" "$FLET_CONFIG_FILE"
            else
                sed -i "/^\[android\]/a keystore_path = \"$keystore_path_rel\"" "$FLET_CONFIG_FILE"
            fi
            
            if grep -q "^keystore_password\s*=" "$FLET_CONFIG_FILE"; then
                sed -i "s|^keystore_password\s*=.*|keystore_password = \"$KEYSTORE_PASSWORD\"|" "$FLET_CONFIG_FILE"
            else
                sed -i "/^keystore_path/a keystore_password = \"$KEYSTORE_PASSWORD\"" "$FLET_CONFIG_FILE"
            fi
            
            if grep -q "^key_alias\s*=" "$FLET_CONFIG_FILE"; then
                sed -i "s|^key_alias\s*=.*|key_alias = \"$KEY_ALIAS\"|" "$FLET_CONFIG_FILE"
            else
                sed -i "/^keystore_password/a key_alias = \"$KEY_ALIAS\"" "$FLET_CONFIG_FILE"
            fi
            
            if grep -q "^key_password\s*=" "$FLET_CONFIG_FILE"; then
                sed -i "s|^key_password\s*=.*|key_password = \"$KEY_PASSWORD\"|" "$FLET_CONFIG_FILE"
            else
                sed -i "/^key_alias/a key_password = \"$KEY_PASSWORD\"" "$FLET_CONFIG_FILE"
            fi
        else
            # Agregar sección [android] completa
            echo "" >> "$FLET_CONFIG_FILE"
            echo "[android]" >> "$FLET_CONFIG_FILE"
            echo "version_code = $version_code" >> "$FLET_CONFIG_FILE"
            echo "version_name = \"$version_name\"" >> "$FLET_CONFIG_FILE"
            echo "keystore_path = \"$keystore_path_rel\"" >> "$FLET_CONFIG_FILE"
            echo "keystore_password = \"$KEYSTORE_PASSWORD\"" >> "$FLET_CONFIG_FILE"
            echo "key_alias = \"$KEY_ALIAS\"" >> "$FLET_CONFIG_FILE"
            echo "key_password = \"$KEY_PASSWORD\"" >> "$FLET_CONFIG_FILE"
        fi
        
        print_success "Archivo $FLET_CONFIG_FILE actualizado"
    fi
    
    # Verificación final: asegurar que icono y keystore estén configurados
    if ! grep -q "^icon\s*=" "$FLET_CONFIG_FILE"; then
        print_error "Error: El icono no se configuró correctamente en $FLET_CONFIG_FILE"
        exit 1
    fi
    
    if ! grep -q "^keystore_path\s*=" "$FLET_CONFIG_FILE"; then
        print_error "Error: El keystore no se configuró correctamente en $FLET_CONFIG_FILE"
        exit 1
    fi
    
    print_success "Configuración verificada: icono y keystore presentes en $FLET_CONFIG_FILE"
}

# Función para validar versionCode
validate_version_code() {
    local version_code="$1"
    
    # Verificar que sea numérico
    if ! [[ "$version_code" =~ ^[0-9]+$ ]]; then
        print_error "versionCode debe ser numérico: $version_code"
        exit 1
    fi
    
    # Verificar que sea mayor a 0
    if [ "$version_code" -le 0 ]; then
        print_error "versionCode debe ser mayor a 0: $version_code"
        exit 1
    fi
    
    # Verificar que no sea demasiado grande (límite de Android: 2147483647)
    if [ "$version_code" -gt 2147483647 ]; then
        print_error "versionCode excede el límite máximo de Android (2147483647): $version_code"
        exit 1
    fi
    
    print_success "versionCode validado: $version_code"
}

# Función para validar versionName
validate_version_name() {
    local version_name="$1"
    
    # Verificar formato semántico
    if ! echo "$version_name" | grep -qE '^[0-9]+\.[0-9]+\.[0-9]+'; then
        print_error "versionName debe seguir el formato MAJOR.MINOR.PATCH: $version_name"
        exit 1
    fi
    
    print_success "versionName validado: $version_name"
}

# Función para cargar variables de entorno desde archivo .env
load_env_file() {
    if [ -f "$ENV_FILE" ]; then
        print_info "Cargando variables de entorno desde $ENV_FILE"
        # Cargar variables desde .env (ignorando comentarios y líneas vacías)
        set -a
        source <(grep -v '^#' "$ENV_FILE" | grep -v '^$' | sed 's/^/export /')
        set +a
        print_success "Variables de entorno cargadas"
    else
        print_warning "Archivo .env no encontrado. Usando variables de entorno del sistema."
    fi
}

# Función para validar credenciales del keystore
validate_keystore_credentials() {
    local missing_vars=()
    
    # Verificar que todas las variables requeridas estén definidas
    if [ -z "$KEYSTORE_PATH" ]; then
        missing_vars+=("KEYSTORE_PATH")
    fi
    
    if [ -z "$KEYSTORE_PASSWORD" ]; then
        missing_vars+=("KEYSTORE_PASSWORD")
    fi
    
    if [ -z "$KEY_ALIAS" ]; then
        missing_vars+=("KEY_ALIAS")
    fi
    
    if [ -z "$KEY_PASSWORD" ]; then
        missing_vars+=("KEY_PASSWORD")
    fi
    
    if [ ${#missing_vars[@]} -gt 0 ]; then
        print_error "Faltan las siguientes variables de entorno:"
        for var in "${missing_vars[@]}"; do
            echo "  - $var"
        done
        echo ""
        print_info "Configura las variables en:"
        echo "  1. Archivo .env (recomendado)"
        echo "  2. Variables de entorno del sistema"
        echo ""
        print_info "Ejemplo de archivo .env:"
        echo "  KEYSTORE_PATH=android/keystore/justice_task_power.jks"
        echo "  KEYSTORE_PASSWORD=tu_contraseña_keystore"
        echo "  KEY_ALIAS=justice_task_power"
        echo "  KEY_PASSWORD=tu_contraseña_key"
        exit 1
    fi
    
    # Si KEYSTORE_PATH no es absoluta, usar la ruta relativa al proyecto
    if [[ ! "$KEYSTORE_PATH" =~ ^/ ]]; then
        KEYSTORE_PATH="$(pwd)/$KEYSTORE_PATH"
    fi
    
    print_success "Todas las credenciales están definidas"
}

# Función para validar que el keystore existe y es válido
validate_keystore() {
    print_info "Validando keystore..."
    
    if [ ! -f "$KEYSTORE_PATH" ]; then
        print_error "Keystore no encontrado: $KEYSTORE_PATH"
        print_info "Crea el keystore con el siguiente comando:"
        echo ""
        echo "  keytool -genkey -v -keystore $KEYSTORE_PATH \\"
        echo "    -alias $KEY_ALIAS -keyalg RSA -keysize 2048 \\"
        echo "    -validity 10000 -storepass \$KEYSTORE_PASSWORD \\"
        echo "    -keypass \$KEY_PASSWORD"
        echo ""
        exit 1
    fi
    
    # Verificar que el keystore es válido y el alias existe
    if ! keytool -list -v -keystore "$KEYSTORE_PATH" \
        -storepass "$KEYSTORE_PASSWORD" \
        -alias "$KEY_ALIAS" &> /dev/null; then
        print_error "Error al validar el keystore"
        print_error "Verifica que:"
        echo "  - El keystore existe: $KEYSTORE_PATH"
        echo "  - La contraseña del keystore es correcta: KEYSTORE_PASSWORD"
        echo "  - El alias existe: $KEY_ALIAS"
        echo "  - La contraseña del alias es correcta: KEY_PASSWORD"
        exit 1
    fi
    
    print_success "Keystore validado correctamente"
    print_info "Keystore: $KEYSTORE_PATH"
    print_info "Alias: $KEY_ALIAS"
}

# Función para verificar que jarsigner está disponible
check_jarsigner() {
    if ! command -v jarsigner &> /dev/null; then
        print_error "jarsigner no está disponible"
        print_info "jarsigner es parte del JDK. Instala Java JDK:"
        echo "  Ubuntu/Debian: sudo apt-get install openjdk-17-jdk"
        echo "  Fedora: sudo dnf install java-17-openjdk-devel"
        exit 1
    fi
    print_success "jarsigner encontrado"
}

# Función para verificar que apksigner está disponible (para verificación)
check_apksigner() {
    # apksigner puede estar en diferentes ubicaciones
    if command -v apksigner &> /dev/null; then
        print_success "apksigner encontrado"
        return 0
    fi
    
    # Buscar en ubicaciones comunes de Android SDK
    local android_home="${ANDROID_HOME:-${ANDROID_SDK_ROOT:-$HOME/Android/Sdk}}"
    local apksigner_paths=(
        "${android_home}/build-tools"/*/apksigner
        "${android_home}/cmdline-tools/latest/bin/apksigner"
    )
    
    for path in "${apksigner_paths[@]}"; do
        if [ -f "$path" ]; then
            export APKSIGNER_PATH="$path"
            print_success "apksigner encontrado: $path"
            return 0
        fi
    done
    
    print_warning "apksigner no encontrado. La verificación del firmado puede fallar."
    print_info "Instala Android SDK Build Tools o configura ANDROID_HOME"
    return 1
}

# Función para verificar si un APK tiene firma de debug
has_debug_signature() {
    local apk_file="$1"
    # Verificar si tiene firma de debug de Android
    if jarsigner -verify -certs "$apk_file" 2>&1 | grep -q "CN=Android Debug"; then
        return 0  # Tiene firma de debug
    fi
    return 1  # No tiene firma de debug
}

# Función para contar firmas únicas en un APK
count_apk_signatures() {
    local apk_file="$1"
    
    # Verificar que el archivo existe
    if [ ! -f "$apk_file" ]; then
        echo "0"
        return
    fi
    
    # Obtener la salida de verificación
    local verify_output=$(jarsigner -verify -verbose -certs "$apk_file" 2>&1)
    
    # Extraer los CN (Common Name) únicos de los certificados
    # Cada firma tiene un CN único, así que contamos CNs únicos
    local unique_cns=$(echo "$verify_output" | grep -A 1 ">>> Signer" | grep "X\.509" | sed 's/.*CN=\([^,]*\).*/\1/' | sort -u)
    local signer_count=$(echo "$unique_cns" | grep -v '^$' | wc -l)
    
    # Limpiar el resultado: solo números
    signer_count=$(echo "$signer_count" | tr -d '[:space:]' | sed 's/[^0-9]//g')
    
    # Si no es un número válido o está vacío, devolver 0
    if ! [[ "$signer_count" =~ ^[0-9]+$ ]] || [ -z "$signer_count" ]; then
        signer_count=0
    fi
    
    # Devolver solo el número
    echo "$signer_count"
}

# Función para firmar APK
sign_apk() {
    local apk_file="$1"
    
    if [ ! -f "$apk_file" ]; then
        print_error "APK no encontrado: $apk_file"
        exit 1
    fi
    
    # Verificar si el APK ya está firmado
    print_info "Verificando estado de firma del APK..."
    local signer_count=$(count_apk_signatures "$apk_file")
    
    if [ "$signer_count" -eq 1 ]; then
        # Verificar si es firma de debug o de producción
        if has_debug_signature "$apk_file"; then
            print_warning "El APK tiene una firma de debug. Reemplazando con firma de producción..."
            # Eliminar la firma de debug antes de firmar con producción
            # Esto requiere descomprimir, eliminar META-INF, y volver a comprimir
            print_info "Eliminando firma de debug..."
            # Eliminar META-INF completamente usando unzip y zip
            # Crear un directorio temporal para descomprimir
            local temp_dir=$(mktemp -d)
            unzip -q "$apk_file" -d "$temp_dir" 2>/dev/null || true
            # Eliminar META-INF
            rm -rf "${temp_dir}/META-INF" 2>/dev/null || true
            # Recrear el APK sin META-INF
            cd "$temp_dir"
            zip -q -r "$apk_file" . -x "*.apk" 2>/dev/null || true
            cd - > /dev/null
            rm -rf "$temp_dir"
            print_success "Firma de debug eliminada"
        else
            print_success "✅ APK ya está firmado con certificado de producción"
            print_info "Verificando la firma..."
            if jarsigner -verify -certs "$apk_file" &> /dev/null; then
                print_success "La firma es válida. El APK está listo para instalar."
                return 0
            else
                print_warning "La firma existe pero la verificación falló. Re-firmando..."
            fi
        fi
    elif [ "$signer_count" -gt 1 ]; then
        print_error "❌ El APK tiene $signer_count firmas (debe tener solo 1)"
        print_error "Esto impide la instalación. Eliminando todas las firmas y re-firmando..."
        # Eliminar todas las firmas usando unzip y zip
        local temp_dir=$(mktemp -d)
        unzip -q "$apk_file" -d "$temp_dir" 2>/dev/null || true
        # Eliminar META-INF
        rm -rf "${temp_dir}/META-INF" 2>/dev/null || true
        # Recrear el APK sin META-INF
        cd "$temp_dir"
        zip -q -r "$apk_file" . -x "*.apk" 2>/dev/null || true
        cd - > /dev/null
        rm -rf "$temp_dir"
        print_success "Todas las firmas eliminadas"
    else
        print_info "El APK no está firmado. Firmando ahora..."
    fi
    
    print_info "Firmando APK: $apk_file"
    
    # Firmar el APK con jarsigner
    # Redirigir stderr para capturar errores, pero permitir que jarsigner muestre progreso
    if jarsigner -sigalg SHA256withRSA -digestalg SHA-256 \
        -keystore "$KEYSTORE_PATH" \
        -storepass "$KEYSTORE_PASSWORD" \
        -keypass "$KEY_PASSWORD" \
        "$apk_file" \
        "$KEY_ALIAS" 2>&1; then
        print_success "APK firmado exitosamente"
    else
        local exit_code=$?
        print_error "Error al firmar APK (código: $exit_code)"
        print_error "Verifica que:"
        echo "  - El keystore existe: $KEYSTORE_PATH"
        echo "  - La contraseña del keystore es correcta"
        echo "  - El alias existe: $KEY_ALIAS"
        echo "  - La contraseña del alias es correcta"
        exit 1
    fi
    
    # Verificar el firmado
    print_info "Verificando firmado del APK..."
    
    # Primero verificar que jarsigner puede verificar el APK
    if ! jarsigner -verify "$apk_file" &> /dev/null; then
        print_error "❌ Error: jarsigner no puede verificar el APK"
        print_error "El APK puede estar corrupto o no estar firmado correctamente"
        exit 1
    fi
    
    local final_signer_count=$(count_apk_signatures "$apk_file")
    # Validar que final_signer_count sea un número válido
    if ! [[ "$final_signer_count" =~ ^[0-9]+$ ]]; then
        print_error "❌ Error al contar firmas: resultado inválido '$final_signer_count'"
        exit 1
    fi
    
    # Verificar si tiene firma de debug
    local has_debug=$(has_debug_signature "$apk_file" && echo "1" || echo "0")
    
    if [ "$final_signer_count" -eq 1 ] && [ "$has_debug" -eq 0 ]; then
        print_success "✅ APK firmado correctamente con certificado de producción (1 firma)"
    elif [ "$final_signer_count" -eq 0 ]; then
        print_error "❌ Error: El APK no tiene firmas después del proceso de firma"
        print_error "Esto puede indicar un problema con el keystore o el proceso de firma"
        print_info "Intentando verificar manualmente..."
        jarsigner -verify -verbose -certs "$apk_file" 2>&1 | head -20
        exit 1
    elif [ "$final_signer_count" -gt 1 ]; then
        print_error "❌ Error: El APK tiene $final_signer_count firmas (debe tener solo 1)"
        exit 1
    elif [ "$has_debug" -eq 1 ]; then
        print_error "❌ Error: El APK aún tiene firma de debug"
        exit 1
    else
        print_warning "⚠️  Advertencia: Estado de firma inesperado (count: $final_signer_count, debug: $has_debug)"
        print_info "El APK puede estar firmado, pero la verificación no es concluyente"
        print_info "Verificando con jarsigner..."
        if jarsigner -verify "$apk_file" &> /dev/null; then
            print_success "✅ jarsigner verifica el APK como válido"
        else
            print_error "❌ jarsigner no puede verificar el APK"
            exit 1
        fi
    fi
    
    # Intentar verificación adicional con apksigner si está disponible
    if command -v apksigner &> /dev/null || [ -n "$APKSIGNER_PATH" ]; then
        local apksigner_cmd="${APKSIGNER_PATH:-apksigner}"
        if $apksigner_cmd verify "$apk_file" &> /dev/null; then
            print_success "Verificación adicional con apksigner: OK"
        else
            print_warning "Verificación con apksigner falló, pero jarsigner verificó correctamente"
        fi
    fi
    
    print_success "APK firmado guardado: $apk_file"
}

# Función para contar cadenas de certificados en un AAB
count_cert_chains() {
    local aab_file="$1"
    
    # Verificar que el archivo existe
    if [ ! -f "$aab_file" ]; then
        echo "0"
        return
    fi
    
    # Intentar verificar con jarsigner y capturar la salida completa
    local verify_output=$(jarsigner -verify -certs "$aab_file" 2>&1)
    local verify_exit_code=$?
    
    # Si la verificación falla completamente, no hay firmas
    if [ $verify_exit_code -ne 0 ]; then
        # Verificar si es porque no está firmado o porque hay un error
        if echo "$verify_output" | grep -q "jar is unsigned"; then
            echo "0"
            return
        fi
        # Si hay otro error, intentar contar de todas formas
    fi
    
    # Contar las cadenas de certificados en la salida
    local cert_count=$(echo "$verify_output" | grep -c "Certificate chain" 2>/dev/null || echo "0")
    
    # Limpiar el resultado: eliminar espacios, saltos de línea y caracteres no numéricos
    cert_count=$(echo "$cert_count" | tr -d '[:space:][:alpha:]' | sed 's/[^0-9]//g' | head -n 1)
    
    # Si después de limpiar está vacío o no es numérico, devolver 0
    if [ -z "$cert_count" ] || ! [[ "$cert_count" =~ ^[0-9]+$ ]]; then
        cert_count=0
    fi
    
    # Convertir a número entero (eliminar ceros a la izquierda si es necesario, pero mantener 0)
    cert_count=$((10#$cert_count))  # Forzar interpretación como base 10
    
    echo "$cert_count"
}

# Función para verificar si un AAB ya está firmado (múltiples métodos)
is_aab_signed() {
    local aab_file="$1"
    
    # Método 1: Verificar con jarsigner -verify
    if jarsigner -verify -certs "$aab_file" &> /dev/null; then
        # Si la verificación pasa, probablemente está firmado
        # Contar el número de firmas (cadenas de certificados)
        local cert_count=$(count_cert_chains "$aab_file")
        if [ "$cert_count" -gt 0 ]; then
            return 0  # Está firmado
        fi
        # Si la verificación pasa pero no encontramos cadenas, puede estar firmado de otra forma
        # Verificar si hay archivos de firma en el AAB
        if unzip -l "$aab_file" 2>/dev/null | grep -q "META-INF/.*\.SF\|META-INF/.*\.RSA\|META-INF/.*\.DSA"; then
            return 0  # Tiene archivos de firma, está firmado
        fi
    fi
    
    # Método 2: Verificar si hay archivos de firma en el AAB directamente
    if unzip -l "$aab_file" 2>/dev/null | grep -qE "META-INF/.*\.(SF|RSA|DSA|EC)"; then
        return 0  # Tiene archivos de firma, está firmado
    fi
    
    return 1  # No está firmado
}

# Función para firmar AAB (solo si no está ya firmado)
sign_aab() {
    local aab_file="$1"
    
    if [ ! -f "$aab_file" ]; then
        print_error "AAB no encontrado: $aab_file"
        exit 1
    fi
    
    # Verificar si el AAB ya está firmado ANTES de intentar firmarlo
    print_info "Verificando estado de firma del AAB..."
    
    # Primero verificar si está firmado usando múltiples métodos
    if is_aab_signed "$aab_file"; then
        # Está firmado, verificar cuántas cadenas tiene
        local cert_count=$(count_cert_chains "$aab_file")
        
        if [ "$cert_count" -eq 1 ]; then
            print_success "✅ AAB ya está correctamente firmado con 1 cadena de certificados"
            print_info "El AAB fue firmado por Flet automáticamente. No es necesario firmar de nuevo."
            print_success "El AAB está listo para Google Play."
            return 0
        elif [ "$cert_count" -gt 1 ]; then
            print_error "❌ El AAB tiene $cert_count cadenas de certificados (debe tener solo 1)"
            print_error "Esto indica que el AAB fue firmado múltiples veces."
            print_error "Posibles causas:"
            echo "  1. El AAB fue firmado por Flet Y luego firmado manualmente"
            echo "  2. El AAB fue reconstruido sobre un AAB previamente firmado"
            print_info "Solución:"
            echo "  1. Elimina el AAB actual: rm -f $aab_file"
            echo "  2. Limpia el build: rm -rf $BUILD_DIR"
            echo "  3. Reconstruye desde cero: ./build_android.sh --aab"
            exit 1
        else
            # Está firmado pero no podemos contar las cadenas (puede ser un problema de detección)
            print_warning "El AAB parece estar firmado pero no pudimos contar las cadenas de certificados"
            print_warning "Para evitar múltiples firmas, NO intentaremos firmarlo de nuevo"
            print_info "Verificando manualmente con jarsigner..."
            if jarsigner -verify "$aab_file" &>/dev/null; then
                print_success "✅ La verificación de jarsigner pasó. El AAB está firmado correctamente."
                print_info "El AAB está listo para Google Play."
                return 0
            else
                print_error "❌ La verificación de jarsigner falló"
                print_info "El AAB puede estar corrupto o tener una firma inválida"
                exit 1
            fi
        fi
    else
        # No está firmado
        print_info "El AAB no está firmado. Flet debería haberlo firmado automáticamente."
        print_warning "Esto puede indicar que el keystore no está configurado correctamente en flet.toml"
        print_info "Verificando configuración del keystore en flet.toml..."
        if grep -q "keystore_path" "$FLET_CONFIG_FILE" 2>/dev/null; then
            print_warning "El keystore está configurado pero Flet no firmó el AAB"
            print_info "Intentando firmar manualmente..."
        else
            print_error "El keystore NO está configurado en flet.toml"
            print_error "El script debería haberlo configurado automáticamente"
            exit 1
        fi
    fi
    
    # Firmar el AAB con jarsigner
    print_info "Firmando AAB: $aab_file"
    if jarsigner -sigalg SHA256withRSA -digestalg SHA-256 \
        -keystore "$KEYSTORE_PATH" \
        -storepass "$KEYSTORE_PASSWORD" \
        -keypass "$KEY_PASSWORD" \
        "$aab_file" \
        "$KEY_ALIAS" 2>&1; then
        print_success "AAB firmado exitosamente"
    else
        local exit_code=$?
        print_error "Error al firmar AAB (código: $exit_code)"
        print_error "Verifica que:"
        echo "  - El keystore existe: $KEYSTORE_PATH"
        echo "  - La contraseña del keystore es correcta"
        echo "  - El alias existe: $KEY_ALIAS"
        echo "  - La contraseña del alias es correcta"
        exit 1
    fi
    
    # Verificar el firmado
    print_info "Verificando firmado del AAB..."
    if jarsigner -verify -certs "$aab_file" &> /dev/null; then
        local cert_count=$(count_cert_chains "$aab_file")
        if [ "$cert_count" -eq 1 ]; then
            print_success "✅ AAB firmado correctamente con 1 cadena de certificados"
        else
            print_error "❌ Error: El AAB tiene $cert_count cadenas de certificados (debe tener solo 1)"
            exit 1
        fi
    else
        print_error "❌ Error en el firmado: verificación falló"
        print_error "El AAB puede estar corrupto o el firmado es inválido"
        exit 1
    fi
    
    print_success "AAB firmado guardado: $aab_file"
}

# Función para construir APK
build_apk() {
    local version_name="$1"
    local version_code="$2"
    
    print_info "Iniciando build de APK..."
    print_info "Building version $version_name (code $version_code)"
    
    local icon_path=$(find_icon 2>/dev/null | tail -n 1)
    # Limpiar cualquier código de color ANSI o mensajes que puedan haber quedado
    icon_path=$(echo "$icon_path" | sed 's/\x1b\[[0-9;]*m//g' | tr -d '\n\r' | sed 's/^[^a-zA-Z]*//' | sed 's/[^a-zA-Z0-9._/-]*$//' | grep -o 'assets/[^"]*' | head -n 1 || echo "$icon_path" | grep -o 'assets/[^"]*' | head -n 1)
    local output_file="${APK_DIR}/${APP_NAME}.apk"
    
    print_info "Usando icono: $icon_path"
    print_info "Flet leerá el icono desde flet.toml y pyproject.toml"
    
    # Asegurar que el icono esté actualizado en flet.toml
    if [ -f "$FLET_CONFIG_FILE" ]; then
        # Escapar la ruta del icono para grep
        local icon_path_escaped_grep=$(echo "$icon_path" | sed 's/[[\.*^$()+?{|]/\\&/g')
        if ! grep -q "^icon\s*=\s*\"$icon_path_escaped_grep\"" "$FLET_CONFIG_FILE"; then
            print_warning "Actualizando icono en flet.toml..."
            if grep -q "^\[app\]" "$FLET_CONFIG_FILE"; then
                if grep -q "^icon\s*=" "$FLET_CONFIG_FILE"; then
                    # Usar awk para reemplazar de forma segura (más seguro que sed con caracteres especiales)
                    awk -v icon_line="icon = \"$icon_path\"" '/^icon\s*=/ {print icon_line; next} {print}' "$FLET_CONFIG_FILE" > "${FLET_CONFIG_FILE}.tmp" && mv "${FLET_CONFIG_FILE}.tmp" "$FLET_CONFIG_FILE"
                else
                    # Usar awk para insertar de forma segura
                    awk -v icon_line="icon = \"$icon_path\"" '/^\[app\]/ {print; print icon_line; next} {print}' "$FLET_CONFIG_FILE" > "${FLET_CONFIG_FILE}.tmp" && mv "${FLET_CONFIG_FILE}.tmp" "$FLET_CONFIG_FILE"
                fi
            fi
        fi
    fi
    
    # Construir APK con Flet (el icono y versión se leen desde flet.toml)
    # Especificar el archivo principal explícitamente
    # Asegurar que el entorno virtual esté activado
    activate_venv
    print_info "Construyendo APK con Flet..."
    print_info "Archivo principal: main.py"
    if flet build apk --verbose; then
        print_success "APK construido exitosamente"
        
        # Buscar el APK generado por Flet (puede estar en diferentes ubicaciones)
        local flet_apk=""
        
        # Buscar en ubicaciones comunes
        local search_paths=(
            "${BUILD_DIR}/apk"
            "${BUILD_DIR}/flutter/build/app/outputs/flutter-apk"
            "${BUILD_DIR}"
        )
        
        for search_path in "${search_paths[@]}"; do
            if [ -d "$search_path" ]; then
                flet_apk=$(find "$search_path" -name "*.apk" -type f ! -name "*.apk.sha1" | head -n 1)
                if [ -n "$flet_apk" ] && [ -f "$flet_apk" ]; then
                    break
                fi
            fi
        done
        
        if [ -z "$flet_apk" ]; then
            # Búsqueda más amplia
            flet_apk=$(find "$BUILD_DIR" -name "*.apk" -type f ! -name "*.apk.sha1" | head -n 1)
        fi
        
        if [ -n "$flet_apk" ] && [ -f "$flet_apk" ]; then
            # Si el archivo ya está en la ubicación correcta con el nombre correcto, no hacer nada
            if [ "$flet_apk" != "$output_file" ]; then
                # Mover y renombrar el APK
                mv "$flet_apk" "$output_file"
                print_success "APK renombrado a: $output_file"
            else
                print_success "APK ya está en la ubicación correcta"
            fi
            
            # Mostrar información del archivo
            local file_size=$(du -h "$output_file" | cut -f1)
            print_success "APK generado: $output_file (${file_size})"
            
            # Firmar el APK
            echo ""
            sign_apk "$output_file"
        else
            print_warning "No se encontró el APK generado en la ubicación esperada"
            print_info "Buscando en: $BUILD_DIR"
            find "$BUILD_DIR" -name "*.apk" -type f 2>/dev/null || true
            print_error "No se pudo encontrar el APK generado"
            exit 1
        fi
    else
        print_error "Error al construir APK"
        exit 1
    fi
}

# Función para construir AAB
build_aab() {
    local version_name="$1"
    local version_code="$2"
    
    print_info "Iniciando build de AAB..."
    print_info "Building version $version_name (code $version_code)"
    
    local icon_path=$(find_icon)
    local output_file="${AAB_DIR}/${APP_NAME}.aab"
    
    print_info "Usando icono: $icon_path"
    print_info "Flet leerá el icono desde flet.toml y pyproject.toml"
    
    # Asegurar que el icono esté actualizado en flet.toml
    if [ -f "$FLET_CONFIG_FILE" ]; then
        # Escapar la ruta del icono para grep
        local icon_path_escaped_grep=$(echo "$icon_path" | sed 's/[[\.*^$()+?{|]/\\&/g')
        if ! grep -q "^icon\s*=\s*\"$icon_path_escaped_grep\"" "$FLET_CONFIG_FILE"; then
            print_warning "Actualizando icono en flet.toml..."
            if grep -q "^\[app\]" "$FLET_CONFIG_FILE"; then
                if grep -q "^icon\s*=" "$FLET_CONFIG_FILE"; then
                    # Usar awk para reemplazar de forma segura (más seguro que sed con caracteres especiales)
                    awk -v icon_line="icon = \"$icon_path\"" '/^icon\s*=/ {print icon_line; next} {print}' "$FLET_CONFIG_FILE" > "${FLET_CONFIG_FILE}.tmp" && mv "${FLET_CONFIG_FILE}.tmp" "$FLET_CONFIG_FILE"
                else
                    # Usar awk para insertar de forma segura
                    awk -v icon_line="icon = \"$icon_path\"" '/^\[app\]/ {print; print icon_line; next} {print}' "$FLET_CONFIG_FILE" > "${FLET_CONFIG_FILE}.tmp" && mv "${FLET_CONFIG_FILE}.tmp" "$FLET_CONFIG_FILE"
                fi
            fi
        fi
    fi
    
    # Construir AAB con Flet (el icono y versión se leen desde flet.toml)
    # Especificar el archivo principal explícitamente
    # Asegurar que el entorno virtual esté activado
    activate_venv
    print_info "Construyendo AAB con Flet..."
    print_info "Archivo principal: main.py"
    if flet build aab --verbose; then
        print_success "AAB construido exitosamente"
        
        # Buscar el AAB generado por Flet (puede estar en diferentes ubicaciones)
        local flet_aab=""
        
        # Buscar en ubicaciones comunes
        local search_paths=(
            "${BUILD_DIR}/aab"
            "${BUILD_DIR}/flutter/build/app/outputs/bundle"
            "${BUILD_DIR}"
        )
        
        for search_path in "${search_paths[@]}"; do
            if [ -d "$search_path" ]; then
                flet_aab=$(find "$search_path" -name "*.aab" -type f | head -n 1)
                if [ -n "$flet_aab" ] && [ -f "$flet_aab" ]; then
                    break
                fi
            fi
        done
        
        if [ -z "$flet_aab" ]; then
            # Búsqueda más amplia
            flet_aab=$(find "$BUILD_DIR" -name "*.aab" -type f | head -n 1)
        fi
        
        if [ -n "$flet_aab" ] && [ -f "$flet_aab" ]; then
            # Si el archivo ya está en la ubicación correcta con el nombre correcto, no hacer nada
            if [ "$flet_aab" != "$output_file" ]; then
                # Mover y renombrar el AAB
                mv "$flet_aab" "$output_file"
                print_success "AAB renombrado a: $output_file"
            else
                print_success "AAB ya está en la ubicación correcta"
            fi
            
            # Mostrar información del archivo
            local file_size=$(du -h "$output_file" | cut -f1)
            print_success "AAB generado: $output_file (${file_size})"
            
            # Firmar el AAB
            echo ""
            sign_aab "$output_file"
        else
            print_warning "No se encontró el AAB generado en la ubicación esperada"
            print_info "Buscando en: $BUILD_DIR"
            find "$BUILD_DIR" -name "*.aab" -type f 2>/dev/null || true
            print_error "No se pudo encontrar el AAB generado"
            exit 1
        fi
    else
        print_error "Error al construir AAB"
        exit 1
    fi
}

# Función para validar argumentos
validate_args() {
    local build_apk=false
    local build_aab=false
    
    for arg in "$@"; do
        case "$arg" in
            --apk)
                build_apk=true
                ;;
            --aab)
                build_aab=true
                ;;
            --help|-h)
                show_help
                exit 0
                ;;
            *)
                print_error "Opción desconocida: $arg"
                show_help
                exit 1
                ;;
        esac
    done
    
    # Si no se especificó ninguna opción, construir ambos
    if [ "$build_apk" = false ] && [ "$build_aab" = false ]; then
        build_apk=true
        build_aab=true
    fi
    
    # Exportar variables para uso en el script principal
    export BUILD_APK=$build_apk
    export BUILD_AAB=$build_aab
}

# ============================================================================
# SCRIPT PRINCIPAL
# ============================================================================

main() {
    print_info "=========================================="
    print_info "  Build Android - Justice Driven Task Power"
    print_info "=========================================="
    echo ""
    
    # Validar argumentos
    validate_args "$@"
    
    # Reactivar set -e para el resto del script
    set -e
    
    # Verificar que estamos en el directorio correcto
    if [ ! -f "main.py" ] && [ ! -f "app/main.py" ]; then
        print_error "No se encontró main.py. Asegúrate de ejecutar el script desde la raíz del proyecto."
        exit 1
    fi
    
    # Verificar Flet
    check_flet
    
    # Validar icono
    find_icon > /dev/null
    
    # Cargar variables de entorno
    load_env_file
    
    # Validar credenciales del keystore
    validate_keystore_credentials
    
    # Validar keystore
    validate_keystore
    
    # Verificar herramientas de firmado
    check_jarsigner
    check_apksigner || true  # No crítico si no está disponible
    
    # ============================================================================
    # GESTIÓN DE VERSIONADO
    # ============================================================================
    echo ""
    print_info "=========================================="
    print_info "  Gestión de Versionado"
    print_info "=========================================="
    
    # Leer versión base
    BASE_VERSION=$(read_base_version)
    print_success "Versión base: $BASE_VERSION"
    
    # Calcular versionCode (los mensajes informativos se imprimen a stderr)
    VERSION_CODE=$(get_version_code "$BASE_VERSION")
    print_success "versionCode: $VERSION_CODE"
    
    # Validar versiones
    validate_version_name "$BASE_VERSION"
    validate_version_code "$VERSION_CODE"
    
    # Actualizar configuración de Flet
    update_flet_version_config "$BASE_VERSION" "$VERSION_CODE"
    
    echo ""
    print_info "=========================================="
    print_info "  Build con versión $BASE_VERSION (code $VERSION_CODE)"
    print_info "=========================================="
    echo ""
    
    # Crear directorios
    create_directories
    
    # Construir según las opciones
    if [ "$BUILD_APK" = true ]; then
        echo ""
        build_apk "$BASE_VERSION" "$VERSION_CODE"
    fi
    
    if [ "$BUILD_AAB" = true ]; then
        echo ""
        build_aab "$BASE_VERSION" "$VERSION_CODE"
    fi
    
    # Resumen final
    echo ""
    print_info "=========================================="
    print_success "Build completado exitosamente!"
    print_info "=========================================="
    echo ""
    print_info "Versión: $BASE_VERSION (code $VERSION_CODE)"
    echo ""
    
    if [ "$BUILD_APK" = true ]; then
        if [ -f "${APK_DIR}/${APP_NAME}.apk" ]; then
            local apk_size=$(du -h "${APK_DIR}/${APP_NAME}.apk" | cut -f1)
            print_success "APK: ${APK_DIR}/${APP_NAME}.apk (${apk_size})"
        fi
    fi
    
    if [ "$BUILD_AAB" = true ]; then
        if [ -f "${AAB_DIR}/${APP_NAME}.aab" ]; then
            local aab_size=$(du -h "${AAB_DIR}/${APP_NAME}.aab" | cut -f1)
            print_success "AAB: ${AAB_DIR}/${APP_NAME}.aab (${aab_size})"
        fi
    fi
    
    echo ""
    print_info "Próximo versionCode: $((VERSION_CODE + 1))"
}

# Ejecutar función principal
main "$@"

