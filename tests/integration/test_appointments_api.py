from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from app.utils.ulid import generate_id

pytestmark = pytest.mark.integration

def test_create_appointment_success(client: TestClient, sample_medspa, sample_service):
    start = (datetime.now(timezone.utc) + timedelta(days=1)).replace(microsecond=0).isoformat()
    r = client.post(
        f"/medspas/{sample_medspa.id}/appointments",
        json={"start_time": start, "service_ids": [sample_service.id]},
    )
    assert r.status_code == 201
    data = r.json()
    assert data["medspa_id"] == sample_medspa.id
    assert "id" in data
    assert data["status"] == "scheduled"
    assert len(data["services"]) == 1
    assert data["total_price"] == 5000
    assert data["total_duration"] == 30


def test_create_appointment_multiple_services(client: TestClient, sample_medspa, sample_services):
    start = (datetime.now(timezone.utc) + timedelta(days=1)).replace(microsecond=0).isoformat()
    r = client.post(
        f"/medspas/{sample_medspa.id}/appointments",
        json={"start_time": start, "service_ids": [s.id for s in sample_services]},
    )
    assert r.status_code == 201
    data = r.json()
    assert len(data["services"]) == 2
    assert data["total_price"] == 3000
    assert data["total_duration"] == 45


def test_create_appointment_medspa_not_found(client: TestClient, sample_service):
    start = (datetime.now(timezone.utc) + timedelta(days=1)).replace(microsecond=0).isoformat()
    r = client.post(
        f"/medspas/{generate_id()}/appointments",
        json={"start_time": start, "service_ids": [sample_service.id]},
    )
    assert r.status_code == 404


def test_create_appointment_past_start_time_returns_400(client: TestClient, sample_medspa, sample_service):
    past = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    r = client.post(
        f"/medspas/{sample_medspa.id}/appointments",
        json={"start_time": past, "service_ids": [sample_service.id]},
    )
    assert r.status_code == 422


def test_get_appointment_success(client: TestClient, sample_appointment):
    r = client.get(f"/appointments/{sample_appointment.id}")
    assert r.status_code == 200
    data = r.json()
    assert data["id"] == sample_appointment.id
    assert len(data["services"]) >= 1


def test_get_appointment_not_found(client: TestClient):
    r = client.get(f"/appointments/{generate_id()}")
    assert r.status_code == 404


def test_patch_appointment_status(client: TestClient, sample_appointment):
    r = client.patch(
        f"/appointments/{sample_appointment.id}",
        json={"status": "completed"},
    )
    assert r.status_code == 200
    assert r.json()["status"] == "completed"


def test_patch_appointment_same_status_returns_200(client: TestClient, sample_appointment):
    """PATCH with same status as current returns 200 and leaves appointment unchanged."""
    r = client.patch(
        f"/appointments/{sample_appointment.id}",
        json={"status": "scheduled"},
    )
    assert r.status_code == 200
    assert r.json()["status"] == "scheduled"


def test_patch_appointment_invalid_status_returns_422(client: TestClient, sample_appointment):
    r = client.patch(
        f"/appointments/{sample_appointment.id}",
        json={"status": "invalid"},
    )
    assert r.status_code == 422


def test_patch_appointment_no_status_returns_422(client: TestClient, sample_appointment):
    r = client.patch(
        f"/appointments/{sample_appointment.id}",
    )
    assert r.status_code == 422


def test_patch_appointment_invalid_transition_returns_400(client: TestClient, sample_appointment):
    """Completed and canceled are final; transitioning back to scheduled returns 400."""
    r = client.patch(
        f"/appointments/{sample_appointment.id}",
        json={"status": "completed"},
    )
    assert r.status_code == 200
    r = client.patch(
        f"/appointments/{sample_appointment.id}",
        json={"status": "scheduled"},
    )
    assert r.status_code == 400
    assert "detail" in r.json()
    assert "Invalid status transition" in r.json()["detail"]


def test_list_appointments(client: TestClient, sample_appointment):
    r = client.get("/appointments")
    assert r.status_code == 200
    data = r.json()
    assert len(data["items"]) >= 1
    ids = [a["id"] for a in data["items"]]
    assert sample_appointment.id in ids
    assert "limit" in data
    assert "next_cursor" in data


def test_list_appointments_invalid_status_returns_422(client: TestClient):
    r = client.get("/appointments", params={"status": "invalid"})
    assert r.status_code == 422


def test_list_appointments_pagination_multiple_pages(client: TestClient, multiple_appointments, sample_medspa):
    """Cursor pagination: first page has next_cursor; second page no overlap; last page next_cursor None."""
    all_ids = []
    cursor = None
    for _ in range(5):
        params = {"limit": 2, "medspa_id": sample_medspa.id}
        if cursor is not None:
            params["cursor"] = cursor
        r = client.get("/appointments", params=params)
        assert r.status_code == 200
        data = r.json()
        items = data["items"]
        all_ids.extend(a["id"] for a in items)
        if len(items) < 2:
            assert data["next_cursor"] is None
            break
        if data["next_cursor"] is not None:
            assert data["next_cursor"] == items[-1]["id"]
            cursor = data["next_cursor"]
        else:
            break
    assert len(all_ids) == 4
    assert len(set(all_ids)) == 4


def test_list_appointments_pagination_ordered_by_id(client: TestClient, multiple_appointments, sample_medspa):
    r = client.get("/appointments", params={"medspa_id": sample_medspa.id, "limit": 10})
    assert r.status_code == 200
    items = r.json()["items"]
    ids = [a["id"] for a in items]
    assert ids == sorted(ids)


def test_create_appointment_same_service_overlapping_returns_409(
    client: TestClient, sample_medspa, sample_service
):
    """POST at time T with service S -> 201; second POST at overlapping time with same service S -> 409."""
    start = (datetime.now(timezone.utc) + timedelta(days=1)).replace(microsecond=0).isoformat()
    r1 = client.post(
        f"/medspas/{sample_medspa.id}/appointments",
        json={"start_time": start, "service_ids": [sample_service.id]},
    )
    assert r1.status_code == 201
    r2 = client.post(
        f"/medspas/{sample_medspa.id}/appointments",
        json={"start_time": start, "service_ids": [sample_service.id]},
    )
    assert r2.status_code == 409
    assert "conflict" in r2.json().get("detail", "").lower() or "booked" in r2.json().get("detail", "").lower()


def test_create_appointment_same_time_different_service_returns_201(
    client: TestClient, sample_medspa, sample_services
):
    """POST at same time T with a different service (same medspa) -> 201 (no conflict)."""
    start = (datetime.now(timezone.utc) + timedelta(days=1)).replace(microsecond=0).isoformat()
    r1 = client.post(
        f"/medspas/{sample_medspa.id}/appointments",
        json={"start_time": start, "service_ids": [sample_services[0].id]},
    )
    assert r1.status_code == 201
    r2 = client.post(
        f"/medspas/{sample_medspa.id}/appointments",
        json={"start_time": start, "service_ids": [sample_services[1].id]},
    )
    assert r2.status_code == 201
