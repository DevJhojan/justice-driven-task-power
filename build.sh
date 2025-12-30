#!/bin/bash

# Script de build para generar paquete .deb para Linux Mint
# Este script construye la aplicación Flet y crea un paquete .deb instalable

set -e  # Salir si hay algún error

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Información de la aplicación (desde pyproject.toml)
APP_NAME="justice-driven-task-power"
APP_VERSION="1.0.0"
APP_DESCRIPTION="conviértete en el héroe de tu propio progreso con tareas y hábitos organizados"
APP_MAINTAINER="Developer <dev@example.com>"

# Directorios
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUILD_DIR="${SCRIPT_DIR}/build"
LINUX_BUILD_DIR="${BUILD_DIR}/linux"
DEB_PACKAGE_DIR="${LINUX_BUILD_DIR}/deb_package"
DEBIAN_DIR="${DEB_PACKAGE_DIR}/DEBIAN"

echo -e "${GREEN}🚀 Iniciando build para Linux Mint...${NC}"

# Limpiar builds anteriores
echo -e "${YELLOW}🧹 Limpiando builds anteriores...${NC}"
rm -rf "${LINUX_BUILD_DIR}"
mkdir -p "${LINUX_BUILD_DIR}"

# Verificar que Flet está instalado
if ! command -v flet &> /dev/null; then
    echo -e "${RED}❌ Error: Flet no está instalado. Instálalo con: pip install flet${NC}"
    exit 1
fi

# Construir la aplicación para Linux
echo -e "${YELLOW}📦 Construyendo aplicación con Flet...${NC}"
cd "${SCRIPT_DIR}"
flet build linux

# Verificar que el build se completó correctamente
if [ ! -f "${LINUX_BUILD_DIR}/${APP_NAME}" ]; then
    echo -e "${RED}❌ Error: El ejecutable no se generó correctamente${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Build de Flet completado${NC}"

# Crear estructura de directorios para el paquete .deb
echo -e "${YELLOW}📁 Creando estructura del paquete .deb...${NC}"
mkdir -p "${DEBIAN_DIR}"
mkdir -p "${DEB_PACKAGE_DIR}/usr/bin"
mkdir -p "${DEB_PACKAGE_DIR}/usr/share/applications"
mkdir -p "${DEB_PACKAGE_DIR}/usr/share/pixmaps"
mkdir -p "${DEB_PACKAGE_DIR}/opt/${APP_NAME}"

# Crear archivo DEBIAN/control
echo -e "${YELLOW}📝 Creando archivo DEBIAN/control...${NC}"
cat > "${DEBIAN_DIR}/control" << EOF
Package: ${APP_NAME}
Version: ${APP_VERSION}
Section: utils
Priority: optional
Architecture: amd64
Depends: python3 (>= 3.8), libc6, libgtk-3-0
Maintainer: ${APP_MAINTAINER}
Description: ${APP_DESCRIPTION}
 Aplicación de productividad personal para gestionar tareas, hábitos y metas.
EOF

# Copiar todo el contenido del build a /opt
echo -e "${YELLOW}📚 Copiando aplicación y dependencias...${NC}"
cp "${LINUX_BUILD_DIR}/${APP_NAME}" "${DEB_PACKAGE_DIR}/opt/${APP_NAME}/"

if [ -d "${LINUX_BUILD_DIR}/lib" ]; then
    cp -r "${LINUX_BUILD_DIR}/lib" "${DEB_PACKAGE_DIR}/opt/${APP_NAME}/"
fi

if [ -d "${LINUX_BUILD_DIR}/data" ]; then
    cp -r "${LINUX_BUILD_DIR}/data" "${DEB_PACKAGE_DIR}/opt/${APP_NAME}/"
fi

if [ -d "${LINUX_BUILD_DIR}/python3.12" ]; then
    cp -r "${LINUX_BUILD_DIR}/python3.12" "${DEB_PACKAGE_DIR}/opt/${APP_NAME}/"
fi

