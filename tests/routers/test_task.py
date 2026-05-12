from passlib.context import CryptContext

from app.models.apiary import Apiary
from app.models.task import Task
from app.models.user import Role, User


def _create_other_user_apiary(db) -> Apiary:
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    other_user = User(
        name="Other",
        surname="User",
        email="other-task-owner@example.com",
        password=pwd_context.hash("password123"),
        role=Role.APICULTOR,
    )
    db.add(other_user)
    db.commit()
    db.refresh(other_user)

    other_apiary = Apiary(
        userId=other_user.id,
        name="Other Apiary",
        hives=1,
        status="normal",
        image="test.jpg",
    )
    db.add(other_apiary)
    db.commit()
    db.refresh(other_apiary)
    return other_apiary


def test_create_task_rejects_apiary_from_another_user(client, auth_headers, db):
    other_apiary = _create_other_user_apiary(db)

    response = client.post(
        "/tasks",
        headers=auth_headers,
        json={
            "title": "Revisar colmena",
            "description": "No debe quedar asociado a otro apiario",
            "completed": False,
            "apiary_id": other_apiary.id,
        },
    )

    assert response.status_code == 404
    assert db.query(Task).filter(Task.apiary_id == other_apiary.id).count() == 0


def test_update_task_rejects_apiary_from_another_user(client, auth_headers, test_user, db):
    other_apiary = _create_other_user_apiary(db)
    task = Task(
        user_id=test_user.id,
        title="Tarea propia",
        completed=False,
        apiary_id=None,
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    response = client.put(
        f"/tasks/{task.id}",
        headers=auth_headers,
        json={"apiary_id": other_apiary.id},
    )

    assert response.status_code == 404
    db.refresh(task)
    assert task.apiary_id is None
