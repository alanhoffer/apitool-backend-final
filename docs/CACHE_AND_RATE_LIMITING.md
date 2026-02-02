# Documentación de Caché y Rate Limiting

## 🚦 Rate Limiting

### Configuración

El rate limiting está configurado con límites diferentes por endpoint:

- **`/auth/login`**: 5 requests por minuto
- **`/auth/register`**: 3 requests por minuto
- **`/auth/*`** (otros endpoints de auth): 10 requests por minuto
- **Default**: 100 requests por minuto

### Headers de Respuesta

Cada respuesta incluye headers de rate limiting:

- `X-RateLimit-Limit`: Límite máximo de requests
- `X-RateLimit-Remaining`: Requests restantes en la ventana actual
- `X-RateLimit-Reset`: Timestamp de cuando se reinicia la ventana

### Respuesta 429 Too Many Requests

Cuando se excede el límite, se retorna:

```json
{
  "detail": "Rate limit exceeded. Maximum X requests per Y seconds.",
  "retry_after": 45
}
```

Con headers:
- `Retry-After`: Segundos hasta que se puede hacer otro request

### Identificación de Clientes

El rate limiting identifica clientes por:
- **IP address** para usuarios no autenticados
- **User ID** para usuarios autenticados (más preciso)

### Notas de Producción

- El rate limiting actual usa memoria local (no distribuido)
- Para producción con múltiples servidores, considerar usar Redis
- Los contadores se limpian automáticamente cada 5 minutos

---

## 💾 Sistema de Caché

### Endpoints con Caché

#### Weather Service
- **TTL**: 10 minutos (600 segundos)
- **Clave**: Basada en latitud y longitud
- **Razón**: Los datos del clima no cambian frecuentemente

#### Recommendations Service
- **TTL**: 1 hora (3600 segundos)
- **Clave**: Basada en hemisferio
- **Razón**: Las recomendaciones estacionales cambian lentamente

### Uso del Decorador @cached

```python
from app.utils.cache import cached

@cached(ttl=600, key_prefix="weather")
async def get_weather(lat: float, lon: float):
    # Esta función se cachea automáticamente
    return weather_data
```

### Gestión del Caché

#### GET /cache/stats
Obtiene estadísticas del caché:

```json
{
  "cache": {
    "size": 15,
    "hits": 234,
    "misses": 12,
    "hit_rate": 95.12
  },
  "message": "Cache statistics"
}
```

#### DELETE /cache
Limpia todo el caché (requiere autenticación).

#### POST /cache/cleanup
Limpia solo entradas expiradas (requiere autenticación).

### Características

- **TTL (Time To Live)**: Cada entrada tiene un tiempo de expiración
- **Limpieza automática**: Las entradas expiradas se eliminan automáticamente
- **Claves basadas en hash**: Las claves se generan automáticamente desde los argumentos
- **Thread-safe**: Seguro para uso concurrente

### Notas de Producción

- El caché actual es en memoria (no distribuido)
- Para producción con múltiples servidores, considerar usar Redis
- El caché se limpia automáticamente, pero también se puede limpiar manualmente
- Estadísticas disponibles para monitoreo

---

## 🔍 Request ID Tracking

### Header X-Request-ID

Cada request recibe un ID único que se incluye en:
- **Header de respuesta**: `X-Request-ID`
- **Logs**: Todos los logs incluyen el `request_id`
- **Métricas**: El request_id está disponible en el contexto

### Uso

El cliente puede enviar su propio Request ID:

```bash
curl -H "X-Request-ID: my-custom-id" http://api.example.com/endpoint
```

Si no se envía, se genera automáticamente un UUID v4.

### Beneficios

- **Trazabilidad**: Seguir un request a través de múltiples servicios
- **Debugging**: Correlacionar logs y errores
- **Monitoreo**: Identificar requests problemáticos

### Ejemplo de Log

```json
{
  "timestamp": "2024-01-28T10:30:45.123456",
  "level": "INFO",
  "logger": "app.services.weather_service",
  "message": "Weather data retrieved",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "module": "weather_service",
  "function": "get_weather"
}
```

---

## 📊 Monitoreo

### Métricas de Rate Limiting

Las métricas de rate limiting se pueden monitorear a través de:
- Logs cuando se excede el límite
- Headers en las respuestas
- Métricas Prometheus (si se implementan)

### Métricas de Caché

Las estadísticas del caché están disponibles en:
- Endpoint `/cache/stats`
- Métricas Prometheus (si se implementan)

### Recomendaciones

1. **Monitorear hit rate**: Un hit rate bajo indica que el caché no es efectivo
2. **Monitorear rate limit hits**: Muchos 429 indican límites muy restrictivos
3. **Ajustar TTLs**: Basado en qué tan frecuentemente cambian los datos
4. **Ajustar límites**: Basado en patrones de uso reales

---

## 🔧 Configuración Futura

### Redis para Rate Limiting

Para producción distribuida:

```python
from redis import Redis
redis_client = Redis(host='localhost', port=6379)

# Usar Redis para almacenar contadores
```

### Redis para Caché

Para producción distribuida:

```python
import redis
from app.utils.cache import cached

# Usar Redis como backend de caché
redis_cache = redis.Redis(host='localhost', port=6379)
```

### Configuración desde Variables de Entorno

Agregar a `.env`:

```env
# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_DEFAULT=100
RATE_LIMIT_AUTH_LOGIN=5
RATE_LIMIT_AUTH_REGISTER=3

# Cache
CACHE_ENABLED=true
CACHE_WEATHER_TTL=600
CACHE_RECOMMENDATIONS_TTL=3600
```


