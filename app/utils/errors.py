"""
Standardized error messages and exception helpers.
"""
from fastapi import HTTPException, status
from typing import Optional

# Standard error messages
ERROR_MESSAGES = {
    "NOT_FOUND": "Resource not found",
    "UNAUTHORIZED": "Unauthorized access",
    "FORBIDDEN": "Access forbidden",
    "VALIDATION_ERROR": "Validation error",
    "CONFLICT": "Resource already exists",
    "INTERNAL_ERROR": "Internal server error",
    "BAD_REQUEST": "Bad request",
}

def raise_not_found(resource: str = "Resource", detail: Optional[str] = None) -> HTTPException:
    """Raise 404 Not Found exception."""
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=detail or f"{resource} not found"
    )

def raise_unauthorized(detail: Optional[str] = None) -> HTTPException:
    """Raise 401 Unauthorized exception."""
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail or ERROR_MESSAGES["UNAUTHORIZED"],
        headers={"WWW-Authenticate": "Bearer"},
    )

def raise_forbidden(detail: Optional[str] = None) -> HTTPException:
    """Raise 403 Forbidden exception."""
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=detail or ERROR_MESSAGES["FORBIDDEN"]
    )

def raise_bad_request(detail: str) -> HTTPException:
    """Raise 400 Bad Request exception."""
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=detail
    )

def raise_conflict(detail: Optional[str] = None) -> HTTPException:
    """Raise 409 Conflict exception."""
    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail=detail or ERROR_MESSAGES["CONFLICT"]
    )

def raise_internal_error(detail: Optional[str] = None) -> HTTPException:
    """Raise 500 Internal Server Error exception."""
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=detail or ERROR_MESSAGES["INTERNAL_ERROR"]
    )


