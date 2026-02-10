from datetime import datetime
from typing import TYPE_CHECKING, List, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

if TYPE_CHECKING:
    from app.models.models import Appointment


VALID_STATUSES = ("scheduled", "completed", "canceled")
AppointmentStatus = Literal["scheduled", "completed", "canceled"]


class AppointmentCreate(BaseModel):
    start_time: datetime
    service_ids: List[str] = Field(..., min_length=1)

    @field_validator("service_ids")
    @classmethod
    def unique_service_ids(cls, v: List[str]) -> List[str]:
        return list(dict.fromkeys(v))

    @field_validator("start_time")
    @classmethod
    def start_time_not_in_past(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            # Naive datetime: treat as UTC for comparison
            from datetime import timezone
            v = v.replace(tzinfo=timezone.utc)
        from datetime import timezone
        if v < datetime.now(timezone.utc):
            raise ValueError("start_time cannot be in the past")
        return v


class AppointmentStatusUpdate(BaseModel):
    status: AppointmentStatus


class ServiceInAppointment(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    name: str
    price: int  # in cents
    duration: int


class AppointmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    medspa_id: str
    start_time: datetime
    status: str
    total_price: int  # in cents
    total_duration: int
    services: List[ServiceInAppointment]
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_appointment(cls, appointment: "Appointment") -> "AppointmentResponse":
        """Map ORM Appointment to AppointmentResponse. Keeps serialization in one place."""
        services = [ServiceInAppointment.model_validate(s) for s in appointment.services]
        return cls(
            id=appointment.id,
            medspa_id=appointment.medspa_id,
            start_time=appointment.start_time,
            status=appointment.status,
            total_price=appointment.total_price,
            total_duration=appointment.total_duration,
            services=services,
            created_at=appointment.created_at,
            updated_at=appointment.updated_at,
        )
