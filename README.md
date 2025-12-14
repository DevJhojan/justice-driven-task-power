# Aplicación de Tareas (Todo App)

Aplicación móvil de gestión de tareas desarrollada con Flet (Python) y base de datos SQLite local.

## Características

- ✅ Crear, editar y eliminar tareas
- ✅ Marcar tareas como completadas/pendientes
- ✅ Prioridades (Baja, Media, Alta)
- ✅ Filtrado por estado (Todas, Pendientes, Completadas)
- ✅ Estadísticas de tareas
- ✅ Base de datos local SQLite
- ✅ Interfaz moderna y responsive
- ✅ Diseño optimizado para móviles

## Estructura del Proyecto

```
App_movil_real_live/
│
├── app/
│   ├── main.py                 # Punto de entrada
│   ├── ui/
│   │   ├── home_view.py        # Vista principal
│   │   ├── task_form.py        # Formulario de tareas
│   │   └── widgets.py          # Componentes reutilizables
│   │
│   ├── data/
│   │   ├── database.py         # Configuración de BD
│   │   ├── task_repository.py  # Operaciones CRUD
│   │   └── models.py           # Modelos de datos
│   │
│   ├── services/
│   │   └── task_service.py     # Lógica de negocio
│
├── assets/                     # Recursos (imágenes, etc.)
├── pyproject.toml              # Configuración del proyecto
├── requirements.txt            # Dependencias
└── README.md                   # Este archivo
```

## Requisitos

- Python 3.8 o superior
- Flet 0.28.0 o superior

## Instalación

1. Clonar o descargar el proyecto

2. Crear un entorno virtual (recomendado):
```bash
python3 -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

3. Instalar dependencias:
```bash
pip install -r requirements.txt
```

O instalar directamente:
```bash
pip install flet
```

## Uso

### Ejecutar la aplicación

Desde el directorio raíz del proyecto:

```bash
python -m app.main
```

O ejecutar directamente:

```bash
python app/main.py
```

### Modos de ejecución

La aplicación puede ejecutarse en diferentes modos modificando `main.py`:

- **Móvil (por defecto)**: `ft.AppView.FLET_APP`
- **Web**: `ft.AppView.WEB_BROWSER`
- **Desktop**: `ft.AppView.FLET_APP_HIDDEN` o sin especificar view

## Base de Datos

La aplicación utiliza SQLite para almacenar las tareas localmente. La base de datos se crea automáticamente en el archivo `tasks.db` dentro del directorio de la aplicación.

### Esquema de la base de datos

```sql
CREATE TABLE tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    completed INTEGER NOT NULL DEFAULT 0,
    priority TEXT NOT NULL DEFAULT 'medium',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
)
```

## Funcionalidades

### Gestión de Tareas

- **Crear**: Presiona el botón flotante "+" para crear una nueva tarea
- **Editar**: Presiona el icono de editar en cualquier tarea
- **Eliminar**: Presiona el icono de eliminar (se pedirá confirmación)
- **Completar**: Presiona el icono de estado para marcar/desmarcar como completada

### Filtros

- **Todas**: Muestra todas las tareas
- **Pendientes**: Muestra solo las tareas no completadas
- **Completadas**: Muestra solo las tareas completadas

### Prioridades

- **Baja** (Verde): Tareas de baja prioridad
- **Media** (Naranja): Tareas de prioridad media
- **Alta** (Rojo): Tareas de alta prioridad

## Desarrollo

### Estructura de Código

- **models.py**: Define el modelo de datos `Task`
- **database.py**: Gestiona la conexión y creación de la base de datos
- **task_repository.py**: Implementa las operaciones CRUD en la base de datos
- **task_service.py**: Contiene la lógica de negocio y validaciones
- **widgets.py**: Componentes UI reutilizables (tarjetas, estadísticas, etc.)
- **task_form.py**: Formulario para crear/editar tareas
- **home_view.py**: Vista principal que coordina todos los componentes
- **main.py**: Punto de entrada de la aplicación

## Personalización

### Cambiar el tema

En `main.py`, modifica:
```python
page.theme_mode = ft.ThemeMode.LIGHT  # o ft.ThemeMode.DARK
```

### Cambiar colores

Los colores se pueden modificar en `widgets.py` y `home_view.py` según sea necesario.

## Licencia

Este proyecto es de código abierto y está disponible para uso personal y comercial.

## Construir APK con Icono Personalizado

Para construir el APK usando el icono personalizado ubicado en `assets/task_logo.ico`:

```bash
./build_with_icon.sh
```

Este script:
1. Convierte el icono ICO a PNG
2. Construye el APK inicial
3. Reemplaza los iconos en todas las resoluciones necesarias
4. Reconstruye el APK con el icono personalizado

El APK final se encontrará en `build/apk/app-release.apk`.

## Contribuciones

Las contribuciones son bienvenidas. Por favor, crea un issue o pull request para cualquier mejora.

