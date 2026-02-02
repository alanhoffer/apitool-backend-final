"""
Middleware para validar tamaño máximo de request body.
"""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from fastapi import status
import logging

logger = logging.getLogger(__name__)

# Tamaño máximo por defecto: 10MB
MAX_REQUEST_SIZE = 10 * 1024 * 1024  # 10MB

class RequestSizeMiddleware(BaseHTTPMiddleware):
    """Middleware que valida el tamaño máximo del request body."""
    
    def __init__(self, app, max_size: int = MAX_REQUEST_SIZE):
        super().__init__(app)
        self.max_size = max_size
    
    async def dispatch(self, request: Request, call_next) -> JSONResponse:
        # Verificar Content-Length si está presente
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                size = int(content_length)
                if size > self.max_size:
                    logger.warning(
                        f"Request too large: {size} bytes (max: {self.max_size})",
                        extra={
                            "request_id": getattr(request.state, "request_id", None),
                            "path": request.url.path,
                            "size": size,
                            "max_size": self.max_size
                        }
                    )
                    return JSONResponse(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        content={
                            "detail": f"Request body too large. Maximum size is {self.max_size / (1024*1024):.0f}MB"
                        }
                    )
            except (ValueError, TypeError):
                # Si no se puede parsear, continuar (el servidor lo manejará)
                pass
        
        response = await call_next(request)
        return response


