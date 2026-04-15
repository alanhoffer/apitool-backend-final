"""
Middleware de rate limiting.
Protege la API contra abuso y ataques de fuerza bruta.
"""
import time
from collections import defaultdict
from typing import Callable

from fastapi import status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.config import settings
import logging

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware de rate limiting simple en memoria.
    En serverless sigue siendo por instancia, pero al menos usa IP real
    de proxy y limites configurables por entorno.
    """

    def __init__(self, app, **kwargs):
        super().__init__(app)
        auth_window = settings.rate_limit_auth_window_seconds
        default_window = settings.rate_limit_default_window_seconds
        self.limits: dict[str, tuple[int, int]] = {
            "/auth/login": (settings.rate_limit_login_requests, auth_window),
            "/auth/register": (settings.rate_limit_register_requests, auth_window),
            "/auth/forgot-password": (settings.rate_limit_forgot_password_requests, auth_window),
            "/auth/reset-password": (settings.rate_limit_forgot_password_requests, auth_window),
            "/auth": (settings.rate_limit_auth_requests, auth_window),
            "default": (settings.rate_limit_default_requests, default_window),
        }

        self.counters: dict[str, dict[str, tuple[int, float]]] = defaultdict(dict)
        self.last_cleanup = time.time()
        self.cleanup_interval = 300

    def _get_limit(self, path: str) -> tuple[int, int]:
        if path in self.limits:
            return self.limits[path]

        for prefix, limit in self.limits.items():
            if prefix != "default" and path.startswith(prefix):
                return limit

        return self.limits["default"]

    def _get_client_ip(self, request: Request) -> str:
        if settings.rate_limit_trust_proxy_headers:
            forwarded_for = request.headers.get("x-forwarded-for")
            if forwarded_for:
                first_hop = forwarded_for.split(",")[0].strip()
                if first_hop:
                    return first_hop

            real_ip = request.headers.get("x-real-ip")
            if real_ip:
                return real_ip.strip()

        if request.client and request.client.host:
            return request.client.host

        return "unknown"

    def _get_client_id(self, request: Request) -> str:
        user_id = getattr(request.state, "user_id", None)
        if user_id:
            return f"user:{user_id}"

        return f"ip:{self._get_client_ip(request)}"

    def _cleanup_old_counters(self):
        current_time = time.time()
        if current_time - self.last_cleanup < self.cleanup_interval:
            return

        self.last_cleanup = current_time
        cutoff_time = current_time - 3600

        for path in list(self.counters.keys()):
            client_counters = self.counters[path]
            for client_id in list(client_counters.keys()):
                _, window_start = client_counters[client_id]
                if window_start < cutoff_time:
                    del client_counters[client_id]

            if not client_counters:
                del self.counters[path]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        path = request.url.path
        if request.method == "OPTIONS":
            return await call_next(request)

        if path in ["/health", "/health/ready", "/health/live", "/metrics"]:
            return await call_next(request)

        self._cleanup_old_counters()

        max_requests, window_seconds = self._get_limit(path)
        client_id = self._get_client_id(request)
        current_time = time.time()

        client_counters = self.counters[path]

        if client_id in client_counters:
            count, window_start = client_counters[client_id]
            if current_time - window_start >= window_seconds:
                count = 0
                window_start = current_time
            count += 1
        else:
            count = 1
            window_start = current_time

        client_counters[client_id] = (count, window_start)

        if count > max_requests:
            retry_after = max(1, int(window_seconds - (current_time - window_start)))
            logger.warning(
                f"Rate limit exceeded for {client_id} on {path}: {count}/{max_requests}",
                extra={
                    "request_id": getattr(request.state, "request_id", None),
                    "client_id": client_id,
                    "path": path,
                    "count": count,
                    "limit": max_requests,
                },
            )

            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": f"Rate limit exceeded. Maximum {max_requests} requests per {window_seconds} seconds.",
                    "retry_after": retry_after,
                },
                headers={
                    "X-RateLimit-Limit": str(max_requests),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(window_start + window_seconds)),
                    "Retry-After": str(retry_after),
                },
            )

        remaining = max(0, max_requests - count)
        reset_time = int(window_start + window_seconds)

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(max_requests)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(reset_time)

        return response
