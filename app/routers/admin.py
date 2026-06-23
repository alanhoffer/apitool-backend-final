from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional

from app.database import get_db
from app.dependencies import require_role
from app.models.user import User, Role
from app.models.apiary import Apiary
from app.services.apiary_service import ApiaryService

router = APIRouter(prefix="/admin", tags=["admin"])


class AdminUserResponse(BaseModel):
    id: int
    name: str
    surname: str
    email: str
    role: str
    apiaryCount: int
    hiveCount: int

    class Config:
        from_attributes = True


class UpdateRoleRequest(BaseModel):
    role: str


@router.get("/users", response_model=List[AdminUserResponse])
async def list_users(
    payload: dict = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    users = db.query(User).order_by(User.createdAt.desc()).all()
    service = ApiaryService(db)
    result = []
    for u in users:
        role = u.role.value if hasattr(u.role, "value") else str(u.role)
        result.append(AdminUserResponse(
            id=u.id, name=u.name, surname=u.surname, email=u.email, role=role,
            apiaryCount=service.count_apiaries_by_user_id(u.id),
            hiveCount=int(service.count_hives_by_user_id(u.id)),
        ))
    return result


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
    service = ApiaryService(db)
    role = user.role.value if hasattr(user.role, "value") else str(user.role)
    return AdminUserResponse(
        id=user.id, name=user.name, surname=user.surname, email=user.email, role=role,
        apiaryCount=service.count_apiaries_by_user_id(user.id),
        hiveCount=int(service.count_hives_by_user_id(user.id)),
    )


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
