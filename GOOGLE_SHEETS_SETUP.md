# Configuración de Google Sheets API

## 📋 Información del Proyecto para Google Cloud Console

### Datos para Configurar OAuth 2.0

**Nombre de la aplicación:**
```
Justice Driven Task Power
```

**Nombre del paquete (Package Name):**
```
com.flet.justice_driven_task_power
```

**Clave SHA1:**
*(Ya la tienes configurada)*

**API Key:**
```
AIzaSyDoI3Q72rpy57OCFcMi2HDUMxIWPXI0afY
```

---

## 🔧 Configuración en Google Cloud Console

### 1. Habilitar Google Sheets API

1. Ve a [Google Cloud Console](https://console.cloud.google.com/)
2. Selecciona tu proyecto (o crea uno nuevo)
3. Ve a **APIs & Services** → **Library**
4. Busca "Google Sheets API"
5. Haz clic en **Enable**

### 2. Crear Credenciales OAuth 2.0

1. Ve a **APIs & Services** → **Credentials**
2. Haz clic en **Create Credentials** → **OAuth client ID**
3. Si es la primera vez, configura la pantalla de consentimiento OAuth:
   - Tipo de aplicación: **External** (o Internal si tienes Google Workspace)
   - Completa la información requerida
4. Selecciona **Application type**: **Android**
5. Completa:
   - **Name**: `Justice Driven Task Power` (o el nombre que prefieras)
   - **Package name**: `com.flet.justice_driven_task_power`
   - **SHA-1 certificate fingerprint**: *(tu clave SHA1)*
6. Haz clic en **Create**
7. Descarga el archivo JSON de credenciales
8. Renómbralo a `credenciales_android.json` y colócalo en la raíz del proyecto

### 3. Verificar Archivo de Credenciales

El archivo `credenciales_android.json` debe estar en:
```
/home/devjdtp/Proyectos/App_movil_real_live/credenciales_android.json
```

Formato esperado:
```json
{
  "installed": {
    "client_id": "...",
    "project_id": "...",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    ...
  }
}
```

---

## 📱 Uso de la Funcionalidad

### Exportar a Google Sheets

1. Ve a **Configuración** en la app
2. Haz clic en **"Exportar a Google Sheets"**
3. La primera vez, se abrirá el navegador para autenticarte con Google
4. Autoriza el acceso a Google Sheets
5. Se creará un nuevo spreadsheet con tus datos
6. Recibirás la URL del spreadsheet creado

### Importar desde Google Sheets

1. Ve a **Configuración** en la app
2. Haz clic en **"Importar desde Google Sheets"**
3. Ingresa el **ID del spreadsheet** que quieres importar
4. El ID se encuentra en la URL del documento:
   ```
   https://docs.google.com/spreadsheets/d/[ID_AQUI]/edit
   ```
5. Los datos se importarán a tu base de datos local

---

## 🔐 Autenticación

### Primera Vez

La primera vez que uses la funcionalidad:
1. Se abrirá el navegador (o se mostrará una URL)
2. Inicia sesión con tu cuenta de Google
3. Autoriza el acceso a Google Sheets
4. Las credenciales se guardarán en `token.pickle` para próximas veces

### Próximas Veces

- Las credenciales se cargan automáticamente desde `token.pickle`
- Si expiran, se refrescan automáticamente
- No necesitarás autenticarte de nuevo

---

## 📊 Estructura del Spreadsheet

Cuando exportas, se crea un spreadsheet con 4 hojas:

1. **tasks** - Todas las tareas
2. **subtasks** - Todas las subtareas
3. **habits** - Todos los hábitos
4. **habit_completions** - Todos los cumplimientos de hábitos

Cada hoja tiene:
- Primera fila: Encabezados (nombres de columnas)
- Filas siguientes: Datos

---

## ⚠️ Notas Importantes

### Seguridad

- **NO subas `token.pickle` al repositorio** (ya está en `.gitignore`)
- El archivo `credenciales_android.json` puede estar en el repo si es necesario
- Las credenciales OAuth son específicas de tu aplicación

### Limitaciones

- **Android**: La autenticación puede requerir abrir manualmente la URL en el navegador
- **Escritorio**: Se abre automáticamente el navegador
- **Primera vez**: Requiere conexión a internet para autenticarse

### Troubleshooting

**Error: "Archivo de credenciales no encontrado"**
- Verifica que `credenciales_android.json` esté en la raíz del proyecto
- Verifica que el formato del JSON sea correcto

**Error: "No se pudo autenticar"**
- Verifica tu conexión a internet
- Verifica que las credenciales OAuth estén correctamente configuradas
- Verifica que el Package Name coincida con el configurado en Google Cloud Console

**Error: "Permission denied"**
- Verifica que hayas habilitado Google Sheets API
- Verifica que los scopes estén correctos

---

## 📚 Referencias

- [Google Sheets API Documentation](https://developers.google.com/sheets/api)
- [OAuth 2.0 for Mobile Apps](https://developers.google.com/identity/protocols/oauth2/native-app)
- [Google Cloud Console](https://console.cloud.google.com/)

---

## ✅ Checklist de Configuración

- [ ] Google Sheets API habilitada en Google Cloud Console
- [ ] Credenciales OAuth 2.0 creadas (tipo Android)
- [ ] Package name configurado: `com.flet.justice_driven_task_power`
- [ ] SHA-1 configurado correctamente
- [ ] Archivo `credenciales_android.json` en la raíz del proyecto
- [ ] Dependencias instaladas: `pip install -r requirements.txt`
- [ ] Probar exportación a Google Sheets
- [ ] Probar importación desde Google Sheets
