"""Persistence only for Service aggregate. No business rules."""

from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.models import Service


class ServiceRepository:
    @staticmethod
    def get_by_id(db: Session, id: int) -> Optional[Service]:
        return db.query(Service).filter(Service.id == id).first()

    @staticmethod
    def get_by_ulid(db: Session, ulid: str) -> Optional[Service]:
        return db.query(Service).filter(Service.ulid == ulid).first()

    @staticmethod
    def list_by_medspa_id(
        db: Session, medspa_id: int, cursor: Optional[str] = None, limit: int = 20
    ) -> List[Service]:
        """Return up to limit+1 items ordered by ulid, after cursor (exclusive)."""
        q = (
            db.query(Service)
            .filter(Service.medspa_id == medspa_id)
            .order_by(Service.ulid)
        )
        if cursor is not None:
            q = q.filter(Service.ulid > cursor)
        return q.limit(limit + 1).all()

    @staticmethod
    def find_by_ulids(db: Session, ulids: List[str]) -> List[Service]:
        if not ulids:
            return []
        return db.query(Service).filter(Service.ulid.in_(ulids)).all()

    @staticmethod
    def persist_new(db: Session, service: Service) -> Service:
        """Persist a new service. For updates to existing entities use persist()."""
        db.add(service)
        db.commit()
        db.refresh(service)
        return service

    @staticmethod
    def persist(db: Session, service: Service) -> Service:
        """Commit and refresh an existing (possibly modified) service."""
        db.commit()
        db.refresh(service)
        return service

    _UPSERT_UPDATE_FIELDS = ("medspa_id", "name", "description", "price", "duration")

    @staticmethod
    def upsert_by_ulid(db: Session, service: Service) -> Service:
        """Insert if no row with service.ulid exists; otherwise update that row. Returns the persisted entity."""
        existing = ServiceRepository.get_by_ulid(db, service.ulid)
        if existing:
            for key in ServiceRepository._UPSERT_UPDATE_FIELDS:
                setattr(existing, key, getattr(service, key))
            db.commit()
            db.refresh(existing)
            return existing
        db.add(service)
        db.commit()
        db.refresh(service)
        return service
