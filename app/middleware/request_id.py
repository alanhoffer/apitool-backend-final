"""
Middleware para tracking de Request ID.
Genera un ID único para cada request y lo incluye en logs y respuestas.
"""
import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from typing import Callable
import logging
from app.utils.logging_config import set_request_id, reset_request_id

logger = logging.getLogger(__name__)

class RequestIDMiddleware(BaseHTTPMiddleware):
    """Middleware que agrega un Request ID único a cada request."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generar o obtener Request ID
        request_id = request.headers.get("X-Request-ID")
        if not request_id:
            request_id = str(uuid.uuid4())
        
        # Agregar al estado de la request para acceso en la app
        request.state.request_id = request_id
        
        token = set_request_id(request_id)
        try:
            response = await call_next(request)
            # Agregar Request ID al header de respuesta
            response.headers["X-Request-ID"] = request_id
            return response
        finally:
            reset_request_id(token)


