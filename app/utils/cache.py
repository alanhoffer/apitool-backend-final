"""
Sistema de caché simple en memoria.
Para producción, considerar usar Redis para caché distribuido.
"""
import time
import hashlib
import json
from typing import Any, Optional, Callable, Dict, Tuple
from functools import wraps
import logging

logger = logging.getLogger(__name__)

class SimpleCache:
    """Caché simple en memoria con TTL."""
    
    def __init__(self):
        self._cache: Dict[str, Tuple[Any, float]] = {}
        self._hits = 0
        self._misses = 0
    
    def get(self, key: str) -> Optional[Any]:
        """Obtiene un valor del caché si existe y no ha expirado."""
        if key not in self._cache:
            self._misses += 1
            return None
        
        value, expiry = self._cache[key]
        
        if time.time() > expiry:
            # Expiró, eliminar
            del self._cache[key]
            self._misses += 1
            return None
        
        self._hits += 1
        return value
    
    def set(self, key: str, value: Any, ttl: int = 300) -> None:
        """
        Guarda un valor en el caché con TTL.
        
        Args:
            key: Clave del caché
            value: Valor a guardar
            ttl: Time to live en segundos (default: 5 minutos)
        """
        expiry = time.time() + ttl
        self._cache[key] = (value, expiry)
    
    def delete(self, key: str) -> None:
        """Elimina una clave del caché."""
        if key in self._cache:
            del self._cache[key]
    
    def clear(self) -> None:
        """Limpia todo el caché."""
        self._cache.clear()
        self._hits = 0
        self._misses = 0
    
    def cleanup_expired(self) -> int:
        """Limpia entradas expiradas y retorna cuántas se eliminaron."""
        current_time = time.time()
        expired_keys = [
            key for key, (_, expiry) in self._cache.items()
            if current_time > expiry
        ]
        
        for key in expired_keys:
            del self._cache[key]
        
        return len(expired_keys)
    
    def get_stats(self) -> dict:
        """Obtiene estadísticas del caché."""
        total_requests = self._hits + self._misses
        hit_rate = (self._hits / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "size": len(self._cache),
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": round(hit_rate, 2)
        }

# Instancia global del caché
cache = SimpleCache()

def cache_key(*args, **kwargs) -> str:
    """
    Genera una clave de caché a partir de argumentos.
    
    Args:
        *args: Argumentos posicionales
        **kwargs: Argumentos con nombre
        
    Returns:
        Clave de caché como string
    """
    # Serializar argumentos a JSON para crear hash
    key_data = {
        "args": args,
        "kwargs": sorted(kwargs.items())
    }
    key_str = json.dumps(key_data, sort_keys=True, default=str)
    return hashlib.md5(key_str.encode()).hexdigest()

def cached(ttl: int = 300, key_prefix: str = ""):
    """
    Decorador para cachear resultados de funciones.
    
    Args:
        ttl: Time to live en segundos (default: 5 minutos)
        key_prefix: Prefijo para la clave de caché
        
    Ejemplo:
        @cached(ttl=600, key_prefix="weather")
        async def get_weather(lat: float, lon: float):
            # ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Generar clave de caché
            key = f"{key_prefix}:{func.__name__}:{cache_key(*args, **kwargs)}"
            
            # Intentar obtener del caché
            cached_value = cache.get(key)
            if cached_value is not None:
                logger.debug(f"Cache hit for {key}")
                return cached_value
            
            # Ejecutar función y cachear resultado
            logger.debug(f"Cache miss for {key}")
            result = await func(*args, **kwargs)
            cache.set(key, result, ttl=ttl)
            
            return result
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Generar clave de caché
            key = f"{key_prefix}:{func.__name__}:{cache_key(*args, **kwargs)}"
            
            # Intentar obtener del caché
            cached_value = cache.get(key)
            if cached_value is not None:
                logger.debug(f"Cache hit for {key}")
                return cached_value
            
            # Ejecutar función y cachear resultado
            logger.debug(f"Cache miss for {key}")
            result = func(*args, **kwargs)
            cache.set(key, result, ttl=ttl)
            
            return result
        
        # Retornar wrapper apropiado según si la función es async
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator

