from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.models.task import Task
from app.schemas.task import TaskCreate, TaskUpdate
from typing import List, Optional

class TaskService:
    def __init__(self, db: Session):
        self.db = db
    
    def create_task(self, user_id: int, task_data: TaskCreate) -> Task:
        task = Task(
            user_id=user_id,
            title=task_data.title,
            description=task_data.description,
            completed=task_data.completed,
            due_date=task_data.due_date,
            apiary_id=task_data.apiary_id
        )
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        return task
    
    def get_tasks(
        self, 
        user_id: int, 
        apiary_id: Optional[int] = None,
        completed: Optional[bool] = None,
        page: int = 1,
        limit: int = 50
    ) -> tuple[List[Task], int]:
        query = self.db.query(Task).filter(Task.user_id == user_id)
        
        if apiary_id is not None:
            query = query.filter(Task.apiary_id == apiary_id)
        
        if completed is not None:
            query = query.filter(Task.completed == completed)
        
        total = query.count()
        offset = (page - 1) * limit
        
        tasks = query.order_by(Task.due_date.asc(), Task.created_at.desc()).offset(offset).limit(limit).all()
        return tasks, total
    
    def get_task_by_id(self, task_id: int, user_id: int) -> Optional[Task]:
        return self.db.query(Task).filter(
            and_(Task.id == task_id, Task.user_id == user_id)
        ).first()
    
    def update_task(self, task_id: int, user_id: int, updates: TaskUpdate) -> Optional[Task]:
        task = self.get_task_by_id(task_id, user_id)
        if not task:
            return None
        
        update_data = updates.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(task, key, value)
        
        self.db.commit()
        self.db.refresh(task)
        return task
    
    def delete_task(self, task_id: int, user_id: int) -> bool:
        task = self.get_task_by_id(task_id, user_id)
        if not task:
            return False
        
        self.db.delete(task)
        self.db.commit()
        return True
