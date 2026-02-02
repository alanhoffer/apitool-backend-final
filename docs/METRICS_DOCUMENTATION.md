# Documentación de Métricas y Monitoreo

## Endpoints de Métricas

### GET /metrics
Endpoint de métricas Prometheus. Expone todas las métricas en formato Prometheus estándar.

**Uso:**
```bash
curl http://localhost:8000/metrics
```

**Respuesta:**
Formato Prometheus estándar con todas las métricas disponibles.

## Métricas HTTP

### http_requests_total
Contador de requests HTTP totales.

**Labels:**
- `method`: Método HTTP (GET, POST, PUT, DELETE, etc.)
- `endpoint`: Endpoint normalizado (ej: `/apiarys/{id}`)
- `status_code`: Código de estado HTTP (200, 404, 500, etc.)

**Ejemplo:**
```
http_requests_total{method="GET",endpoint="/apiarys",status_code="200"} 150
```

### http_request_duration_seconds
Histograma de duración de requests HTTP.

**Labels:**
- `method`: Método HTTP
- `endpoint`: Endpoint normalizado

**Buckets:** 0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0 segundos

### http_request_size_bytes
Histograma del tamaño de requests HTTP.

**Labels:**
- `method`: Método HTTP
- `endpoint`: Endpoint normalizado

### http_response_size_bytes
Histograma del tamaño de responses HTTP.

**Labels:**
- `method`: Método HTTP
- `endpoint`: Endpoint normalizado

### http_active_requests
Gauge del número de requests HTTP activos.

**Labels:**
- `method`: Método HTTP
- `endpoint`: Endpoint normalizado

### http_errors_total
Contador de errores HTTP.

**Labels:**
- `method`: Método HTTP
- `endpoint`: Endpoint normalizado
- `error_type`: Tipo de error (`client_error`, `server_error`, `exception`)

## Métricas de Negocio

### Usuarios

#### users_total
Número total de usuarios en el sistema.

#### users_active
Número de usuarios activos (con actividad reciente).

### Apiarios

#### apiaries_total
Número total de apiarios.

#### apiaries_per_user
Histograma del número de apiarios por usuario.

#### hives_total
Número total de colmenas en todos los apiarios.

### Cosecha

#### harvested_boxes_total
Contador de alzas cosechadas.

**Labels:**
- `box_type`: Tipo de alza (`box`, `boxMedium`, `boxSmall`)

#### harvested_apiaries_count
Número de apiarios con alzas cosechadas.

### Notificaciones

#### notifications_sent_total
Contador de notificaciones enviadas.

**Labels:**
- `notification_type`: Tipo de notificación
- `status`: Estado (`success`, `failed`)

#### notifications_pending
Número de notificaciones pendientes.

### Dispositivos

#### devices_total
Número total de dispositivos registrados.

#### devices_by_platform
Número de dispositivos por plataforma.

**Labels:**
- `platform`: Plataforma (`ios`, `android`)

### Base de Datos

#### db_connections_active
Número de conexiones activas a la base de datos.

#### db_query_duration_seconds
Histograma de duración de queries a la base de datos.

**Labels:**
- `operation`: Tipo de operación (`select`, `insert`, `update`, `delete`)

#### db_errors_total
Contador de errores de base de datos.

**Labels:**
- `error_type`: Tipo de error

### Tareas Programadas (Cron)

#### cron_jobs_executed_total
Contador de tareas cron ejecutadas.

**Labels:**
- `job_name`: Nombre de la tarea
- `status`: Estado (`success`, `failed`)

#### cron_job_duration_seconds
Histograma de duración de ejecución de tareas cron.

**Labels:**
- `job_name`: Nombre de la tarea

## Configuración de Logging

### Variables de Entorno

- `LOG_LEVEL`: Nivel de logging (DEBUG, INFO, WARNING, ERROR, CRITICAL). Default: `INFO`
- `JSON_LOGGING`: Si se debe usar formato JSON estructurado (`true`/`false`). Default: `false`

### Ejemplo de configuración en .env

```env
LOG_LEVEL=INFO
JSON_LOGGING=false
```

### Formato de Logs

#### Formato estándar (JSON_LOGGING=false)
```
2024-01-28 10:30:45 - app.main - INFO - Database tables created/verified successfully
```

#### Formato JSON estructurado (JSON_LOGGING=true)
```json
{
  "timestamp": "2024-01-28T10:30:45.123456",
  "level": "INFO",
  "logger": "app.main",
  "message": "Database tables created/verified successfully",
  "module": "main",
  "function": "lifespan",
  "line": 25
}
```

## Integración con Prometheus

### Configuración de Prometheus

Agrega esta configuración a tu `prometheus.yml`:

```yaml
scrape_configs:
  - job_name: 'apitool-api'
    scrape_interval: 15s
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
```

### Grafana Dashboards

Puedes crear dashboards en Grafana usando las métricas expuestas. Ejemplos de queries útiles:

**Requests por segundo:**
```
rate(http_requests_total[5m])
```

**Latencia promedio (p95):**
```
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))
```

**Tasa de errores:**
```
rate(http_errors_total[5m]) / rate(http_requests_total[5m])
```

**Requests activos:**
```
http_active_requests
```

## Alertas Recomendadas

### Alta tasa de errores
```yaml
- alert: HighErrorRate
  expr: rate(http_errors_total[5m]) > 0.1
  for: 5m
  annotations:
    summary: "Alta tasa de errores HTTP"
```

### Latencia alta
```yaml
- alert: HighLatency
  expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 1
  for: 5m
  annotations:
    summary: "Latencia p95 mayor a 1 segundo"
```

### Base de datos desconectada
```yaml
- alert: DatabaseDown
  expr: up{job="apitool-api"} == 0
  for: 1m
  annotations:
    summary: "API no responde"
```

## Monitoreo de Performance

### Métricas Clave a Monitorear

1. **Throughput**: `rate(http_requests_total[5m])`
2. **Latencia**: `histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))`
3. **Tasa de errores**: `rate(http_errors_total[5m]) / rate(http_requests_total[5m])`
4. **Requests activos**: `http_active_requests`
5. **Tamaño de requests/responses**: `http_request_size_bytes`, `http_response_size_bytes`

### Métricas de Negocio

1. **Crecimiento de usuarios**: `users_total`
2. **Actividad de usuarios**: `users_active`
3. **Cosecha**: `harvested_boxes_total`
4. **Notificaciones**: `notifications_sent_total`, `notifications_pending`
5. **Dispositivos**: `devices_total`, `devices_by_platform`

## Normalización de Paths

Los paths se normalizan automáticamente para evitar cardinalidad alta en las métricas:

- `/apiarys/123` → `/apiarys/{id}`
- `/users/456` → `/users/{id}`
- `/drums/789` → `/drums/{id}`
- `/apiarys/123/history` → `/apiarys/{id}/history`

Esto permite agrupar métricas por endpoint sin crear una serie de tiempo por cada ID único.


