"""
Métricas de negocio específicas de la aplicación.
"""
import logging

logger = logging.getLogger(__name__)

try:
    from prometheus_client import Counter, Gauge, Histogram
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    # Crear objetos dummy para evitar errores
    class DummyMetric:
        def labels(self, **kwargs):
            return self
        def inc(self, value=1):
            pass
        def dec(self, value=1):
            pass
        def observe(self, value):
            pass
        def set(self, value):
            pass
    
    Counter = Gauge = Histogram = lambda *args, **kwargs: DummyMetric()
    logger.warning("Prometheus client not available. Business metrics will be disabled. Install with: pip install prometheus-client")

# Métricas de usuarios
users_total = Gauge(
    'users_total',
    'Total number of users'
)

users_active = Gauge(
    'users_active',
    'Number of active users (with recent activity)'
)

# Métricas de apiarios
apiaries_total = Gauge(
    'apiaries_total',
    'Total number of apiaries'
)

apiaries_by_user = Histogram(
    'apiaries_per_user',
    'Number of apiaries per user',
    buckets=(1, 2, 5, 10, 20, 50, 100)
)

hives_total = Gauge(
    'hives_total',
    'Total number of hives across all apiaries'
)

# Métricas de cosecha
harvested_boxes_total = Counter(
    'harvested_boxes_total',
    'Total boxes harvested',
    ['box_type']  # box, boxMedium, boxSmall
)

harvested_apiaries_count = Gauge(
    'harvested_apiaries_count',
    'Number of apiaries with harvested boxes'
)

# Métricas de notificaciones
notifications_sent_total = Counter(
    'notifications_sent_total',
    'Total notifications sent',
    ['notification_type', 'status']  # status: success, failed
)

notifications_pending = Gauge(
    'notifications_pending',
    'Number of pending notifications'
)

# Métricas de dispositivos
devices_total = Gauge(
    'devices_total',
    'Total number of registered devices'
)

devices_by_platform = Gauge(
    'devices_by_platform',
    'Number of devices by platform',
    ['platform']  # ios, android
)

# Métricas de base de datos
db_connections_active = Gauge(
    'db_connections_active',
    'Number of active database connections'
)

db_query_duration_seconds = Histogram(
    'db_query_duration_seconds',
    'Database query duration in seconds',
    ['operation'],  # select, insert, update, delete
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0)
)

db_errors_total = Counter(
    'db_errors_total',
    'Total database errors',
    ['error_type']
)

# Métricas de tareas programadas (cron)
cron_jobs_executed_total = Counter(
    'cron_jobs_executed_total',
    'Total cron jobs executed',
    ['job_name', 'status']  # status: success, failed
)

cron_job_duration_seconds = Histogram(
    'cron_job_duration_seconds',
    'Cron job execution duration in seconds',
    ['job_name'],
    buckets=(1.0, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0, 600.0)
)


