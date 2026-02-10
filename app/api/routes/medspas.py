from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.medspas import MedspaCreate, MedspaResponse
from app.services.medspa_service import MedspaService

router = APIRouter(tags=["medspas"])


@router.get("", response_model=list[MedspaResponse])
def list_medspas(db: Session = Depends(get_db)):
    medspas = MedspaService.list_medspas(db)
    return [MedspaResponse.from_medspa(m) for m in medspas]


@router.get("/{medspa_ulid}", response_model=MedspaResponse)
def get_medspa(medspa_ulid: str, db: Session = Depends(get_db)):
    medspa = MedspaService.get_medspa(db, medspa_ulid)
    return MedspaResponse.from_medspa(medspa)


@router.post("", response_model=MedspaResponse, status_code=201)
def create_medspa(data: MedspaCreate, db: Session = Depends(get_db)):
    medspa = MedspaService.create_medspa(db, data)
    return MedspaResponse.from_medspa(medspa)
