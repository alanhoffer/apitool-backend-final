"""
Middleware de Rate Limiting.
Protege la API contra abuso y ataques DDoS.
"""
import time
from collections import defaultdict
from typing import Dict, Tuple, Callable
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
from fastapi import status
import logging

logger = logging.getLogger(__name__)

class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware de rate limiting simple en memoria.
    Para producción, considerar usar Redis para rate limiting distribuido.
    """
    
    def __init__(self, app, **kwargs):
        super().__init__(app)
        # Configuración de límites por endpoint
        self.limits: Dict[str, Tuple[int, int]] = {
            # (requests, window_seconds)
            "/auth/login": (5, 60),  # 5 requests por minuto
            "/auth/register": (3, 60),  # 3 requests por minuto
            "/auth": (10, 60),  # 10 requests por minuto para otros endpoints de auth
            "default": (100, 60),  # 100 requests por minuto por defecto
        }
        
        # Almacenar contadores (en producción usar Redis)
        self.counters: Dict[str, Dict[str, Tuple[int, float]]] = defaultdict(dict)
        
        # Limpiar contadores antiguos cada 5 minutos
        self.last_cleanup = time.time()
        self.cleanup_interval = 300  # 5 minutos
    
    def _get_limit(self, path: str) -> Tuple[int, int]:
        """Obtiene el límite para un path específico."""
        # Buscar coincidencia exacta primero
        if path in self.limits:
            return self.limits[path]
        
        # Buscar por prefijo
        for prefix, limit in self.limits.items():
            if path.startswith(prefix):
                return limit
        
        # Usar límite por defecto
        return self.limits["default"]
    
    def _get_client_id(self, request: Request) -> str:
        """Obtiene un identificador único del cliente."""
        # Intentar obtener IP del cliente
        client_ip = request.client.host if request.client else "unknown"
        
        # Si hay usuario autenticado, usar user_id también
        # Esto permite límites diferentes por usuario
        user_id = getattr(request.state, "user_id", None)
        if user_id:
            return f"user:{user_id}"
        
        return f"ip:{client_ip}"
    
    def _cleanup_old_counters(self):
        """Limpia contadores antiguos para evitar memory leak."""
        current_time = time.time()
        if current_time - self.last_cleanup < self.cleanup_interval:
            return
        
        self.last_cleanup = current_time
        cutoff_time = current_time - 3600  # Mantener solo últimos 60 minutos
        
        for path in list(self.counters.keys()):
            client_counters = self.counters[path]
            for client_id in list(client_counters.keys()):
                _, window_start = client_counters[client_id]
                if window_start < cutoff_time:
                    del client_counters[client_id]
            
            # Eliminar paths vacíos
            if not client_counters:
                del self.counters[path]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Excluir health checks y métricas del rate limiting
        path = request.url.path
        if path in ["/health", "/health/ready", "/health/live", "/metrics"]:
            return await call_next(request)
        
        # Limpiar contadores antiguos periódicamente
        self._cleanup_old_counters()
        
        # Obtener límite para este endpoint
        max_requests, window_seconds = self._get_limit(path)
        
        # Obtener identificador del cliente
        client_id = self._get_client_id(request)
        
        # Obtener contador actual
        current_time = time.time()
        counter_key = f"{path}:{client_id}"
        
        if path not in self.counters:
            self.counters[path] = {}
        
        client_counters = self.counters[path]
        
        if client_id in client_counters:
            count, window_start = client_counters[client_id]
            
            # Si la ventana expiró, reiniciar contador
            if current_time - window_start >= window_seconds:
                count = 0
                window_start = current_time
            else:
                count += 1
        else:
            count = 1
            window_start = current_time
        
        # Actualizar contador
        client_counters[client_id] = (count, window_start)
        
        # Verificar si excedió el límite
        if count > max_requests:
            retry_after = int(window_seconds - (current_time - window_start))
            logger.warning(
                f"Rate limit exceeded for {client_id} on {path}: {count}/{max_requests}",
                extra={
                    "request_id": getattr(request.state, "request_id", None),
                    "client_id": client_id,
                    "path": path,
                    "count": count,
                    "limit": max_requests
                }
            )
            
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": f"Rate limit exceeded. Maximum {max_requests} requests per {window_seconds} seconds.",
                    "retry_after": retry_after
                },
                headers={
                    "X-RateLimit-Limit": str(max_requests),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(window_start + window_seconds)),
                    "Retry-After": str(retry_after)
                }
            )
        
        # Agregar headers de rate limit a la respuesta
        remaining = max(0, max_requests - count)
        reset_time = int(window_start + window_seconds)
        
        response = await call_next(request)
        
        response.headers["X-RateLimit-Limit"] = str(max_requests)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(reset_time)
        
        return response


