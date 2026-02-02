"""
Database utility functions for transaction management.
"""
from sqlalchemy.orm import Session
from typing import Callable, TypeVar, Any
from functools import wraps
import logging

logger = logging.getLogger(__name__)

T = TypeVar('T')

def with_transaction(db: Session):
    """
    Decorator para manejar transacciones con rollback automático en caso de error.
    
    Uso:
        @with_transaction(db)
        def my_service_method(self, ...):
            # código que usa self.db
            self.db.commit()  # El decorator manejará el rollback si falla
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                db.rollback()
                logger.error(f"Transaction rolled back due to error in {func.__name__}: {e}")
                raise
        return wrapper
    return decorator

def safe_commit(db: Session, operation_name: str = "operation") -> None:
    """
    Ejecuta commit con manejo de errores y rollback automático.
    
    Args:
        db: Database session
        operation_name: Nombre de la operación para logging
    """
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Error committing {operation_name}: {e}")
        raise


