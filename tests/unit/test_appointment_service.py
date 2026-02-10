from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.orm import Session

pytestmark = pytest.mark.unit

from app.exceptions import BadRequestError, NotFoundError
from app.models.models import Medspa, Service
from app.services.appointment_service import AppointmentService
from app.schemas.appointments import AppointmentCreate
from app.utils.ulid import generate_ulid


def test_create_appointment_services_not_found(db_session: Session, sample_medspa: Medspa):
    start = (datetime.now(timezone.utc) + timedelta(days=1)).replace(microsecond=0)
    data = AppointmentCreate(start_time=start, service_ulids=[generate_ulid(), generate_ulid()])
    with pytest.raises(NotFoundError, match="Service\\(s\\) not found"):
        AppointmentService.create_appointment(db_session, sample_medspa.ulid, data)


def test_create_appointment_service_from_other_medspa(db_session: Session, sample_medspa: Medspa, sample_service: Service):
    other_medspa = Medspa(
        ulid=generate_ulid(),
        name="Other MedSpa",
        address="Elsewhere",
        phone_number=None,
        email=None,
    )
    db_session.add(other_medspa)
    db_session.flush()
    other_service = Service(
        ulid=generate_ulid(),
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
    data = AppointmentCreate(start_time=start, service_ulids=[sample_service.ulid, other_service.ulid])
    with pytest.raises(BadRequestError, match="All services must belong to the same medspa"):
        AppointmentService.create_appointment(db_session, sample_medspa.ulid, data)


def test_list_appointments_filter_by_medspa_ulid(db_session: Session, sample_medspa: Medspa, sample_appointment):
    result = AppointmentService.list_appointments(db_session, medspa_ulid=sample_medspa.ulid)
    assert len(result) >= 1
    assert all(a.medspa_id == sample_medspa.id for a in result)


def test_list_appointments_filter_by_status(db_session: Session, sample_appointment):
    result = AppointmentService.list_appointments(db_session, status="scheduled")
    assert len(result) >= 1
    assert all(a.status == "scheduled" for a in result)
