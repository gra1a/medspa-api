import pytest
from sqlalchemy.orm import Session

pytestmark = pytest.mark.unit

from app.exceptions import NotFoundError
from app.models.models import Medspa, Service
from app.schemas.services import ServiceCreate, ServiceUpdate
from app.services.offerings_service import OfferingsService
from app.utils.ulid import generate_id


def test_create_service_success(db_session: Session, sample_medspa: Medspa):
    data = ServiceCreate(
        name="New Service",
        description="Desc",
        price=2500,  # cents
        duration=45,
    )
    service = OfferingsService.create_service(db_session, sample_medspa.id, data)
    assert service.id is not None
    assert service.name == "New Service"
    assert service.medspa_id == sample_medspa.id


def test_create_service_medspa_not_found(db_session: Session):
    data = ServiceCreate(name="X", price=1000, duration=30)
    with pytest.raises(NotFoundError, match="Medspa not found"):
        OfferingsService.create_service(db_session, generate_id(), data)


def test_get_service_exists(db_session: Session, sample_service: Service):
    s = OfferingsService.get_service(db_session, sample_service.id)
    assert s.id == sample_service.id
    assert s.name == sample_service.name


def test_get_service_not_found(db_session: Session):
    with pytest.raises(NotFoundError, match="Service not found"):
        OfferingsService.get_service(db_session, generate_id())


def test_list_services_empty(db_session: Session, sample_medspa: Medspa):
    items, next_cursor = OfferingsService.list_services_by_medspa(
        db_session, sample_medspa.id, limit=20
    )
    assert isinstance(items, list)
    assert next_cursor is None
    assert items == []


def test_list_services_by_medspa(db_session: Session, sample_medspa: Medspa, sample_service: Service):
    items, next_cursor = OfferingsService.list_services_by_medspa(
        db_session, sample_medspa.id, limit=20
    )
    assert len(items) == 1
    assert items[0].id == sample_service.id


def test_update_service_partial(db_session: Session, sample_service: Service):
    data = ServiceUpdate(name="Updated")
    s = OfferingsService.update_service(db_session, sample_service.id, data)
    assert s.name == "Updated"
    assert s.price == sample_service.price


def test_update_service_all_four_fields(db_session: Session, sample_service: Service):
    """Spec: Update a service (name, description, price, duration). Service layer must apply all four."""
    data = ServiceUpdate(
        name="New Name",
        description="New description",
        price=9999,
        duration=120,
    )
    s = OfferingsService.update_service(db_session, sample_service.id, data)
    assert s.name == "New Name"
    assert s.description == "New description"
    assert s.price == 9999
    assert s.duration == 120
    assert s.id == sample_service.id


def test_update_service_not_found(db_session: Session):
    with pytest.raises(NotFoundError, match="Service not found"):
        OfferingsService.update_service(db_session, generate_id(), ServiceUpdate(name="X"))
