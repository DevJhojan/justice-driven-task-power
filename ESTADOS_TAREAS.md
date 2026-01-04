# Sistema de Estados de Tareas

## Descripción

Se ha implementado un sistema automático de estados para las tareas que funciona diferente dependiendo de si la tarea tiene subtareas o no.

## Estados Disponibles

- **pendiente**: La tarea aún no ha comenzado
- **en_progreso**: La tarea está siendo trabajada
- **completada**: La tarea ha sido completada
- **cancelada**: La tarea ha sido cancelada

## Lógica de Cambio de Estados

### Tareas SIN Subtareas

El estado se controla **manualmente** mediante un checkbox visible en la tarjeta:

```
☐ Mi tarea sin subtareas
```

- **Checkbox unchecked** → Estado: `pendiente`
- **Checkbox checked** → Estado: `completada`

El checkbox solo aparece en tareas que no tienen subtareas asociadas.

### Tareas CON Subtareas

El estado se calcula **automáticamente** basado en el progreso de las subtareas:

```
Mi tarea con subtareas
2/3 completadas - en_progreso
```

#### Lógica:

1. **Ninguna subtarea completada** → `pendiente`
   - Ninguno de los checkboxes de subtareas está marcado

2. **Al menos 1 subtarea completada (pero no todas)** → `en_progreso`
   - Algunos checkboxes de subtareas están marcados
   - Mostración: `X/Total completadas - en_progreso`

3. **Todas las subtareas completadas** → `completada`
   - Todos los checkboxes de subtareas están marcados
   - Mostración: `Total/Total completadas - completada`

## Ejemplo de Uso

### Crear tarea sin subtareas

1. Hacer clic en el botón FAB rojo "+"
2. Ingresar título y descripción
3. Guardar
4. En la tarjeta, hacer clic en el checkbox para marcar como completada

### Crear tarea con subtareas

1. Hacer clic en el botón FAB rojo "+"
2. Ingresar título y descripción
3. En la sección "Subtareas", agregar al menos una subtarea
4. Guardar
5. El estado se calculará automáticamente:
   - Inicialmente: `pendiente` (0 subtareas completadas)
   - Al completar algunas: `en_progreso` (N subtareas completadas)
   - Al completar todas: `completada` (todas completadas)

## Cambios en el Código

### Archivos Modificados

1. **app/models/task.py**
   - Nuevo método: `update_status_from_subtasks()`
   - Calcula automáticamente el estado basado en subtareas

2. **app/ui/task/card/task_card_view.py**
   - Nuevos métodos: `_get_status_text()`, `_on_task_checkbox_changed()`
   - Mostración de estado con indicador de progreso
   - Manejo de checkbox toggle para tareas sin subtareas

3. **app/ui/task/form/subtask_manager.py**
   - Nuevo parámetro: `on_subtask_changed` callback
   - Llama al callback cuando cambia el estado de una subtarea

4. **app/ui/task/form/task_form.py**
   - Nuevo parámetro: `on_subtask_changed` callback
   - Pasa el callback al SubtaskManager

5. **app/ui/task/task_view.py**
   - Nuevos métodos: `_on_subtask_changed()`, `_on_task_updated()`
   - Actualiza el estado cuando se guardan o modifican subtareas

## Visualización en la UI

### Tarjeta sin Subtareas
```
[✓] Mi primera tarea
    Sin descripción
```

### Tarjeta con Subtareas (Pendiente)
```
Mi tarea importante
Sin descripción
0/3 completadas - pendiente
[Subtareas] (botón para expandir)
```

### Tarjeta con Subtareas (En Progreso)
```
Mi tarea importante
Sin descripción
2/3 completadas - en_progreso
[Subtareas]
  ☑ Subtarea 1
  ☑ Subtarea 2
  ☐ Subtarea 3
```

### Tarjeta con Subtareas (Completada)
```
Mi tarea importante
Sin descripción
3/3 completadas - completada
[Subtareas]
  ☑ Subtarea 1
  ☑ Subtarea 2
  ☑ Subtarea 3
```
