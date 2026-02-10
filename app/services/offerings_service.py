from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.models import Service
from app.repositories.service_repository import ServiceRepository
from app.schemas.services import ServiceCreate, ServiceUpdate
from app.services.medspa_service import MedspaService
from app.utils.query import get_by_ulid
from app.utils.ulid import generate_ulid


class OfferingsService:
    @staticmethod
    def create_service(db: Session, medspa_ulid: str, data: ServiceCreate) -> Service:
        medspa = MedspaService.get_medspa(db, medspa_ulid)
        service = Service(
            ulid=generate_ulid(),
            medspa_id=medspa.id,
            name=data.name,
            description=data.description,
            price=data.price,
            duration=data.duration,
        )
        return ServiceRepository.upsert_by_ulid(db, service)

    @staticmethod
    def get_service(db: Session, ulid: str) -> Service:
        return get_by_ulid(db, Service, ulid, "Service not found")

    @staticmethod
    def list_services_by_medspa(
        db: Session, medspa_ulid: str, cursor: Optional[str] = None, limit: int = 20
    ) -> tuple[List[Service], Optional[str]]:
        medspa = MedspaService.get_medspa(db, medspa_ulid)
        raw = ServiceRepository.list_by_medspa_id(db, medspa.id, cursor=cursor, limit=limit)
        items = raw[:limit]
        next_cursor = items[-1].ulid if len(raw) > limit else None
        return items, next_cursor

    @staticmethod
    def update_service(db: Session, service_ulid: str, data: ServiceUpdate) -> Service:
        service = OfferingsService.get_service(db, service_ulid)
        update = data.model_dump(exclude_unset=True)
        allowed = {"name", "description", "price", "duration"}
        for key in allowed & update.keys():
            setattr(service, key, update[key])
        return ServiceRepository.upsert_by_ulid(db, service)
