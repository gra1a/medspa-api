from datetime import datetime
from typing import TYPE_CHECKING, Optional

from pydantic import BaseModel, ConfigDict, Field

if TYPE_CHECKING:
    from app.models.models import Service


class ServiceBase(BaseModel):
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    price: int = Field(..., gt=0, description="Price in cents")
    duration: int = Field(..., gt=0)


class ServiceCreate(ServiceBase):
    pass


class ServiceUpdate(BaseModel):
    name: Optional[str] = Field(default=None, max_length=255)
    description: Optional[str] = None
    price: Optional[int] = Field(default=None, gt=0, description="Price in cents")
    duration: Optional[int] = Field(default=None, gt=0)


class ServiceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    medspa_id: str
    name: str
    description: Optional[str] = None
    price: int  # in cents
    duration: int
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_service(cls, service: "Service") -> "ServiceResponse":
        """Map ORM Service to ServiceResponse. Keeps serialization in one place."""
        return cls.model_validate(service)
