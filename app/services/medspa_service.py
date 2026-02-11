
from typing import Optional

from sqlalchemy.orm import Session

from app.db.database import transaction
from app.models.models import Medspa
from app.repositories.medspa_repository import MedspaRepository
from app.schemas.medspas import MedspaCreate
from app.utils.query import get_by_id
from app.utils.ulid import generate_id


class MedspaService:
    @staticmethod
    def get_medspa(db: Session, id: str) -> Medspa:
        return get_by_id(db, Medspa, id, "Medspa not found")

    @staticmethod
    def list_medspas(
        db: Session, cursor: Optional[str] = None, limit: int = 20
    ) -> tuple[list[Medspa], Optional[str]]:
        raw = MedspaRepository.list(db, cursor=cursor, limit=limit)
        items = raw[:limit]
        next_cursor = items[-1].id if len(raw) > limit else None
        return items, next_cursor

    @staticmethod
    def create_medspa(db: Session, data: MedspaCreate) -> Medspa:
        medspa = Medspa(
            id=generate_id(),
            name=data.name,
            address=data.address,
            phone_number=data.phone_number,
            email=data.email,
        )
        with transaction(db):
            return MedspaRepository.upsert_by_id(db, medspa)
