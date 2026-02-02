# API de Dispositivos - ApiTool

## Descripción General

El sistema de dispositivos permite registrar y gestionar todos los dispositivos desde los cuales un usuario accede a la aplicación. Esto incluye información detallada del dispositivo, sistema operativo, versión de la app, y tokens de push notifications.

## Información Capturada

El frontend captura automáticamente la siguiente información del dispositivo:

- **deviceName**: Nombre del dispositivo (ej: "iPhone 13 Pro", "Samsung Galaxy S21")
- **modelName**: Modelo específico del dispositivo
- **brand**: Marca del dispositivo (ej: "Apple", "Samsung")
- **manufacturer**: Fabricante del dispositivo
- **platform**: Plataforma ("ios" o "android")
- **osVersion**: Versión del sistema operativo
- **deviceType**: Tipo de dispositivo ("PHONE", "TABLET", "DESKTOP", etc.)
- **appVersion**: Versión de la aplicación
- **buildVersion**: Número de build de la aplicación
- **pushToken**: Token de push notifications (opcional)

## Endpoints

### 1. Registrar/Actualizar Dispositivo

**Endpoint:** `POST /users/devices` o `PUT /users/devices`

**Descripción:** Registra o actualiza la información del dispositivo del usuario. Se llama automáticamente después del login y registro, y también cuando se registra un push token.

**Request Body:**
```json
{
  "deviceName": "iPhone 13 Pro",
  "modelName": "iPhone14,2",
  "brand": "Apple",
  "manufacturer": "Apple",
  "platform": "ios",
  "osVersion": "17.0",
  "deviceType": "PHONE",
  "appVersion": "1.0.0",
  "buildVersion": "2",
  "pushToken": "ExponentPushToken[xxxxx]"
}
```

**Estructura de la Request:**
- `deviceName` (string, **requerido**): Nombre del dispositivo
- `modelName` (string, opcional): Modelo específico del dispositivo
- `brand` (string, opcional): Marca del dispositivo
- `manufacturer` (string, opcional): Fabricante del dispositivo
- `platform` (string, **requerido**): Plataforma ("ios" o "android")
- `osVersion` (string, opcional): Versión del sistema operativo
- `deviceType` (string, opcional): Tipo de dispositivo ("PHONE", "TABLET", "DESKTOP", etc.)
- `appVersion` (string, opcional): Versión de la aplicación
- `buildVersion` (string, opcional): Número de build de la aplicación
- `pushToken` (string, opcional): Token de push notifications

**Respuesta Esperada:**
```json
{
  "id": 1,
  "deviceName": "iPhone 13 Pro",
  "modelName": "iPhone14,2",
  "brand": "Apple",
  "manufacturer": "Apple",
  "platform": "ios",
  "osVersion": "17.0",
  "deviceType": "PHONE",
  "appVersion": "1.0.0",
  "buildVersion": "2",
  "pushToken": "ExponentPushToken[xxxxx]",
  "lastActive": "2024-01-15T10:30:00Z",
  "createdAt": "2024-01-10T08:00:00Z"
}
```

**Status Codes:**
- `200` o `201`: Dispositivo registrado/actualizado exitosamente
- `409`: Dispositivo ya existe (en caso de POST, el frontend intentará PUT)
- `400`: Datos inválidos
- `401`: No autenticado

**Comportamiento:**
- Si el dispositivo ya existe (identificado por `deviceName` y `platform`), se actualiza con la nueva información
- El campo `lastActive` se actualiza automáticamente en cada login
- El `pushToken` se puede actualizar cuando el usuario registra notificaciones push
- Si se envía `POST` y el dispositivo existe, el backend puede retornar `409` y el frontend intentará `PUT`

**Cuándo se llama:**
1. Automáticamente después de un login exitoso
2. Automáticamente después de un registro exitoso
3. Cuando se registra un push token para notificaciones

---

### 2. Obtener Dispositivos del Usuario

**Endpoint:** `GET /users/devices`

**Descripción:** Retorna todos los dispositivos registrados del usuario actual.

**Headers:**
- `Authorization: Bearer {token}` (requerido)

