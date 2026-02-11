import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.db.database import transaction
from app.exceptions import BadRequestError, ConflictError, NotFoundError
from app.models.models import Appointment
from app.repositories.appointment_repository import AppointmentRepository
from app.repositories.service_repository import ServiceRepository
from app.schemas.appointments import (
    VALID_STATUS_TRANSITIONS,
    AppointmentCreate,
    AppointmentStatus,
)
from app.services.medspa_service import MedspaService
from app.utils.ulid import generate_id

logger = logging.getLogger(__name__)


class AppointmentService:
    @staticmethod
    def create_appointment(db: Session, medspa_id: str, data: AppointmentCreate) -> Appointment:
        # Enforce start_time not in past here too so callers that bypass the schema
        # (e.g. internal or admin APIs) cannot skip the rule. Schema remains canonical for API input.
        start = data.start_time
        if start.tzinfo is None:
            start = start.replace(tzinfo=timezone.utc)
        if start < datetime.now(timezone.utc):
            raise BadRequestError("start_time cannot be in the past")

        medspa = MedspaService.get_medspa(db, medspa_id)

        services = ServiceRepository.find_by_ids(db, data.service_ids)
        if len(services) != len(data.service_ids):
            found_ids = {s.id for s in services}
            missing = list(set(data.service_ids) - found_ids)
            raise NotFoundError(f"Service(s) not found: {sorted(missing)}")

        for s in services:
            if s.medspa_id != medspa.id:
                raise BadRequestError("All services must belong to the same medspa")

        total_price = sum(s.price for s in services)
        total_duration = sum(s.duration for s in services)
        end_time = start + timedelta(minutes=total_duration)
        overlapping = AppointmentRepository.find_scheduled_overlapping(
            db, medspa.id, start, end_time, [s.id for s in services]
        )
        if overlapping:
            raise ConflictError("One or more services are already booked for this time slot.")

        appointment = Appointment(
            id=generate_id(),
            medspa_id=medspa.id,
            start_time=data.start_time,
            status=AppointmentStatus.SCHEDULED,
            total_price=total_price,
            total_duration=total_duration,
        )
        with transaction(db):
            created = AppointmentRepository.create_with_services(
                db, appointment, [s.id for s in services]
            )
        logger.info(
            "appointment_created appointment_id=%s medspa_id=%s start_time=%s",
            created.id,
            medspa_id,
            data.start_time.isoformat(),
        )
        return created

    @staticmethod
    def get_appointment(db: Session, id: str) -> Appointment:
        return AppointmentRepository.get_by_id(db, id)

    @staticmethod
    def update_status(db: Session, appointment_id: str, status: AppointmentStatus) -> Appointment:
        appointment = AppointmentService.get_appointment(db, appointment_id)
        current = appointment.status
        if status == current:
            return appointment
        allowed = VALID_STATUS_TRANSITIONS.get(AppointmentStatus(current), ())
        if status not in allowed:
            raise BadRequestError(
                f"Invalid status transition: cannot change appointment from '{current}' to '{status}'. "
                f"Allowed transitions from '{current}': {list(allowed) or 'none (final state)'}."
            )
        appointment.status = status
        with transaction(db):
            updated = AppointmentRepository.update(db, appointment)
        logger.info(
            "appointment_status_updated appointment_id=%s from=%s to=%s",
            appointment_id,
            current,
            status,
        )
        return updated

    @staticmethod
    def list_appointments(
        db: Session,
        medspa_id: Optional[str] = None,
        status: Optional[AppointmentStatus] = None,
        cursor: Optional[str] = None,
        limit: int = 20,
    ) -> tuple[list[Appointment], Optional[str]]:
        medspa_id_filter = None
        if medspa_id is not None:
            medspa = MedspaService.get_medspa(db, medspa_id)
            medspa_id_filter = medspa.id
        raw = AppointmentRepository.list(
            db, medspa_id=medspa_id_filter, status=status, cursor=cursor, limit=limit
        )
        items = raw[:limit]
        next_cursor = items[-1].id if len(raw) > limit else None
        return items, next_cursor
