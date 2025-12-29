# Build para Linux - Paquete .deb

Este documento explica cómo generar un paquete `.deb` para distribuciones basadas en Debian/Ubuntu.

## Requisitos

1. **Flet instalado** (en venv o sistema)
2. **dpkg-deb** instalado (generalmente viene con el sistema)
3. **Linux** (Debian/Ubuntu/Mint)

## Instalación de dependencias

```bash
# Activar entorno virtual (si usas uno)
source venv/bin/activate

# Instalar Flet si no está instalado
pip install flet
```

## Uso

### Build básico

```bash
./build_linux.sh
```

### Limpiar y construir

```bash
./build_linux.sh --clean
```

### Ver ayuda

```bash
./build_linux.sh --help
```

## Archivo generado

El paquete `.deb` se generará en:

```
build/justice-driven-task-power_1.0.0_<arch>.deb
```

Donde `<arch>` puede ser:
- `amd64` para sistemas x86_64
- `arm64` para sistemas ARM 64-bit
- `armhf` para sistemas ARM 32-bit

## Instalación del paquete

### Instalar el .deb

```bash
sudo dpkg -i build/justice-driven-task-power_*.deb
```

### Si faltan dependencias

```bash
sudo apt-get install -f
```

### Desinstalar

```bash
sudo apt-get remove justice-driven-task-power
```

## Estructura del paquete

El paquete `.deb` incluye:

- **Ejecutable**: `/usr/bin/justice-driven-task-power`
- **Icono**: `/usr/share/icons/hicolor/256x256/apps/justice-driven-task-power.png`
- **Archivo .desktop**: `/usr/share/applications/justice-driven-task-power.desktop`
- **Archivos de la aplicación**: `/usr/share/justice-driven-task-power/`

## Verificación

Después de instalar, puedes verificar que la aplicación esté disponible:

```bash
# Verificar que el ejecutable existe
which justice-driven-task-power

# Verificar que el .desktop existe
ls /usr/share/applications/justice-driven-task-power.desktop

# Ejecutar la aplicación
justice-driven-task-power
```

## Troubleshooting

### Error: "Flet no está instalado"

```bash
# Activar entorno virtual
source venv/bin/activate

# O instalar Flet globalmente
pip install flet
```

### Error: "dpkg-deb no encontrado"

```bash
# Instalar dpkg-dev
sudo apt-get install dpkg-dev
```

### Error: "No se encontró el ejecutable de Linux"

Asegúrate de que Flet haya construido correctamente la aplicación:

```bash
# Construir manualmente para ver errores
flet build linux --verbose
```

### El paquete se instala pero la app no inicia

Verifica los logs:

```bash
# Ejecutar desde terminal para ver errores
justice-driven-task-power
```

## Notas

- El paquete `.deb` es específico para la arquitectura del sistema donde se construye
- Para distribuir, necesitarás construir paquetes para cada arquitectura objetivo
- El paquete incluye todas las dependencias necesarias de la aplicación

