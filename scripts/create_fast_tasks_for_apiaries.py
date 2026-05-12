from app.database import SessionLocal
from app.models.apiary import Apiary
from app.services.task_service import TaskService


def main():
    db = SessionLocal()
    try:
        apiaries = db.query(Apiary.id, Apiary.userId).all()
        service = TaskService(db)
        created = 0
        for apiary_id, user_id in apiaries:
            created += service.create_fast_tasks_for_apiary(user_id, apiary_id, commit=False)
        db.commit()
        print(f"Created {created} fast tasks across {len(apiaries)} apiaries")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == '__main__':
    main()
