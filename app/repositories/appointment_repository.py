"""Persistence only for Appointment aggregate. No business rules."""

from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.models import Appointment, appointment_services_table


class AppointmentRepository:
    @staticmethod
    def get_by_id(db: Session, id: int) -> Optional[Appointment]:
        return db.query(Appointment).filter(Appointment.id == id).first()

    @staticmethod
    def get_by_ulid(db: Session, ulid: str) -> Optional[Appointment]:
        return db.query(Appointment).filter(Appointment.ulid == ulid).first()

    @staticmethod
    def list(
        db: Session,
        medspa_id: Optional[int] = None,
        status: Optional[str] = None,
        cursor: Optional[str] = None,
        limit: int = 20,
    ) -> List[Appointment]:
        """Return up to limit+1 items ordered by ulid, after cursor (exclusive)."""
        q = db.query(Appointment)
        if medspa_id is not None:
            q = q.filter(Appointment.medspa_id == medspa_id)
        if status is not None:
            q = q.filter(Appointment.status == status)
        q = q.order_by(Appointment.ulid)
        if cursor is not None:
            q = q.filter(Appointment.ulid > cursor)
        return q.limit(limit + 1).all()

    @staticmethod
    def persist_new(db: Session, appointment: Appointment) -> Appointment:
        """Persist a new appointment (no service links). For appointment + services use persist_new_with_services()."""
        db.add(appointment)
        db.commit()
        db.refresh(appointment)
        return appointment

    @staticmethod
    def persist_new_with_services(
        db: Session,
        appointment: Appointment,
        service_ids: List[int],
    ) -> Appointment:
        """Persist a new appointment and its service links."""
        db.add(appointment)
        db.flush()
        for service_id in service_ids:
            db.execute(
                appointment_services_table.insert().values(
                    appointment_id=appointment.id,
                    service_id=service_id,
                )
            )
        db.commit()
        db.refresh(appointment)
        return appointment

    @staticmethod
    def persist(db: Session, appointment: Appointment) -> Appointment:
        """Commit and refresh an existing (possibly modified) appointment."""
        db.commit()
        db.refresh(appointment)
        return appointment

    _UPSERT_UPDATE_FIELDS = ("medspa_id", "start_time", "status", "total_price", "total_duration")

    @staticmethod
    def upsert_by_ulid(db: Session, appointment: Appointment) -> Appointment:
        """Insert if no row with appointment.ulid exists; otherwise update that row (scalar fields only, not service links). Returns the persisted entity."""
        existing = AppointmentRepository.get_by_ulid(db, appointment.ulid)
        if existing:
            for key in AppointmentRepository._UPSERT_UPDATE_FIELDS:
                setattr(existing, key, getattr(appointment, key))
            db.commit()
            db.refresh(existing)
            return existing
        db.add(appointment)
        db.commit()
        db.refresh(appointment)
        return appointment

    @staticmethod
    def upsert_by_ulid_with_services(
        db: Session,
        appointment: Appointment,
        service_ids: List[int],
    ) -> Appointment:
        """Insert appointment + service links if ulid is new; otherwise update the row and replace service links. Returns the persisted entity."""
        existing = AppointmentRepository.get_by_ulid(db, appointment.ulid)
        if existing:
            for key in AppointmentRepository._UPSERT_UPDATE_FIELDS:
                setattr(existing, key, getattr(appointment, key))
            db.execute(
                appointment_services_table.delete().where(
                    appointment_services_table.c.appointment_id == existing.id
                )
            )
            for service_id in service_ids:
                db.execute(
                    appointment_services_table.insert().values(
                        appointment_id=existing.id,
                        service_id=service_id,
                    )
                )
            db.commit()
            db.refresh(existing)
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
        db.commit()
        db.refresh(appointment)
        return appointment
