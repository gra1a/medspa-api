from typing import List

from sqlalchemy.orm import Session

from app.models.models import Medspa
from app.repositories.medspa_repository import MedspaRepository
from app.schemas.medspas import MedspaCreate
from app.utils.query import get_by_ulid
from app.utils.ulid import generate_ulid


class MedspaService:
    @staticmethod
    def get_medspa(db: Session, ulid: str) -> Medspa:
        return get_by_ulid(db, Medspa, ulid, "Medspa not found")

    @staticmethod
    def list_medspas(db: Session) -> List[Medspa]:
        return MedspaRepository.list_all(db)

    @staticmethod
    def create_medspa(db: Session, data: MedspaCreate) -> Medspa:
        medspa = Medspa(
            ulid=generate_ulid(),
            name=data.name,
            address=data.address,
            phone_number=data.phone_number,
            email=data.email,
        )
        return MedspaRepository.upsert_by_ulid(db, medspa)
