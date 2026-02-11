"""Persistence only for Medspa aggregate. No business rules."""


from typing import Optional, List
from sqlalchemy.orm import Session

from app.models.models import Medspa


class MedspaRepository:
    @staticmethod
    def get_by_id(db: Session, id: str) -> Optional[Medspa]:
        return db.query(Medspa).filter(Medspa.id == id).first()

    @staticmethod
    def list(db: Session, cursor: Optional[str] = None, limit: int = 20) -> List[Medspa]:
        """Return up to limit+1 items ordered by id, after cursor (exclusive)."""
        q = db.query(Medspa).order_by(Medspa.id)
        if cursor is not None:
            q = q.filter(Medspa.id > cursor)
        return q.limit(limit + 1).all()

    @staticmethod
    def persist_new(db: Session, medspa: Medspa) -> Medspa:
        """Persist a new medspa. For updates to existing entities use persist()."""
        db.add(medspa)
        return medspa

    _UPSERT_UPDATE_FIELDS = ("name", "address", "phone_number", "email")

    @staticmethod
    def upsert_by_id(db: Session, medspa: Medspa) -> Medspa:
        """Insert if no row with medspa.id exists; otherwise update that row. Returns the persisted entity."""
        existing = MedspaRepository.get_by_id(db, medspa.id)
        if existing:
            for key in MedspaRepository._UPSERT_UPDATE_FIELDS:
                setattr(existing, key, getattr(medspa, key))
            return existing
        db.add(medspa)
        return medspa
