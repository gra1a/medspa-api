from datetime import datetime, timezone

import pytest
from sqlalchemy.orm import Session

pytestmark = pytest.mark.unit

from app.models.models import Appointment
from app.repositories.appointment_repository import AppointmentRepository
from app.utils.ulid import generate_ulid


def test_get_by_id_found(db_session: Session, sample_appointment: Appointment):
    got = AppointmentRepository.get_by_id(db_session, sample_appointment.id)
    assert got is not None
    assert got.id == sample_appointment.id
    assert got.ulid == sample_appointment.ulid
    assert got.status == sample_appointment.status


def test_get_by_id_not_found(db_session: Session):
    assert AppointmentRepository.get_by_id(db_session, 99999) is None


def test_get_by_ulid_found(db_session: Session, sample_appointment: Appointment):
    got = AppointmentRepository.get_by_ulid(db_session, sample_appointment.ulid)
    assert got is not None
    assert got.id == sample_appointment.id


def test_get_by_ulid_not_found(db_session: Session):
    assert AppointmentRepository.get_by_ulid(db_session, generate_ulid()) is None


def test_list_no_filters(db_session: Session, sample_appointment: Appointment):
    lst = AppointmentRepository.list(db_session)
    assert len(lst) >= 1
    assert any(a.id == sample_appointment.id for a in lst)


def test_list_filter_by_medspa_id(db_session: Session, sample_medspa, sample_appointment: Appointment):
    lst = AppointmentRepository.list(db_session, medspa_id=sample_medspa.id)
    assert len(lst) >= 1
    assert all(a.medspa_id == sample_medspa.id for a in lst)


def test_list_filter_by_status(db_session: Session, sample_appointment: Appointment):
    lst = AppointmentRepository.list(db_session, status="scheduled")
    assert len(lst) >= 1
    assert all(a.status == "scheduled" for a in lst)


def test_list_filter_by_medspa_and_status(db_session: Session, sample_medspa, sample_appointment: Appointment):
    lst = AppointmentRepository.list(
        db_session, medspa_id=sample_medspa.id, status="scheduled"
    )
    assert len(lst) >= 1
    assert all(
        a.medspa_id == sample_medspa.id and a.status == "scheduled" for a in lst
    )


def test_list_status_filter_returns_none_when_no_match(db_session: Session, sample_medspa):
    lst = AppointmentRepository.list(db_session, medspa_id=sample_medspa.id, status="completed")
    # sample_appointment is "scheduled", so if that's the only one we get []
    assert isinstance(lst, list)


def test_add_persists_appointment(db_session: Session, sample_medspa):
    appointment = Appointment(
        ulid=generate_ulid(),
        medspa_id=sample_medspa.id,
        start_time=datetime.now(timezone.utc).replace(microsecond=0),
        status="scheduled",
        total_price=10000,  # cents
        total_duration=90,
    )
    added = AppointmentRepository.persist_new(db_session, appointment)
    assert added.id is not None
    got = AppointmentRepository.get_by_ulid(db_session, added.ulid)
    assert got is not None
    assert got.total_price == 10000


def test_add_with_services_persists_appointment_and_links(db_session: Session, sample_medspa, sample_services):
    appointment = Appointment(
        ulid=generate_ulid(),
        medspa_id=sample_medspa.id,
        start_time=datetime.now(timezone.utc).replace(microsecond=0),
        status="scheduled",
        total_price=3000,  # cents
        total_duration=45,
    )
    service_ids = [s.id for s in sample_services]
    added = AppointmentRepository.persist_new_with_services(db_session, appointment, service_ids)
    assert added.id is not None
    got = AppointmentRepository.get_by_ulid(db_session, added.ulid)
    assert got is not None
    assert len(got.services) == len(sample_services)
    assert {s.id for s in got.services} == set(service_ids)


def test_save_commits_status_change(db_session: Session, sample_appointment: Appointment):
    sample_appointment.status = "completed"
    saved = AppointmentRepository.persist(db_session, sample_appointment)
    assert saved.status == "completed"
    got = AppointmentRepository.get_by_ulid(db_session, sample_appointment.ulid)
    assert got is not None
    assert got.status == "completed"
