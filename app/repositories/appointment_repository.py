"""Persistence only for Appointment aggregate. No business rules."""

import builtins
from datetime import datetime
from typing import Optional

from sqlalchemy import text
from sqlalchemy.orm import Session, selectinload

from app.exceptions import NotFoundError
from app.models.models import Appointment, appointment_services_table
from app.schemas.appointments import AppointmentStatus


class AppointmentRepository:
    @staticmethod
    def get_by_id(db: Session, id: str) -> Appointment:
        """Load a single appointment by id with services eager-loaded. Raises NotFoundError if missing."""
        appointment = (
            db.query(Appointment)
            .options(selectinload(Appointment.services))
            .filter(Appointment.id == id)
            .first()
        )
        if not appointment:
            raise NotFoundError("Appointment not found")
        return appointment

    @staticmethod
    def find_scheduled_overlapping(
        db: Session,
        medspa_id: str,
        start_time: datetime,
        end_time: datetime,
        service_ids: list[str],
    ) -> list[Appointment]:
        """Return scheduled appointments at this medspa that overlap [start_time, end_time) and use any of the given services."""
        if not service_ids:
            return []
        overlap_end = text(
            "appointments.start_time + (appointments.total_duration * interval '1 minute') > :start_time"
        )
        return (
            db.query(Appointment)
            .join(
                appointment_services_table,
                Appointment.id == appointment_services_table.c.appointment_id,
            )
            .filter(
                Appointment.medspa_id == medspa_id,
                Appointment.status == AppointmentStatus.SCHEDULED,
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
    ) -> list[Appointment]:
        """Return up to limit+1 items ordered by id, after cursor (exclusive)."""
        q = db.query(Appointment).options(selectinload(Appointment.services))
        if medspa_id is not None:
            q = q.filter(Appointment.medspa_id == medspa_id)
        if status is not None:
            q = q.filter(Appointment.status == status)
        q = q.order_by(Appointment.id)
        if cursor is not None:
            q = q.filter(Appointment.id > cursor)
        return q.limit(limit + 1).all()

    @staticmethod
    def create_with_services(
        db: Session,
        appointment: Appointment,
        service_ids: builtins.list[str],
    ) -> Appointment:
        """Insert a new appointment and its service links. For updates use update()."""
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
    def update(db: Session, appointment: Appointment) -> Appointment:
        """Persist changes to an existing appointment. Reattaches if detached, then flushes."""
        merged = db.merge(appointment)
        db.flush()
        return merged
