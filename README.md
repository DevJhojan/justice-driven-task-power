# Aplicación de Productividad Personal

Aplicación completa de productividad personal para gestionar tareas, hábitos y metas.

## 🎯 Características

### Módulos Principales

- **📋 Tareas**: Gestión completa de tareas con estados (pendiente/completada)
- **🔁 Hábitos**: Seguimiento diario de hábitos con métricas (completados, rachas)
- **🎯 Metas**: Definición y monitoreo de metas con progreso
- **⚙️ Configuración**: Ajustes básicos de la aplicación

## 🏗️ Arquitectura

La aplicación sigue una arquitectura modular y escalable:

```
app/
├── data/           # Capa de persistencia
│   ├── models.py              # Modelos de datos
│   ├── database.py            # Gestión de SQLite
│   ├── task_repository.py     # CRUD de tareas
│   ├── habit_repository.py    # CRUD de hábitos
│   └── goal_repository.py     # CRUD de metas
│
├── services/       # Lógica de negocio
│   ├── task_service.py
│   ├── habit_service.py
│   └── goal_service.py
│
└── ui/            # Interfaz de usuario
    ├── home_view.py           # Vista principal con navegación
    ├── tasks/                 # Módulo de tareas
    ├── habits/                # Módulo de hábitos
    ├── goals/                 # Módulo de metas
    └── settings/              # Configuración
```

## 🚀 Instalación

1. **Instalar dependencias:**
```bash
pip install -r requirements.txt
```

2. **Ejecutar la aplicación:**
```bash
python main.py
```

O desde el módulo app:
```bash
python -m app.app
```

## 📱 Plataformas

- **💻 Escritorio**: Linux, Windows, macOS
- **📱 Android**: Compilar con `build_android.sh`

## 🗄️ Base de Datos

La aplicación utiliza SQLite como base de datos local. La base de datos se crea automáticamente en:
- Linux/macOS: `~/.productivity_app/app.db`
- Windows: `%USERPROFILE%\.productivity_app\app.db`

### Esquema de Base de Datos

- **tasks**: Tareas con título, descripción, fecha de vencimiento y estado
- **habits**: Hábitos con título y descripción
- **habit_completions**: Registros diarios de completación de hábitos
- **goals**: Metas con título, descripción, valor objetivo, valor actual y unidad

## 🎨 Características de la UI

- **Barra de navegación inferior**: Acceso rápido a todas las secciones
- **Modo oscuro/claro**: Toggle en configuración
- **Interfaz intuitiva**: Diseño limpio y fácil de usar
- **Formularios modales**: Para crear y editar elementos

## 📋 Funcionalidades por Módulo

### Tareas
- Crear, editar y eliminar tareas
- Marcar como completada/pendiente
- Fecha de vencimiento opcional
- Descripción opcional

### Hábitos
- Crear, editar y eliminar hábitos
- Marcar completación diaria
- Métricas: días completados y racha actual
- Histórico de completaciones

### Metas
- Crear, editar y eliminar metas
- Valor objetivo y valor actual
- Unidad de medida personalizable
- Barra de progreso visual
- Porcentaje de completación

### Configuración
- Cambio de tema (oscuro/claro)
- Información de la aplicación

## 🔧 Desarrollo

La aplicación está diseñada para ser fácilmente extensible:

1. **Agregar nuevas entidades**: Crear modelo, repository y service siguiendo el patrón existente
2. **Nuevas vistas**: Agregar módulo en `ui/` y registrar en `home_view.py`
3. **Nuevas funcionalidades**: Extender servicios con nueva lógica de negocio

## 📝 Notas Técnicas

- **Offline-first**: Todos los datos se almacenan localmente
- **Sin dependencias externas**: Solo SQLite y Flet
- **Arquitectura limpia**: Separación clara de responsabilidades
- **Código documentado**: Docstrings en todas las clases y métodos principales

## 🐛 Solución de Problemas

Si la aplicación no se ejecuta:

1. Verificar que todas las dependencias estén instaladas
2. Verificar que Python 3.8+ esté instalado
3. Verificar permisos de escritura en el directorio home del usuario

## 📄 Licencia

Este proyecto es de uso personal.
