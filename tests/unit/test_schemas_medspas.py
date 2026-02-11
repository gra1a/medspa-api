"""Unit tests for medspa schemas — phone validation and MedspaResponse."""

from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from app.schemas.medspas import MedspaCreate, MedspaResponse

pytestmark = pytest.mark.unit


def test_medspa_create_normalizes_phone_10_digits():
    """Phone with 10 digits is normalized to (XXX) XXX-XXXX."""
    data = MedspaCreate(
        name="Test",
        address="123 Main St",
        phone_number="555-123-4567",
        email="test@example.com",
    )
    assert data.phone_number == "(555) 123-4567"


def test_medspa_create_normalizes_phone_11_digits_leading_one():
    """Phone with 11 digits starting with 1 (e.g. +1) strips leading 1 and normalizes."""
    data = MedspaCreate(
        name="Test",
        address="123 Main St",
        phone_number="+1 555 123 4567",
        email="test@example.com",
    )
    assert data.phone_number == "(555) 123-4567"


def test_medspa_create_phone_11_digits_no_leading_one_invalid():
    """Phone with 11 digits not starting with 1 is invalid (not a US number)."""
    with pytest.raises(ValueError, match="10-digit US number"):
        MedspaCreate(
            name="Test",
            address="123 Main St",
            phone_number="555-123-45678",
            email="test@example.com",
        )


def test_medspa_create_phone_too_few_digits_invalid():
    """Phone with fewer than 10 digits raises."""
    with pytest.raises(ValueError, match="10-digit US number"):
        MedspaCreate(
            name="Test",
            address="123 Main St",
            phone_number="555-123-456",
            email="test@example.com",
        )


def test_medspa_response_from_medspa():
    """MedspaResponse.from_medspa maps ORM to response."""
    now = datetime.now(timezone.utc)
    medspa = MagicMock()
    medspa.id = "01ARZ3NDEKTSV4RRFFQ69G5FAV"
    medspa.name = "Spa"
    medspa.address = "123 St"
    medspa.phone_number = "(555) 123-4567"
    medspa.email = "a@b.com"
    medspa.created_at = now
    medspa.updated_at = now
    result = MedspaResponse.from_medspa(medspa)
    assert result.id == medspa.id
    assert result.name == medspa.name
    assert result.phone_number == medspa.phone_number
