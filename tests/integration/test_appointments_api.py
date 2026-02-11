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


def test_create_appointment_past_start_time_returns_400(
    client: TestClient, sample_medspa, sample_service
):
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


def test_list_appointments_pagination_multiple_pages(
    client: TestClient, multiple_appointments, sample_medspa
):
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


def test_list_appointments_pagination_ordered_by_id(
    client: TestClient, multiple_appointments, sample_medspa
):
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
    assert (
        "conflict" in r2.json().get("detail", "").lower()
        or "booked" in r2.json().get("detail", "").lower()
    )


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


def test_list_medspa_appointments(client: TestClient, sample_appointment, sample_medspa):
    """GET /medspas/{medspa_id}/appointments returns 200 with the medspa's appointments."""
    r = client.get(f"/medspas/{sample_medspa.id}/appointments")
    assert r.status_code == 200
    data = r.json()
    assert "items" in data
    assert "limit" in data
    assert "next_cursor" in data
    ids = [a["id"] for a in data["items"]]
    assert sample_appointment.id in ids
    assert all(a["medspa_id"] == sample_medspa.id for a in data["items"])


def test_list_medspa_appointments_not_found(client: TestClient):
    """Returns 404 when medspa_id does not exist."""
    r = client.get(f"/medspas/{generate_id()}/appointments")
    assert r.status_code == 404


def test_list_medspa_appointments_filters_by_medspa(client: TestClient, sample_medspa, sample_appointment):
    """Nested endpoint returns only appointments for that medspa."""
    # Create second medspa with its own service and appointment via API
    r_medspa = client.post(
        "/medspas",
        json={
            "name": "Other MedSpa",
            "address": "456 Other St",
            "phone_number": "512-555-9999",
            "email": "other@test.com",
        },
    )
    assert r_medspa.status_code == 201
    medspa_b_id = r_medspa.json()["id"]
    r_svc = client.post(
        f"/medspas/{medspa_b_id}/services",
        json={"name": "Other Service", "description": "", "price": 2000, "duration": 20},
    )
    assert r_svc.status_code == 201
    svc_b_id = r_svc.json()["id"]
    start = (datetime.now(timezone.utc) + timedelta(days=2)).replace(microsecond=0).isoformat()
    r_appt = client.post(
        f"/medspas/{medspa_b_id}/appointments",
        json={"start_time": start, "service_ids": [svc_b_id]},
    )
    assert r_appt.status_code == 201
    appt_b_id = r_appt.json()["id"]
    # List for medspa A: only A's appointment
    r_a = client.get(f"/medspas/{sample_medspa.id}/appointments")
    assert r_a.status_code == 200
    ids_a = [a["id"] for a in r_a.json()["items"]]
    assert sample_appointment.id in ids_a
    assert appt_b_id not in ids_a
    # List for medspa B: only B's appointment
    r_b = client.get(f"/medspas/{medspa_b_id}/appointments")
    assert r_b.status_code == 200
    ids_b = [a["id"] for a in r_b.json()["items"]]
    assert appt_b_id in ids_b
    assert sample_appointment.id not in ids_b


def test_list_medspa_appointments_status_filter(client: TestClient, sample_medspa, sample_appointment):
    """Nested endpoint respects status query param."""
    r = client.get(
        f"/medspas/{sample_medspa.id}/appointments",
        params={"status": "scheduled"},
    )
    assert r.status_code == 200
    items = r.json()["items"]
    assert any(a["id"] == sample_appointment.id for a in items)
    assert all(a["status"] == "scheduled" for a in items)
    r_completed = client.get(
        f"/medspas/{sample_medspa.id}/appointments",
        params={"status": "completed"},
    )
    assert r_completed.status_code == 200
    assert len(r_completed.json()["items"]) == 0
    # Complete the appointment and query again
    client.patch(f"/appointments/{sample_appointment.id}", json={"status": "completed"})
    r_after = client.get(
        f"/medspas/{sample_medspa.id}/appointments",
        params={"status": "completed"},
    )
    assert r_after.status_code == 200
    assert len(r_after.json()["items"]) == 1
    assert r_after.json()["items"][0]["status"] == "completed"


def test_list_appointments_returns_all_medspas(client: TestClient, sample_medspa, sample_appointment):
    """GET /appointments without medspa_id returns appointments from all medspas."""
    # Create second medspa with service and appointment via API
    r_medspa = client.post(
        "/medspas",
        json={
            "name": "Second MedSpa",
            "address": "789 Second St",
            "phone_number": "512-555-8888",
            "email": "second@test.com",
        },
    )
    assert r_medspa.status_code == 201
    medspa2_id = r_medspa.json()["id"]
    r_svc = client.post(
        f"/medspas/{medspa2_id}/services",
        json={"name": "Second Service", "description": "", "price": 1000, "duration": 15},
    )
    assert r_svc.status_code == 201
    svc2_id = r_svc.json()["id"]
    start = (datetime.now(timezone.utc) + timedelta(days=3)).replace(microsecond=0).isoformat()
    r_appt = client.post(
        f"/medspas/{medspa2_id}/appointments",
        json={"start_time": start, "service_ids": [svc2_id]},
    )
    assert r_appt.status_code == 201
    appt2_id = r_appt.json()["id"]
    r = client.get("/appointments")
    assert r.status_code == 200
    ids = [a["id"] for a in r.json()["items"]]
    assert sample_appointment.id in ids
    assert appt2_id in ids
