"""Persistence only for Service aggregate. No business rules."""

from typing import List, Optional

from sqlalchemy.orm import Session

from app.db.database import transaction
from app.models.models import Service


class ServiceRepository:
    @staticmethod
    def get_by_id(db: Session, id: str) -> Optional[Service]:
        return db.query(Service).filter(Service.id == id).first()

    @staticmethod
    def list_by_medspa_id(
        db: Session, medspa_id: str, cursor: Optional[str] = None, limit: int = 20
    ) -> List[Service]:
        """Return up to limit+1 items ordered by id, after cursor (exclusive)."""
        q = (
            db.query(Service)
            .filter(Service.medspa_id == medspa_id)
            .order_by(Service.id)
        )
        if cursor is not None:
            q = q.filter(Service.id > cursor)
        return q.limit(limit + 1).all()

    @staticmethod
    def find_by_ids(db: Session, ids: List[str]) -> List[Service]:
        if not ids:
            return []
        return db.query(Service).filter(Service.id.in_(ids)).all()

    _UPSERT_UPDATE_FIELDS = ("medspa_id", "name", "description", "price", "duration")

    @staticmethod
    @transaction
    def upsert_by_id(db: Session, service: Service) -> Service:
        """Insert if no row with service.id exists; otherwise update that row. Returns the persisted entity."""
        existing = ServiceRepository.get_by_id(db, service.id)
        if existing:
            for key in ServiceRepository._UPSERT_UPDATE_FIELDS:
                setattr(existing, key, getattr(service, key))
            return existing
        db.add(service)
        return service
