from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy.orm import Session

from app.exceptions import BadRequestError, NotFoundError
from app.models.models import Appointment
from app.repositories.appointment_repository import AppointmentRepository
from app.repositories.service_repository import ServiceRepository
from app.schemas.appointments import AppointmentCreate, AppointmentStatus
from app.services.medspa_service import MedspaService
from app.utils.query import get_by_id
from app.utils.ulid import generate_id


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

        appointment = Appointment(
            id=generate_id(),
            medspa_id=medspa.id,
            start_time=data.start_time,
            status="scheduled",
            total_price=total_price,
            total_duration=total_duration,
        )
        return AppointmentRepository.upsert_by_id_with_services(
            db, appointment, [s.id for s in services]
        )

    @staticmethod
    def get_appointment(db: Session, id: str) -> Appointment:
        return get_by_id(db, Appointment, id, "Appointment not found")

    @staticmethod
    def update_status(db: Session, appointment_id: str, status: AppointmentStatus) -> Appointment:
        appointment = AppointmentService.get_appointment(db, appointment_id)
        setattr(appointment, "status", status)
        return AppointmentRepository.upsert_by_id(db, appointment)

    @staticmethod
    def list_appointments(
        db: Session,
        medspa_id: Optional[str] = None,
        status: Optional[AppointmentStatus] = None,
        cursor: Optional[str] = None,
        limit: int = 20,
    ) -> tuple[List[Appointment], Optional[str]]:
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
