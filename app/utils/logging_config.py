"""
Configuración de logging estructurado.
"""
import logging
import sys
import json
from datetime import datetime
from typing import Any, Dict
from contextvars import ContextVar

class StructuredFormatter(logging.Formatter):
    """Formatter que genera logs en formato JSON estructurado."""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        
        # Agregar información adicional si existe
        if hasattr(record, 'user_id'):
            log_data['user_id'] = record.user_id
        if hasattr(record, 'request_id'):
            log_data['request_id'] = record.request_id
        if hasattr(record, 'endpoint'):
            log_data['endpoint'] = record.endpoint
        if hasattr(record, 'method'):
            log_data['method'] = record.method
        if hasattr(record, 'status_code'):
            log_data['status_code'] = record.status_code
        if hasattr(record, 'duration'):
            log_data['duration'] = record.duration
        
        # Agregar excepciones si existen
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        # Agregar campos extra si existen
        if hasattr(record, 'extra_fields'):
            log_data.update(record.extra_fields)
        
        return json.dumps(log_data, ensure_ascii=False)

_request_id_ctx: ContextVar[str | None] = ContextVar("request_id", default=None)
_factory_installed = False

def set_request_id(request_id: str | None):
    return _request_id_ctx.set(request_id)

def reset_request_id(token) -> None:
    _request_id_ctx.reset(token)

def get_request_id() -> str | None:
    return _request_id_ctx.get()

def setup_logging(log_level: str = "INFO", use_json: bool = False) -> None:
    """
    Configura el logging de la aplicación.
    
    Args:
        log_level: Nivel de logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        use_json: Si True, usa formato JSON estructurado
    """
    level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Configurar handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    
    if use_json:
        formatter = StructuredFormatter()
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    handler.setFormatter(formatter)
    
    # Configurar root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.addHandler(handler)

    # Instalar LogRecordFactory una sola vez para request_id
    global _factory_installed
    if not _factory_installed:
        old_factory = logging.getLogRecordFactory()
        def record_factory(*args, **kwargs):
            record = old_factory(*args, **kwargs)
            request_id = get_request_id()
            if request_id:
                record.request_id = request_id
            return record
        logging.setLogRecordFactory(record_factory)
        _factory_installed = True
    
    # Configurar loggers específicos
    logging.getLogger("uvicorn").setLevel(level)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)  # Reducir logs de acceso
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)  # Reducir logs de SQL

def get_logger(name: str) -> logging.Logger:
    """Obtiene un logger con el nombre especificado."""
    return logging.getLogger(name)


