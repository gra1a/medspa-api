import pytest
from fastapi.testclient import TestClient

from app.utils.ulid import generate_ulid

pytestmark = pytest.mark.integration


def test_health(client: TestClient):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_create_service_success(client: TestClient, sample_medspa):
    r = client.post(
        f"/medspas/{sample_medspa.ulid}/services",
        json={
            "name": "Facial",
            "description": "Relaxing facial",
            "price": 8500,
            "duration": 60,
        },
    )
    assert r.status_code == 201
    data = r.json()
    assert data["name"] == "Facial"
    assert data["medspa_id"] == sample_medspa.id
    assert "ulid" in data
    assert data["price"] == 8500
    assert data["duration"] == 60


def test_create_service_medspa_not_found(client: TestClient):
    r = client.post(
        f"/medspas/{generate_ulid()}/services",
        json={"name": "X", "description": "", "price": 1000, "duration": 30},
    )
    assert r.status_code == 404


def test_create_service_negative_price_returns_422(client: TestClient, sample_medspa):
    r = client.post(
        f"/medspas/{sample_medspa.ulid}/services",
        json={"name": "X", "description": "", "price": -1, "duration": 30},
    )
    assert r.status_code == 422


def test_get_service_success(client: TestClient, sample_service):
    r = client.get(f"/services/{sample_service.ulid}")
    assert r.status_code == 200
    assert r.json()["id"] == sample_service.id
    assert r.json()["ulid"] == sample_service.ulid
    assert r.json()["name"] == sample_service.name


def test_get_service_not_found(client: TestClient):
    r = client.get(f"/services/{generate_ulid()}")
    assert r.status_code == 404


def test_list_services_empty(client: TestClient, sample_medspa):
    r = client.get(f"/medspas/{sample_medspa.ulid}/services")
    assert r.status_code == 200
    assert r.json() == []


def test_list_services_returns_medspa_services(client: TestClient, sample_medspa, sample_service):
    r = client.get(f"/medspas/{sample_medspa.ulid}/services")
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 1
    assert data[0]["ulid"] == sample_service.ulid


def test_patch_service_success(client: TestClient, sample_service):
    r = client.patch(
        f"/services/{sample_service.ulid}",
        json={"name": "Updated Name", "price": 7500},
    )
    assert r.status_code == 200
    assert r.json()["name"] == "Updated Name"
    assert r.json()["price"] == 7500


def test_patch_service_not_found(client: TestClient):
    r = client.patch(f"/services/{generate_ulid()}", json={"name": "X"})
    assert r.status_code == 404
