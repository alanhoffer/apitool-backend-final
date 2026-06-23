from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional

from sqlalchemy import func

from app.database import get_db
from app.dependencies import require_role
from app.models.user import User, Role
from app.models.apiary import Apiary
from app.models.hive import Hive
from app.models.news import News
from app.models.task import Task
from app.models.notification import Notification
from app.services.apiary_service import ApiaryService
from app.services.notification_service import NotificationService

router = APIRouter(prefix="/admin", tags=["admin"])


class AdminStatsResponse(BaseModel):
    users: int
    apiaries: int
    hives: int
    news: int
    guides: int
    tasks: int


class BroadcastRequest(BaseModel):
    title: str
    message: str
    type: Optional[str] = "INFO"


@router.get("/stats", response_model=AdminStatsResponse)
async def admin_stats(
    payload: dict = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    try:
        from app.models.guide import Guide
        guides = db.query(Guide).count()
    except Exception:
        guides = 0
    hives = db.query(func.coalesce(func.sum(Apiary.hives), 0)).scalar() or 0
    return AdminStatsResponse(
        users=db.query(User).count(),
        apiaries=db.query(Apiary).count(),
        hives=int(hives),
        news=db.query(News).count(),
        guides=guides,
        tasks=db.query(Task).count(),
    )


@router.post("/broadcast")
async def admin_broadcast(
    body: BroadcastRequest,
    payload: dict = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    title = (body.title or "").strip()
    message = (body.message or "").strip()
    if not title or not message:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Título y mensaje son obligatorios")
    ntype = body.type if body.type in {"INFO", "ALERT", "WARNING"} else "INFO"

    users = db.query(User).all()
    for u in users:
        db.add(Notification(userId=u.id, title=title, message=message, type=ntype))
    db.commit()

    # Push best-effort (no rompe si falla)
    service = NotificationService(db)
    pushed = 0
    for u in users:
        try:
            service.send_push_notification(u.id, title, message, {"broadcast": True})
            pushed += 1
        except Exception:
            pass

    return {"message": "Aviso enviado", "recipients": len(users), "pushed": pushed}


class AdminUserResponse(BaseModel):
    id: int
    name: str
    surname: str
    email: str
    role: str
    active: bool
    apiaryCount: int
    hiveCount: int

    class Config:
        from_attributes = True


class UpdateRoleRequest(BaseModel):
    role: str


class UpdateActiveRequest(BaseModel):
    active: bool


def _user_to_admin_response(u: User, service: "ApiaryService") -> "AdminUserResponse":
    role = u.role.value if hasattr(u.role, "value") else str(u.role)
    return AdminUserResponse(
        id=u.id, name=u.name, surname=u.surname, email=u.email, role=role,
        active=bool(getattr(u, "is_active", True)),
        apiaryCount=service.count_apiaries_by_user_id(u.id),
        hiveCount=int(service.count_hives_by_user_id(u.id)),
    )


@router.get("/users", response_model=List[AdminUserResponse])
async def list_users(
    payload: dict = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    users = db.query(User).order_by(User.createdAt.desc()).all()
    service = ApiaryService(db)
    return [_user_to_admin_response(u, service) for u in users]


@router.get("/users/{user_id}/apiaries")
async def list_user_apiaries(
    user_id: int,
    payload: dict = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return ApiaryService(db).get_all_by_user_id(user_id)


@router.put("/users/{user_id}/role", response_model=AdminUserResponse)
async def update_user_role(
    user_id: int,
    body: UpdateRoleRequest,
    payload: dict = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    valid = {r.value for r in Role}
    if body.role not in valid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Rol inválido. Válidos: {sorted(valid)}")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    user.role = Role(body.role)
    db.commit()
    db.refresh(user)
    return _user_to_admin_response(user, ApiaryService(db))


@router.put("/users/{user_id}/active", response_model=AdminUserResponse)
async def update_user_active(
    user_id: int,
    body: UpdateActiveRequest,
    payload: dict = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    requester_id = int(payload.get("sub"))
    if requester_id == user_id and not body.active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No podés desactivar tu propia cuenta")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    user.is_active = bool(body.active)
    db.commit()
    db.refresh(user)
    return _user_to_admin_response(user, ApiaryService(db))


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    payload: dict = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    requester_id = int(payload.get("sub"))
    if requester_id == user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No podés eliminar tu propia cuenta desde el panel")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    db.delete(user)  # cascada: apiarios, colmenas, tareas, dispositivos, etc.
    db.commit()
    return {"message": "Usuario eliminado", "id": user_id}
