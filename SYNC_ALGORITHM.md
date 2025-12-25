# Algoritmo de Sincronización Inteligente y Granular

## Problema Resuelto

**Problema anterior**: 
1. Los datos se duplicaban en Firebase al sincronizar, incluso cuando no habían cambiado.
2. Se sincronizaban objetos completos cuando solo había cambiado una parte (ej: marcar un día en el calendario subía todo el hábito).
3. Sincronización ineficiente que consumía ancho de banda innecesariamente.

**Solución implementada**: 
1. Sistema de sincronización inteligente que compara datos locales vs remotos antes de subir.
2. **Sincronización granular**: Solo sincroniza los campos/entidades que han cambiado.
3. **Diff a nivel de campo**: Calcula diferencias campo por campo, no objeto por objeto.
4. **Sub-entidades separadas**: Completions de hábitos y subtareas se sincronizan independientemente.

---

## Arquitectura de Sincronización

### Principios Fundamentales

1. **OFFLINE-FIRST**: SQLite es la fuente de verdad principal
2. **IDs Únicos Persistentes**: Cada tarea/hábito tiene un ID único que persiste entre dispositivos
3. **Timestamps para Detección de Cambios**: `created_at`, `updated_at`, `deleted_at`
4. **Comparación Inteligente**: Solo sincroniza si hay diferencias reales
5. **No Destructivo**: Nunca sobrescribe datos sin verificar timestamps

---

## Algoritmo de Sincronización Paso a Paso

### Fase 1: Subida de Datos Locales a Firebase

#### Paso 1.1: Descargar Datos Remotos para Comparar
```python
# Descargar todos los datos remotos (tareas y hábitos)
remote_tasks_dict = {task_id: task_data, ...}
remote_habits_dict = {habit_id: habit_data, ...}
```

#### Paso 1.2: Comparar Cada Dato Local con su Versión Remota

**Para cada tarea/hábito local:**

1. **¿Existe en la nube?**
   - Si NO existe → **SUBIR** (nuevo)
   - Si existe → Continuar al paso 2

2. **¿Ha sido modificado localmente?**
   - Comparar `updated_at` local vs `updated_at` remoto
   - Si `updated_at_local > updated_at_remoto` → **SUBIR** (modificado)
   - Si `updated_at_local <= updated_at_remoto` → **OMITIR** (sin cambios o remoto más nuevo)

#### Paso 1.3: Subir Solo Datos que Necesitan Sincronización
- Solo se suben datos nuevos o modificados
- Los datos sin cambios se omiten (no se suben)

#### Paso 1.4: Subir Eliminaciones Pendientes
- Las eliminaciones siempre se suben si están pendientes de sincronizar

---

### Fase 2: Descarga de Datos Remotos

#### Paso 2.1: Descargar Todos los Datos Remotos
```python
remote_tasks = download_tasks_from_firebase()
remote_habits = download_habits_from_firebase()
remote_deletions = download_deletions_from_firebase()
```

#### Paso 2.2: Fusionar Cada Dato Remoto con Datos Locales

**Para cada tarea/hábito remoto:**

1. **¿Existe localmente?**
   - Si NO existe → **CREAR** con ID remoto (evita duplicados)
   - Si existe → Continuar al paso 2

2. **¿Es más reciente que la local?**
   - Comparar `updated_at` remoto vs `updated_at` local
   - Si `updated_at_remoto > updated_at_local` → **ACTUALIZAR** local
   - Si `updated_at_remoto <= updated_at_local` → **OMITIR** (local más reciente o igual)

#### Paso 2.3: Aplicar Eliminaciones Remotas
- Si una eliminación remota es más reciente que la local, aplicarla localmente

---

## Estrategia para Evitar Duplicados

### 1. IDs Únicos Persistentes

**Implementación:**
- Cada tarea/hábito tiene un ID único (`id`) que se mantiene entre dispositivos
- Al crear desde datos remotos, se usa el ID remoto, no se genera uno nuevo

**Código clave:**
```python
# En _merge_task y _merge_habit:
if remote_id:
    task.id = remote_id  # Mantener ID remoto
    task_repository.create(task)  # Crear con ID específico
```

### 2. Verificación de Existencia por ID

**Antes de crear:**
- Verificar si ya existe un elemento con ese ID
- Si existe, actualizar en lugar de crear

**Código clave:**
```python
# En TaskRepository.create y HabitRepository.create:
if task.id is not None:
    cursor.execute('SELECT id FROM tasks WHERE id = ?', (task.id,))
    if cursor.fetchone():
        return self.update(task)  # Actualizar si existe
```

### 3. Comparación de Timestamps

**Solo sincronizar si hay cambios reales:**
```python
def _should_upload_task(local_task, remote_task_data):
    if remote_task_data is None:
        return True  # No existe en nube, subir
    
    local_updated = local_task.updated_at.isoformat()
    remote_updated = remote_task_data.get('updated_at')
    
    # Solo subir si local es más reciente
    return local_updated > remote_updated
```

---

## Manejo de Conflictos

### Resolución de Conflictos: Last-Write-Wins con Verificación

**Regla**: El dato más reciente (según `updated_at`) gana.

**Proceso:**

1. **Al subir datos locales:**
   - Solo se sube si `updated_at_local > updated_at_remoto`
   - Si remoto es más reciente, se omite la subida

2. **Al descargar datos remotos:**
   - Solo se actualiza local si `updated_at_remoto > updated_at_local`
   - Si local es más reciente, se omite la descarga

3. **Si ambos tienen el mismo timestamp:**
   - Se considera que están sincronizados
   - No se realiza ninguna acción

---

## Flujo de Sincronización entre Múltiples Dispositivos

### Escenario 1: Dispositivo A crea una tarea