**Respuesta Esperada:**
```json
{
  "devices": [
    {
      "id": 1,
      "deviceName": "iPhone 13 Pro",
      "modelName": "iPhone14,2",
      "brand": "Apple",
      "manufacturer": "Apple",
      "platform": "ios",
      "osVersion": "17.0",
      "deviceType": "PHONE",
      "appVersion": "1.0.0",
      "buildVersion": "2",
      "pushToken": "ExponentPushToken[xxxxx]",
      "lastActive": "2024-01-15T10:30:00Z",
      "createdAt": "2024-01-10T08:00:00Z"
    },
    {
      "id": 2,
      "deviceName": "Samsung Galaxy S21",
      "modelName": "SM-G991B",
      "brand": "Samsung",
      "manufacturer": "Samsung",
      "platform": "android",
      "osVersion": "13",
      "deviceType": "PHONE",
      "appVersion": "1.0.0",
      "buildVersion": "2",
      "pushToken": null,
      "lastActive": "2024-01-14T15:20:00Z",
      "createdAt": "2024-01-12T09:00:00Z"
    }
  ]
}
```

**Status Codes:**
- `200`: Lista de dispositivos obtenida exitosamente
- `401`: No autenticado

**Nota:** Este endpoint ya existe y se usa en `DevicesScreen` para mostrar los dispositivos del usuario.

---

### 3. Eliminar Dispositivo

**Endpoint:** `DELETE /users/devices/:id`

**Descripción:** Elimina un dispositivo del usuario.

**Headers:**
- `Authorization: Bearer {token}` (requerido)

**Parámetros:**
- `id` (number, requerido): ID del dispositivo a eliminar

**Respuesta Esperada:**
```json
{
  "message": "Dispositivo eliminado exitosamente"
}
```

**Status Codes:**
- `200` o `204`: Dispositivo eliminado exitosamente
- `404`: Dispositivo no encontrado
- `403`: No autorizado (intentar eliminar dispositivo de otro usuario)
- `401`: No autenticado

**Nota:** Este endpoint ya existe y se usa en `DevicesScreen` para eliminar dispositivos.

---

## Implementación en el Backend

### Modelo de Datos Sugerido

```typescript
interface Device {
  id: number;
  userId: number; // Foreign key al usuario
  deviceName: string;
  modelName?: string | null;
  brand?: string | null;
  manufacturer?: string | null;
  platform: string; // 'ios' | 'android'
  osVersion?: string | null;
  deviceType?: string | null; // 'PHONE' | 'TABLET' | 'DESKTOP'
  appVersion?: string | null;
  buildVersion?: string | null;
  pushToken?: string | null;
  lastActive: Date;
  createdAt: Date;
  updatedAt: Date;
}
```

### Lógica de Registro/Actualización

1. **POST /users/devices**:
   - Buscar si existe un dispositivo con el mismo `deviceName` y `platform` para el usuario
   - Si existe, actualizar con la nueva información y retornar `200`
   - Si no existe, crear uno nuevo y retornar `201`
   - Actualizar `lastActive` a la fecha/hora actual

2. **PUT /users/devices**:
   - Buscar dispositivo por `deviceName` y `platform` del usuario actual
   - Si existe, actualizar todos los campos enviados
   - Si no existe, crear uno nuevo
   - Actualizar `lastActive` a la fecha/hora actual

### Consideraciones de Seguridad

- Verificar que el usuario esté autenticado en todos los endpoints
- Asegurar que un usuario solo pueda ver/eliminar sus propios dispositivos
- Validar que `platform` sea solo "ios" o "android"
- Sanitizar todos los campos de texto para evitar inyección de datos

### Actualización de `lastActive`

El campo `lastActive` debe actualizarse automáticamente:
- Cada vez que el usuario hace login (si el dispositivo ya está registrado)
- Cada vez que se actualiza el dispositivo (POST o PUT)

---

## Información del Usuario

Además de la información del dispositivo, el frontend también puede enviar información adicional del usuario en el futuro:

### Información Actualmente Disponible
- Email (ya se envía en login/register)
- Token de autenticación

### Información Adicional Sugerida (Futuro)
- Última ubicación conocida (opcional, con permisos)
- Preferencias de notificaciones
- Configuración de la app
- Estadísticas de uso

---

## Notas de Implementación

1. **Registro Automático**: El dispositivo se registra automáticamente después del login/registro, sin intervención del usuario.

2. **Actualización de Push Token**: Cuando el usuario registra notificaciones push, el `pushToken` se actualiza automáticamente en el dispositivo.

3. **Manejo de Errores**: Si el registro del dispositivo falla, no debe interrumpir el flujo de login/registro. El error se registra pero el usuario puede continuar usando la app.

4. **Identificación de Dispositivos**: Los dispositivos se identifican por la combinación de `deviceName` + `platform` + `userId`. Si un usuario tiene el mismo modelo de dispositivo en diferentes plataformas, se consideran dispositivos diferentes.

5. **Limpieza de Dispositivos**: Se recomienda implementar una tarea periódica en el backend para eliminar dispositivos inactivos (por ejemplo, sin actividad por más de 90 días).

