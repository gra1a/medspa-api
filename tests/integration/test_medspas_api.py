import pytest
from fastapi.testclient import TestClient

from app.utils.ulid import generate_id

pytestmark = pytest.mark.integration


def test_list_medspas_empty(client: TestClient):
    r = client.get("/medspas")
    assert r.status_code == 200
    data = r.json()
    assert data["items"] == []
    assert data["next_cursor"] is None
    assert data["limit"] == 20


def test_list_medspas_returns_medspas(client: TestClient, sample_medspa):
    r = client.get("/medspas")
    assert r.status_code == 200
    data = r.json()
    assert len(data["items"]) >= 1
    assert any(m["id"] == sample_medspa.id for m in data["items"])
    assert data["limit"] == 20
    assert "next_cursor" in data


def test_get_medspa_success(client: TestClient, sample_medspa):
    r = client.get(f"/medspas/{sample_medspa.id}")
    assert r.status_code == 200
    data = r.json()
    assert data["id"] == sample_medspa.id
    assert data["name"] == sample_medspa.name


def test_get_medspa_not_found(client: TestClient):
    r = client.get(f"/medspas/{generate_id()}")
    assert r.status_code == 404


def test_list_medspas_pagination_multiple_pages(client: TestClient, multiple_medspas):
    """First page has next_cursor; using it returns next page with no overlap; last page has no next_cursor."""
    all_ids = []
    cursor = None
    for _ in range(4):  # enough to exhaust 5 items with limit=2
        params = {"limit": 2}
        if cursor is not None:
            params["cursor"] = cursor
        r = client.get("/medspas", params=params)
        assert r.status_code == 200
        data = r.json()
        items = data["items"]
        all_ids.extend(m["id"] for m in items)
        if len(items) < 2:
            assert data["next_cursor"] is None
            break
        if data["next_cursor"] is not None:
            assert data["next_cursor"] == items[-1]["id"]
            cursor = data["next_cursor"]
        else:
            break
    assert len(all_ids) == 5
    assert len(set(all_ids)) == 5


def test_list_medspas_pagination_limit_respected(client: TestClient, multiple_medspas):
    r = client.get("/medspas", params={"limit": 1})
    assert r.status_code == 200
    data = r.json()
    assert len(data["items"]) == 1
    assert data["limit"] == 1


def test_list_medspas_pagination_ordered_by_id(client: TestClient, multiple_medspas):
    r = client.get("/medspas", params={"limit": 10})
    assert r.status_code == 200
    items = r.json()["items"]
    ids = [m["id"] for m in items]
    assert ids == sorted(ids)


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
    assert "id" in data
    assert data["address"] == "100 Main St"
