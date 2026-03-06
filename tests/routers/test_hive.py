def test_create_hive(client, auth_headers, test_apiary):
    response = client.post(
        "/hives",
        headers=auth_headers,
        json={
            "apiaryId": test_apiary.id,
            "name": "H-001",
            "status": "Bueno",
            "queenStatus": "present",
            "population": 7,
            "swarming": False,
            "lastInspection": "2026-03-05",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "H-001"
    assert data["apiaryId"] == test_apiary.id
    assert data["userId"] == test_apiary.userId


def test_get_hives_by_apiary(client, auth_headers, test_apiary):
    create_response = client.post(
        "/hives",
        headers=auth_headers,
        json={
            "apiaryId": test_apiary.id,
            "name": "H-002",
        },
    )
    assert create_response.status_code == 201

    response = client.get(f"/hives?apiary_id={test_apiary.id}", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == 1
    assert data[0]["name"] == "H-002"


def test_update_hive(client, auth_headers, test_apiary):
    create_response = client.post(
        "/hives",
        headers=auth_headers,
        json={
            "apiaryId": test_apiary.id,
            "name": "H-003",
        },
    )
    hive_id = create_response.json()["id"]

    response = client.put(
        f"/hives/{hive_id}",
        headers=auth_headers,
        json={
            "status": "Excel.",
            "production": "12.5",
            "tComment": "Visita de control",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "Excel."
    assert data["production"] == "12.50"
    assert data["tComment"] == "Visita de control"


def test_delete_hive_updates_apiary_count(client, auth_headers, test_apiary):
    create_response = client.post(
        "/hives",
        headers=auth_headers,
        json={
            "apiaryId": test_apiary.id,
            "name": "H-004",
        },
    )
    hive_id = create_response.json()["id"]

    delete_response = client.delete(f"/hives/{hive_id}", headers=auth_headers)
    assert delete_response.status_code == 200

    apiary_response = client.get(f"/apiarys/{test_apiary.id}", headers=auth_headers)
    assert apiary_response.status_code == 200
    assert apiary_response.json()["hives"] == 0


def test_get_hive_history(client, auth_headers, test_apiary):
    create_response = client.post(
        "/hives",
        headers=auth_headers,
        json={
            "apiaryId": test_apiary.id,
            "name": "H-005",
            "status": "Bueno",
            "population": 5,
        },
    )
    assert create_response.status_code == 201
    hive_id = create_response.json()["id"]

    update_response = client.put(
        f"/hives/{hive_id}",
        headers=auth_headers,
        json={
            "status": "Excel.",
            "population": 8,
            "tComment": "Revisión general",
        },
    )
    assert update_response.status_code == 200

    response = client.get(f"/hives/{hive_id}/history", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert data[0]["hiveId"] == hive_id
    assert data[0]["changes"]["status"] == "Excel."
    assert data[0]["changes"]["population"] == 8
