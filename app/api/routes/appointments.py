from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.appointments import (
    AppointmentCreate,
    AppointmentResponse,
    AppointmentStatus,
    AppointmentStatusUpdate,
)
from app.services.appointment_service import AppointmentService

router = APIRouter()


@router.post("/medspas/{medspa_ulid}/appointments", response_model=AppointmentResponse, status_code=201)
def create_appointment(medspa_ulid: str, data: AppointmentCreate, db: Session = Depends(get_db)):
    appointment = AppointmentService.create_appointment(db, medspa_ulid, data)
    return AppointmentResponse.from_appointment(appointment)


@router.get("/appointments/{appointment_ulid}", response_model=AppointmentResponse)
def get_appointment(appointment_ulid: str, db: Session = Depends(get_db)):
    appointment = AppointmentService.get_appointment(db, appointment_ulid)
    return AppointmentResponse.from_appointment(appointment)


@router.patch("/appointments/{appointment_ulid}", response_model=AppointmentResponse)
def update_appointment_status(
    appointment_ulid: str,
    data: AppointmentStatusUpdate,
    db: Session = Depends(get_db),
):
    appointment = AppointmentService.update_status(db, appointment_ulid, data.status)
    return AppointmentResponse.from_appointment(appointment)


@router.get("/appointments", response_model=list[AppointmentResponse])
def list_appointments(
    medspa_ulid: Optional[str] = Query(None),
    status: Optional[AppointmentStatus] = Query(None),
    db: Session = Depends(get_db),
):
    appointments = AppointmentService.list_appointments(db, medspa_ulid=medspa_ulid, status=status)
    return [AppointmentResponse.from_appointment(a) for a in appointments]
