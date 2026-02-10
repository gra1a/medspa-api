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
    data = r.json()
    assert data["items"] == []
    assert data["next_cursor"] is None


def test_list_services_returns_medspa_services(client: TestClient, sample_medspa, sample_service):
    r = client.get(f"/medspas/{sample_medspa.ulid}/services")
    assert r.status_code == 200
    data = r.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["ulid"] == sample_service.ulid
    assert "next_cursor" in data


def test_list_services_pagination_multiple_pages(client: TestClient, sample_medspa, sample_services):
    """With 2 services, limit=1: first page has next_cursor; second page has 1 item and next_cursor None."""
    r = client.get(f"/medspas/{sample_medspa.ulid}/services", params={"limit": 1})
    assert r.status_code == 200
    data = r.json()
    assert len(data["items"]) == 1
    assert data["next_cursor"] is not None
    assert data["next_cursor"] == data["items"][0]["ulid"]
    r2 = client.get(
        f"/medspas/{sample_medspa.ulid}/services",
        params={"limit": 1, "cursor": data["next_cursor"]},
    )
    assert r2.status_code == 200
    data2 = r2.json()
    assert len(data2["items"]) == 1
    assert data2["next_cursor"] is None
    assert data["items"][0]["ulid"] != data2["items"][0]["ulid"]


def test_list_services_pagination_ordered_by_ulid(client: TestClient, sample_medspa, sample_services):
    r = client.get(f"/medspas/{sample_medspa.ulid}/services", params={"limit": 10})
    assert r.status_code == 200
    items = r.json()["items"]
    ulids = [s["ulid"] for s in items]
    assert ulids == sorted(ulids)


def test_patch_service_success(client: TestClient, sample_service):
    r = client.patch(
        f"/services/{sample_service.ulid}",
        json={"name": "Updated Name", "price": 7500},
    )
    assert r.status_code == 200
    assert r.json()["name"] == "Updated Name"
    assert r.json()["price"] == 7500


def test_patch_service_updates_all_four_fields(client: TestClient, sample_service):
    """Spec: Update a service (name, description, price, duration). All four must be updatable."""
    r = client.patch(
        f"/services/{sample_service.ulid}",
        json={
            "name": "New Name",
            "description": "New description",
            "price": 12000,
            "duration": 90,
        },
    )
    assert r.status_code == 200
    data = r.json()
    assert data["name"] == "New Name"
    assert data["description"] == "New description"
    assert data["price"] == 12000
    assert data["duration"] == 90
    assert data["ulid"] == sample_service.ulid
    assert data["medspa_id"] == sample_service.medspa_id


def test_patch_service_not_found(client: TestClient):
    r = client.patch(f"/services/{generate_ulid()}", json={"name": "X"})
    assert r.status_code == 404
