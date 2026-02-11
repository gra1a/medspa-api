"""Persistence only for Service aggregate. No business rules."""

from typing import Optional

from sqlalchemy.orm import Session

from app.models.models import Service


class ServiceRepository:
    @staticmethod
    def list_by_medspa_id(
        db: Session, medspa_id: str, cursor: Optional[str] = None, limit: int = 20
    ) -> list[Service]:
        """Return up to limit+1 items ordered by id, after cursor (exclusive)."""
        q = db.query(Service).filter(Service.medspa_id == medspa_id).order_by(Service.id)
        if cursor is not None:
            q = q.filter(Service.id > cursor)
        return q.limit(limit + 1).all()

    @staticmethod
    def find_by_ids(db: Session, ids: list[str]) -> list[Service]:
        if not ids:
            return []
        return db.query(Service).filter(Service.id.in_(ids)).all()

    @staticmethod
    def create(db: Session, service: Service) -> Service:
        """Persist a new service. For updates use update()."""
        db.add(service)
        return service

    @staticmethod
    def update(db: Session, service: Service) -> Service:
        """Persist changes to an existing service. Reattaches if detached, then flushes."""
        merged = db.merge(service)
        db.flush()
        return merged