1. **Dispositivo A (local):**
   - Crea tarea con ID=1, `updated_at=2024-01-15T10:00:00`
   - Sincroniza → Sube a Firebase

2. **Dispositivo B (remoto):**
   - Descarga tarea con ID=1
   - Crea localmente con ID=1 (mismo ID, no duplicado)
   - Resultado: Ambos dispositivos tienen la misma tarea con ID=1

### Escenario 2: Dispositivo A modifica, Dispositivo B también modifica

1. **Dispositivo A:**
   - Modifica tarea ID=1, `updated_at=2024-01-15T11:00:00`
   - Sincroniza → Sube a Firebase

2. **Dispositivo B:**
   - Modifica tarea ID=1, `updated_at=2024-01-15T10:30:00`
   - Sincroniza → Compara timestamps
   - Detecta que remoto (11:00) es más reciente que local (10:30)
   - Descarga y actualiza local con datos remotos
   - Resultado: Dispositivo B tiene la versión más reciente

### Escenario 3: Sin cambios (caso crítico resuelto)

1. **Dispositivo A:**
   - Tiene 3 hábitos, todos sincronizados
   - Sincroniza → Compara cada hábito
   - Detecta que todos tienen `updated_at_local == updated_at_remoto`
   - No sube nada → `no_changes = True`
   - Muestra mensaje: "Los datos no han sido modificados, no es necesario sincronizar"

2. **Dispositivo B:**
   - Descarga los mismos 3 hábitos
   - Detecta que todos ya existen localmente con los mismos timestamps
   - No crea duplicados → `no_changes = True`
   - Resultado: Sin duplicados, sin cambios innecesarios

---

## Estados de Sincronización

### Estados de un Elemento

1. **Nuevo**: No existe en la nube → Debe subirse
2. **Modificado**: Existe pero `updated_at_local > updated_at_remoto` → Debe subirse
3. **Sincronizado**: Existe y timestamps son iguales → No necesita sincronización
4. **Remoto más nuevo**: Existe pero `updated_at_remoto > updated_at_local` → Debe descargarse
5. **Eliminado**: Marcado para eliminación → Debe sincronizarse la eliminación

---

## Detección de "Sin Cambios"

### Criterios para `no_changes = True`

```python
total_changes = (
    tasks_uploaded + habits_uploaded + deletions_uploaded +
    tasks_downloaded + habits_downloaded + deletions_downloaded
)

if total_changes == 0:
    result.no_changes = True
```

**Significado:**
- No se subió ningún dato nuevo o modificado
- No se descargó ningún dato nuevo o modificado
- No hay eliminaciones pendientes
- **Conclusión**: Todos los datos están sincronizados

---

## Ventajas de la Solución

1. **Evita Duplicados**: Usa IDs únicos persistentes y verifica existencia
2. **Eficiente**: Solo sincroniza cuando es necesario
3. **Transparente**: Muestra claramente cuando no hay cambios
4. **Robusto**: Maneja conflictos usando timestamps
5. **Escalable**: Funciona con múltiples dispositivos
6. **Seguro**: No destructivo, verifica antes de sobrescribir

---

## Ejemplo de Flujo Completo

### Situación Inicial
- **Dispositivo A**: 3 hábitos (IDs: 1, 2, 3)
- **Firebase**: 3 hábitos (IDs: 1, 2, 3) - mismos datos

### Dispositivo A sincroniza

1. **Fase de Subida:**
   - Compara hábito 1: `updated_at_local == updated_at_remoto` → Omitir
   - Compara hábito 2: `updated_at_local == updated_at_remoto` → Omitir
   - Compara hábito 3: `updated_at_local == updated_at_remoto` → Omitir
   - Resultado: `habits_uploaded = 0`, `habits_skipped = 3`

2. **Fase de Descarga:**
   - Descarga hábito 1: Ya existe local, timestamps iguales → Omitir
   - Descarga hábito 2: Ya existe local, timestamps iguales → Omitir
   - Descarga hábito 3: Ya existe local, timestamps iguales → Omitir
   - Resultado: `habits_downloaded = 0`

3. **Resultado Final:**
   - `total_changes = 0`
   - `no_changes = True`
   - Mensaje: "Los datos no han sido modificados, no es necesario sincronizar"
   - **Firebase sigue teniendo 3 hábitos (sin duplicados)**

---

## Código Clave Implementado

### 1. Comparación antes de subir
```python
def _should_upload_task(local_task, remote_task_data):
    if remote_task_data is None:
        return True  # Nuevo, subir
    
    local_updated = local_task.updated_at.isoformat()
    remote_updated = remote_task_data.get('updated_at')
    
    return local_updated > remote_updated  # Solo si local es más reciente
```

### 2. Creación con ID remoto
```python
# En HabitRepository.create:
if habit.id is not None:
    cursor.execute('SELECT id FROM habits WHERE id = ?', (habit.id,))
    if cursor.fetchone():
        return self.update(habit)  # Actualizar si existe
    
    # Crear con ID específico
    cursor.execute('INSERT INTO habits (id, ...) VALUES (?, ...)', (habit.id, ...))
```

### 3. Detección de sin cambios
```python
if total_changes == 0:
    result.no_changes = True
    # UI muestra: "Los datos no han sido modificados, no es necesario sincronizar"
```

---

## Conclusión

La solución implementada garantiza:

✅ **Sin duplicados**: IDs únicos persistentes y verificación de existencia  
✅ **Sincronización inteligente**: Solo cuando hay cambios reales  
✅ **Transparencia**: Mensaje claro cuando no hay cambios  
✅ **Robustez**: Manejo de conflictos con timestamps  
✅ **Escalabilidad**: Funciona con múltiples dispositivos  
✅ **Seguridad**: No destructivo, verifica antes de sobrescribir

