import pytest


# ─── Apiary history ───────────────────────────────────────────────────────────

def test_apiary_history_empty(client, auth_headers, test_apiary):
    """History endpoint returns empty list when no changes recorded."""
    response = client.get(f"/apiarys/history/{test_apiary.id}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json() == []


def test_apiary_history_records_change_and_returns_user_name(client, auth_headers, test_apiary, test_user):
    """After updating an apiary, history returns entries with userName."""
    update_response = client.put(
        f"/apiarys/{test_apiary.id}",
        headers=auth_headers,
        data={"hives": "15", "status": "active", "managementType": "apiary"},
    )
    assert update_response.status_code == 200

    response = client.get(f"/apiarys/history/{test_apiary.id}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0

    entry = data[0]
    assert "field" in entry
    assert "previousValue" in entry
    assert "newValue" in entry
    assert "userName" in entry
    # The user who made the change should have a name
    assert entry["userName"] == f"{test_user.name} {test_user.surname}"


def test_apiary_history_previous_and_new_value(client, auth_headers, test_apiary):
    """History entries contain both previousValue and newValue."""
    # First update
    client.put(
        f"/apiarys/{test_apiary.id}",
        headers=auth_headers,
        data={"hives": "8", "managementType": "apiary"},
    )
    # Second update to create a diff with a known previous value
    client.put(
        f"/apiarys/{test_apiary.id}",
        headers=auth_headers,
        data={"hives": "12", "managementType": "apiary"},
    )

    response = client.get(f"/apiarys/history/{test_apiary.id}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()

    hive_changes = [e for e in data if e["field"] == "hives"]
    assert len(hive_changes) >= 1
    for entry in hive_changes:
        assert entry["newValue"] is not None


def test_apiary_history_unauthorized(client, test_apiary):
    """History endpoint requires authentication."""
    response = client.get(f"/apiarys/history/{test_apiary.id}")
    assert response.status_code == 403


# ─── Hive history ─────────────────────────────────────────────────────────────

def _create_and_update_hive(client, auth_headers, apiary_id):
    """Helper: create a hive then update it to generate a history entry."""
    create = client.post(
        "/hives",
        headers=auth_headers,
        json={"apiaryId": apiary_id, "name": "H-HIST", "status": "Bueno", "population": 5},
    )
    assert create.status_code == 201
    hive_id = create.json()["id"]

    update = client.put(
        f"/hives/{hive_id}",
        headers=auth_headers,
        json={"status": "Excel.", "population": 9},
    )
    assert update.status_code == 200
    return hive_id


def test_hive_history_returns_created_by_name(client, auth_headers, test_apiary, test_user):
    """Hive history entries include createdByName."""
    hive_id = _create_and_update_hive(client, auth_headers, test_apiary.id)

    response = client.get(f"/hives/{hive_id}/history", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1

    entry = data[0]
    assert "createdByName" in entry
    assert entry["createdByName"] == f"{test_user.name} {test_user.surname}"


def test_hive_history_changes_contain_updated_fields(client, auth_headers, test_apiary):
    """Hive history changes dict contains the fields that were modified."""
    hive_id = _create_and_update_hive(client, auth_headers, test_apiary.id)

    response = client.get(f"/hives/{hive_id}/history", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()

    entry = data[0]
    assert "changes" in entry
    assert entry["changes"]["status"] == "Excel."
    assert entry["changes"]["population"] == 9


def test_hive_history_creation_generates_initial_entry(client, auth_headers, test_apiary):
    """Creating a hive generates an initial history entry with its starting values."""
    create = client.post(
        "/hives",
        headers=auth_headers,
        json={"apiaryId": test_apiary.id, "name": "H-NEW"},
    )
    assert create.status_code == 201
    hive_id = create.json()["id"]

    response = client.get(f"/hives/{hive_id}/history", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    # Creation always logs initial state
    assert len(data) >= 1
    assert data[0]["hiveId"] == hive_id
    assert "changes" in data[0]


def test_hive_history_unauthorized(client, auth_headers, test_apiary):
    """History endpoint requires authentication."""
    create = client.post(
        "/hives",
        headers=auth_headers,
        json={"apiaryId": test_apiary.id, "name": "H-UNAUTH"},
    )
    hive_id = create.json()["id"]

    response = client.get(f"/hives/{hive_id}/history")
    assert response.status_code == 403
