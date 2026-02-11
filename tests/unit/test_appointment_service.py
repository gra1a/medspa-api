"""Unit tests for AppointmentService — all repository and external dependencies are mocked."""

from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest

from app.exceptions import BadRequestError, ConflictError, NotFoundError
from app.models.models import Appointment, Medspa, Service
from app.schemas.appointments import AppointmentCreate, AppointmentStatus
from app.services.appointment_service import AppointmentService

pytestmark = pytest.mark.unit

FAKE_ID = "01HXXXXXXXXXXXXXXXXXXXXXXX"
MEDSPA_ID = "01MYYYYYYYYYYYYYYYYYYYYYYYY"
SERVICE_ID_1 = "01SAAAAAAAAAAAAAAAAAAAAAAAA"
SERVICE_ID_2 = "01SBBBBBBBBBBBBBBBBBBBBBBB"
APPOINTMENT_ID = "01APPPPPPPPPPPPPPPPPPPPPPP"


@contextmanager
def _noop_transaction(session):
    yield session


def _make_medspa(id=MEDSPA_ID):
    m = MagicMock(spec=Medspa)
    m.id = id
    m.name = "Test MedSpa"
    return m


def _make_service(id=SERVICE_ID_1, medspa_id=MEDSPA_ID, price=5000, duration=30):
    s = MagicMock(spec=Service)
    s.id = id
    s.medspa_id = medspa_id
    s.price = price
    s.duration = duration
    s.name = "Test Service"
    return s


def _make_appointment(id=APPOINTMENT_ID, medspa_id=MEDSPA_ID, status="scheduled"):
    a = MagicMock(spec=Appointment)
    a.id = id
    a.medspa_id = medspa_id
    a.status = status
    return a


