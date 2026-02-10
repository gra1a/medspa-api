from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.medspas import MedspaCreate, MedspaResponse
from app.schemas.pagination import PaginatedResponse, get_pagination, PaginationParams
from app.services.medspa_service import MedspaService

router = APIRouter(tags=["medspas"])


@router.get("", response_model=PaginatedResponse[MedspaResponse])
def list_medspas(
    db: Session = Depends(get_db),
    pagination: PaginationParams = Depends(get_pagination),
):
    items, next_cursor = MedspaService.list_medspas(
        db, cursor=pagination.cursor, limit=pagination.limit
    )
    return PaginatedResponse(
        items=[MedspaResponse.from_medspa(m) for m in items],
        next_cursor=next_cursor,
        limit=pagination.limit,
    )


@router.get("/{medspa_id}", response_model=MedspaResponse)
def get_medspa(medspa_id: str, db: Session = Depends(get_db)):
    medspa = MedspaService.get_medspa(db, medspa_id)
    return MedspaResponse.from_medspa(medspa)


@router.post("", response_model=MedspaResponse, status_code=201)
def create_medspa(data: MedspaCreate, db: Session = Depends(get_db)):
    medspa = MedspaService.create_medspa(db, data)
    return MedspaResponse.from_medspa(medspa)
