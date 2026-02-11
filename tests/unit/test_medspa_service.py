"""Unit tests for MedspaService — all repository and external dependencies are mocked."""

from contextlib import contextmanager
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.exc import IntegrityError

from app.exceptions import ConflictError, NotFoundError
from app.models.models import Medspa
from app.schemas.medspas import MedspaCreate
from app.services.medspa_service import MedspaService

pytestmark = pytest.mark.unit

MEDSPA_ID = "01MYYYYYYYYYYYYYYYYYYYYYYYY"
FAKE_ID = "01HXXXXXXXXXXXXXXXXXXXXXXX"


@contextmanager
def _noop_transaction(session):
    yield session


def _make_medspa(id=MEDSPA_ID, name="Test MedSpa"):
    m = MagicMock(spec=Medspa)
    m.id = id
    m.name = name
    m.address = "123 Test St"
    m.phone_number = "(512) 555-0100"
    m.email = "test@test.com"
    return m


# ---------------------------------------------------------------------------
# get_medspa
# ---------------------------------------------------------------------------
class TestGetMedspa:
    @patch("app.services.medspa_service.get_by_id")
    def test_found(self, mock_get_by_id):
        medspa = _make_medspa()
        mock_get_by_id.return_value = medspa

        db = MagicMock()
        result = MedspaService.get_medspa(db, MEDSPA_ID)
        assert result.id == MEDSPA_ID
        assert result.name == "Test MedSpa"
        mock_get_by_id.assert_called_once_with(db, Medspa, MEDSPA_ID, "Medspa not found")

    @patch("app.services.medspa_service.get_by_id")
    def test_not_found(self, mock_get_by_id):
        mock_get_by_id.side_effect = NotFoundError("Medspa not found")

        db = MagicMock()
        with pytest.raises(NotFoundError, match="Medspa not found"):
            MedspaService.get_medspa(db, MEDSPA_ID)


# ---------------------------------------------------------------------------
# list_medspas
# ---------------------------------------------------------------------------
@patch("app.services.medspa_service.MedspaRepository")
class TestListMedspas:
    def test_empty(self, mock_repo):
        mock_repo.list.return_value = []

        db = MagicMock()
        items, next_cursor = MedspaService.list_medspas(db, limit=20)
        assert items == []
        assert next_cursor is None

    def test_returns_items(self, mock_repo):
        medspa = _make_medspa()
        mock_repo.list.return_value = [medspa]

        db = MagicMock()
        items, next_cursor = MedspaService.list_medspas(db, limit=20)
        assert len(items) == 1
        assert items[0].id == MEDSPA_ID
        assert next_cursor is None

    def test_next_cursor_set_when_more_results(self, mock_repo):
        m1 = _make_medspa(id="01AAAAAAAAAAAAAAAAAAAAAAAAA")
        m2 = _make_medspa(id="01BBBBBBBBBBBBBBBBBBBBBBBBB")
        m3 = _make_medspa(id="01CCCCCCCCCCCCCCCCCCCCCCCCC")  # extra item signals more pages
        mock_repo.list.return_value = [m1, m2, m3]

        db = MagicMock()
        items, next_cursor = MedspaService.list_medspas(db, limit=2)
        assert len(items) == 2
        assert next_cursor == "01BBBBBBBBBBBBBBBBBBBBBBBBB"

    def test_next_cursor_none_when_no_more(self, mock_repo):
        mock_repo.list.return_value = [_make_medspa()]

        db = MagicMock()
        items, next_cursor = MedspaService.list_medspas(db, limit=20)
        assert len(items) == 1
        assert next_cursor is None

    def test_cursor_forwarded_to_repo(self, mock_repo):
        mock_repo.list.return_value = []

        db = MagicMock()
        MedspaService.list_medspas(db, cursor="some-cursor", limit=10)
        mock_repo.list.assert_called_once_with(db, cursor="some-cursor", limit=10)


# ---------------------------------------------------------------------------
# create_medspa
# ---------------------------------------------------------------------------
@patch("app.services.medspa_service.transaction", _noop_transaction)
@patch("app.services.medspa_service.generate_id", return_value=FAKE_ID)
@patch("app.services.medspa_service.MedspaRepository")
class TestCreateMedspa:
    def test_success(self, mock_repo, _gen_id):
        mock_repo.create.side_effect = lambda db, medspa: medspa

        db = MagicMock()
        data = MedspaCreate(
            name="New MedSpa",
            address="100 Main St",
            phone_number="512-555-1234",
            email="contact@example.com",
        )

        result = MedspaService.create_medspa(db, data)
        assert result.id == FAKE_ID
        assert result.name == "New MedSpa"
        assert result.address == "100 Main St"
        mock_repo.create.assert_called_once()

    def test_duplicate_name_raises_conflict(self, mock_repo, _gen_id):
        mock_repo.create.side_effect = IntegrityError("stmt", {}, Exception("duplicate"))

        db = MagicMock()
        data = MedspaCreate(
            name="Duplicate MedSpa",
            address="100 Main St",
            phone_number="512-555-1234",
            email="first@example.com",
        )

        with pytest.raises(ConflictError, match="already exists"):
            MedspaService.create_medspa(db, data)