# ---------------------------------------------------------------------------
# create_appointment
# ---------------------------------------------------------------------------
@patch("app.services.appointment_service.transaction", _noop_transaction)
@patch("app.services.appointment_service.generate_id", return_value=FAKE_ID)
@patch("app.services.appointment_service.AppointmentRepository")
@patch("app.services.appointment_service.ServiceRepository")
@patch("app.services.appointment_service.MedspaService")
class TestCreateAppointment:
    def test_services_not_found_raises(
        self, mock_medspa_svc, mock_service_repo, mock_appt_repo, _gen_id
    ):
        mock_medspa_svc.get_medspa.return_value = _make_medspa()
        mock_service_repo.find_by_ids.return_value = []  # none found

        db = MagicMock()
        start = (datetime.now(timezone.utc) + timedelta(days=1)).replace(microsecond=0)
        data = AppointmentCreate(start_time=start, service_ids=[SERVICE_ID_1, SERVICE_ID_2])

        with pytest.raises(NotFoundError, match="Service\\(s\\) not found"):
            AppointmentService.create_appointment(db, MEDSPA_ID, data)

    def test_start_time_in_past_raises(
        self, mock_medspa_svc, mock_service_repo, mock_appt_repo, _gen_id
    ):
        """Service enforces past-time check for callers that bypass the Pydantic schema."""
        db = MagicMock()
        start = (datetime.now(timezone.utc) - timedelta(hours=1)).replace(microsecond=0)
        data = AppointmentCreate.model_construct(start_time=start, service_ids=[SERVICE_ID_1])

        with pytest.raises(BadRequestError, match="start_time cannot be in the past"):
            AppointmentService.create_appointment(db, MEDSPA_ID, data)

        # Should fail before ever looking up the medspa
        mock_medspa_svc.get_medspa.assert_not_called()

    def test_naive_start_time_treated_as_utc(
        self, mock_medspa_svc, mock_service_repo, mock_appt_repo, _gen_id
    ):
        """Naive datetime is coerced to UTC so the past-time check and create succeed."""
        medspa = _make_medspa()
        service = _make_service()
        mock_medspa_svc.get_medspa.return_value = medspa
        mock_service_repo.find_by_ids.return_value = [service]
        mock_appt_repo.find_scheduled_overlapping.return_value = []
        created = _make_appointment(id=FAKE_ID)
        mock_appt_repo.create_with_services.return_value = created

        db = MagicMock()
        start_naive = (datetime.now(timezone.utc) + timedelta(days=1)).replace(tzinfo=None)
        data = AppointmentCreate(start_time=start_naive, service_ids=[SERVICE_ID_1])

        result = AppointmentService.create_appointment(db, MEDSPA_ID, data)
        assert result.id == FAKE_ID
        assert result.medspa_id == MEDSPA_ID

    def test_service_from_other_medspa_raises(
        self, mock_medspa_svc, mock_service_repo, mock_appt_repo, _gen_id
    ):
        medspa = _make_medspa()
        own_service = _make_service(id=SERVICE_ID_1, medspa_id=MEDSPA_ID)
        other_service = _make_service(id=SERVICE_ID_2, medspa_id="other-medspa-id")
        mock_medspa_svc.get_medspa.return_value = medspa
        mock_service_repo.find_by_ids.return_value = [own_service, other_service]

        db = MagicMock()
        start = (datetime.now(timezone.utc) + timedelta(days=1)).replace(microsecond=0)
        data = AppointmentCreate(start_time=start, service_ids=[SERVICE_ID_1, SERVICE_ID_2])

        with pytest.raises(BadRequestError, match="All services must belong to the same medspa"):
            AppointmentService.create_appointment(db, MEDSPA_ID, data)

    def test_succeeds_when_no_overlap(
        self, mock_medspa_svc, mock_service_repo, mock_appt_repo, _gen_id
    ):
        medspa = _make_medspa()
        service = _make_service()
        mock_medspa_svc.get_medspa.return_value = medspa
        mock_service_repo.find_by_ids.return_value = [service]
        mock_appt_repo.find_scheduled_overlapping.return_value = []
        created = _make_appointment(id=FAKE_ID, status="scheduled")
        mock_appt_repo.create_with_services.return_value = created

        db = MagicMock()
        start = (datetime.now(timezone.utc) + timedelta(days=1)).replace(microsecond=0)
        data = AppointmentCreate(start_time=start, service_ids=[SERVICE_ID_1])

        result = AppointmentService.create_appointment(db, MEDSPA_ID, data)
        assert result.id == FAKE_ID
        assert result.status == "scheduled"
        mock_appt_repo.create_with_services.assert_called_once()

    def test_raises_conflict_when_overlapping(
        self, mock_medspa_svc, mock_service_repo, mock_appt_repo, _gen_id
    ):
        medspa = _make_medspa()
        service = _make_service()
        mock_medspa_svc.get_medspa.return_value = medspa
        mock_service_repo.find_by_ids.return_value = [service]
        mock_appt_repo.find_scheduled_overlapping.return_value = [_make_appointment()]

        db = MagicMock()
        start = (datetime.now(timezone.utc) + timedelta(days=1)).replace(microsecond=0)
        data = AppointmentCreate(start_time=start, service_ids=[SERVICE_ID_1])

        with pytest.raises(ConflictError, match="already booked for this time slot"):
            AppointmentService.create_appointment(db, MEDSPA_ID, data)

    def test_computes_total_price_and_duration(
        self, mock_medspa_svc, mock_service_repo, mock_appt_repo, _gen_id
    ):
        """Verify the service aggregates price/duration from the selected services."""
        medspa = _make_medspa()
        s1 = _make_service(id=SERVICE_ID_1, price=1000, duration=15)
        s2 = _make_service(id=SERVICE_ID_2, price=2000, duration=30)
        mock_medspa_svc.get_medspa.return_value = medspa
        mock_service_repo.find_by_ids.return_value = [s1, s2]
        mock_appt_repo.find_scheduled_overlapping.return_value = []
        mock_appt_repo.create_with_services.side_effect = lambda db, appt, sids: appt

        db = MagicMock()
        start = (datetime.now(timezone.utc) + timedelta(days=1)).replace(microsecond=0)
        data = AppointmentCreate(start_time=start, service_ids=[SERVICE_ID_1, SERVICE_ID_2])

        result = AppointmentService.create_appointment(db, MEDSPA_ID, data)
        assert result.total_price == 3000
        assert result.total_duration == 45


