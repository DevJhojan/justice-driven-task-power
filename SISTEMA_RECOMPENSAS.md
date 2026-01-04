# 🌟 Sistema de Puntos, Niveles y Recompensas

## 📋 Descripción

Este es un sistema gamificado completo que permite:
- **Ganar puntos** por completar tareas, hábitos y objetivos
- **Subir de nivel** con 10 niveles diferentes (de "Nadie" a "Como Dios")
- **Desbloquear recompensas** cuando alcanzas ciertos hitos de puntos
- **Ver tu progreso** con barras de progreso y estadísticas
- **Competir en rankings** contra otros usuarios

## 🎯 Los 10 Niveles

| Nivel | Puntos | Icono | Descripción |
|-------|--------|-------|-------------|
| Nadie | 0 | 👤 | Punto de partida |
| Desconocido | 50 | 🔍 | Comienzas tu viaje |
| Novato | 100 | 🌱 | Ganando experiencia |
| Conocido | 500 | 📚 | Ya tienes presencia |
| Respetado | 1,000 | 🏆 | La comunidad te reconoce |
| Influyente | 5,000 | ⭐ | Tu influencia crece |
| Líder | 10,000 | 👑 | Lideras el cambio |
| Legendario | 50,000 | 🔥 | Eres una leyenda |
| Todopoderoso | 100,000 | ⚡ | Casi al pico |
| Como Dios | 500,000 | 🌟 | El máximo nivel |

## 💰 Puntos por Acción

```python
POINTS_BY_ACTION = {
    "task_completed": 10,          # Completar una tarea
    "subtask_completed": 5,        # Completar una subtarea
    "habit_completed": 15,         # Completar un hábito
    "goal_achieved": 50,           # Alcanzar un objetivo
    "daily_streak": 20,            # Racha diaria
}
```

## 📁 Estructura de Archivos

```
app/
├── logic/
│   ├── system_points.py          # Definición de puntos y niveles
│   └── system_levels.py          # Gestión de niveles de usuario
├── models/
│   ├── user.py                   # Modelo de Usuario
│   └── reward.py                 # Modelo de Recompensa
├── services/
│   ├── user_service.py           # Servicio de usuarios
│   └── rewards_service.py        # Servicio de recompensas
└── ui/
    └── resume/
        └── rewards/
            └── rewards_view.py   # Vista Flet de recompensas
```

## 🚀 Uso del Sistema

### 1. Crear un Usuario

```python
from app.services.user_service import UserService

user_service = UserService()
user = user_service.create_user("jhojan", "jhojan@example.com")
print(f"Usuario creado: {user.username}, Nivel: {user.level}")
```

### 2. Ganar Puntos

```python
# Añadir puntos por completar una tarea
level_up = user_service.add_points_to_user(user.id, "task_completed")

if level_up:
    print(f"¡Subiste de nivel! Ahora eres: {user.level}")

# O añadir cantidad específica de puntos
user_service.add_points_to_user(user.id, "custom_action", amount=50)
```

### 3. Ver Estadísticas

```python
stats = user_service.get_user_stats(user.id)

print(f"Nivel: {stats['level']}")
print(f"Puntos: {stats['points']}")
print(f"Progreso: {stats['progress_percent']:.1f}%")
print(f"Próximo nivel: {stats['next_level']}")
```

### 4. Gestionar Recompensas

```python
from app.services.rewards_service import RewardsService

rewards_service = RewardsService()

# Crear recompensa
reward = rewards_service.create_reward({
    "title": "Primer Paso",
    "description": "Completa tu primera tarea",
    "points_required": 50,
    "icon": "👣",
    "color": "#4CAF50",
    "category": "achievement",
})

# Ver recompensas desbloqueadas
unlocked = rewards_service.get_unlocked_rewards(user.points)
for reward in unlocked:
    print(f"✓ {reward.icon} {reward.title}")

# Ver próximas recompensas
next_rewards = rewards_service.get_next_rewards(user.points, limit=5)
for reward in next_rewards:
    missing = reward.points_required - user.points
    print(f"⏳ {reward.icon} {reward.title} - Faltan {int(missing)} puntos")

# Editar recompensa
rewards_service.update_reward(reward.id, {
    "title": "Primer Paso Avanzado",
    "points_required": 100,
})

# Eliminar recompensa
rewards_service.delete_reward(reward.id)
```

### 5. Ver Ranking

```python
# Obtener top 10 usuarios
ranking = user_service.get_ranking(limit=10)

for rank_item in ranking:
    print(f"{rank_item['rank']}. {rank_item['user_id']} - {rank_item['level']} ({int(rank_item['points'])} pts)")
```

## 🎨 Componentes Flet

### RewardsView

Vista completa de recompensas con:
- Lista de recompensas con estado de desbloqueo
- Crear nuevas recompensas
- Editar recompensas existentes
- Eliminar recompensas
- Filtros (Todas, Desbloqueadas, Bloqueadas)
- Información del usuario (puntos y nivel)

```python
from app.ui.resume.rewards.rewards_view import RewardsView

rewards_view = RewardsView()

# Establecer puntos del usuario
rewards_view.set_user_points(150.0)

# Establecer nivel del usuario
rewards_view.set_user_level("Novato")
```

## 📊 Progresión del Sistema

1. **Usuario Nuevo**: Comienza en "Nadie" con 0 puntos
2. **Completa Tareas**: Gana puntos por cada acción
3. **Sube de Nivel**: Cada 50-500k puntos
4. **Desbloquea Recompensas**: Basadas en puntos totales
5. **Compite en Rankings**: Ve tu posición contra otros

## 🔧 Personalización

### Cambiar Puntos por Acción

En `app/logic/system_points.py`:

```python
POINTS_BY_ACTION = {
    "task_completed": 15,  # Aumentar a 15 puntos
    "subtask_completed": 7,
    # ... agregar nuevas acciones
}
```

### Cambiar Colores de Niveles

En `app/logic/system_points.py`:

```python
LEVEL_COLORS = {
    Level.NADIE: "#808080",           # Gris
    Level.DESCONOCIDO: "#8B7355",     # Marrón
    # ... personalizar colores
}
```

### Cambiar Iconos

En `app/logic/system_points.py`:

```python
LEVEL_ICONS = {
    Level.NADIE: "👤",
    Level.DESCONOCIDO: "🔍",
    # ... personalizar iconos
}
```

## 🧪 Ejecutar Ejemplo

```bash
python example_system.py
```

Esto mostrará un ejemplo completo del sistema en acción.

## 📝 Notas

- Los puntos se almacenan en memoria (puedes integrar con base de datos)
- Los niveles se calculan automáticamente basados en puntos
- Las recompensas se actualizan automáticamente cuando subes de nivel
- El sistema soporta múltiples usuarios simultáneamente

## 🎁 Características Futuras

- [ ] Integración con base de datos SQLite
- [ ] Achievements personalizados por usuario
- [ ] Temporadas de competencia
- [ ] Badges especiales por racha
- [ ] Notificaciones de nivel up
- [ ] Exportar estadísticas
