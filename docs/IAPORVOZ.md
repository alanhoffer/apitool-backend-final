# API de audio para el chat con IA

La app móvil (React Native) permite enviar mensajes de voz al asistente de IA. El backend debe exponer un endpoint que reciba el audio y devuelva la respuesta (texto y/o audio).

## Endpoint

| Método | Ruta        | Descripción                    |
|--------|-------------|--------------------------------|
| `POST` | `/api/audio` | Recibe un audio y devuelve la respuesta del agente. |

**URL base:** la misma que el resto de la API (ej. `https://tu-dominio.com/api/audio`).

---

## Request

### Headers

| Header            | Obligatorio | Descripción                          |
|-------------------|------------|--------------------------------------|
| `Authorization`   | Sí*        | `Bearer <token>` si la API requiere autenticación. |
| `Content-Type`    | No         | No enviar: el cliente usa `multipart/form-data` con boundary. |

\* La app envía el token JWT del usuario logueado en `Authorization` cuando existe.

### Body (multipart/form-data)

| Campo    | Tipo   | Obligatorio | Descripción |
|----------|--------|-------------|-------------|
| `audio`  | File   | Sí          | Archivo de audio. La app graba con el dispositivo (expo-av). Formatos típicos: `.m4a` (iOS), `.3gp` / `.m4a` (Android). Aceptar al menos `audio/m4a`, `audio/3gpp`, `audio/webm`. |
| `chatId` | string | No          | Identificador de la conversación para mantener contexto. La app lo envía cuando ya existe una conversación previa. |

### Ejemplo (pseudo-código backend)

```text
POST /api/audio
Authorization: Bearer <token>
Content-Type: multipart/form-data; boundary=----WebKitFormBoundary...

------WebKitFormBoundary...
Content-Disposition: form-data; name="audio"; filename="grabacion.m4a"
Content-Type: audio/m4a

<bytes del archivo>
------WebKitFormBoundary...
Content-Disposition: form-data; name="chatId"

<id_de_conversacion>
------WebKitFormBoundary...--
```

---

## Response

### Success (200 OK)

Cuerpo JSON con los campos que necesites. La app usa:

| Campo       | Tipo   | Obligatorio | Descripción |
|------------|--------|-------------|-------------|
| `text`     | string | Recomendado | Respuesta en texto. Se muestra en el chat. |
| `audio_url`| string | Opcional    | URL pública de un audio de respuesta. Si se envía, la app muestra un botón "Reproducir respuesta". |
| `chatId`   | string | Opcional    | ID de la conversación (o el mismo que enviaron). La app lo guarda para el siguiente mensaje. |

**Ejemplo mínimo (solo texto):**

```json
{
  "text": "Aquí va la respuesta del agente en texto.",
  "chatId": "conv_abc123"
}
```

**Ejemplo con respuesta de voz:**

```json
{
  "text": "Respuesta de voz",
  "audio_url": "https://tu-cdn.com/audios/respuesta-xyz.mp3",
  "chatId": "conv_abc123"
}
```

Si solo envías `audio_url` y no `text`, la app muestra igualmente "Respuesta de voz" y el botón de reproducir.

### Error (4xx / 5xx)

Cuerpo en texto o JSON. La app intenta mostrar un mensaje al usuario:

- Si el cuerpo es JSON con `message` o `error`, usa ese valor.
- Si no, usa el cuerpo como texto o un mensaje genérico.

**Ejemplo:**

```json
{
  "message": "No se pudo procesar el audio."
}
```

---

## Flujo en la app

1. El usuario pulsa el micrófono en el chat de IA.
2. La app pide permiso de micrófono y graba (expo-av).
3. Al pulsar "Detener y enviar", se sube el archivo con `POST /api/audio` (campo `audio` y opcionalmente `chatId`).
4. La app muestra en el chat:
   - Mensaje del usuario: "Mensaje de voz".
   - Respuesta del asistente: `text` y, si existe, botón para reproducir `audio_url`.
5. Si la respuesta incluye `chatId`, la app lo guarda y lo envía en las siguientes peticiones de audio (o de texto) para mantener el hilo de la conversación.

---

## Resumen para implementar en el backend

1. Crear `POST /api/audio`.
2. Aceptar `multipart/form-data` con campo obligatorio `audio` (archivo) y opcional `chatId` (string).
3. Validar autenticación con el token en `Authorization` si aplica.
4. Procesar el audio (transcripción, agente de IA, etc.) y generar respuesta en texto y/o audio.
5. Responder 200 con JSON: `{ "text": "...", "audio_url": "..." (opcional), "chatId": "..." (opcional) }`.
6. En errores, responder con código 4xx/5xx y, si es posible, cuerpo `{ "message": "..." }` o `{ "error": "..." }`.

---

## Implementación en este backend

- **Ruta:** `POST /api/audio` (requiere `Authorization: Bearer <token>`).
- **Body:** `multipart/form-data` con `audio` (archivo) y opcionalmente `chatId` (string).
- **Respuesta:** JSON con `text`, `audio_url` (opcional), `chatId` (opcional).

Para activar transcripción (Whisper) y chat (GPT), define en el servidor la variable de entorno **`OPENAI_API_KEY`**. Si no está definida, el endpoint responde con un mensaje indicando que la funcionalidad de voz no está configurada (la app puede seguir llamando al endpoint sin error).
