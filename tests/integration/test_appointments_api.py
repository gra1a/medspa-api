from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from app.utils.ulid import generate_ulid

pytestmark = pytest.mark.integration

def test_create_appointment_success(client: TestClient, sample_medspa, sample_service):
    start = (datetime.now(timezone.utc) + timedelta(days=1)).replace(microsecond=0).isoformat()
    r = client.post(
        f"/medspas/{sample_medspa.ulid}/appointments",
        json={"start_time": start, "service_ulids": [sample_service.ulid]},
    )
    assert r.status_code == 201
    data = r.json()
    assert data["medspa_id"] == sample_medspa.id
    assert "ulid" in data
    assert data["status"] == "scheduled"
    assert len(data["services"]) == 1
    assert data["total_price"] == 5000
    assert data["total_duration"] == 30


def test_create_appointment_multiple_services(client: TestClient, sample_medspa, sample_services):
    start = (datetime.now(timezone.utc) + timedelta(days=1)).replace(microsecond=0).isoformat()
    r = client.post(
        f"/medspas/{sample_medspa.ulid}/appointments",
        json={"start_time": start, "service_ulids": [s.ulid for s in sample_services]},
    )
    assert r.status_code == 201
    data = r.json()
    assert len(data["services"]) == 2
    assert data["total_price"] == 3000
    assert data["total_duration"] == 45


def test_create_appointment_medspa_not_found(client: TestClient, sample_service):
    start = (datetime.now(timezone.utc) + timedelta(days=1)).replace(microsecond=0).isoformat()
    r = client.post(
        f"/medspas/{generate_ulid()}/appointments",
        json={"start_time": start, "service_ulids": [sample_service.ulid]},
    )
    assert r.status_code == 404


def test_create_appointment_past_start_time_returns_400(client: TestClient, sample_medspa, sample_service):
    past = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    r = client.post(
        f"/medspas/{sample_medspa.ulid}/appointments",
        json={"start_time": past, "service_ulids": [sample_service.ulid]},
    )
    assert r.status_code == 422


def test_get_appointment_success(client: TestClient, sample_appointment):
    r = client.get(f"/appointments/{sample_appointment.ulid}")
    assert r.status_code == 200
    data = r.json()
    assert data["id"] == sample_appointment.id
    assert data["ulid"] == sample_appointment.ulid
    assert len(data["services"]) >= 1


def test_get_appointment_not_found(client: TestClient):
    r = client.get(f"/appointments/{generate_ulid()}")
    assert r.status_code == 404


def test_patch_appointment_status(client: TestClient, sample_appointment):
    r = client.patch(
        f"/appointments/{sample_appointment.ulid}",
        json={"status": "completed"},
    )
    assert r.status_code == 200
    assert r.json()["status"] == "completed"


def test_patch_appointment_invalid_status_returns_422(client: TestClient, sample_appointment):
    r = client.patch(
        f"/appointments/{sample_appointment.ulid}",
        json={"status": "invalid"},
    )
    assert r.status_code == 422


def test_patch_appointment_no_status_returns_422(client: TestClient, sample_appointment):
    r = client.patch(
        f"/appointments/{sample_appointment.ulid}",
    )
    assert r.status_code == 422


def test_list_appointments(client: TestClient, sample_appointment):
    r = client.get("/appointments")
    assert r.status_code == 200
    data = r.json()
    assert len(data) >= 1
    ulids = [a["ulid"] for a in data]
    assert sample_appointment.ulid in ulids


def test_list_appointments_invalid_status_returns_422(client: TestClient):
    r = client.get("/appointments", params={"status": "invalid"})
    assert r.status_code == 422