if [ -d "${LINUX_BUILD_DIR}/site-packages" ]; then
    cp -r "${LINUX_BUILD_DIR}/site-packages" "${DEB_PACKAGE_DIR}/opt/${APP_NAME}/"
fi

# Crear script launcher en /usr/bin que ejecuta desde /opt
echo -e "${YELLOW}📋 Creando script launcher...${NC}"
cat > "${DEB_PACKAGE_DIR}/usr/bin/${APP_NAME}" << LAUNCHER_EOF
#!/bin/bash
# Launcher script para la aplicación
APP_DIR="/opt/${APP_NAME}"
cd "\${APP_DIR}"
exec "\${APP_DIR}/${APP_NAME}" "\$@"
LAUNCHER_EOF
chmod +x "${DEB_PACKAGE_DIR}/usr/bin/${APP_NAME}"

# Copiar icono
echo -e "${YELLOW}🖼️  Copiando icono...${NC}"
if [ -f "${SCRIPT_DIR}/assets/app_icon.png" ]; then
    cp "${SCRIPT_DIR}/assets/app_icon.png" "${DEB_PACKAGE_DIR}/usr/share/pixmaps/${APP_NAME}.png"
elif [ -f "${DEB_PACKAGE_DIR}/usr/share/pixmaps/${APP_NAME}.png" ]; then
    # Si ya existe en el build anterior, mantenerlo
    echo "Icono ya existe"
else
    echo -e "${YELLOW}⚠️  Advertencia: No se encontró el icono en assets/app_icon.png${NC}"
fi

# Crear archivo .desktop
echo -e "${YELLOW}🖥️  Creando archivo .desktop...${NC}"
cat > "${DEB_PACKAGE_DIR}/usr/share/applications/${APP_NAME}.desktop" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Justice Driven Task Power
Comment=${APP_DESCRIPTION}
Exec=${APP_NAME}
Icon=${APP_NAME}
Terminal=false
Categories=Utility;Productivity;
EOF

# Actualizar el ejecutable para que use las rutas correctas
echo -e "${YELLOW}🔧 Configurando rutas del ejecutable...${NC}"
# El ejecutable de Flet ya debería estar configurado, pero verificamos

# Calcular el tamaño del paquete (requerido por dpkg)
INSTALLED_SIZE=$(du -sk "${DEB_PACKAGE_DIR}/usr" "${DEB_PACKAGE_DIR}/opt" 2>/dev/null | awk '{sum+=$1} END {print sum}')
sed -i "s/^Installed-Size:.*/Installed-Size: ${INSTALLED_SIZE}/" "${DEBIAN_DIR}/control" 2>/dev/null || \
    echo "Installed-Size: ${INSTALLED_SIZE}" >> "${DEBIAN_DIR}/control"

# Construir el paquete .deb
echo -e "${YELLOW}📦 Construyendo paquete .deb...${NC}"
DEB_FILE="${LINUX_BUILD_DIR}/${APP_NAME}_${APP_VERSION}_amd64.deb"
dpkg-deb --build "${DEB_PACKAGE_DIR}" "${DEB_FILE}"

# Verificar que el paquete se creó correctamente
if [ -f "${DEB_FILE}" ]; then
    DEB_SIZE=$(du -h "${DEB_FILE}" | cut -f1)
    echo -e "${GREEN}✅ Paquete .deb creado exitosamente!${NC}"
    echo -e "${GREEN}📦 Archivo: ${DEB_FILE}${NC}"
    echo -e "${GREEN}📊 Tamaño: ${DEB_SIZE}${NC}"
    echo ""
    echo -e "${GREEN}Para instalar el paquete, ejecuta:${NC}"
    echo -e "${YELLOW}sudo dpkg -i ${DEB_FILE}${NC}"
    echo ""
    echo -e "${GREEN}Si hay dependencias faltantes, ejecuta:${NC}"
    echo -e "${YELLOW}sudo apt-get install -f${NC}"
else
    echo -e "${RED}❌ Error: No se pudo crear el paquete .deb${NC}"
    exit 1
fi

echo -e "${GREEN}🎉 Build completado exitosamente!${NC}"

