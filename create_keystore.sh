#!/bin/bash

################################################################################
# Script para crear el keystore de Android
# 
# Este script ayuda a crear el keystore necesario para firmar APK y AAB.
# 
# Uso:
#   ./create_keystore.sh
#
################################################################################

set -e

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

# Configuración
KEYSTORE_DIR="android/keystore"
KEYSTORE_FILE="${KEYSTORE_DIR}/justice_task_power.jks"
KEY_ALIAS="justice_task_power"
VALIDITY_DAYS=10000

# Verificar que keytool está disponible
if ! command -v keytool &> /dev/null; then
    print_error "keytool no está disponible"
    print_info "keytool es parte del JDK. Instala Java JDK:"
    echo "  Ubuntu/Debian: sudo apt-get install openjdk-17-jdk"
    echo "  Fedora: sudo dnf install java-17-openjdk-devel"
    exit 1
fi

print_info "=========================================="
print_info "  Crear Keystore para Android"
print_info "=========================================="
echo ""

# Verificar si el keystore ya existe
if [ -f "$KEYSTORE_FILE" ]; then
    print_warning "El keystore ya existe: $KEYSTORE_FILE"
    read -p "¿Deseas sobrescribirlo? (s/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Ss]$ ]]; then
        print_info "Operación cancelada"
        exit 0
    fi
    rm -f "$KEYSTORE_FILE"
fi

# Crear directorio si no existe
mkdir -p "$KEYSTORE_DIR"

# Solicitar información
print_info "Ingresa la información para el keystore:"
echo ""

read -sp "Contraseña del keystore: " KEYSTORE_PASSWORD
echo ""
read -sp "Confirma la contraseña del keystore: " KEYSTORE_PASSWORD_CONFIRM
echo ""

if [ "$KEYSTORE_PASSWORD" != "$KEYSTORE_PASSWORD_CONFIRM" ]; then
    print_error "Las contraseñas no coinciden"
    exit 1
fi

read -sp "Contraseña de la clave (puede ser la misma): " KEY_PASSWORD
echo ""

if [ -z "$KEY_PASSWORD" ]; then
    KEY_PASSWORD="$KEYSTORE_PASSWORD"
    print_info "Usando la misma contraseña para la clave"
fi

read -p "Nombre completo (CN): " CN
read -p "Unidad organizacional (OU): " OU
read -p "Organización (O): " O
read -p "Ciudad (L): " L
read -p "Estado/Provincia (ST): " ST
read -p "Código de país (C) [ej: US, ES, MX]: " C

# Valores por defecto si están vacíos
CN=${CN:-"Justice Driven Task Power"}
OU=${OU:-"Development"}
O=${O:-"Justice Driven Task Power"}
L=${L:-"Unknown"}
ST=${ST:-"Unknown"}
C=${C:-"US"}

print_info ""
print_info "Creando keystore..."
print_info "Ubicación: $KEYSTORE_FILE"
print_info "Alias: $KEY_ALIAS"
print_info "Validez: $VALIDITY_DAYS días"
echo ""

# Crear el keystore
if keytool -genkey -v \
    -keystore "$KEYSTORE_FILE" \
    -alias "$KEY_ALIAS" \
    -keyalg RSA \
    -keysize 2048 \
    -validity $VALIDITY_DAYS \
    -storepass "$KEYSTORE_PASSWORD" \
    -keypass "$KEY_PASSWORD" \
    -dname "CN=$CN, OU=$OU, O=$O, L=$L, ST=$ST, C=$C"; then
    
    print_success "Keystore creado exitosamente: $KEYSTORE_FILE"
    echo ""
    print_info "Ahora crea un archivo .env con las siguientes variables:"
    echo ""
    echo "KEYSTORE_PATH=$KEYSTORE_FILE"
    echo "KEYSTORE_PASSWORD=$KEYSTORE_PASSWORD"
    echo "KEY_ALIAS=$KEY_ALIAS"
    echo "KEY_PASSWORD=$KEY_PASSWORD"
    echo ""
    print_info "O copia .env.example y completa los valores:"
    echo "  cp .env.example .env"
    echo ""
    print_warning "⚠️  IMPORTANTE: Guarda estas credenciales de forma segura."
    print_warning "Sin el keystore y las contraseñas, NO podrás actualizar tu app en Google Play."
else
    print_error "Error al crear el keystore"
    exit 1
fi

