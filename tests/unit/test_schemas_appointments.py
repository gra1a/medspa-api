from datetime import datetime, timezone, timedelta

import pytest

pytestmark = pytest.mark.unit

from app.schemas.appointments import AppointmentCreate


def test_appointment_create_naive_future_datetime_treated_as_utc():
    """Covers validator branch where tzinfo is None: replace with UTC then validate."""
    naive_future = (datetime.now(timezone.utc) + timedelta(days=1)).replace(tzinfo=None)
    data = AppointmentCreate(start_time=naive_future, service_ids=["01ARZ3NDEKTSV4RRFFQ69G5FAV"])
    assert data.start_time.tzinfo is not None
    assert data.service_ids == ["01ARZ3NDEKTSV4RRFFQ69G5FAV"]


def test_appointment_create_naive_past_raises():
    naive_past = (datetime.now(timezone.utc) - timedelta(days=1)).replace(tzinfo=None)
    with pytest.raises(ValueError, match="start_time cannot be in the past"):
        AppointmentCreate(start_time=naive_past, service_ids=["01ARZ3NDEKTSV4RRFFQ69G5FAV"])
