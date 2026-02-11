import re
from datetime import datetime
from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

if TYPE_CHECKING:
    from app.models.models import Medspa

# Matches 10 US digits with optional leading +1/1 and common separators.
_US_PHONE_DIGITS_RE = re.compile(r"[^\d]")


def _normalize_us_phone(raw: str) -> str:
    """Validate and normalise a US phone number to (XXX) XXX-XXXX.

    Accepts formats like 5551234567, 555-123-4567, (555) 123-4567,
    +1 555 123 4567, 1-555-123-4567, etc.
    """
    digits = _US_PHONE_DIGITS_RE.sub("", raw)
    if len(digits) == 11 and digits.startswith("1"):
        digits = digits[1:]
    if len(digits) != 10:
        raise ValueError(
            "Phone number must be a valid 10-digit US number "
            "(e.g. 555-123-4567, (555) 123-4567, +15551234567)"
        )
    return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"


class MedspaBase(BaseModel):
    name: str = Field(..., max_length=255)
    address: str = Field(..., min_length=1, description="Street address of the medspa")
    phone_number: str = Field(
        ...,
        max_length=50,
        description="US phone number (e.g. 555-123-4567, (555) 123-4567, +15551234567)",
    )
    email: EmailStr = Field(..., description="Contact email address")

    @field_validator("phone_number")
    @classmethod
    def validate_us_phone(cls, v: str) -> str:
        return _normalize_us_phone(v)


class MedspaCreate(MedspaBase):
    pass


class MedspaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    name: str
    address: str
    phone_number: str
    email: str
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_medspa(cls, medspa: "Medspa") -> "MedspaResponse":
        """Map ORM Medspa to MedspaResponse. Keeps serialization in one place."""
        return cls.model_validate(medspa)
