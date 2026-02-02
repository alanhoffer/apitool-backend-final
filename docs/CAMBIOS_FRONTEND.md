# Cambios Necesarios en el Frontend

## 📋 Resumen

La mayoría de los cambios son **transparentes** para el frontend, pero hay algunos **nuevos códigos de error** que deberías manejar para mejorar la experiencia del usuario.

## ✅ Cambios que NO Requieren Acción

Estos cambios son transparentes y no requieren cambios en el frontend:

- ✅ **Request ID**: Se envía automáticamente en header `X-Request-ID` (opcional leerlo)
- ✅ **Headers de seguridad**: No afectan al frontend
- ✅ **Caché**: Mejora performance pero es transparente
- ✅ **Métricas**: No afectan al frontend
- ✅ **Timezone UTC**: Las fechas se manejan igual, solo internamente en UTC
- ✅ **Validaciones mejoradas**: Los errores siguen siendo los mismos, solo más específicos

## ⚠️ Cambios que SÍ Requieren Acción

### 1. Manejo de Rate Limiting (429 Too Many Requests)

**Nuevo código de error:** `429`

El backend ahora puede retornar `429` cuando se exceden los límites de requests.

**Respuesta del servidor:**
```json
{
  "detail": "Rate limit exceeded. Maximum 5 requests per 60 seconds.",
  "retry_after": 45
}
```

**Headers incluidos:**
- `X-RateLimit-Limit`: Límite máximo
- `X-RateLimit-Remaining`: Requests restantes
- `X-RateLimit-Reset`: Timestamp de reset
- `Retry-After`: Segundos hasta poder hacer otro request

**Implementación recomendada:**

```typescript
// En tu interceptor de axios/fetch
axios.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 429) {
      const retryAfter = error.response.headers['retry-after'] || 
                        error.response.data?.retry_after || 
                        60;
      
      // Mostrar mensaje al usuario
      showError(
        `Demasiadas solicitudes. Por favor espera ${retryAfter} segundos.`
      );
      
      // Opcional: Implementar retry automático
      // return new Promise(resolve => {
      //   setTimeout(() => resolve(axios.request(error.config)), retryAfter * 1000);
      // });
    }
    return Promise.reject(error);
  }
);
```

**Límites actuales:**
- `/auth/login`: 5 requests/minuto
- `/auth/register`: 3 requests/minuto
- Otros endpoints: 100 requests/minuto

### 2. Manejo de Request Too Large (413 Request Entity Too Large)

**Nuevo código de error:** `413`

El backend rechaza requests mayores a 10MB.

**Respuesta del servidor:**
```json
{
  "detail": "Request body too large. Maximum size is 10MB"
}
```

**Implementación recomendada:**

```typescript
// Validar tamaño antes de enviar
const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB

function validateFileSize(file: File): boolean {
  if (file.size > MAX_FILE_SIZE) {
    showError('El archivo es demasiado grande. Máximo 10MB.');
    return false;
  }
  return true;
}

// En interceptor
axios.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 413) {
      showError('El archivo o datos enviados son demasiado grandes. Máximo 10MB.');
    }
    return Promise.reject(error);
  }
);
```

### 3. Validaciones Más Estrictas

**Cambio:** Los errores de validación ahora son más específicos.

**Antes:** Podías enviar valores negativos y recibir error genérico
**Ahora:** Recibirás errores específicos como:
- `"hives" must be greater than or equal to 0`
- `"name" must have at least 1 character`

**Implementación recomendada:**

```typescript
// Mejorar mensajes de error de validación
function handleValidationError(error: AxiosError) {
  if (error.response?.status === 422) {
    const errors = error.response.data?.detail || [];
    
    // Si es array de errores (FastAPI validation)
    if (Array.isArray(errors)) {
      errors.forEach(err => {
        const field = err.loc?.[err.loc.length - 1];
        const message = err.msg;
        showFieldError(field, message);
      });
    } else {
      // Error simple
      showError(errors);
    }
  }
}
```

**Campos que ahora tienen validaciones más estrictas:**
- `hives`: Debe ser >= 0
- `box`, `boxMedium`, `boxSmall`: Deben ser >= 0
- `honey`, `levudex`, `sugar`: Deben ser >= 0
- `name`: Debe tener al menos 1 carácter
- `tComment`: Máximo 1000 caracteres

### 4. Headers de Rate Limit (Opcional pero Recomendado)

Puedes leer los headers de rate limit para mostrar información al usuario:

```typescript
// Ejemplo: Mostrar cuántos requests quedan
function checkRateLimit(response: AxiosResponse) {
  const remaining = response.headers['x-ratelimit-remaining'];
  const limit = response.headers['x-ratelimit-limit'];
  
  if (remaining && parseInt(remaining) < 10) {
    console.warn(`Quedan ${remaining} requests de ${limit}`);
    // Opcional: Mostrar advertencia al usuario
  }
}
```

## 📝 Ejemplo Completo de Manejo de Errores

