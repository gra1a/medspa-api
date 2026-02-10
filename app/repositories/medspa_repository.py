"""Persistence only for Medspa aggregate. No business rules."""

from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.models import Medspa


class MedspaRepository:
    @staticmethod
    def get_by_id(db: Session, id: int) -> Optional[Medspa]:
        return db.query(Medspa).filter(Medspa.id == id).first()

    @staticmethod
    def get_by_ulid(db: Session, ulid: str) -> Optional[Medspa]:
        return db.query(Medspa).filter(Medspa.ulid == ulid).first()

    @staticmethod
    def list(db: Session, cursor: Optional[str] = None, limit: int = 20) -> List[Medspa]:
        """Return up to limit+1 items ordered by ulid, after cursor (exclusive)."""
        q = db.query(Medspa).order_by(Medspa.ulid)
        if cursor is not None:
            q = q.filter(Medspa.ulid > cursor)
        return q.limit(limit + 1).all()

    @staticmethod
    def persist_new(db: Session, medspa: Medspa) -> Medspa:
        """Persist a new medspa. For updates to existing entities use persist()."""
        db.add(medspa)
        db.commit()
        db.refresh(medspa)
        return medspa

    _UPSERT_UPDATE_FIELDS = ("name", "address", "phone_number", "email")

    @staticmethod
    def upsert_by_ulid(db: Session, medspa: Medspa) -> Medspa:
        """Insert if no row with medspa.ulid exists; otherwise update that row. Returns the persisted entity."""
        existing = MedspaRepository.get_by_ulid(db, medspa.ulid)
        if existing:
            for key in MedspaRepository._UPSERT_UPDATE_FIELDS:
                setattr(existing, key, getattr(medspa, key))
            db.commit()
            db.refresh(existing)
            return existing
        db.add(medspa)
        db.commit()
        db.refresh(medspa)
        return medspa
