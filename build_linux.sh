#!/bin/bash

# Script de build para Linux
# Genera paquetes para Debian (.deb), Arch Linux (.pkg.tar.zst) y Fedora (.rpm)
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
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Cambiar al directorio del script
cd "$SCRIPT_DIR"

# Función para mostrar ayuda
show_help() {
    echo -e "${CYAN}Script de Build para Linux${NC}"
    echo ""
    echo "Uso: $0 [opciones]"
    echo ""
    echo "Opciones:"
    echo "  --deb        Genera solo el paquete .deb (Debian/Ubuntu)"
    echo "  --arch        Genera solo el paquete .pkg.tar.zst (Arch Linux)"
    echo "  --rpm         Genera solo el paquete .rpm (Fedora/RHEL)"
    echo "  --all         Genera todos los paquetes (por defecto)"
    echo "  --help, -h    Muestra esta ayuda"
    echo ""
    echo "Ejemplos:"
    echo "  $0              # Genera todos los paquetes"
    echo "  $0 --deb        # Genera solo .deb"
    echo "  $0 --arch       # Genera solo .pkg.tar.zst"
    echo "  $0 --rpm        # Genera solo .rpm"
    echo "  $0 --all        # Genera todos los paquetes"
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
        log_warning "No se encontró $PYPROJECT_TOML, usando versión por defecto 1.0.0"
        echo "1.0.0"
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
        match = re.search(r'\[project\].*?^version\s*=\s*["\']?([0-9]+\.[0-9]+\.[0-9]+)["\']?', content, re.MULTILINE | re.DOTALL)
        if match:
            print(match.group(1))
except Exception:
    pass
PYTHON_SCRIPT
)
    fi
    
    # Si Python falla, usar método alternativo
    if [ -z "$version" ] || [[ ! $version =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
        local version_line=$(grep -A 20 "\[project\]" "$PYPROJECT_TOML" | grep -E "^version\s*=" | head -1)
        if [ -n "$version_line" ]; then
            version=$(echo "$version_line" | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1)
        fi
    fi
    
    if [ -z "$version" ] || [[ ! $version =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
        log_warning "No se pudo leer versión de $PYPROJECT_TOML, usando versión por defecto 1.0.0"
        echo "1.0.0"
    else
        echo "$version"
    fi
}

# Función para leer nombre del proyecto
read_project_name() {
    if [ ! -f "$PYPROJECT_TOML" ]; then
        echo "justice-driven-task-power"
        return
    fi
    
    local name=""
    if command -v python3 &> /dev/null; then
        name=$(python3 <<'PYTHON_SCRIPT'
import re
try:
    with open('pyproject.toml', 'r') as f:
        content = f.read()
        match = re.search(r'\[project\].*?^name\s*=\s*["\']?([^"\']+)["\']?', content, re.MULTILINE | re.DOTALL)
        if match:
            print(match.group(1))
except Exception:
    pass
PYTHON_SCRIPT
)
    fi
    
    if [ -z "$name" ]; then
        local name_line=$(grep -A 20 "\[project\]" "$PYPROJECT_TOML" | grep -E "^name\s*=" | head -1)
        if [ -n "$name_line" ]; then
            name=$(echo "$name_line" | sed -E 's/.*name\s*=\s*["\047]?([^"\047]+)["\047]?.*/\1/' | tr -d ' ')
        fi
    fi
    
    if [ -z "$name" ]; then
        echo "justice-driven-task-power"
    else
        echo "$name"
    fi
}

# Función para leer descripción del proyecto
read_project_description() {
    if [ ! -f "$PYPROJECT_TOML" ]; then
        echo "Aplicación de productividad personal"
        return
    fi
    
    local desc=""
    if command -v python3 &> /dev/null; then
        desc=$(python3 <<'PYTHON_SCRIPT'
import re
try:
    with open('pyproject.toml', 'r') as f:
        content = f.read()
        match = re.search(r'\[project\].*?^description\s*=\s*["\']([^"\']+)["\']', content, re.MULTILINE | re.DOTALL)
        if match:
            print(match.group(1))
except Exception:
    pass
PYTHON_SCRIPT
)
    fi
    
    if [ -z "$desc" ]; then
        local desc_line=$(grep -A 20 "\[project\]" "$PYPROJECT_TOML" | grep -E "^description\s*=" | head -1)
        if [ -n "$desc_line" ]; then
            desc=$(echo "$desc_line" | sed -E 's/.*description\s*=\s*["\047]([^"\047]+)["\047].*/\1/')
        fi
    fi
    
    if [ -z "$desc" ]; then
        echo "Aplicación de productividad personal"
    else
        echo "$desc"
    fi
}

# Función para verificar que Flet está instalado
check_flet() {
    # Activar venv si existe
    if [ -d "venv" ]; then
        source venv/bin/activate
    fi
    
    if ! command -v flet &> /dev/null; then
        log_error "Flet no está instalado"
        log_info "Instala Flet con: pip install flet"
        log_info "O activa el entorno virtual: source venv/bin/activate"
        exit 1
    fi
}

# Función para detectar arquitectura
detect_architecture() {
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
            echo "$arch"
            ;;
    esac
}

# Función para verificar requisitos de Linux
check_linux_requirements() {
    log_info "Verificando requisitos para build de Linux..."
    
    local missing_tools=()
    
    if ! command -v clang++ &> /dev/null; then
        missing_tools+=("clang++ (sudo apt install clang)")
    fi
    
    if ! command -v cmake &> /dev/null; then
        missing_tools+=("cmake (sudo apt install cmake)")
    fi
    
    if ! command -v ninja &> /dev/null; then
        missing_tools+=("ninja (sudo apt install ninja-build)")
    fi
    
    # Verificar GTK 3.0 (verificar si existe pkg-config y puede encontrar gtk+-3.0)
    if ! pkg-config --exists gtk+-3.0 2>/dev/null; then
        missing_tools+=("libgtk-3-dev (sudo apt install libgtk-3-dev)")
    fi
    
    if [ ${#missing_tools[@]} -gt 0 ]; then
        log_error "Faltan herramientas necesarias para el build de Linux:"
        for tool in "${missing_tools[@]}"; do
            log_error "  - $tool"
        done
        log_info ""
        log_info "Instala todas las herramientas con:"
        log_info "  sudo apt install clang cmake ninja-build libgtk-3-dev"
        return 1
    fi
    
    log_success "Todos los requisitos están instalados"
    return 0
}

# Función para construir el bundle de Linux primero
build_linux_bundle() {
    log_info "Construyendo bundle de Linux con Flet..."
    
    # Verificar requisitos primero
    if ! check_linux_requirements; then
        log_error "No se pueden construir paquetes sin las herramientas necesarias"
        return 1
    fi
    
    # Activar venv si existe (ya debería estar activado por check_flet)
    if [ -d "venv" ] && [ -z "$VIRTUAL_ENV" ]; then
        source venv/bin/activate
    fi
    
    # Limpiar build anterior si existe
    if [ -d "build/linux" ]; then
        log_info "Limpiando build anterior..."
        rm -rf build/linux
    fi
    
    # Capturar salida del build
    local build_log=$(mktemp)
    local build_success=false
    
    log_info "Ejecutando 'flet build linux'..."
    if flet build linux > "$build_log" 2>&1; then
        # Verificar si realmente se generó algo
        if [ -d "build/linux" ]; then
            # Buscar ejecutable generado
            local executable=$(find build/linux -type f -executable ! -name "*.so" ! -name "*.so.*" 2>/dev/null | head -1)
            if [ -n "$executable" ] && [ -f "$executable" ]; then
                build_success=true
            fi
        fi
    fi
    
    # Mostrar log si falló o si no se encontró ejecutable
    if [ "$build_success" = false ]; then
        log_error "Error al generar bundle de Linux"
        log_info "Log del build:"
        cat "$build_log"
        log_info ""
        log_error "El build de Flet falló. Verifica:"
        log_error "  1. Que todas las herramientas estén instaladas (clang++, cmake, ninja, libgtk-3-dev)"
        log_error "  2. Que el proyecto compile correctamente"
        log_error "  3. Ejecuta 'flet doctor' para verificar el entorno"
        rm -f "$build_log"
        return 1
    fi
    
    log_success "Bundle de Linux generado exitosamente"
    
    # Verificar qué se generó
    if [ -d "build/linux" ]; then
        log_info "Contenido generado en build/linux:"
        ls -lah build/linux/ | head -10
    fi
    
    rm -f "$build_log"
    return 0
}

# Función para construir paquete .deb (Debian/Ubuntu)
build_deb() {
    log_info "Generando paquete .deb para Debian/Ubuntu..."
    
    # Verificar que dpkg-deb esté disponible
    if ! command -v dpkg-deb &> /dev/null; then
        log_error "dpkg-deb no está instalado. Instálalo con: sudo apt install dpkg-dev"
        return 1
    fi
    
    # Construir bundle primero (solo si no se construyó ya)
    if [ "$BUNDLE_BUILT" != "true" ]; then
        if ! build_linux_bundle; then
            return 1
        fi
        BUNDLE_BUILT=true
    fi
    
    local arch=$(detect_architecture)
    local package_name=$(echo "$PROJECT_NAME" | tr '_' '-')
    local deb_dir="build/linux/deb_package"
    
    # Limpiar directorio anterior
    rm -rf "$deb_dir"
    
    # Crear estructura de directorios
    mkdir -p "$deb_dir/DEBIAN"
    mkdir -p "$deb_dir/usr/bin"
    mkdir -p "$deb_dir/usr/share/applications"
    mkdir -p "$deb_dir/usr/share/pixmaps"
    
    # Buscar el ejecutable generado por Flet
    local executable=""
    
    # Buscar en diferentes ubicaciones posibles
    if [ -d "build/linux" ]; then
        # Buscar ejecutables en build/linux
        executable=$(find build/linux -type f -executable ! -name "*.so" ! -name "*.so.*" 2>/dev/null | head -1)
        
        # Si no se encuentra, buscar archivos sin extensión que sean ejecutables
        if [ -z "$executable" ]; then
            executable=$(find build/linux -type f ! -name "*.so" ! -name "*.so.*" ! -name "*.json" ! -name "*.txt" 2>/dev/null | head -1)
        fi
        
        # Buscar específicamente el nombre del proyecto
        local project_executable="build/linux/$(echo "$PROJECT_NAME" | tr '_' '-')"
        if [ -f "$project_executable" ] && [ -x "$project_executable" ]; then
            executable="$project_executable"
        fi
    fi
    
    if [ -z "$executable" ] || [ ! -f "$executable" ]; then
        log_error "No se encontró el ejecutable generado por Flet en build/linux"
        log_info "Contenido de build/linux:"
        ls -la build/linux/ 2>/dev/null || log_warning "Directorio build/linux no existe"
        log_info "Asegúrate de que 'flet build linux' se haya ejecutado correctamente"
        return 1
    fi
    
    log_info "Ejecutable encontrado: $executable"
    
    # Copiar ejecutable
    cp "$executable" "$deb_dir/usr/bin/$package_name"
    chmod +x "$deb_dir/usr/bin/$package_name"
    
    # Copiar icono si existe
    if [ -f "assets/app_icon.png" ]; then
        cp "assets/app_icon.png" "$deb_dir/usr/share/pixmaps/$package_name.png"
    fi
    
    # Crear archivo .desktop
    cat > "$deb_dir/usr/share/applications/$package_name.desktop" <<EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Justice Driven Task Power
Comment=$PROJECT_DESC
Exec=$package_name
Icon=$package_name
Terminal=false
Categories=Utility;Productivity;
EOF
    
    # Crear archivo control
    cat > "$deb_dir/DEBIAN/control" <<EOF
Package: $package_name
Version: $PROJECT_VERSION
Section: utils
Priority: optional
Architecture: $arch
Depends: python3 (>= 3.8), libc6
Maintainer: Developer <dev@example.com>
Description: $PROJECT_DESC
 Aplicación de productividad personal para gestionar tareas, hábitos y metas.
EOF
    
    # Construir paquete .deb
    local deb_file="build/linux/${package_name}_${PROJECT_VERSION}_${arch}.deb"
    log_info "Construyendo paquete .deb..."
    if dpkg-deb --build "$deb_dir" "$deb_file" 2>&1; then
        if [ -f "$deb_file" ]; then
            log_success "Paquete .deb generado: $deb_file"
            log_info "Tamaño: $(du -h "$deb_file" | cut -f1)"
            return 0
        else
            log_error "El comando dpkg-deb no generó el archivo esperado"
            return 1
        fi
    else
        log_error "Error al construir paquete .deb"
        log_info "Verifica que todos los archivos necesarios estén en $deb_dir"
        return 1
    fi
}

# Función para construir paquete .pkg.tar.zst (Arch Linux)
build_arch() {
    log_info "Generando paquete .pkg.tar.zst para Arch Linux..."
    
    # Construir bundle primero (solo si no se construyó ya)
    if [ "$BUNDLE_BUILT" != "true" ]; then
        if ! build_linux_bundle; then
            return 1
        fi
        BUNDLE_BUILT=true
    fi
    
    local package_name=$(echo "$PROJECT_NAME" | tr '_' '-')
    local arch_dir="build/linux/arch_package"
    
    # Limpiar directorio anterior
    rm -rf "$arch_dir"
    mkdir -p "$arch_dir/src"
    mkdir -p "$arch_dir/pkg"
    
    # Buscar el ejecutable
    local executable=""
    
    if [ -d "build/linux" ]; then
        executable=$(find build/linux -type f -executable ! -name "*.so" ! -name "*.so.*" 2>/dev/null | head -1)
        
        if [ -z "$executable" ]; then
            executable=$(find build/linux -type f ! -name "*.so" ! -name "*.so.*" ! -name "*.json" ! -name "*.txt" 2>/dev/null | head -1)
        fi
        
        local project_executable="build/linux/$(echo "$PROJECT_NAME" | tr '_' '-')"
        if [ -f "$project_executable" ] && [ -x "$project_executable" ]; then
            executable="$project_executable"
        fi
    fi
    
    if [ -z "$executable" ] || [ ! -f "$executable" ]; then
        log_error "No se encontró el ejecutable generado por Flet en build/linux"
        log_info "Asegúrate de que 'flet build linux' se haya ejecutado correctamente"
        return 1
    fi
    
    log_info "Ejecutable encontrado: $executable"
    
    # Crear PKGBUILD
    cat > "$arch_dir/PKGBUILD" <<EOF
# Maintainer: Developer <dev@example.com>
pkgname=$package_name
pkgver=$PROJECT_VERSION
pkgrel=1
pkgdesc="$PROJECT_DESC"
arch=('x86_64')
url="https://github.com/example/$package_name"
license=('MIT')
depends=('python3')
source=("$executable")
package() {
    install -Dm755 "\$srcdir/$(basename $executable)" "\$pkgdir/usr/bin/$package_name"
}
EOF
    
    # Copiar ejecutable al directorio src
    cp "$executable" "$arch_dir/src/"
    
    # Construir paquete (requiere makepkg)
    if command -v makepkg &> /dev/null; then
        cd "$arch_dir"
        if makepkg -f; then
            cd - > /dev/null
            local pkg_file=$(find "$arch_dir" -name "*.pkg.tar.zst" | head -1)
            if [ -n "$pkg_file" ]; then
                mv "$pkg_file" "build/linux/"
                log_success "Paquete .pkg.tar.zst generado: build/linux/$(basename $pkg_file)"
                cd - > /dev/null
                return 0
            fi
        fi
        cd - > /dev/null
    else
        log_warning "makepkg no está disponible. El paquete PKGBUILD se ha creado en $arch_dir/PKGBUILD"
        log_info "Para construir el paquete, ejecuta: cd $arch_dir && makepkg"
        return 1
    fi
    
    log_error "Error al construir paquete .pkg.tar.zst"
    return 1
}

# Función para construir paquete .rpm (Fedora/RHEL)
build_rpm() {
    log_info "Generando paquete .rpm para Fedora/RHEL..."
    
    # Verificar que rpmbuild esté disponible
    if ! command -v rpmbuild &> /dev/null; then
        log_error "rpmbuild no está instalado. Instálalo con: sudo dnf install rpm-build"
        return 1
    fi
    
    # Construir bundle primero (solo si no se construyó ya)
    if [ "$BUNDLE_BUILT" != "true" ]; then
        if ! build_linux_bundle; then
            return 1
        fi
        BUNDLE_BUILT=true
    fi
    
    local package_name=$(echo "$PROJECT_NAME" | tr '_' '-')
    local arch=$(detect_architecture)
    local rpm_dir="build/linux/rpm_package"
    
    # Limpiar directorio anterior
    rm -rf "$rpm_dir"
    mkdir -p "$rpm_dir/SPECS"
    mkdir -p "$rpm_dir/SOURCES"
    mkdir -p "$rpm_dir/BUILD"
    mkdir -p "$rpm_dir/RPMS"
    
    # Buscar el ejecutable
    local executable=""
    
    if [ -d "build/linux" ]; then
        executable=$(find build/linux -type f -executable ! -name "*.so" ! -name "*.so.*" 2>/dev/null | head -1)
        
        if [ -z "$executable" ]; then
            executable=$(find build/linux -type f ! -name "*.so" ! -name "*.so.*" ! -name "*.json" ! -name "*.txt" 2>/dev/null | head -1)
        fi
        
        local project_executable="build/linux/$(echo "$PROJECT_NAME" | tr '_' '-')"
        if [ -f "$project_executable" ] && [ -x "$project_executable" ]; then
            executable="$project_executable"
        fi
    fi
    
    if [ -z "$executable" ] || [ ! -f "$executable" ]; then
        log_error "No se encontró el ejecutable generado por Flet en build/linux"
        log_info "Asegúrate de que 'flet build linux' se haya ejecutado correctamente"
        return 1
    fi
    
    log_info "Ejecutable encontrado: $executable"
    
    # Copiar ejecutable a SOURCES
    cp "$executable" "$rpm_dir/SOURCES/$package_name"
    chmod +x "$rpm_dir/SOURCES/$package_name"
    
    # Crear archivo .spec
    cat > "$rpm_dir/SPECS/$package_name.spec" <<EOF
Name:           $package_name
Version:        $PROJECT_VERSION
Release:        1%{?dist}
Summary:        $PROJECT_DESC
License:        MIT
Source0:        $package_name
BuildArch:      noarch
Requires:       python3 >= 3.8

%description
$PROJECT_DESC

%prep
# No hay preparación necesaria

%build
# No hay compilación necesaria

%install
install -Dm755 %{SOURCE0} %{buildroot}/usr/bin/$package_name

%files
/usr/bin/$package_name

%changelog
* $(date '+%a %b %d %Y') Developer <dev@example.com> - $PROJECT_VERSION-1
- Initial release
EOF
    
    # Construir paquete .rpm
    if rpmbuild --define "_topdir $(pwd)/$rpm_dir" -ba "$rpm_dir/SPECS/$package_name.spec"; then
        local rpm_file=$(find "$rpm_dir/RPMS" -name "*.rpm" | head -1)
        if [ -n "$rpm_file" ]; then
            mv "$rpm_file" "build/linux/"
            log_success "Paquete .rpm generado: build/linux/$(basename $rpm_file)"
            return 0
        fi
    fi
    
    log_error "Error al construir paquete .rpm"
    return 1
}

# Procesar argumentos
BUILD_DEB=false
BUILD_ARCH=false
BUILD_RPM=false

if [ $# -eq 0 ]; then
    # Por defecto, construir todos
    BUILD_DEB=true
    BUILD_ARCH=true
    BUILD_RPM=true
else
    case "$1" in
        --deb)
            BUILD_DEB=true
            ;;
        --arch)
            BUILD_ARCH=true
            ;;
        --rpm)
            BUILD_RPM=true
            ;;
        --all)
            BUILD_DEB=true
            BUILD_ARCH=true
            BUILD_RPM=true
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

# Leer información del proyecto
log_info "Leyendo información del proyecto..."
PROJECT_VERSION=$(read_version_from_pyproject)
PROJECT_NAME=$(read_project_name)
PROJECT_DESC=$(read_project_description)

log_success "Proyecto: $PROJECT_NAME"
log_success "Versión: $PROJECT_VERSION"
log_success "Descripción: $PROJECT_DESC"

echo ""
log_info "═══════════════════════════════════════════════════════════"
log_info "Iniciando build de Linux"
log_info "Versión: $PROJECT_VERSION"
log_info "═══════════════════════════════════════════════════════════"
echo ""

# Construir bundle una sola vez si se necesita
BUNDLE_BUILT=false
if [ "$BUILD_DEB" = true ] || [ "$BUILD_ARCH" = true ] || [ "$BUILD_RPM" = true ]; then
    # Construir bundle primero (solo una vez)
    if ! build_linux_bundle; then
        log_error "No se pudo construir el bundle de Linux. Abortando."
        exit 1
    fi
    BUNDLE_BUILT=true
fi

# Construir según las opciones
BUILD_SUCCESS=true
DEB_SUCCESS=false
ARCH_SUCCESS=false
RPM_SUCCESS=false

if [ "$BUILD_DEB" = true ]; then
    echo ""
    if build_deb; then
        DEB_SUCCESS=true
    else
        BUILD_SUCCESS=false
    fi
    echo ""
fi

if [ "$BUILD_ARCH" = true ]; then
    echo ""
    if build_arch; then
        ARCH_SUCCESS=true
    else
        BUILD_SUCCESS=false
    fi
    echo ""
fi

if [ "$BUILD_RPM" = true ]; then
    echo ""
    if build_rpm; then
        RPM_SUCCESS=true
    else
        BUILD_SUCCESS=false
    fi
    echo ""
fi

# Resumen final
echo ""
log_info "═══════════════════════════════════════════════════════════"
if [ "$BUILD_SUCCESS" = true ]; then
    log_success "Build completado exitosamente"
else
    log_warning "Build completado con algunos errores"
fi
log_info "Versión: $PROJECT_VERSION"
echo ""

# Mostrar estado de cada paquete
if [ "$BUILD_DEB" = true ]; then
    if [ "$DEB_SUCCESS" = true ]; then
        log_success "✓ Paquete .deb generado para Debian/Ubuntu"
    else
        log_error "✗ Paquete .deb NO se generó"
    fi
fi

if [ "$BUILD_ARCH" = true ]; then
    if [ "$ARCH_SUCCESS" = true ]; then
        log_success "✓ Paquete .pkg.tar.zst generado para Arch Linux"
    else
        log_error "✗ Paquete .pkg.tar.zst NO se generó"
    fi
fi

if [ "$BUILD_RPM" = true ]; then
    if [ "$RPM_SUCCESS" = true ]; then
        log_success "✓ Paquete .rpm generado para Fedora/RHEL"
    else
        log_error "✗ Paquete .rpm NO se generó"
    fi
fi

log_info "═══════════════════════════════════════════════════════════"
echo ""

# Listar archivos generados
if [ -d "build/linux" ]; then
    log_info "Archivos generados en build/linux:"
    find build/linux -maxdepth 1 -type f \( -name "*.deb" -o -name "*.pkg.tar.zst" -o -name "*.rpm" \) 2>/dev/null | while read file; do
        log_success "  - $(basename "$file") ($(du -h "$file" | cut -f1))"
    done
    echo ""
fi

if [ "$BUILD_SUCCESS" = false ]; then
    log_error "Algunos paquetes no se pudieron generar. Revisa los errores arriba."
    exit 1
fi

