#!/bin/bash

################################################################################
# Script de Build para Linux - Justice Driven Task Power
# 
# Este script genera un paquete .deb para distribuciones basadas en Debian/Ubuntu
# 
# Requisitos:
#   - Flet instalado (en venv o sistema)
#   - dpkg-deb instalado
#   - Linux (Debian/Ubuntu/Mint)
# 
# Uso:
#   ./build_linux.sh           # Genera el paquete .deb
#   ./build_linux.sh --clean   # Limpia builds anteriores
#   ./build_linux.sh --help    # Muestra esta ayuda
#
################################################################################

set +e

# ============================================================================
# CONFIGURACIÓN
# ============================================================================

APP_NAME="justice-driven-task-power"
APP_DISPLAY_NAME="Justice Driven Task Power"
APP_DESCRIPTION="Aplicación de productividad con tareas, hábitos, metas, puntos y recompensas"
APP_VERSION="1.0.0"
MAINTAINER="Justice Driven Task Power Team"
PACKAGE_NAME="justice-driven-task-power"

# Directorios
BUILD_DIR="build"
DEB_DIR="${BUILD_DIR}/deb"
DEB_PACKAGE_DIR="${DEB_DIR}/${PACKAGE_NAME}"

# Rutas de iconos
ICON_PATHS=(
    "assets/app_icon.png"
    "assets/task_logo.ico"
)

# ============================================================================
# FUNCIONES DE UTILIDAD
# ============================================================================

print_info() {
    echo -e "\033[0;34m[INFO]\033[0m $1"
}

print_success() {
    echo -e "\033[0;32m[SUCCESS]\033[0m $1"
}

print_warning() {
    echo -e "\033[1;33m[WARNING]\033[0m $1"
}

print_error() {
    echo -e "\033[0;31m[ERROR]\033[0m $1"
}

# Función para activar entorno virtual
activate_venv() {
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
    
    if [ -n "$VIRTUAL_ENV" ]; then
        export PATH="$VIRTUAL_ENV/bin:$PATH"
    fi
}

# Función para validar que Flet está instalado
check_flet() {
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
    
    echo "$icon_path"
}

# Función para leer versión desde pyproject.toml
read_version() {
    local version="$APP_VERSION"
    
    if [ -f "pyproject.toml" ]; then
        local version_from_file=$(grep -E "^version\s*=" pyproject.toml | head -n 1 | sed -E 's/.*version\s*=\s*["'\'']?([^"'\'']+)["'\'']?.*/\1/' | tr -d '[:space:]')
        if [ -n "$version_from_file" ]; then
            version="$version_from_file"
        fi
    fi
    
    echo "$version"
}

# Función para obtener arquitectura
get_architecture() {
    local arch=$(uname -m)
    case "$arch" in
        x86_64)
            echo "amd64"
            ;;
        aarch64|arm64)
            echo "arm64"
            ;;
        armv7l|armv6l)
            echo "armhf"
            ;;
        *)
            echo "amd64"  # Default
            ;;
    esac
}

# Función para limpiar builds anteriores
clean_build() {
    print_info "Limpiando builds anteriores..."
    rm -rf "$BUILD_DIR/linux"
    rm -rf "$DEB_DIR"
    rm -rf "$BUILD_DIR/flutter"
    rm -rf ".flet/build"
    print_success "Builds anteriores limpiados"
}

