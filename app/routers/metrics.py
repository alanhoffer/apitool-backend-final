"""
Endpoint de métricas Prometheus.
"""
from fastapi import APIRouter, Response, HTTPException, status

try:
    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False

router = APIRouter(prefix="/metrics", tags=["metrics"])

@router.get("")
async def get_metrics():
    """
    Endpoint de métricas Prometheus.
    Expone todas las métricas en formato Prometheus.
    """
    if not PROMETHEUS_AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Prometheus client not installed. Install with: pip install prometheus-client"
        )
    
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )


