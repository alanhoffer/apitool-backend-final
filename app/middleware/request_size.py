"""
Middleware para validar el tamano maximo del request body.
"""
import logging

from fastapi import status
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)

# Tamano maximo por defecto: 10MB
MAX_REQUEST_SIZE = 10 * 1024 * 1024  # 10MB
PATH_LIMITS = {
    "/api/audio": 25 * 1024 * 1024,  # 25MB para audio
}
PATH_PREFIX_LIMITS = {
    "/apiarys": 6 * 1024 * 1024,  # 5MB imagen + overhead multipart
}


class RequestSizeMiddleware:
    """ASGI middleware que valida el tamano maximo del request body."""

    def __init__(self, app, max_size: int = MAX_REQUEST_SIZE):
        self.app = app
        self.max_size = max_size

    def _get_max_size(self, path: str) -> int:
        if path in PATH_LIMITS:
            return PATH_LIMITS[path]

        for prefix, limit in PATH_PREFIX_LIMITS.items():
            if path == prefix or path.startswith(f"{prefix}/"):
                return limit

        return self.max_size

    async def _reject(self, scope, receive, send, max_size: int):
        response = JSONResponse(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            content={
                "detail": f"Request body too large. Maximum size is {max_size / (1024 * 1024):.0f}MB"
            },
        )
        await response(scope, receive, send)

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "")
        method = (scope.get("method") or "").upper()
        max_size = self._get_max_size(path)
        headers = {
            key.decode("latin-1").lower(): value.decode("latin-1")
            for key, value in scope.get("headers", [])
        }

        # Requests that normally carry no body should pass through untouched
        # unless the client explicitly declares one. This avoids blocking on
        # body reads for health checks and other simple GET/HEAD requests.
        has_body_hint = bool(headers.get("content-length")) or bool(headers.get("transfer-encoding"))
        if method in {"GET", "HEAD", "OPTIONS"} and not has_body_hint:
            await self.app(scope, receive, send)
            return

        content_length = headers.get("content-length")
        if content_length:
            try:
                declared_size = int(content_length)
                if declared_size > max_size:
                    logger.warning(
                        "Request too large via Content-Length",
                        extra={"path": path, "size": declared_size, "max_size": max_size},
                    )
                    await self._reject(scope, receive, send, max_size)
                    return
            except (TypeError, ValueError):
                pass

        total_size = 0
        body_chunks: list[bytes] = []

        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                break
            if message["type"] != "http.request":
                continue

            chunk = message.get("body", b"")
            if chunk:
                total_size += len(chunk)
                if total_size > max_size:
                    logger.warning(
                        "Request too large while streaming body",
                        extra={"path": path, "size": total_size, "max_size": max_size},
                    )
                    await self._reject(scope, receive, send, max_size)
                    return
                body_chunks.append(chunk)

            if not message.get("more_body", False):
                break

        body = b"".join(body_chunks)
        body_sent = False

        async def replay_receive():
            nonlocal body_sent
            if body_sent:
                return {"type": "http.request", "body": b"", "more_body": False}

            body_sent = True
            return {"type": "http.request", "body": body, "more_body": False}

        await self.app(scope, replay_receive, send)
