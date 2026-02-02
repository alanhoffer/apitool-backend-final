# Guía de Migración del Frontend

## 🚀 Cambios Mínimos Requeridos

### 1. Agregar Manejo de Error 429 (CRÍTICO)

**Ubicación:** Interceptor de axios/fetch

```typescript
// Antes
axios.interceptors.response.use(
  response => response,
  error => {
    if (error.response?.status === 401) {
      // Manejar no autorizado
    }
    return Promise.reject(error);
  }
);

// Después - Agregar caso 429
axios.interceptors.response.use(
  response => response,
  error => {
    if (error.response?.status === 401) {
      // Manejar no autorizado
    }
    if (error.response?.status === 429) {
      const retryAfter = error.response.data?.retry_after || 60;
      Alert.alert(
        'Demasiadas solicitudes',
        `Por favor espera ${retryAfter} segundos antes de intentar nuevamente.`
      );
    }
    return Promise.reject(error);
  }
);
```

### 2. Validar Tamaño de Archivos (RECOMENDADO)

**Ubicación:** Antes de subir imágenes

```typescript
// Agregar validación antes de subir
const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB

const handleImageUpload = (file: File) => {
  if (file.size > MAX_FILE_SIZE) {
    Alert.alert('Error', 'La imagen no puede ser mayor a 10MB');
    return;
  }
  // Continuar con upload...
};
```

### 3. Validar Valores Negativos (RECOMENDADO)

**Ubicación:** Formularios de apiarios

```typescript
// Validar antes de enviar
const validateApiaryForm = (data) => {
  if (data.hives < 0) {
    return 'El número de colmenas no puede ser negativo';
  }
  if (data.box < 0) {
    return 'El número de alzas no puede ser negativo';
  }
  // ... más validaciones
  return null; // Sin errores
};
```

## 📋 Cambios por Tipo de Frontend

### React Native

```typescript
// utils/api.ts
import axios from 'axios';
import { Alert } from 'react-native';

axios.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error.response?.status;
    
    if (status === 429) {
      const retryAfter = error.response.data?.retry_after || 60;
      Alert.alert(
        'Demasiadas solicitudes',
        `Espera ${retryAfter} segundos antes de intentar nuevamente.`
      );
    }
    
    if (status === 413) {
      Alert.alert('Error', 'El archivo es demasiado grande. Máximo 10MB.');
    }
    
    return Promise.reject(error);
  }
);
```

### React Web

```typescript
// utils/api.ts
import axios from 'axios';
import { toast } from 'react-toastify'; // o tu librería de notificaciones

axios.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error.response?.status;
    
    if (status === 429) {
      const retryAfter = error.response.data?.retry_after || 60;
      toast.error(`Demasiadas solicitudes. Espera ${retryAfter} segundos.`);
    }
    
    if (status === 413) {
      toast.error('El archivo es demasiado grande. Máximo 10MB.');
    }
    
    return Promise.reject(error);
  }
);
```

## ✅ Testing Recomendado

1. **Test de Rate Limiting:**
   - Hacer 6 requests rápidos a `/auth/login`
   - Verificar que el 6to retorne 429

2. **Test de Tamaño de Archivo:**
   - Intentar subir archivo > 10MB
   - Verificar que muestre error apropiado

3. **Test de Validaciones:**
   - Intentar crear apiario con `hives: -1`
   - Verificar que muestre error de validación

## 🔄 Compatibilidad

**✅ Compatible hacia atrás:** Los endpoints existentes funcionan igual. Solo necesitas agregar manejo para los nuevos códigos de error.

**⚠️ Breaking Changes:** Ninguno. Todos los cambios son aditivos.


