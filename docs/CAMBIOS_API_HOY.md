# Documentación de Cambios en la API - ApiTool

## 1. Actualización de `createApiary` y `updateApiary`

**Endpoint:** `POST /apiarys` y `PUT /apiarys/:id`

### Cambios Requeridos en Backend:
El backend debe aceptar y procesar dos nuevos campos numéricos opcionales:
- `latitude` (Float/Double)
- `longitude` (Float/Double)

Si el backend usa un ORM (como TypeORM o Sequelize), actualizar el modelo `Apiary` para incluir:
```typescript
@Column({ type: 'float', nullable: true })
latitude: number;

@Column({ type: 'float', nullable: true })
longitude: number;
```

## 2. Actualización de `ApiarySettings`

**Endpoint:** `PUT /apiarys/settings/:id`

### Cambios Requeridos en Backend:
El backend debe permitir guardar un campo de texto largo (JSON string) llamado `tasks` en la tabla/entidad `ApiarySettings`.

Si el backend usa un ORM:
```typescript
@Column({ type: 'text', nullable: true }) // O 'longtext' si se espera mucho contenido
tasks: string;
```

Este campo almacenará un array de objetos JSON con la estructura:
```json
[
  {
    "id": "1715628392",
    "text": "Llevar alzas",
    "completed": false
  },
  ...
]
```

## 3. Consideraciones de Seguridad
Asegurarse de sanear el input del campo `tasks` si se renderiza en algún panel web administrativo para evitar XSS, aunque en la app móvil se maneja como texto plano.

## 4. Endpoints de Estadísticas de Cosecha

### 4.1. Estadísticas Agregadas de Cosecha

**Endpoint:** `GET /apiarys/harvested/stats`

**Descripción:** Retorna las estadísticas agregadas (totales acumulados) de todas las alzas cosechadas de todos los apiarios.

**Respuesta Esperada:**
```json
{
  "box": 150,
  "boxMedium": 75,
  "boxSmall": 30,
  "total": 255
}
```

**Estructura de la Respuesta:**
- `box` (number, requerido): Total acumulado de alzas completas cosechadas
- `boxMedium` (number, requerido): Total acumulado de alzas 3/4 cosechadas
- `boxSmall` (number, requerido): Total acumulado de alzas 1/2 cosechadas
- `total` (number, opcional): Total calculado (suma de box + boxMedium + boxSmall)

**Nota:** El frontend usa estos valores para mostrar los totales en la sección "Cosecha" de las estadísticas. Si el endpoint retorna `null` o no está disponible (404), el frontend calculará los totales desde los datos individuales de cada apiario como fallback.

---

### 4.2. Cantidad de Apiarios en Cosecha

**Endpoint:** `GET /apiarys/harvesting/count`

**Descripción:** Retorna la cantidad de apiarios que están actualmente en modo cosecha (con `harvesting: true`).

**Respuesta Esperada:**
```json
{
  "harvestingCount": 12
}
```

**Estructura de la Respuesta:**
- `harvestingCount` (number, requerido): Cantidad de apiarios con `settings.harvesting === true`

**Nota:** Si el endpoint no está disponible (404), el frontend calculará este valor desde los datos individuales de cada apiario como fallback.

---

### 4.3. Cantidad de Apiarios con Alzas Cosechadas

**Endpoint:** `GET /apiarys/harvested/count`

**Descripción:** Retorna la cantidad de apiarios que tienen alzas cosechadas (es decir, apiarios que tienen al menos una alza con valores > 0 en box, boxMedium o boxSmall).

**Respuesta Esperada (múltiples formatos soportados):**

**Opción 1 - Objeto con campo `count`:**
```json
{
  "count": 8
}
```

**Opción 2 - Objeto con campo `harvestedBoxesCount`:**
```json
{
  "harvestedBoxesCount": 8
}
```

**Opción 3 - Número directo:**
```json
8
```

**Estructura de la Respuesta:**
El frontend acepta cualquiera de estas tres estructuras:
- Un número directamente
- Un objeto con la propiedad `count`
- Un objeto con la propiedad `harvestedBoxesCount`

**Nota:** El frontend mostrará este valor en la sección "Cosecha" como "Cosechados" (apiarios con alzas cosechadas).

---

### 4.4. Totales de Cosecha por Apiario

**Endpoint:** `GET /apiarys/:id/harvested`

**Descripción:** Retorna los totales acumulados de cosecha para un apiario específico.

**Respuesta Esperada:**
```json
{
  "name": "Apiario Norte",
  "box": 25,
  "boxMedium": 15,
  "boxSmall": 5,
  "total": 45
}
```

**Estructura de la Respuesta:**
- `name` (string, opcional): Nombre del apiario
- `box` (number, requerido): Total acumulado de alzas completas cosechadas para este apiario
- `boxMedium` (number, requerido): Total acumulado de alzas 3/4 cosechadas para este apiario
- `boxSmall` (number, requerido): Total acumulado de alzas 1/2 cosechadas para este apiario
- `total` (number, opcional): Total calculado (suma de box + boxMedium + boxSmall)

**Nota:** Este endpoint se usa en la pantalla de detalle del apiario para mostrar los totales acumulados de cosecha. Si el endpoint no está disponible (404), el frontend usará los valores actuales del apiario.