# Función para construir la aplicación Linux
build_linux_app() {
    print_info "Construyendo aplicación Linux con Flet..." >&2
    
    activate_venv
    
    # Limpiar caché de Flet y templates si existen
    print_info "Limpiando cachés de Flet y templates..." >&2
    rm -rf .flet/build 2>/dev/null || true
    rm -rf ~/.cookiecutters/flet-build-template 2>/dev/null || true
    rm -rf build/flutter 2>/dev/null || true
    
    # Construir con Flet (redirigir stderr para capturar errores pero mostrar progreso)
    local build_exit_code=0
    flet build linux 2>&1 | tee /tmp/flet_build_linux.log || build_exit_code=$?
    
    # Verificar si hubo errores en el log
    if grep -qi "ERROR.*pyrebase4\|No matching distribution\|satisfies the requirement" /tmp/flet_build_linux.log 2>/dev/null; then
        print_error "Error en las dependencias. Verificando pyproject.toml..." >&2
        if grep -q "pyrebase4>=4.9.0" pyproject.toml 2>/dev/null; then
            print_error "pyproject.toml aún tiene pyrebase4>=4.9.0. Debe ser >=4.8.0" >&2
            exit 1
        fi
        print_warning "El error puede ser de caché. Limpiando completamente y reintentando..." >&2
        rm -rf .flet/build build/flutter ~/.cookiecutters/flet-build-template 2>/dev/null || true
        sleep 1  # Dar tiempo para que se liberen los archivos
        if ! flet build linux 2>&1 | tee -a /tmp/flet_build_linux.log; then
            print_error "Error al construir aplicación Linux después de limpiar caché" >&2
            print_info "Revisa el log: /tmp/flet_build_linux.log" >&2
            exit 1
        fi
    elif [ $build_exit_code -ne 0 ]; then
        print_error "Error al construir aplicación Linux (código: $build_exit_code)" >&2
        print_info "Revisa el log: /tmp/flet_build_linux.log" >&2
        exit 1
    fi
    
    print_success "Aplicación Linux construida exitosamente" >&2
    
    # Buscar el ejecutable generado
    # Flet para Linux genera el ejecutable en diferentes ubicaciones según la versión
    local linux_executable=""
    
    # Esperar un momento para que el build termine completamente
    sleep 2
    
    # Buscar en ubicaciones comunes de Flet para Linux
    local search_paths=(
        # Ubicaciones estándar de Flutter Linux
        "${BUILD_DIR}/flutter/build/linux/x64/release/bundle/${APP_NAME}"
        "${BUILD_DIR}/flutter/build/linux/x64/release/bundle/my_application"
        "${BUILD_DIR}/flutter/build/linux/x64/release/bundle"
        # Ubicaciones alternativas
        "${BUILD_DIR}/linux/${APP_NAME}"
        "${BUILD_DIR}/linux/my_application"
        "${BUILD_DIR}/linux"
        # Directorio raíz de build
        "${BUILD_DIR}/${APP_NAME}"
        "${BUILD_DIR}/my_application"
    )
    
    print_info "Buscando ejecutable en ubicaciones estándar..." >&2
    for search_path in "${search_paths[@]}"; do
        if [ -f "$search_path" ] && [ -x "$search_path" ]; then
            # Verificar que sea un ejecutable ELF (no un script)
            if file "$search_path" 2>/dev/null | grep -q "ELF\|executable"; then
                linux_executable="$search_path"
                print_success "Ejecutable encontrado: $linux_executable" >&2
                break
            fi
        elif [ -d "$search_path" ]; then
            # Buscar ejecutables ELF en el directorio
            local found=$(find "$search_path" -type f -executable 2>/dev/null | while read f; do
                if file "$f" 2>/dev/null | grep -q "ELF\|executable"; then
                    echo "$f"
                    break
                fi
            done | head -n 1)
            if [ -n "$found" ] && [ -f "$found" ]; then
                linux_executable="$found"
                print_success "Ejecutable encontrado en directorio: $linux_executable" >&2
                break
            fi
        fi
    done
    
    # Si aún no se encontró, búsqueda más amplia pero solo ejecutables ELF
    if [ -z "$linux_executable" ]; then
        print_warning "Búsqueda amplia de ejecutables ELF..." >&2
        linux_executable=$(find "$BUILD_DIR/flutter/build/linux" -type f -executable 2>/dev/null | while read f; do
            if file "$f" 2>/dev/null | grep -qE "ELF.*executable|executable.*ELF"; then
                # Excluir librerías .so
                if [[ ! "$f" =~ \.so$ ]] && [[ ! "$f" =~ \.so\.[0-9] ]]; then
                    echo "$f"
                    break
                fi
            fi
        done | head -n 1)
    fi
    
    if [ -z "$linux_executable" ] || [ ! -f "$linux_executable" ]; then
        print_error "No se encontró el ejecutable de Linux después del build" >&2
        
        # Verificar si el build realmente se completó
        if grep -qi "ERROR.*pyrebase4\|No matching distribution" /tmp/flet_build_linux.log 2>/dev/null; then
            print_error "El build falló debido a problemas con las dependencias" >&2
            print_info "Últimas líneas del log:" >&2
            tail -20 /tmp/flet_build_linux.log >&2
            print_info "" >&2
            print_info "Solución: Verifica que pyproject.toml tenga pyrebase4>=4.8.0 (no 4.9.0)" >&2
            exit 1
        fi
        
        # Si no hay errores de dependencias, el ejecutable puede estar en otra ubicación
        print_info "Buscando todos los archivos en build/flutter/build/linux:" >&2
        find "$BUILD_DIR/flutter/build/linux" -type f 2>/dev/null | grep -v ".so" | grep -v "demo" | head -20 >&2
        exit 1
    fi
    
    print_success "Ejecutable encontrado: $linux_executable" >&2
    # Solo imprimir la ruta a stdout (sin mensajes)
    echo "$linux_executable"
}

