"""
Middleware para tracking de métricas de requests.
"""
import time
import logging
from typing import Callable
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

try:
    from prometheus_client import Counter, Histogram, Gauge
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
    
    Counter = Histogram = Gauge = lambda *args, **kwargs: DummyMetric()

logger = logging.getLogger(__name__)

# Métricas Prometheus (solo si está disponible)
if PROMETHEUS_AVAILABLE:
    http_requests_total = Counter(
        'http_requests_total',
        'Total HTTP requests',
        ['method', 'endpoint', 'status_code']
    )

    http_request_duration_seconds = Histogram(
        'http_request_duration_seconds',
        'HTTP request duration in seconds',
        ['method', 'endpoint'],
        buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)
    )

    http_request_size_bytes = Histogram(
        'http_request_size_bytes',
        'HTTP request size in bytes',
        ['method', 'endpoint'],
        buckets=(100, 500, 1000, 5000, 10000, 50000, 100000, 500000, 1000000)
    )

    http_response_size_bytes = Histogram(
        'http_response_size_bytes',
        'HTTP response size in bytes',
        ['method', 'endpoint'],
        buckets=(100, 500, 1000, 5000, 10000, 50000, 100000, 500000, 1000000)
    )

    active_requests = Gauge(
        'http_active_requests',
        'Number of active HTTP requests',
        ['method', 'endpoint']
    )

    http_errors_total = Counter(
        'http_errors_total',
        'Total HTTP errors',
        ['method', 'endpoint', 'error_type']
    )
else:
    # Crear métricas dummy si prometheus no está disponible
    http_requests_total = DummyMetric()
    http_request_duration_seconds = DummyMetric()
    http_request_size_bytes = DummyMetric()
    http_response_size_bytes = DummyMetric()
    active_requests = DummyMetric()
    http_errors_total = DummyMetric()
    
    logger.warning("Prometheus client not available. Metrics will be disabled. Install with: pip install prometheus-client")

def normalize_path(path: str) -> str:
    """
    Normaliza el path para métricas (reemplaza IDs con placeholders).
    Ejemplo: /apiarys/123 -> /apiarys/{id}
    """
    # Lista de patrones a normalizar
    import re
    patterns = [
        (r'/apiarys/\d+', '/apiarys/{id}'),
        (r'/users/\d+', '/users/{id}'),
        (r'/drums/\d+', '/drums/{id}'),
        (r'/news/\d+', '/news/{id}'),
        (r'/notifications/\d+', '/notifications/{id}'),
        (r'/apiarys/\d+/history', '/apiarys/{id}/history'),
        (r'/apiarys/\d+/harvested', '/apiarys/{id}/harvested'),
        (r'/profile/image/[^/]+', '/profile/image/{id}'),
    ]
    
    normalized = path
    for pattern, replacement in patterns:
        normalized = re.sub(pattern, replacement, normalized)
    
    return normalized

class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware para tracking de métricas HTTP."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Normalizar path para métricas
        endpoint = normalize_path(request.url.path)
        method = request.method
        
        # Excluir health checks y métricas del tracking
        if endpoint in ['/health', '/health/ready', '/health/live', '/metrics']:
            return await call_next(request)
        
        # Incrementar requests activos
        active_requests.labels(method=method, endpoint=endpoint).inc()
        
        # Medir tamaño de request
        request_size = 0
        if hasattr(request, '_body'):
            request_size = len(request._body) if request._body else 0
        
        # Medir tiempo de respuesta
        start_time = time.time()
        
        try:
            response = await call_next(request)
            
            # Calcular duración
            duration = time.time() - start_time
            
            # Medir tamaño de response
            response_size = 0
            if hasattr(response, 'body'):
                response_size = len(response.body) if response.body else 0
            
            # Registrar métricas
            status_code = response.status_code
            http_requests_total.labels(
                method=method,
                endpoint=endpoint,
                status_code=status_code
            ).inc()
            
            http_request_duration_seconds.labels(
                method=method,
                endpoint=endpoint
            ).observe(duration)
            
            if request_size > 0:
                http_request_size_bytes.labels(
                    method=method,
                    endpoint=endpoint
                ).observe(request_size)
            
            if response_size > 0:
                http_response_size_bytes.labels(
                    method=method,
                    endpoint=endpoint
                ).observe(response_size)
            
            # Registrar errores (4xx, 5xx)
            if status_code >= 400:
                error_type = 'client_error' if status_code < 500 else 'server_error'
                http_errors_total.labels(
                    method=method,
                    endpoint=endpoint,
                    error_type=error_type
                ).inc()
            
            return response
            
        except Exception as e:
            # Registrar excepciones
            duration = time.time() - start_time
            http_errors_total.labels(
                method=method,
                endpoint=endpoint,
                error_type='exception'
            ).inc()
            
            http_request_duration_seconds.labels(
                method=method,
                endpoint=endpoint
            ).observe(duration)
            
            logger.error(f"Error processing request {method} {endpoint}: {e}", exc_info=True)
            raise
            
        finally:
            # Decrementar requests activos
            active_requests.labels(method=method, endpoint=endpoint).dec()


