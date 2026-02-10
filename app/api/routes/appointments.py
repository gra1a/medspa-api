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
from app.schemas.pagination import PaginatedResponse, PaginationParams, get_pagination
from app.services.appointment_service import AppointmentService

router = APIRouter()


@router.post("/medspas/{medspa_id}/appointments", response_model=AppointmentResponse, status_code=201)
def create_appointment(medspa_id: str, data: AppointmentCreate, db: Session = Depends(get_db)):
    appointment = AppointmentService.create_appointment(db, medspa_id, data)
    return AppointmentResponse.from_appointment(appointment)


@router.get("/appointments/{appointment_id}", response_model=AppointmentResponse)
def get_appointment(appointment_id: str, db: Session = Depends(get_db)):
    appointment = AppointmentService.get_appointment(db, appointment_id)
    return AppointmentResponse.from_appointment(appointment)


@router.patch("/appointments/{appointment_id}", response_model=AppointmentResponse)
def update_appointment_status(
    appointment_id: str,
    data: AppointmentStatusUpdate,
    db: Session = Depends(get_db),
):
    appointment = AppointmentService.update_status(db, appointment_id, data.status)
    return AppointmentResponse.from_appointment(appointment)


@router.get("/appointments", response_model=PaginatedResponse[AppointmentResponse])
def list_appointments(
    medspa_id: Optional[str] = Query(None),
    status: Optional[AppointmentStatus] = Query(None),
    db: Session = Depends(get_db),
    pagination: PaginationParams = Depends(get_pagination),
):
    items, next_cursor = AppointmentService.list_appointments(
        db,
        medspa_id=medspa_id,
        status=status,
        cursor=pagination.cursor,
        limit=pagination.limit,
    )
    return PaginatedResponse(
        items=[AppointmentResponse.from_appointment(a) for a in items],
        next_cursor=next_cursor,
        limit=pagination.limit,
    )
