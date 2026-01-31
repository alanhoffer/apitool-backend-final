from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies import get_current_user_payload, require_role
from app.services.recommendations_service import RecommendationsService
from app.schemas.recommendations import RecommendationsResponse, SeasonalTipCreate, SeasonalTipResponse

router = APIRouter(prefix="/recommendations", tags=["recommendations"])

@router.get("", response_model=RecommendationsResponse)
async def get_current_recommendations(
    db: Session = Depends(get_db)
    # Puede ser público o requerir auth. Lo dejaremos público para la home de la app.
):
    service = RecommendationsService(db)
    return service.get_recommendations() # Default South hemisphere

@router.post("", response_model=SeasonalTipResponse)
async def create_recommendation(
    tip_data: SeasonalTipCreate,
    payload: dict = Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    service = RecommendationsService(db)
    return service.create_tip(tip_data)

