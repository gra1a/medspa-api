from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.pagination import PaginatedResponse, PaginationParams, get_pagination
from app.schemas.services import ServiceCreate, ServiceResponse, ServiceUpdate
from app.services.offerings_service import OfferingsService

router = APIRouter()


@router.post("/medspas/{medspa_ulid}/services", response_model=ServiceResponse, status_code=201)
def create_service(medspa_ulid: str, data: ServiceCreate, db: Session = Depends(get_db)):
    service = OfferingsService.create_service(db, medspa_ulid, data)
    return ServiceResponse.from_service(service)


@router.get("/services/{service_ulid}", response_model=ServiceResponse)
def get_service(service_ulid: str, db: Session = Depends(get_db)):
    service = OfferingsService.get_service(db, service_ulid)
    return ServiceResponse.from_service(service)


@router.get("/medspas/{medspa_ulid}/services", response_model=PaginatedResponse[ServiceResponse])
def list_services(
    medspa_ulid: str,
    db: Session = Depends(get_db),
    pagination: PaginationParams = Depends(get_pagination),
):
    items, next_cursor = OfferingsService.list_services_by_medspa(
        db, medspa_ulid, cursor=pagination.cursor, limit=pagination.limit
    )
    return PaginatedResponse(
        items=[ServiceResponse.from_service(s) for s in items],
        next_cursor=next_cursor,
        limit=pagination.limit,
    )


@router.patch("/services/{service_ulid}", response_model=ServiceResponse)
def update_service(service_ulid: str, data: ServiceUpdate, db: Session = Depends(get_db)):
    service = OfferingsService.update_service(db, service_ulid, data)
    return ServiceResponse.from_service(service)