# Función para crear estructura del paquete .deb
create_deb_structure() {
    print_info "Creando estructura del paquete .deb..."
    
    # Limpiar directorio anterior
    rm -rf "$DEB_PACKAGE_DIR"
    
    # Crear estructura de directorios
    mkdir -p "${DEB_PACKAGE_DIR}/DEBIAN"
    mkdir -p "${DEB_PACKAGE_DIR}/usr/bin"
    mkdir -p "${DEB_PACKAGE_DIR}/usr/share/applications"
    mkdir -p "${DEB_PACKAGE_DIR}/usr/share/${PACKAGE_NAME}"
    mkdir -p "${DEB_PACKAGE_DIR}/usr/share/icons/hicolor/256x256/apps"
    mkdir -p "${DEB_PACKAGE_DIR}/usr/share/pixmaps"
    
    print_success "Estructura de directorios creada"
}

# Función para copiar archivos de la aplicación
copy_app_files() {
    local linux_executable="$1"
    local icon_path="$2"
    
    print_info "Copiando archivos de la aplicación..."
    
    # Copiar ejecutable
    if [ -f "$linux_executable" ]; then
        cp "$linux_executable" "${DEB_PACKAGE_DIR}/usr/bin/${PACKAGE_NAME}"
        chmod +x "${DEB_PACKAGE_DIR}/usr/bin/${PACKAGE_NAME}"
        print_success "Ejecutable copiado"
    else
        print_error "Ejecutable no encontrado: $linux_executable"
        exit 1
    fi
    
    # Copiar icono
    if [ -f "$icon_path" ]; then
        # Copiar a hicolor
        cp "$icon_path" "${DEB_PACKAGE_DIR}/usr/share/icons/hicolor/256x256/apps/${PACKAGE_NAME}.png"
        # Copiar a pixmaps
        cp "$icon_path" "${DEB_PACKAGE_DIR}/usr/share/pixmaps/${PACKAGE_NAME}.png"
        print_success "Icono copiado"
    else
        print_warning "Icono no encontrado: $icon_path"
    fi
    
    # Copiar directorio completo de la aplicación si existe
    local app_dir=$(dirname "$linux_executable")
    if [ -d "$app_dir" ] && [ "$app_dir" != "." ]; then
        print_info "Copiando directorio de la aplicación..."
        cp -r "$app_dir"/* "${DEB_PACKAGE_DIR}/usr/share/${PACKAGE_NAME}/" 2>/dev/null || true
    fi
}

# Función para crear archivo control
create_control_file() {
    local version="$1"
    local architecture="$2"
    
    print_info "Creando archivo control..."
    
    local control_file="${DEB_PACKAGE_DIR}/DEBIAN/control"
    cat > "$control_file" << EOF
Package: ${PACKAGE_NAME}
Version: ${version}
Section: utils
Priority: optional
Architecture: ${architecture}
Depends: libc6 (>= 2.17), libgcc1 (>= 1:4.2), libstdc++6 (>= 4.2)
Maintainer: ${MAINTAINER}
Description: ${APP_DESCRIPTION}
 ${APP_DISPLAY_NAME} es una aplicación de productividad completa
 para gestionar tareas, hábitos y metas con sistema de puntos
 y recompensas. Incluye gamificación, funciona offline y ofrece
 sincronización opcional con Firebase.
EOF
    
    print_success "Archivo control creado"
}

# Función para crear archivo .desktop
create_desktop_file() {
    print_info "Creando archivo .desktop..."
    
    local desktop_file="${DEB_PACKAGE_DIR}/usr/share/applications/${PACKAGE_NAME}.desktop"
    cat > "$desktop_file" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=${APP_DISPLAY_NAME}
Comment=${APP_DESCRIPTION}
Exec=${PACKAGE_NAME}
Icon=${PACKAGE_NAME}
Terminal=false
Categories=Utility;Productivity;Office;
Keywords=productivity;tasks;habits;goals;gamification;
StartupNotify=true
EOF
    
    chmod 644 "$desktop_file"
    print_success "Archivo .desktop creado"
}

# Función para construir el paquete .deb
build_deb_package() {
    local version="$1"
    local architecture="$2"
    
    print_info "Construyendo paquete .deb..."
    
    local deb_filename="${PACKAGE_NAME}_${version}_${architecture}.deb"
    local deb_output="${BUILD_DIR}/${deb_filename}"
    
    # Construir el paquete
    if dpkg-deb --build "$DEB_PACKAGE_DIR" "$deb_output" 2>&1; then
        print_success "Paquete .deb construido exitosamente: $deb_output"
        
        # Mostrar información del paquete
        local file_size=$(du -h "$deb_output" | cut -f1)
        print_info "Tamaño del paquete: ${file_size}"
        
        # Verificar el paquete
        print_info "Verificando paquete .deb..."
        if dpkg-deb -I "$deb_output" &> /dev/null; then
            print_success "Paquete .deb válido"
            dpkg-deb -I "$deb_output" | head -15
        else
            print_warning "No se pudo verificar el paquete"
        fi
        
        echo ""
        print_success "=========================================="
        print_success "  Build completado exitosamente"
        print_success "=========================================="
        print_info "Paquete generado: $deb_output"
        print_info "Para instalar: sudo dpkg -i $deb_output"
        print_info "Para instalar dependencias faltantes: sudo apt-get install -f"
    else
        print_error "Error al construir el paquete .deb"
        exit 1
    fi
}

# Función para mostrar ayuda
show_help() {
    cat << EOF
Uso: ./build_linux.sh [OPCIONES]

Genera un paquete .deb para distribuciones basadas en Debian/Ubuntu.

OPCIONES:
    --clean     Limpia builds anteriores antes de construir
    --help      Muestra esta ayuda

EJEMPLOS:
    ./build_linux.sh              # Genera el paquete .deb
    ./build_linux.sh --clean      # Limpia y genera el paquete .deb

REQUISITOS:
    - Flet instalado (en venv o sistema)
    - dpkg-deb instalado
    - Linux (Debian/Ubuntu/Mint)

El paquete .deb se generará en: build/${PACKAGE_NAME}_${APP_VERSION}_<arch>.deb
EOF
}

# ============================================================================
# SCRIPT PRINCIPAL
# ============================================================================

main() {
    print_info "=========================================="
    print_info "  Build Linux - Justice Driven Task Power"
    print_info "=========================================="
    echo ""
    
    # Procesar argumentos
    local clean_build_flag=false
    
    for arg in "$@"; do
        case "$arg" in
            --clean)
                clean_build_flag=true
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
    
    set -e
    
    # Verificar que estamos en el directorio correcto
    if [ ! -f "main.py" ] && [ ! -f "app/main.py" ]; then
        print_error "No se encontró main.py. Asegúrate de ejecutar el script desde la raíz del proyecto."
        exit 1
    fi
    
    # Verificar Flet
    check_flet
    
    # Limpiar si se solicita
    if [ "$clean_build_flag" = true ]; then
        clean_build
    else
        # Limpiar caché de Flet siempre para evitar problemas con dependencias
        print_info "Limpiando caché de Flet..."
        rm -rf ".flet/build" 2>/dev/null || true
    fi
    
    # Validar icono
    local icon_path=$(find_icon)
    print_info "Icono: $icon_path"
    
    # Leer versión
    local version=$(read_version)
    print_info "Versión: $version"
    
    # Obtener arquitectura
    local architecture=$(get_architecture)
    print_info "Arquitectura: $architecture"
    
    # Construir aplicación Linux
    # Ejecutar build_linux_app y capturar solo la ruta del ejecutable (última línea)
    print_info "Iniciando build de aplicación Linux..."
    local build_output=$(build_linux_app 2>&1)
    local linux_executable=$(echo "$build_output" | grep -E "^/|^\./" | tail -n 1)
    
    # Si no se encontró en el output, buscar manualmente
    if [ -z "$linux_executable" ] || [ ! -f "$linux_executable" ]; then
        print_warning "No se pudo capturar la ruta del ejecutable desde el output, buscando manualmente..."
        linux_executable=$(find "$BUILD_DIR" -type f -executable \( -name "${APP_NAME}" -o -name "${APP_NAME}.bin" -o -name "app" -o -name "*.AppImage" \) 2>/dev/null | head -n 1)
    fi
    
    if [ -z "$linux_executable" ] || [ ! -f "$linux_executable" ]; then
        print_error "No se pudo encontrar el ejecutable de Linux después del build"
        print_info "Buscando todos los ejecutables en $BUILD_DIR:"
        find "$BUILD_DIR" -type f -executable 2>/dev/null | head -10
        exit 1
    fi
    
    print_success "Ejecutable encontrado: $linux_executable"
    
    # Crear estructura del paquete .deb
    create_deb_structure
    
    # Copiar archivos
    copy_app_files "$linux_executable" "$icon_path"
    
    # Crear archivos de control
    create_control_file "$version" "$architecture"
    create_desktop_file
    
    # Construir paquete .deb
    build_deb_package "$version" "$architecture"
}

# Ejecutar script principal
main "$@"