```typescript
// utils/apiErrorHandler.ts
import { AxiosError, AxiosResponse } from 'axios';

export function handleApiError(error: AxiosError) {
  if (!error.response) {
    // Error de red
    return {
      message: 'Error de conexión. Verifica tu internet.',
      type: 'network'
    };
  }

  const { status, data, headers } = error.response;

  switch (status) {
    case 400:
      return {
        message: data?.detail || 'Solicitud inválida',
        type: 'bad_request',
        data
      };

    case 401:
      return {
        message: 'Sesión expirada. Por favor inicia sesión nuevamente.',
        type: 'unauthorized',
        // Opcional: Redirigir a login
        redirect: '/login'
      };

    case 403:
      return {
        message: 'No tienes permisos para esta acción',
        type: 'forbidden'
      };

    case 404:
      return {
        message: 'Recurso no encontrado',
        type: 'not_found'
      };

    case 413:
      return {
        message: 'El archivo o datos son demasiado grandes. Máximo 10MB.',
        type: 'too_large'
      };

    case 422:
      // Errores de validación
      const validationErrors = Array.isArray(data?.detail) 
        ? data.detail 
        : [{ msg: data?.detail || 'Error de validación' }];
      
      return {
        message: 'Datos inválidos',
        type: 'validation',
        errors: validationErrors
      };

    case 429:
      const retryAfter = headers['retry-after'] || data?.retry_after || 60;
      return {
        message: `Demasiadas solicitudes. Espera ${retryAfter} segundos.`,
        type: 'rate_limit',
        retryAfter: parseInt(retryAfter)
      };

    case 500:
    case 502:
    case 503:
    case 504:
      return {
        message: 'Error del servidor. Por favor intenta más tarde.',
        type: 'server_error'
      };

    default:
      return {
        message: data?.detail || 'Error desconocido',
        type: 'unknown',
        status
      };
  }
}

// Uso en interceptor
axios.interceptors.response.use(
  (response: AxiosResponse) => {
    // Opcional: Log request ID para debugging
    const requestId = response.headers['x-request-id'];
    if (requestId) {
      console.debug('Request ID:', requestId);
    }
    return response;
  },
  (error: AxiosError) => {
    const errorInfo = handleApiError(error);
    
    // Mostrar error al usuario
    showError(errorInfo.message);
    
    // Manejar casos especiales
    if (errorInfo.type === 'unauthorized' && errorInfo.redirect) {
      // Redirigir a login
      router.push(errorInfo.redirect);
    }
    
    if (errorInfo.type === 'rate_limit') {
      // Opcional: Implementar retry después de retryAfter
      // setTimeout(() => retryRequest(error.config), errorInfo.retryAfter * 1000);
    }
    
    return Promise.reject(error);
  }
);
```

## 🔍 Validación en el Frontend (Recomendado)

Para mejorar UX, valida antes de enviar:

```typescript
// Validaciones antes de enviar
function validateApiaryData(data: CreateApiaryData): ValidationResult {
  const errors: string[] = [];

  if (!data.name || data.name.trim().length === 0) {
    errors.push('El nombre es requerido');
  }

  if (data.hives < 0) {
    errors.push('El número de colmenas no puede ser negativo');
  }

  if (data.box !== undefined && data.box < 0) {
    errors.push('El número de alzas no puede ser negativo');
  }

  // Validar tamaño de archivo
  if (data.imageFile && data.imageFile.size > 10 * 1024 * 1024) {
    errors.push('La imagen no puede ser mayor a 10MB');
  }

  return {
    isValid: errors.length === 0,
    errors
  };
}
```

## 📊 Resumen de Códigos de Error

| Código | Significado | Acción Recomendada |
|--------|-------------|-------------------|
| 400 | Bad Request | Mostrar mensaje de error |
| 401 | Unauthorized | Redirigir a login |
| 403 | Forbidden | Mostrar mensaje de permisos |
| 404 | Not Found | Mostrar "no encontrado" |
| 413 | Request Too Large | Validar tamaño antes de enviar |
| 422 | Validation Error | Mostrar errores de campo |
| 429 | Too Many Requests | Mostrar mensaje y esperar |
| 500+ | Server Error | Mostrar mensaje genérico |

## ✅ Checklist para el Frontend

- [ ] Agregar manejo de error 429 (Rate Limiting)
- [ ] Agregar manejo de error 413 (Request Too Large)
- [ ] Mejorar mensajes de error de validación (422)
- [ ] Validar datos antes de enviar (valores negativos, tamaño de archivos)
- [ ] (Opcional) Leer y mostrar headers de rate limit
- [ ] (Opcional) Leer Request ID para debugging

## 🎯 Prioridad

**ALTA:**
1. Manejo de error 429
2. Validación de tamaño de archivos antes de enviar

**MEDIA:**
3. Mejores mensajes de error de validación
4. Validación de valores negativos en frontend

**BAJA:**
5. Mostrar información de rate limit
6. Usar Request ID para debugging

---

**Nota:** La mayoría de los cambios son compatibles hacia atrás. Solo necesitas agregar manejo para los nuevos códigos de error para mejorar la experiencia del usuario.


