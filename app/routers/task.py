from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.services.task_service import TaskService
from app.schemas.task import (
    TaskCreate, TaskUpdate, TaskResponse, TasksListResponse
)
from typing import Optional

router = APIRouter(prefix="/tasks", tags=["tasks"])

@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    task_data: TaskCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Crea una nueva tarea."""
    service = TaskService(db)
    return service.create_task(current_user.id, task_data)

@router.get("", response_model=TasksListResponse)
async def get_tasks(
    apiary_id: Optional[int] = Query(None, description="Filtrar por ID de apiario"),
    completed: Optional[bool] = Query(None, description="Filtrar por estado completado"),
    page: int = Query(1, ge=1, description="Número de página"),
    limit: int = Query(50, ge=1, le=100, description="Resultados por página"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtiene la lista de tareas del usuario autenticado con paginación."""
    service = TaskService(db)
    tasks, total = service.get_tasks(current_user.id, apiary_id, completed, page, limit)
    
    return {
        "data": tasks,
        "pagination": {
            "page": page,
            "limit": limit,
            "total": total,
            "totalPages": (total + limit - 1) // limit if total > 0 else 0
        }
    }

@router.get("/{id}", response_model=TaskResponse)
async def get_task(
    id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtiene una tarea específica por su ID."""
    service = TaskService(db)
    task = service.get_task_by_id(id, current_user.id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tarea no encontrada"
        )
    return task

@router.put("/{id}", response_model=TaskResponse)
async def update_task(
    id: int,
    updates: TaskUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Actualiza una tarea existente."""
    service = TaskService(db)
    task = service.update_task(id, current_user.id, updates)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tarea no encontrada"
        )
    return task

@router.delete("/{id}")
async def delete_task(
    id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Elimina una tarea específica."""
    service = TaskService(db)
    if not service.delete_task(id, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tarea no encontrada"
        )
    return {"message": "Tarea eliminada correctamente"}
