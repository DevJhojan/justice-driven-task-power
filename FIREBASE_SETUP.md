# Configuración de Firebase para Sincronización

## Instalación

1. Instala las dependencias necesarias:
```bash
pip install pyrebase4 python-dotenv
```

## Configuración en Firebase Console

### 1. Crear Base de Datos Realtime Database

1. Ve a [Firebase Console](https://console.firebase.google.com/)
2. Selecciona el proyecto: **justice-driven-task-power**
3. Ve a **Realtime Database**
4. Si no existe, crea una nueva base de datos
5. Selecciona la ubicación más cercana (recomendado: us-central1)

### 2. Configurar Reglas de Seguridad

1. Ve a la pestaña **Rules** en Realtime Database
2. Copia el contenido de `firebase_database_rules.json`
3. Pega las reglas en Firebase Console
4. Haz clic en **Publish** para aplicar las reglas

### 3. Habilitar Autenticación

1. Ve a **Authentication** > **Sign-in method**
2. Habilita **Email/Password**
3. Guarda los cambios

## Uso en la Aplicación

1. Ve a la sección **⚙️ Configuración**
2. En la sección **Sincronización Firebase**:
   - **Registrar**: Crea una nueva cuenta con email y contraseña
   - **Iniciar sesión**: Inicia sesión con tu cuenta
   - **Subir a Firebase**: Sincroniza tus datos locales a Firebase
   - **Descargar de Firebase**: Descarga datos de Firebase a local
   - **Cerrar sesión**: Cierra la sesión actual

## Estructura de Datos en Firebase

Los datos se almacenan en la siguiente estructura:

```
users/
  {userId}/
    tasks/
      {taskId}/
        id, title, description, due_date, status, created_at, updated_at
    habits/
      {habitId}/
        id, title, description, created_at, updated_at, completions[]
    goals/
      {goalId}/
        id, title, description, target_value, current_value, unit, created_at, updated_at
```

## Reglas de Seguridad

Las reglas aseguran que:
- Cada usuario solo puede acceder a sus propios datos
- Los datos deben tener la estructura correcta (validación)
- El acceso está restringido a usuarios autenticados