# ---------------------------------------------------------------------------
# list_appointments
# ---------------------------------------------------------------------------
@patch("app.services.appointment_service.AppointmentRepository")
class TestListAppointments:
    @patch("app.services.appointment_service.MedspaService")
    def test_filter_by_medspa_id(self, mock_medspa_svc, mock_appt_repo):
        medspa = _make_medspa()
        mock_medspa_svc.get_medspa.return_value = medspa
        appt = _make_appointment()
        mock_appt_repo.list.return_value = [appt]

        db = MagicMock()
        items, cursor = AppointmentService.list_appointments(db, medspa_id=MEDSPA_ID, limit=20)

        assert len(items) == 1
        assert items[0].medspa_id == MEDSPA_ID
        mock_appt_repo.list.assert_called_once_with(
            db, medspa_id=medspa.id, status=None, cursor=None, limit=20
        )

    def test_filter_by_status(self, mock_appt_repo):
        appt = _make_appointment()
        mock_appt_repo.list.return_value = [appt]

        db = MagicMock()
        items, cursor = AppointmentService.list_appointments(
            db, status=AppointmentStatus.SCHEDULED, limit=20
        )

        assert len(items) == 1
        mock_appt_repo.list.assert_called_once_with(
            db, medspa_id=None, status=AppointmentStatus.SCHEDULED, cursor=None, limit=20
        )

    def test_next_cursor_set_when_more_results(self, mock_appt_repo):
        a1 = _make_appointment(id="01A")
        a2 = _make_appointment(id="01B")
        a3 = _make_appointment(id="01C")  # extra item signals more pages
        mock_appt_repo.list.return_value = [a1, a2, a3]

        db = MagicMock()
        items, cursor = AppointmentService.list_appointments(db, limit=2)
        assert len(items) == 2
        assert cursor == "01B"

    def test_next_cursor_none_when_no_more(self, mock_appt_repo):
        mock_appt_repo.list.return_value = [_make_appointment()]

        db = MagicMock()
        items, cursor = AppointmentService.list_appointments(db, limit=20)
        assert len(items) == 1
        assert cursor is None


# ---------------------------------------------------------------------------
# update_status
# ---------------------------------------------------------------------------
@patch("app.services.appointment_service.transaction", _noop_transaction)
@patch("app.services.appointment_service.AppointmentRepository")
class TestUpdateStatus:
    def test_scheduled_to_completed(self, mock_appt_repo):
        appt = _make_appointment(status="scheduled")
        mock_appt_repo.get_by_id.return_value = appt
        mock_appt_repo.update.return_value = appt

        db = MagicMock()
        result = AppointmentService.update_status(db, APPOINTMENT_ID, AppointmentStatus.COMPLETED)
        assert result.status == AppointmentStatus.COMPLETED
        mock_appt_repo.update.assert_called_once()

    def test_scheduled_to_canceled(self, mock_appt_repo):
        appt = _make_appointment(status="scheduled")
        mock_appt_repo.get_by_id.return_value = appt
        mock_appt_repo.update.return_value = appt

        db = MagicMock()
        result = AppointmentService.update_status(db, APPOINTMENT_ID, AppointmentStatus.CANCELED)
        assert result.status == AppointmentStatus.CANCELED
        mock_appt_repo.update.assert_called_once()

    def test_same_status_returns_without_persisting(self, mock_appt_repo):
        appt = _make_appointment(status="scheduled")
        mock_appt_repo.get_by_id.return_value = appt

        db = MagicMock()
        result = AppointmentService.update_status(db, APPOINTMENT_ID, AppointmentStatus.SCHEDULED)
        assert result is appt
        mock_appt_repo.update.assert_not_called()

    def test_completed_to_scheduled_raises(self, mock_appt_repo):
        appt = _make_appointment(status="completed")
        mock_appt_repo.get_by_id.return_value = appt

        db = MagicMock()
        with pytest.raises(BadRequestError, match="Invalid status transition"):
            AppointmentService.update_status(db, APPOINTMENT_ID, AppointmentStatus.SCHEDULED)

    def test_canceled_to_completed_raises(self, mock_appt_repo):
        appt = _make_appointment(status="canceled")
        mock_appt_repo.get_by_id.return_value = appt

        db = MagicMock()
        with pytest.raises(BadRequestError, match="Invalid status transition"):
            AppointmentService.update_status(db, APPOINTMENT_ID, AppointmentStatus.COMPLETED)

    def test_completed_to_canceled_raises(self, mock_appt_repo):
        appt = _make_appointment(status="completed")
        mock_appt_repo.get_by_id.return_value = appt

        db = MagicMock()
        with pytest.raises(BadRequestError, match="Invalid status transition"):
            AppointmentService.update_status(db, APPOINTMENT_ID, AppointmentStatus.CANCELED)
