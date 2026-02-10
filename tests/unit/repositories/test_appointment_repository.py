from datetime import datetime, timezone

import pytest
from sqlalchemy.orm import Session

pytestmark = pytest.mark.unit

from app.models.models import Appointment, Service
from app.repositories.appointment_repository import AppointmentRepository
from app.utils.ulid import generate_id


def test_get_by_id_found(db_session: Session, sample_appointment: Appointment):
    got = AppointmentRepository.get_by_id(db_session, sample_appointment.id)
    assert got is not None
    assert got.id == sample_appointment.id
    assert got.status == sample_appointment.status


def test_get_by_id_not_found(db_session: Session):
    assert AppointmentRepository.get_by_id(db_session, generate_id()) is None


def test_list_no_filters(db_session: Session, sample_appointment: Appointment):
    lst = AppointmentRepository.list(db_session, limit=20)
    assert len(lst) >= 1
    assert any(a.id == sample_appointment.id for a in lst)


def test_list_filter_by_medspa_id(db_session: Session, sample_medspa, sample_appointment: Appointment):
    lst = AppointmentRepository.list(db_session, medspa_id=sample_medspa.id, limit=20)
    assert len(lst) >= 1
    assert all(a.medspa_id == sample_medspa.id for a in lst)


def test_list_filter_by_status(db_session: Session, sample_appointment: Appointment):
    lst = AppointmentRepository.list(db_session, status="scheduled", limit=20)
    assert len(lst) >= 1
    assert all(a.status == "scheduled" for a in lst)


def test_list_filter_by_medspa_and_status(db_session: Session, sample_medspa, sample_appointment: Appointment):
    lst = AppointmentRepository.list(
        db_session, medspa_id=sample_medspa.id, status="scheduled", limit=20
    )
    assert len(lst) >= 1
    assert all(
        a.medspa_id == sample_medspa.id and a.status == "scheduled" for a in lst
    )


def test_list_status_filter_returns_none_when_no_match(db_session: Session, sample_medspa):
    lst = AppointmentRepository.list(db_session, medspa_id=sample_medspa.id, status="completed", limit=20)
    assert isinstance(lst, list)


def test_upsert_by_id_inserts_appointment(db_session: Session, sample_medspa):
    appointment = Appointment(
        id=generate_id(),
        medspa_id=sample_medspa.id,
        start_time=datetime.now(timezone.utc).replace(microsecond=0),
        status="scheduled",
        total_price=10000,  # cents
        total_duration=90,
    )
    added = AppointmentRepository.upsert_by_id(db_session, appointment)
    assert added.id is not None
    got = AppointmentRepository.get_by_id(db_session, added.id)
    assert got is not None
    assert got.total_price == 10000


def test_upsert_by_id_with_services_inserts_appointment_and_links(db_session: Session, sample_medspa, sample_services):
    appointment = Appointment(
        id=generate_id(),
        medspa_id=sample_medspa.id,
        start_time=datetime.now(timezone.utc).replace(microsecond=0),
        status="scheduled",
        total_price=3000,  # cents
        total_duration=45,
    )
    service_ids = [s.id for s in sample_services]
    added = AppointmentRepository.upsert_by_id_with_services(db_session, appointment, service_ids)
    assert added.id is not None
    got = AppointmentRepository.get_by_id(db_session, added.id)
    assert got is not None
    assert len(got.services) == len(sample_services)
    assert {s.id for s in got.services} == set(service_ids)


def test_upsert_by_id_updates_status(db_session: Session, sample_appointment: Appointment):
    sample_appointment.status = "completed"
    saved = AppointmentRepository.upsert_by_id(db_session, sample_appointment)
    assert saved.status == "completed"
    got = AppointmentRepository.get_by_id(db_session, sample_appointment.id)
    assert got is not None
    assert got.status == "completed"


def test_upsert_by_id_with_services_updates_existing_appointment_and_syncs_links(
    db_session: Session, sample_medspa, sample_services, sample_appointment: Appointment
):
    """Update existing appointment via upsert_by_id_with_services; covers sync_appointment_services (remove + add)."""
    extra_service = Service(
        id=generate_id(),
        medspa_id=sample_medspa.id,
        name="S3",
        description="",
        price=1500,
        duration=20,
    )
    db_session.add(extra_service)
    db_session.commit()
    db_session.refresh(extra_service)

    initial_ids = [s.id for s in sample_services]
    got_before = AppointmentRepository.get_by_id(db_session, sample_appointment.id)
    assert got_before is not None
    assert {s.id for s in got_before.services} == set(initial_ids)

    # Replace links: drop first service, add extra_service (hits both to_delete and to_insert)
    new_service_ids = [sample_services[1].id, extra_service.id]
    sample_appointment.total_price = 5000
    updated = AppointmentRepository.upsert_by_id_with_services(
        db_session, sample_appointment, new_service_ids
    )
    assert updated.id == sample_appointment.id
    assert updated.total_price == 5000

    got_after = AppointmentRepository.get_by_id(db_session, sample_appointment.id)
    assert got_after is not None
    assert {s.id for s in got_after.services} == set(new_service_ids)
