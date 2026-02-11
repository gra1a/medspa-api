"""Persistence only for Appointment aggregate. No business rules."""

from typing import Optional, List
from datetime import datetime

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.models.models import Appointment, appointment_services_table


class AppointmentRepository:
    @staticmethod
    def get_by_id(db: Session, id: str) -> Optional[Appointment]:
        return db.query(Appointment).filter(Appointment.id == id).first()

    @staticmethod
    def find_scheduled_overlapping(
        db: Session,
        medspa_id: str,
        start_time: datetime,
        end_time: datetime,
        service_ids: list[str],
    ) -> List[Appointment]:
        """Return scheduled appointments at this medspa that overlap [start_time, end_time) and use any of the given services."""
        if not service_ids:
            return []
        overlap_end = text(
            "appointments.start_time + (appointments.total_duration * interval '1 minute') > :start_time"
        )
        return (
            db.query(Appointment)
            .join(appointment_services_table, Appointment.id == appointment_services_table.c.appointment_id)
            .filter(
                Appointment.medspa_id == medspa_id,
                Appointment.status == "scheduled",
                Appointment.start_time < end_time,
                overlap_end,
                appointment_services_table.c.service_id.in_(service_ids),
            )
            .params(start_time=start_time)
            .distinct()
            .all()
        )

    @staticmethod
    def list(
        db: Session,
        medspa_id: Optional[str] = None,
        status: Optional[str] = None,
        cursor: Optional[str] = None,
        limit: int = 20,
    ) -> List[Appointment]:
        """Return up to limit+1 items ordered by id, after cursor (exclusive)."""
        q = db.query(Appointment)
        if medspa_id is not None:
            q = q.filter(Appointment.medspa_id == medspa_id)
        if status is not None:
            q = q.filter(Appointment.status == status)
        q = q.order_by(Appointment.id)
        if cursor is not None:
            q = q.filter(Appointment.id > cursor)
        return q.limit(limit + 1).all()

    _UPSERT_UPDATE_FIELDS = ("medspa_id", "start_time", "status", "total_price", "total_duration")

    @staticmethod
    def create_with_services(
        db: Session,
        appointment: Appointment,
        service_ids: List[str],
    ) -> Appointment:
        """Insert a new appointment and its service links. For updates use upsert_by_id / upsert_by_id_with_services."""
        db.add(appointment)
        db.flush()
        for service_id in service_ids:
            db.execute(
                appointment_services_table.insert().values(
                    appointment_id=appointment.id,
                    service_id=service_id,
                )
            )
        return appointment

    @staticmethod
    def sync_appointment_services(db: Session, appointment_id: str, service_ids: List[str]) -> None:
        """Update appointment-service links: remove ones not in service_ids, add new ones. Does not delete all and re-add."""
        new_ids = set(service_ids)
        rows = db.execute(
            select(appointment_services_table.c.service_id).where(
                appointment_services_table.c.appointment_id == appointment_id
            )
        ).fetchall()
        existing_ids = {r[0] for r in rows}
        to_delete = existing_ids - new_ids
        to_insert = new_ids - existing_ids
        if to_delete:
            db.execute(
                appointment_services_table.delete().where(
                    appointment_services_table.c.appointment_id == appointment_id,
                    appointment_services_table.c.service_id.in_(to_delete),
                )
            )
        for service_id in to_insert:
            db.execute(
                appointment_services_table.insert().values(
                    appointment_id=appointment_id,
                    service_id=service_id,
                )
            )

    @staticmethod
    def upsert_by_id(db: Session, appointment: Appointment) -> Appointment:
        """Insert if no row with appointment.id exists; otherwise update that row (scalar fields only, not service links). Returns the persisted entity."""
        existing = AppointmentRepository.get_by_id(db, appointment.id)
        if existing:
            for key in AppointmentRepository._UPSERT_UPDATE_FIELDS:
                setattr(existing, key, getattr(appointment, key))
            return existing
        db.add(appointment)
        return appointment

    @staticmethod
    def upsert_by_id_with_services(
        db: Session,
        appointment: Appointment,
        service_ids: List[str],
    ) -> Appointment:
        """Insert appointment + service links if id is new; otherwise update the row and replace service links. Returns the persisted entity."""
        existing = AppointmentRepository.get_by_id(db, appointment.id)
        if existing:
            for key in AppointmentRepository._UPSERT_UPDATE_FIELDS:
                setattr(existing, key, getattr(appointment, key))
            AppointmentRepository.sync_appointment_services(db, existing.id, service_ids)
            return existing

        db.add(appointment)
        db.flush()
        for service_id in service_ids:
            db.execute(
                appointment_services_table.insert().values(
                    appointment_id=appointment.id,
                    service_id=service_id,
                )
            )
        return appointment
