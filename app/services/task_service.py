from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.models.apiary import Apiary
from app.models.task import Task
from app.schemas.task import TaskCreate, TaskUpdate
from typing import List, Optional

DEFAULT_FAST_TASK_TITLES = [
    "Revisar colmena",
    "Alimentar",
    "Tratamiento sanitario",
    "Cosecha",
    "Revision reina",
]

class TaskService:
    def __init__(self, db: Session):
        self.db = db

    def _apiary_belongs_to_user(self, apiary_id: int, user_id: int) -> bool:
        return self.db.query(Apiary.id).filter(
            and_(Apiary.id == apiary_id, Apiary.userId == user_id)
        ).first() is not None
    
    def create_task(self, user_id: int, task_data: TaskCreate) -> Optional[Task]:
        if task_data.apiary_id is not None and not self._apiary_belongs_to_user(task_data.apiary_id, user_id):
            return None

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

    def create_fast_tasks_for_apiary(self, user_id: int, apiary_id: int, commit: bool = True) -> int:
        existing = self.db.query(Task.title).filter(
            Task.user_id == user_id,
            Task.apiary_id == apiary_id
        ).all()
        existing_titles = {row[0] for row in existing}
        created = 0

        for title in DEFAULT_FAST_TASK_TITLES:
            if title in existing_titles:
                continue
            task = Task(
                user_id=user_id,
                title=title,
                description=None,
                completed=False,
                due_date=None,
                apiary_id=apiary_id
            )
            self.db.add(task)
            created += 1

        if commit:
            self.db.commit()

        return created
    
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
        next_apiary_id = update_data.get("apiary_id")
        if next_apiary_id is not None and not self._apiary_belongs_to_user(next_apiary_id, user_id):
            return None

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
