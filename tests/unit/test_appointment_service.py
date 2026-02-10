from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.orm import Session

pytestmark = pytest.mark.unit

from app.exceptions import BadRequestError, NotFoundError
from app.models.models import Medspa, Service
from app.services.appointment_service import AppointmentService
from app.schemas.appointments import AppointmentCreate
from app.utils.ulid import generate_id


def test_create_appointment_services_not_found(db_session: Session, sample_medspa: Medspa):
    start = (datetime.now(timezone.utc) + timedelta(days=1)).replace(microsecond=0)
    data = AppointmentCreate(start_time=start, service_ids=[generate_id(), generate_id()])
    with pytest.raises(NotFoundError, match="Service\\(s\\) not found"):
        AppointmentService.create_appointment(db_session, sample_medspa.id, data)


def test_create_appointment_start_time_in_past_raises(db_session: Session, sample_medspa: Medspa, sample_service: Service):
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


def test_create_appointment_service_from_other_medspa(db_session: Session, sample_medspa: Medspa, sample_service: Service):
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


def test_list_appointments_filter_by_medspa_id(db_session: Session, sample_medspa: Medspa, sample_appointment):
    items, _ = AppointmentService.list_appointments(
        db_session, medspa_id=sample_medspa.id, limit=20
    )
    assert len(items) >= 1
    assert all(a.medspa_id == sample_medspa.id for a in items)


def test_list_appointments_filter_by_status(db_session: Session, sample_appointment):
    items, _ = AppointmentService.list_appointments(
        db_session, status="scheduled", limit=20
    )
    assert len(items) >= 1
    assert all(a.status == "scheduled" for a in items)
