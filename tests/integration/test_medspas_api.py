import pytest
from fastapi.testclient import TestClient

from app.utils.ulid import generate_ulid

pytestmark = pytest.mark.integration


def test_list_medspas_empty(client: TestClient):
    r = client.get("/medspas")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_list_medspas_returns_medspas(client: TestClient, sample_medspa):
    r = client.get("/medspas")
    assert r.status_code == 200
    data = r.json()
    assert len(data) >= 1
    assert any(m["ulid"] == sample_medspa.ulid for m in data)


def test_get_medspa_success(client: TestClient, sample_medspa):
    r = client.get(f"/medspas/{sample_medspa.ulid}")
    assert r.status_code == 200
    data = r.json()
    assert data["id"] == sample_medspa.id
    assert data["ulid"] == sample_medspa.ulid
    assert data["name"] == sample_medspa.name


def test_get_medspa_not_found(client: TestClient):
    r = client.get(f"/medspas/{generate_ulid()}")
    assert r.status_code == 404


def test_create_medspa_success(client: TestClient):
    r = client.post(
        "/medspas",
        json={
            "name": "New MedSpa",
            "address": "100 Main St",
            "phone_number": "555-1234",
            "email": "contact@newmedspa.com",
        },
    )
    assert r.status_code == 201
    data = r.json()
    assert data["name"] == "New MedSpa"
    assert "ulid" in data
    assert data["address"] == "100 Main St"
