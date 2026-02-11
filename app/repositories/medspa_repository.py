"""Persistence only for Medspa aggregate. No business rules."""

from typing import Optional

from sqlalchemy.orm import Session

from app.models.models import Medspa


class MedspaRepository:
    @staticmethod
    def list(db: Session, cursor: Optional[str] = None, limit: int = 20) -> list[Medspa]:
        """Return up to limit+1 items ordered by id, after cursor (exclusive)."""
        q = db.query(Medspa).order_by(Medspa.id)
        if cursor is not None:
            q = q.filter(Medspa.id > cursor)
        return q.limit(limit + 1).all()

    @staticmethod
    def create(db: Session, medspa: Medspa) -> Medspa:
        """Persist a new medspa."""
        db.add(medspa)
        return medspa
