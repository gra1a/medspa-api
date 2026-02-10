from datetime import datetime
from typing import TYPE_CHECKING, Optional

from pydantic import BaseModel, ConfigDict, Field

if TYPE_CHECKING:
    from app.models.models import Medspa


class MedspaBase(BaseModel):
    name: str = Field(..., max_length=255)
    address: Optional[str] = None
    phone_number: Optional[str] = Field(default=None, max_length=50)
    email: Optional[str] = Field(default=None, max_length=255)


class MedspaCreate(MedspaBase):
    pass


class MedspaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    name: str
    address: Optional[str] = None
    phone_number: Optional[str] = None
    email: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_medspa(cls, medspa: "Medspa") -> "MedspaResponse":
        """Map ORM Medspa to MedspaResponse. Keeps serialization in one place."""
        return cls.model_validate(medspa)
