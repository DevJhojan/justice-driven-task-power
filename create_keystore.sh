#!/bin/bash

################################################################################
# create_keystore.sh - Script para crear el keystore de firma para Android
#
# Este script crea un keystore necesario para firmar la aplicación en modo
# release antes de subirla a Google Play Console.
#
# Uso:
#   ./create_keystore.sh
#
# IMPORTANTE: Guarda las credenciales en un lugar seguro. Las necesitarás
# para futuras actualizaciones de la aplicación en Google Play.
#
################################################################################

set -e

# Colores para mensajes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_section() {
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
}

# Verificar que keytool está disponible
if ! command -v keytool &> /dev/null; then
    print_error "keytool no está instalado. Necesitas instalar Java JDK."
    print_info "Instala Java JDK con: sudo apt-get install openjdk-17-jdk"
    exit 1
fi

print_section "Creación de Keystore para Firma de Release"

KEYSTORE_PATH="build/flutter/android/app/upload-keystore.jks"
KEY_PROPERTIES_PATH="build/flutter/android/key.properties"

# Verificar si el keystore ya existe
if [ -f "$KEYSTORE_PATH" ]; then
    print_warning "El keystore ya existe en: $KEYSTORE_PATH"
    read -p "¿Deseas sobrescribirlo? (s/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Ss]$ ]]; then
        print_info "Operación cancelada."
        exit 0
    fi
fi

# Crear directorio si no existe
mkdir -p "$(dirname "$KEYSTORE_PATH")"

print_info "Vas a crear un keystore para firmar tu aplicación Android."
print_info "Necesitarás proporcionar la siguiente información:"
echo ""
echo "  - Alias de la clave (por defecto: upload)"
echo "  - Contraseña del keystore"
echo "  - Contraseña de la clave (puede ser la misma)"
echo "  - Información personal (nombre, organización, etc.)"
echo ""
print_warning "IMPORTANTE: Guarda estas credenciales en un lugar seguro."
print_warning "Las necesitarás para todas las actualizaciones futuras de tu app."
echo ""

# Valores por defecto
KEY_ALIAS="upload"
KEYSTORE_PASSWORD=""
KEY_PASSWORD=""
VALIDITY_YEARS=25

# Solicitar información
read -p "Alias de la clave [$KEY_ALIAS]: " input_alias
KEY_ALIAS=${input_alias:-$KEY_ALIAS}

read -sp "Contraseña del keystore: " KEYSTORE_PASSWORD
echo ""
if [ -z "$KEYSTORE_PASSWORD" ]; then
    print_error "La contraseña del keystore es obligatoria."
    exit 1
fi

read -sp "Contraseña de la clave (Enter para usar la misma): " KEY_PASSWORD
echo ""
KEY_PASSWORD=${KEY_PASSWORD:-$KEYSTORE_PASSWORD}

read -p "Nombre completo: " CN
read -p "Unidad organizacional (OU): " OU
read -p "Organización (O): " O
read -p "Ciudad (L): " L
read -p "Estado/Provincia (ST): " ST
read -p "Código de país (2 letras, ej: ES): " C

# Construir DN (Distinguished Name)
DN="CN=$CN"
if [ -n "$OU" ]; then
    DN="$DN, OU=$OU"
fi
if [ -n "$O" ]; then
    DN="$DN, O=$O"
fi
if [ -n "$L" ]; then
    DN="$DN, L=$L"
fi
if [ -n "$ST" ]; then
    DN="$DN, ST=$ST"
fi
if [ -n "$C" ]; then
    DN="$DN, C=$C"
fi

print_info "Creando keystore..."
print_info "Ruta: $KEYSTORE_PATH"
print_info "Alias: $KEY_ALIAS"
print_info "Validez: $VALIDITY_YEARS años"
echo ""

# Crear el keystore
keytool -genkey -v -keystore "$KEYSTORE_PATH" \
    -alias "$KEY_ALIAS" \
    -keyalg RSA \
    -keysize 2048 \
    -validity $((VALIDITY_YEARS * 365)) \
    -storepass "$KEYSTORE_PASSWORD" \
    -keypass "$KEY_PASSWORD" \
    -dname "$DN" || {
    print_error "Error al crear el keystore."
    exit 1
}

print_success "Keystore creado exitosamente!"

# Crear archivo key.properties
print_info "Creando archivo key.properties..."

mkdir -p "$(dirname "$KEY_PROPERTIES_PATH")"

cat > "$KEY_PROPERTIES_PATH" << EOF
storePassword=$KEYSTORE_PASSWORD
keyPassword=$KEY_PASSWORD
keyAlias=$KEY_ALIAS
storeFile=upload-keystore.jks
EOF

print_success "Archivo key.properties creado en: $KEY_PROPERTIES_PATH"

echo ""
print_section "Resumen"
print_success "Keystore creado exitosamente!"
echo ""
print_info "Archivos creados:"
echo "  📦 $KEYSTORE_PATH"
echo "  📄 $KEY_PROPERTIES_PATH"
echo ""
print_warning "IMPORTANTE: Guarda estas credenciales de forma segura:"
echo "  - Alias: $KEY_ALIAS"
echo "  - Contraseña del keystore: [la que ingresaste]"
echo "  - Contraseña de la clave: [la que ingresaste]"
echo ""
print_info "Ahora puedes ejecutar ./build_android.sh para construir tu app firmada en modo release."

