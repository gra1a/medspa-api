"""Unit tests for OfferingsService — all repository and external dependencies are mocked."""

from contextlib import contextmanager
from unittest.mock import MagicMock, patch

import pytest

from app.exceptions import NotFoundError
from app.models.models import Medspa, Service
from app.schemas.services import ServiceCreate, ServiceUpdate
from app.services.offerings_service import OfferingsService

pytestmark = pytest.mark.unit

MEDSPA_ID = "01MYYYYYYYYYYYYYYYYYYYYYYYY"
SERVICE_ID = "01SAAAAAAAAAAAAAAAAAAAAAAAA"
FAKE_ID = "01HXXXXXXXXXXXXXXXXXXXXXXX"


@contextmanager
def _noop_transaction(session):
    yield session


def _make_medspa(id=MEDSPA_ID):
    m = MagicMock(spec=Medspa)
    m.id = id
    return m


def _make_service(id=SERVICE_ID, medspa_id=MEDSPA_ID, name="Test Service", price=5000, duration=30):
    s = MagicMock(spec=Service)
    s.id = id
    s.medspa_id = medspa_id
    s.name = name
    s.description = "A test"
    s.price = price
    s.duration = duration
    return s


# ---------------------------------------------------------------------------
# create_service
# ---------------------------------------------------------------------------
@patch("app.services.offerings_service.transaction", _noop_transaction)
@patch("app.services.offerings_service.generate_id", return_value=FAKE_ID)
@patch("app.services.offerings_service.ServiceRepository")
@patch("app.services.offerings_service.MedspaService")
class TestCreateService:
    def test_success(self, mock_medspa_svc, mock_service_repo, _gen_id):
        medspa = _make_medspa()
        mock_medspa_svc.get_medspa.return_value = medspa
        mock_service_repo.create.side_effect = lambda db, service: service

        db = MagicMock()
        data = ServiceCreate(name="New Service", description="Desc", price=2500, duration=45)

        result = OfferingsService.create_service(db, MEDSPA_ID, data)
        assert result.id == FAKE_ID
        assert result.name == "New Service"
        assert result.medspa_id == MEDSPA_ID
        mock_service_repo.create.assert_called_once()

    def test_medspa_not_found(self, mock_medspa_svc, mock_service_repo, _gen_id):
        mock_medspa_svc.get_medspa.side_effect = NotFoundError("Medspa not found")

        db = MagicMock()
        data = ServiceCreate(name="X", price=1000, duration=30)

        with pytest.raises(NotFoundError, match="Medspa not found"):
            OfferingsService.create_service(db, "nonexistent-id", data)


# ---------------------------------------------------------------------------
# get_service
# ---------------------------------------------------------------------------
class TestGetService:
    @patch("app.services.offerings_service.get_by_id")
    def test_exists(self, mock_get_by_id):
        service = _make_service()
        mock_get_by_id.return_value = service

        db = MagicMock()
        result = OfferingsService.get_service(db, SERVICE_ID)
        assert result.id == SERVICE_ID
        assert result.name == "Test Service"
        mock_get_by_id.assert_called_once_with(db, Service, SERVICE_ID, "Service not found")

    @patch("app.services.offerings_service.get_by_id")
    def test_not_found(self, mock_get_by_id):
        mock_get_by_id.side_effect = NotFoundError("Service not found")

        db = MagicMock()
        with pytest.raises(NotFoundError, match="Service not found"):
            OfferingsService.get_service(db, "nonexistent-id")


# ---------------------------------------------------------------------------
# list_services_by_medspa
# ---------------------------------------------------------------------------
@patch("app.services.offerings_service.ServiceRepository")
@patch("app.services.offerings_service.MedspaService")
class TestListServicesByMedspa:
    def test_empty(self, mock_medspa_svc, mock_service_repo):
        mock_medspa_svc.get_medspa.return_value = _make_medspa()
        mock_service_repo.list_by_medspa_id.return_value = []

        db = MagicMock()
        items, next_cursor = OfferingsService.list_services_by_medspa(db, MEDSPA_ID, limit=20)
        assert items == []
        assert next_cursor is None

    def test_returns_services(self, mock_medspa_svc, mock_service_repo):
        medspa = _make_medspa()
        service = _make_service()
        mock_medspa_svc.get_medspa.return_value = medspa
        mock_service_repo.list_by_medspa_id.return_value = [service]

        db = MagicMock()
        items, next_cursor = OfferingsService.list_services_by_medspa(db, MEDSPA_ID, limit=20)
        assert len(items) == 1
        assert items[0].id == SERVICE_ID


# ---------------------------------------------------------------------------
# update_service
# ---------------------------------------------------------------------------
@patch("app.services.offerings_service.transaction", _noop_transaction)
@patch("app.services.offerings_service.ServiceRepository")
@patch("app.services.offerings_service.get_by_id")
class TestUpdateService:
    def test_partial_update(self, mock_get_by_id, mock_service_repo):
        service = _make_service(name="Old Name", price=5000)
        mock_get_by_id.return_value = service
        mock_service_repo.update.side_effect = lambda db, s: s

        db = MagicMock()
        data = ServiceUpdate(name="Updated")
        result = OfferingsService.update_service(db, SERVICE_ID, data)
        assert result.name == "Updated"
        assert result.price == 5000  # unchanged

    def test_all_four_fields(self, mock_get_by_id, mock_service_repo):
        service = _make_service()
        mock_get_by_id.return_value = service
        mock_service_repo.update.side_effect = lambda db, s: s

        db = MagicMock()
        data = ServiceUpdate(
            name="New Name", description="New description", price=9999, duration=120
        )
        result = OfferingsService.update_service(db, SERVICE_ID, data)
        assert result.name == "New Name"
        assert result.description == "New description"
        assert result.price == 9999
        assert result.duration == 120
        assert result.id == SERVICE_ID

    def test_not_found(self, mock_get_by_id, mock_service_repo):
        mock_get_by_id.side_effect = NotFoundError("Service not found")

        db = MagicMock()
        with pytest.raises(NotFoundError, match="Service not found"):
            OfferingsService.update_service(db, "nonexistent-id", ServiceUpdate(name="X"))
