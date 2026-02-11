from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.orm import Session

from app.models.models import Appointment, Service, appointment_services_table
from app.repositories.appointment_repository import AppointmentRepository
from app.utils.ulid import generate_id

pytestmark = pytest.mark.unit


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


def test_list_filter_by_medspa_id(
    db_session: Session, sample_medspa, sample_appointment: Appointment
):
    lst = AppointmentRepository.list(db_session, medspa_id=sample_medspa.id, limit=20)
    assert len(lst) >= 1
    assert all(a.medspa_id == sample_medspa.id for a in lst)


def test_list_filter_by_status(db_session: Session, sample_appointment: Appointment):
    lst = AppointmentRepository.list(db_session, status="scheduled", limit=20)
    assert len(lst) >= 1
    assert all(a.status == "scheduled" for a in lst)


def test_list_filter_by_medspa_and_status(
    db_session: Session, sample_medspa, sample_appointment: Appointment
):
    lst = AppointmentRepository.list(
        db_session, medspa_id=sample_medspa.id, status="scheduled", limit=20
    )
    assert len(lst) >= 1
    assert all(a.medspa_id == sample_medspa.id and a.status == "scheduled" for a in lst)


def test_list_status_filter_returns_none_when_no_match(db_session: Session, sample_medspa):
    lst = AppointmentRepository.list(
        db_session, medspa_id=sample_medspa.id, status="completed", limit=20
    )
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
    db_session.commit()
    got = AppointmentRepository.get_by_id(db_session, added.id)
    assert got is not None
    assert got.total_price == 10000


def test_upsert_by_id_with_services_inserts_appointment_and_links(
    db_session: Session, sample_medspa, sample_services
):
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
    db_session.commit()
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


def test_find_scheduled_overlapping_returns_nothing_when_no_overlap(
    db_session: Session, sample_medspa, sample_services
):
    """No overlap or different service returns nothing."""
    base = datetime(2025, 6, 1, 10, 0, 0, tzinfo=timezone.utc)
    appt = Appointment(
        id=generate_id(),
        medspa_id=sample_medspa.id,
        start_time=base,
        status="scheduled",
        total_price=3000,
        total_duration=45,
    )
    db_session.add(appt)
    db_session.flush()
    for s in sample_services:
        db_session.execute(
            appointment_services_table.insert().values(appointment_id=appt.id, service_id=s.id)
        )
    db_session.commit()
    db_session.refresh(appt)
    # Query window after this appointment ends (base+45min to base+60min)
    start = base + timedelta(minutes=45)
    end = base + timedelta(minutes=60)
    result = AppointmentRepository.find_scheduled_overlapping(
        db_session, sample_medspa.id, start, end, [sample_services[0].id]
    )
    assert result == []


def test_find_scheduled_overlapping_returns_appointment_when_same_service_overlapping_time(
    db_session: Session, sample_medspa, sample_services
):
    """Same service and overlapping time returns the existing appointment."""
    base = datetime(2025, 6, 1, 10, 0, 0, tzinfo=timezone.utc)
    appt = Appointment(
        id=generate_id(),
        medspa_id=sample_medspa.id,
        start_time=base,
        status="scheduled",
        total_price=3000,
        total_duration=45,
    )
    db_session.add(appt)
    db_session.flush()
    for s in sample_services:
        db_session.execute(
            appointment_services_table.insert().values(appointment_id=appt.id, service_id=s.id)
        )
    db_session.commit()
    db_session.refresh(appt)
    start = base + timedelta(minutes=10)
    end = base + timedelta(minutes=20)
    result = AppointmentRepository.find_scheduled_overlapping(
        db_session, sample_medspa.id, start, end, [sample_services[0].id]
    )
    assert len(result) == 1
    assert result[0].id == appt.id