---

### 4.5. Conteos de Apiarios y Colmenas Cosechadas (General)

**Endpoint:** `GET /apiarys/harvested/counts`

**Descripción:** Retorna la cantidad de apiarios y colmenas que tienen alzas cosechadas (datos históricos acumulados).

**Respuesta Esperada:**
```json
{
  "apiaryCount": 15,
  "hiveCount": 120
}
```

**Estructura de la Respuesta:**
- `apiaryCount` (number, requerido): Cantidad de apiarios con alzas cosechadas
- `hiveCount` (number, requerido): Cantidad de colmenas con alzas cosechadas

**Nota:** Este endpoint reemplaza al endpoint legacy `/apiarys/harvested/count` y proporciona información más completa. Si el endpoint no está disponible (404), el frontend usará el endpoint legacy como fallback.

---

### 4.6. Conteos de Apiarios y Colmenas Cosechadas Hoy

**Endpoint:** `GET /apiarys/harvested/today/counts`

**Descripción:** Retorna la cantidad de apiarios y colmenas que fueron cosechadas **hoy** (solo datos del día actual).

**Respuesta Esperada:**
```json
{
  "apiaryCount": 5,
  "hiveCount": 35
}
```

**Estructura de la Respuesta:**
- `apiaryCount` (number, requerido): Cantidad de apiarios cosechados hoy
- `hiveCount` (number, requerido): Cantidad de colmenas cosechadas hoy

**Nota:** Este endpoint se usa en la sección "Cosecha > Hoy" de las estadísticas. Si el endpoint no está disponible (404), el frontend mostrará 0 para estos valores.

---

### 4.7. Alzas Cosechadas Hoy

**Endpoint:** `GET /apiarys/harvested/today/boxes`

**Descripción:** Retorna las cantidades de alzas cosechadas **hoy** (solo datos del día actual).

**Respuesta Esperada:**
```json
{
  "box": 12,
  "boxMedium": 8,
  "boxSmall": 4,
  "total": 24
}
```

**Estructura de la Respuesta:**
- `box` (number, requerido): Cantidad de alzas completas cosechadas hoy
- `boxMedium` (number, requerido): Cantidad de alzas 3/4 cosechadas hoy
- `boxSmall` (number, requerido): Cantidad de alzas 1/2 cosechadas hoy
- `total` (number, opcional): Total calculado (suma de box + boxMedium + boxSmall)

**Nota:** Este endpoint se usa en la sección "Cosecha > Hoy" de las estadísticas. Si el endpoint no está disponible (404), el frontend mostrará 0 para estos valores.

---

## 5. Endpoints de Autenticación y Usuario

### 5.1. Recuperación de Contraseña

**Endpoint:** `POST /auth/forgot-password`

**Descripción:** Envía un email con un enlace para restablecer la contraseña del usuario.

**Request Body:**
```json
{
  "email": "usuario@example.com"
}
```

**Respuesta Esperada:**
```json
{
  "message": "Se ha enviado un enlace de recuperación a tu email"
}
```

**Status Codes:**
- `200` o `201`: Email enviado exitosamente
- `404`: Usuario no encontrado
- `400`: Email inválido

**Nota:** Este endpoint es requerido para la funcionalidad de `ForgotPasswordScreen`.

---

### 5.2. Restablecer Contraseña

**Endpoint:** `POST /auth/reset-password`

**Descripción:** Restablece la contraseña del usuario usando un token recibido por email.

**Request Body:**
```json
{
  "token": "token_recibido_por_email",
  "newPassword": "nueva_contraseña_segura"
}
```

**Respuesta Esperada:**
```json
{
  "message": "Contraseña restablecida exitosamente"
}
```

---

### 5.3. Actualizar Perfil de Usuario

**Endpoint:** `PUT /users/profile`

**Descripción:** Actualiza la información del perfil del usuario (nombre, email, etc.).

**Request Body:**
```json
{
  "name": "Nuevo Nombre",
  "email": "nuevo@email.com"
}
```

**Respuesta Esperada:**
```json
{
  "id": 1,
  "name": "Nuevo Nombre",
  "email": "nuevo@email.com",
  "updatedAt": "2024-01-15T10:30:00Z"
}
```

**Status Codes:**
- `200` o `201`: Perfil actualizado exitosamente
- `400`: Datos inválidos
- `409`: Email ya en uso (si se cambia el email)

**Nota:** Este endpoint es requerido para la funcionalidad de `EditProfileScreen`.

---

### 5.4. Cambiar Contraseña

**Endpoint:** `PUT /users/password`

**Descripción:** Cambia la contraseña del usuario autenticado.

**Request Body:**
```json
{
  "currentPassword": "contraseña_actual",
  "newPassword": "nueva_contraseña_segura"
}
```

**Respuesta Esperada:**
```json
{
  "message": "Contraseña actualizada exitosamente"
}
```

**Status Codes:**
- `200` o `201`: Contraseña actualizada exitosamente
- `400`: Contraseña actual incorrecta o nueva contraseña inválida
- `401`: No autenticado

**Nota:** Este endpoint es requerido para la funcionalidad de `ChangePasswordScreen`.

















