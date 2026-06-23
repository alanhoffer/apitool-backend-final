from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.dependencies import get_current_user_payload, require_role
from app.models.guide import Guide
from app.schemas.guide import GuideCreate, GuideUpdate, GuideResponse

router = APIRouter(prefix="/guides", tags=["guides"])


@router.get("", response_model=List[GuideResponse])
async def list_guides(db: Session = Depends(get_db)):
    return db.query(Guide).order_by(Guide.featured.desc(), Guide.date.desc()).all()


@router.get("/{guide_id}", response_model=GuideResponse)
async def get_guide(guide_id: int, db: Session = Depends(get_db)):
    guide = db.query(Guide).filter(Guide.id == guide_id).first()
    if not guide:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Guide not found")
    return guide


@router.post("", response_model=GuideResponse)
async def create_guide(
    data: GuideCreate,
    payload: dict = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    guide = Guide(**data.dict())
    db.add(guide)
    db.commit()
    db.refresh(guide)
    return guide


@router.put("/{guide_id}", response_model=GuideResponse)
async def update_guide(
    guide_id: int,
    data: GuideUpdate,
    payload: dict = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    guide = db.query(Guide).filter(Guide.id == guide_id).first()
    if not guide:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Guide not found")
    for key, value in data.dict(exclude_unset=True).items():
        setattr(guide, key, value)
    db.commit()
    db.refresh(guide)
    return guide


@router.delete("/{guide_id}")
async def delete_guide(
    guide_id: int,
    payload: dict = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    guide = db.query(Guide).filter(Guide.id == guide_id).first()
    if not guide:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Guide not found")
    db.delete(guide)
    db.commit()
    return {"message": "Guide deleted", "id": guide_id}