def test_find_scheduled_overlapping_returns_nothing_when_appointment_completed(
    db_session: Session, sample_medspa, sample_services
):
    """Completed appointments do not block."""
    base = datetime(2025, 6, 1, 10, 0, 0, tzinfo=timezone.utc)
    appt = Appointment(
        id=generate_id(),
        medspa_id=sample_medspa.id,
        start_time=base,
        status="completed",
        total_price=3000,
        total_duration=45,
    )
    db_session.add(appt)
    db_session.flush()
    for s in sample_services:
        db_session.execute(
            appointment_services_table.insert().values(appointment_id=appt.id, service_id=s.id)
        )
    db_session.commit()
    db_session.refresh(appt)
    start = base
    end = base + timedelta(minutes=60)
    result = AppointmentRepository.find_scheduled_overlapping(
        db_session, sample_medspa.id, start, end, [sample_services[0].id]
    )
    assert result == []


def test_find_scheduled_overlapping_returns_nothing_when_appointment_canceled(
    db_session: Session, sample_medspa, sample_services
):
    """Canceled appointments do not block."""
    base = datetime(2025, 6, 1, 10, 0, 0, tzinfo=timezone.utc)
    appt = Appointment(
        id=generate_id(),
        medspa_id=sample_medspa.id,
        start_time=base,
        status="canceled",
        total_price=3000,
        total_duration=45,
    )
    db_session.add(appt)
    db_session.flush()
    for s in sample_services:
        db_session.execute(
            appointment_services_table.insert().values(appointment_id=appt.id, service_id=s.id)
        )
    db_session.commit()
    db_session.refresh(appt)
    start = base
    end = base + timedelta(minutes=60)
    result = AppointmentRepository.find_scheduled_overlapping(
        db_session, sample_medspa.id, start, end, [sample_services[0].id]
    )
    assert result == []


def test_find_scheduled_overlapping_returns_nothing_when_different_service(
    db_session: Session, sample_medspa, sample_services
):
    """Different service, same time window returns nothing."""
    base = datetime(2025, 6, 1, 10, 0, 0, tzinfo=timezone.utc)
    other_service = Service(
        id=generate_id(),
        medspa_id=sample_medspa.id,
        name="Other",
        description="",
        price=500,
        duration=10,
    )
    db_session.add(other_service)
    db_session.flush()
    appt = Appointment(
        id=generate_id(),
        medspa_id=sample_medspa.id,
        start_time=base,
        status="scheduled",
        total_price=500,
        total_duration=10,
    )
    db_session.add(appt)
    db_session.flush()
    db_session.execute(
        appointment_services_table.insert().values(
            appointment_id=appt.id, service_id=other_service.id
        )
    )
    db_session.commit()
    db_session.refresh(appt)
    start = base
    end = base + timedelta(minutes=30)
    result = AppointmentRepository.find_scheduled_overlapping(
        db_session, sample_medspa.id, start, end, [sample_services[0].id]
    )
    assert result == []


def test_find_scheduled_overlapping_two_services_overlap_on_one(
    db_session: Session, sample_medspa, sample_services
):
    """Existing appointment has two services; query with one shared service in overlapping window returns that appointment."""
    base = datetime(2025, 6, 1, 10, 0, 0, tzinfo=timezone.utc)
    appt = Appointment(
        id=generate_id(),
        medspa_id=sample_medspa.id,
        start_time=base,
        status="scheduled",
        total_price=3000,
        total_duration=45,
    )
    db_session.add(appt)
    db_session.flush()
    for s in sample_services:
        db_session.execute(
            appointment_services_table.insert().values(appointment_id=appt.id, service_id=s.id)
        )
    db_session.commit()
    db_session.refresh(appt)
    start = base + timedelta(minutes=5)
    end = base + timedelta(minutes=15)
    result = AppointmentRepository.find_scheduled_overlapping(
        db_session, sample_medspa.id, start, end, [sample_services[0].id]
    )
    assert len(result) == 1
    assert result[0].id == appt.id


def test_find_scheduled_overlapping_empty_service_ids_returns_empty(
    db_session: Session, sample_medspa
):
    base = datetime(2025, 6, 1, 10, 0, 0, tzinfo=timezone.utc)
    result = AppointmentRepository.find_scheduled_overlapping(
        db_session, sample_medspa.id, base, base + timedelta(minutes=30), []
    )
    assert result == []


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
    db_session.commit()

    got_after = AppointmentRepository.get_by_id(db_session, sample_appointment.id)
    assert got_after is not None
    assert {s.id for s in got_after.services} == set(new_service_ids)
