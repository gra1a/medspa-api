from typing import Optional

from sqlalchemy.orm import Session

from app.db.database import transaction
from app.models.models import Service
from app.repositories.service_repository import ServiceRepository
from app.schemas.services import ServiceCreate, ServiceUpdate
from app.services.medspa_service import MedspaService
from app.utils.query import get_by_id
from app.utils.ulid import generate_id


class OfferingsService:
    @staticmethod
    def create_service(db: Session, medspa_id: str, data: ServiceCreate) -> Service:
        medspa = MedspaService.get_medspa(db, medspa_id)
        service = Service(
            id=generate_id(),
            medspa_id=medspa.id,
            name=data.name,
            description=data.description,
            price=data.price,
            duration=data.duration,
        )
        with transaction(db):
            return ServiceRepository.create(db, service)

    @staticmethod
    def get_service(db: Session, id: str) -> Service:
        return get_by_id(db, Service, id, "Service not found")

    @staticmethod
    def list_services_by_medspa(
        db: Session, medspa_id: str, cursor: Optional[str] = None, limit: int = 20
    ) -> tuple[list[Service], Optional[str]]:
        medspa = MedspaService.get_medspa(db, medspa_id)
        raw = ServiceRepository.list_by_medspa_id(db, medspa.id, cursor=cursor, limit=limit)
        items = raw[:limit]
        next_cursor = items[-1].id if len(raw) > limit else None
        return items, next_cursor

    @staticmethod
    def update_service(db: Session, service_id: str, data: ServiceUpdate) -> Service:
        service = OfferingsService.get_service(db, service_id)
        update = data.model_dump(exclude_unset=True)
        allowed = {"name", "description", "price", "duration"}
        for key in allowed & update.keys():
            setattr(service, key, update[key])
        with transaction(db):
            return ServiceRepository.update(db, service)
