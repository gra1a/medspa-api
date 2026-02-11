from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.orm import Session

from app.exceptions import BadRequestError, ConflictError, NotFoundError
from app.models.models import Medspa, Service
from app.schemas.appointments import AppointmentCreate
from app.services.appointment_service import AppointmentService
from app.utils.ulid import generate_id

pytestmark = pytest.mark.unit


def test_create_appointment_services_not_found(db_session: Session, sample_medspa: Medspa):
    start = (datetime.now(timezone.utc) + timedelta(days=1)).replace(microsecond=0)
    data = AppointmentCreate(start_time=start, service_ids=[generate_id(), generate_id()])
    with pytest.raises(NotFoundError, match="Service\\(s\\) not found"):
        AppointmentService.create_appointment(db_session, sample_medspa.id, data)


def test_create_appointment_start_time_in_past_raises(
    db_session: Session, sample_medspa: Medspa, sample_service: Service
):
    """Service enforces past check for callers that bypass schema (e.g. internal APIs)."""
    start = (datetime.now(timezone.utc) - timedelta(hours=1)).replace(microsecond=0)
    data = AppointmentCreate.model_construct(start_time=start, service_ids=[sample_service.id])
    with pytest.raises(BadRequestError, match="start_time cannot be in the past"):
        AppointmentService.create_appointment(db_session, sample_medspa.id, data)


def test_create_appointment_naive_start_time_treated_as_utc(
    db_session: Session, sample_medspa: Medspa, sample_service: Service
):
    """Naive start_time gets tzinfo=timezone.utc so validation and create succeed."""
    start_naive = (datetime.now(timezone.utc) + timedelta(days=1)).replace(tzinfo=None)
    assert start_naive.tzinfo is None
    data = AppointmentCreate(start_time=start_naive, service_ids=[sample_service.id])
    appointment = AppointmentService.create_appointment(db_session, sample_medspa.id, data)
    assert appointment.id is not None
    assert appointment.medspa_id == sample_medspa.id


def test_create_appointment_service_from_other_medspa(
    db_session: Session, sample_medspa: Medspa, sample_service: Service
):
    other_medspa = Medspa(
        id=generate_id(),
        name="Other MedSpa",
        address="Elsewhere",
        phone_number=None,
        email=None,
    )
    db_session.add(other_medspa)
    db_session.flush()
    other_service = Service(
        id=generate_id(),
        medspa_id=other_medspa.id,
        name="Other Service",
        description="",
        price=1000,  # cents
        duration=15,
    )
    db_session.add(other_service)
    db_session.commit()
    db_session.refresh(other_service)

    start = (datetime.now(timezone.utc) + timedelta(days=1)).replace(microsecond=0)
    data = AppointmentCreate(start_time=start, service_ids=[sample_service.id, other_service.id])
    with pytest.raises(BadRequestError, match="All services must belong to the same medspa"):
        AppointmentService.create_appointment(db_session, sample_medspa.id, data)


def test_list_appointments_filter_by_medspa_id(
    db_session: Session, sample_medspa: Medspa, sample_appointment
):
    items, _ = AppointmentService.list_appointments(
        db_session, medspa_id=sample_medspa.id, limit=20
    )
    assert len(items) >= 1
    assert all(a.medspa_id == sample_medspa.id for a in items)


def test_list_appointments_filter_by_status(db_session: Session, sample_appointment):
    items, _ = AppointmentService.list_appointments(db_session, status="scheduled", limit=20)
    assert len(items) >= 1
    assert all(a.status == "scheduled" for a in items)


def test_create_appointment_succeeds_when_no_overlapping_scheduled(
    db_session: Session, sample_medspa: Medspa, sample_service: Service
):
    """Create succeeds when no overlapping scheduled appointment for that service."""
    start = (datetime.now(timezone.utc) + timedelta(days=1)).replace(microsecond=0)
    data = AppointmentCreate(start_time=start, service_ids=[sample_service.id])
    appointment = AppointmentService.create_appointment(db_session, sample_medspa.id, data)
    assert appointment.id is not None
    assert appointment.status == "scheduled"


def test_create_appointment_raises_conflict_when_same_service_overlapping_window(
    db_session: Session, sample_medspa: Medspa, sample_service: Service
):
    """Create raises ConflictError when a scheduled appointment already uses the same service in an overlapping window."""
    from app.models.models import Appointment, appointment_services_table

    base = (datetime.now(timezone.utc) + timedelta(days=1)).replace(microsecond=0)
    existing = Appointment(
        id=generate_id(),
        medspa_id=sample_medspa.id,
        start_time=base,
        status="scheduled",
        total_price=sample_service.price,
        total_duration=sample_service.duration,
    )
    db_session.add(existing)
    db_session.flush()
    db_session.execute(
        appointment_services_table.insert().values(
            appointment_id=existing.id, service_id=sample_service.id
        )
    )
    db_session.commit()
    db_session.refresh(existing)

    data = AppointmentCreate(start_time=base, service_ids=[sample_service.id])
    with pytest.raises(ConflictError, match="already booked for this time slot"):
        AppointmentService.create_appointment(db_session, sample_medspa.id, data)


def test_update_status_scheduled_to_completed_succeeds(db_session: Session, sample_appointment):
    """Valid transition: scheduled -> completed."""
    result = AppointmentService.update_status(db_session, sample_appointment.id, "completed")
    assert result.status == "completed"


def test_update_status_scheduled_to_canceled_succeeds(db_session: Session, sample_appointment):
    """Valid transition: scheduled -> canceled."""
    result = AppointmentService.update_status(db_session, sample_appointment.id, "canceled")
    assert result.status == "canceled"


def test_update_status_same_status_returns_appointment_without_change(
    db_session: Session, sample_appointment
):
    """Same status as current returns success without persisting a change."""
    result = AppointmentService.update_status(db_session, sample_appointment.id, "scheduled")
    assert result.id == sample_appointment.id
    assert result.status == "scheduled"


def test_update_status_completed_to_scheduled_raises_bad_request(
    db_session: Session, sample_appointment
):
    """Invalid transition: completed is final, cannot go back to scheduled."""
    AppointmentService.update_status(db_session, sample_appointment.id, "completed")
    with pytest.raises(BadRequestError, match="Invalid status transition"):
        AppointmentService.update_status(db_session, sample_appointment.id, "scheduled")


def test_update_status_canceled_to_completed_raises_bad_request(
    db_session: Session, sample_appointment
):
    """Invalid transition: canceled is final, cannot go to completed."""
    AppointmentService.update_status(db_session, sample_appointment.id, "canceled")
    with pytest.raises(BadRequestError, match="Invalid status transition"):
        AppointmentService.update_status(db_session, sample_appointment.id, "completed")


def test_update_status_completed_to_canceled_raises_bad_request(
    db_session: Session, sample_appointment
):
    """Invalid transition: completed -> canceled not allowed."""
    AppointmentService.update_status(db_session, sample_appointment.id, "completed")
    with pytest.raises(BadRequestError, match="Invalid status transition"):
        AppointmentService.update_status(db_session, sample_appointment.id, "canceled")
