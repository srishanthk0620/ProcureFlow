from datetime import date, time
from decimal import Decimal
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy import func, inspect, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.orm.exc import StaleDataError

from app.api.dependencies import get_current_principal, require_roles
from app.core.errors import Conflict, register_error_handlers
from app.core.security import hash_password, verify_password
from app.db.base import Base, utc_now
from app.db.seed import seed_development, seed_id
from app.db.session import make_engine
from app.models import (Booking, BookingGroupMetadata, CentreResource, Commodity,
    Disruption, FarmerProfile, Grievance, Notification, PriceRecord,
    ProcurementCentre, QueueEntry, Role, StaffProfile, User)
from app.models.enums import (BookingStatus, DisruptionStatus, GrievanceCategory,
    NoticeType, ResourceType, RoleName, Severity)
from app.schemas.core import (BookingCreate, BookingRead, CentreRead, CommodityRead,
    DisruptionCreate, DisruptionRead, GrievanceCreate, GrievanceRead,
    NotificationRead, PriceRead, QueueRead, UserRead)
from app.services.auth_service import Principal


def migrate(engine, target="head"):
    with engine.begin() as connection:
        config = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
        config.attributes["connection"] = connection
        if target == "base":
            command.downgrade(config, target)
        else:
            command.upgrade(config, target)


@pytest.fixture
def database(tmp_path):
    engine = make_engine("sqlite:///" + (tmp_path / "test.db").as_posix())
    migrate(engine)
    try:
        yield engine
    finally:
        engine.dispose()


@pytest.fixture
def seeded(database):
    with Session(database) as session:
        with session.begin():
            seed_development(session, "test")
    return database


def new_booking(**overrides):
    values = dict(farmer_id=seed_id("user:farmer"), centre_id=seed_id("centre:kollam-east"),
        commodity_id=seed_id("commodity:paddy"), quantity=Decimal("600"),
        appointment_date=date(2026, 9, 20), start_time=time(9), token="TEST-001")
    values.update(overrides)
    return Booking(**values)


def test_migration_roundtrip_and_metadata(database):
    with database.connect() as connection:
        assert connection.exec_driver_sql("PRAGMA foreign_keys").scalar() == 1
        assert set(Base.metadata.tables) <= set(inspect(connection).get_table_names())
        assert compare_metadata(MigrationContext.configure(connection), Base.metadata) == []
    migrate(database, "base")
    assert set(inspect(database).get_table_names()) == {"alembic_version"}
    migrate(database)
    assert "bookings" in inspect(database).get_table_names()


def test_seed_idempotent_preserves_edits_and_persists(seeded):
    with Session(seeded) as session:
        counts = {table.name: session.scalar(select(func.count()).select_from(table))
                  for table in Base.metadata.sorted_tables}
        centre = session.get(ProcurementCentre, seed_id("centre:kollam-east"))
        centre.name = "Preserved user edit"
        session.commit()
        seed_development(session, "test")
        session.commit()
        assert counts == {table.name: session.scalar(select(func.count()).select_from(table))
                          for table in Base.metadata.sorted_tables}
        assert session.scalar(select(func.count()).select_from(Role)) == 7
        assert all(u.password_hash is None and not u.is_active for u in session.scalars(select(User)))
        assert session.scalar(select(func.count()).select_from(CentreResource)) == 12
    # Dispose/reconnect demonstrates disk persistence independently of the first connection.
    seeded.dispose()
    with Session(seeded) as reopened:
        assert reopened.get(ProcurementCentre, seed_id("centre:kollam-east")).name == "Preserved user edit"
        assert reopened.scalar(select(func.count()).select_from(PriceRecord)) == 3


def test_seed_rejects_production(database):
    with Session(database) as session:
        with pytest.raises(RuntimeError, match="disabled"):
            seed_development(session, "production")
        assert session.scalar(select(func.count()).select_from(User)) == 0


def test_relationships_and_read_schemas(seeded):
    with Session(seeded) as session:
        booking = new_booking()
        booking.group_metadata = BookingGroupMetadata(group_name="Development group", farmer_count=2, contact_name="Test Contact")
        booking.queue_entry = QueueEntry(centre_id=booking.centre_id, position=1)
        session.add(booking)
        session.flush()
        notice = Notification(recipient_id=booking.farmer_id, category=NoticeType.CONFIRMED,
                              title="Confirmed", message="Test booking", booking=booking)
        grievance = Grievance(user_id=booking.farmer_id, category=GrievanceCategory.BOOKINGS,
                              description="Test grievance details", reference="GR-TEST", booking=booking, centre=booking.centre)
        session.add_all([notice, grievance])
        session.commit()
        session.expire_all()
        assert booking.farmer.user.farmer_profile.user_id == booking.farmer_id
        assert booking.queue_entry.booking is booking
        assert booking.group_metadata.booking is booking
        assert booking.commodity.code == "paddy"
        staff = session.get(StaffProfile, seed_id("user:staff"))
        assert staff.centre.id == booking.centre_id
        assert staff.user.roles[0].name == RoleName.STAFF
        assert BookingRead.model_validate(booking).model_dump(mode="json")["created_at"].endswith("Z")
        assert QueueRead.model_validate(booking.queue_entry).version == 1
        assert CentreRead.model_validate(booking.centre).resources
        assert CommodityRead.model_validate(booking.commodity).unit == "kg"
        assert NotificationRead.model_validate(notice).booking_id == booking.id
        assert GrievanceRead.model_validate(grievance).reference == "GR-TEST"
        assert PriceRead.model_validate(session.scalars(select(PriceRecord)).first()).illustrative
        assert "password_hash" not in UserRead.model_validate(staff.user).model_dump()


@pytest.mark.parametrize("overrides", [
    {"quantity": Decimal("0")}, {"quantity": Decimal("-1")},
    {"farmer_id": "missing-owner"}, {"centre_id": "missing-centre"},
    {"commodity_id": "missing-commodity"},
    {"status": BookingStatus.CANCELLED},
    {"cancelled_at": utc_now()},
])
def test_booking_database_constraints(seeded, overrides):
    with Session(seeded) as session:
        session.add(new_booking(**overrides))
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()
        assert session.scalar(select(func.count()).select_from(Booking)) == 0


def test_token_group_and_queue_constraints(seeded):
    with Session(seeded) as session:
        booking = new_booking()
        session.add(booking)
        session.commit()
        session.add(new_booking())
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()
        session.add(BookingGroupMetadata(booking_id=booking.id, group_name="Invalid", farmer_count=1, contact_name="Test"))
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()
        session.add(QueueEntry(booking_id=booking.id, centre_id=seed_id("centre:kollam-town")))
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()
        session.add(QueueEntry(booking_id=booking.id, centre_id=booking.centre_id))
        session.commit()
        session.add(QueueEntry(booking_id=booking.id, centre_id=booking.centre_id))
        with pytest.raises(IntegrityError):
            session.commit()


@pytest.mark.parametrize("model", [Booking, QueueEntry])
def test_optimistic_version_conflict(seeded, model):
    with Session(seeded) as setup:
        booking = new_booking()
        booking.queue_entry = QueueEntry(centre_id=booking.centre_id)
        setup.add(booking)
        setup.commit()
        identifier = booking.id if model is Booking else booking.queue_entry.id
    with Session(seeded) as first, Session(seeded) as second:
        a, b = first.get(model, identifier), second.get(model, identifier)
        if model is Booking:
            a.quantity, b.quantity = Decimal("700"), Decimal("800")
        else:
            a.position, b.position = 2, 3
        first.commit()
        assert a.version == 2
        with pytest.raises(StaleDataError):
            second.commit()


def test_disruption_lifecycle_and_resources(seeded):
    with Session(seeded) as session:
        incident = Disruption(centre_id=seed_id("centre:kollam-east"), resource_type=ResourceType.WEIGHBRIDGE,
            severity=Severity.MEDIUM, note="Development outage", expected_recovery_minutes=30,
            reported_by=seed_id("user:staff"))
        session.add(incident)
        session.commit()
        assert incident.status == DisruptionStatus.ACTIVE and incident.resolved_at is None
        assert incident.reporter.centre.id == incident.centre.id
        incident.status = DisruptionStatus.RESOLVED
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()
        incident.status, incident.resolved_at = DisruptionStatus.RESOLVED, utc_now()
        session.commit()
        assert DisruptionRead.model_validate(incident).resolved_at is not None
        resource = session.scalars(select(CentreResource)).first()
        resource.active_count = resource.total_count + 1
        with pytest.raises(IntegrityError):
            session.commit()


def test_request_sessions_close_and_rollback(database, monkeypatch):
    import app.db.session as module
    monkeypatch.setattr(module, "SessionLocal", sessionmaker(database))
    request_a, request_b = module.get_db(), module.get_db()
    first, second = next(request_a), next(request_b)
    assert first is not second
    first.add(Commodity(code="temporary", name="Temporary", unit="kg"))
    first.flush()
    with pytest.raises(RuntimeError):
        request_a.throw(RuntimeError("failed request"))
    request_b.close()
    with Session(database) as check:
        assert check.scalar(select(func.count()).select_from(Commodity)) == 0


@pytest.mark.parametrize("changes", [
    {"quantity": 0}, {"quantity": "NaN"}, {"quantity": "1.0001"},
    {"appointment_date": "not-a-date"}, {"start_time": "25:00"},
    {"farmer_id": "client-owned"}, {"status": "completed"}, {"roles": ["super_admin"]},
    {"group_metadata": {"group_name": " ", "farmer_count": 2, "contact_name": "Test"}},
])
def test_booking_schema_rejects_invalid_and_privileged_fields(changes):
    payload = dict(centre_id="centre", commodity_id="paddy", quantity="50",
                   appointment_date="2026-09-20", start_time="09:00")
    with pytest.raises(ValidationError):
        BookingCreate.model_validate(payload | changes)


def test_other_input_validation():
    with pytest.raises(ValidationError):
        DisruptionCreate(centre_id="c", resource_type="invalid", severity="high", note="x", expected_recovery_minutes=30)
    with pytest.raises(ValidationError):
        GrievanceCreate(category="other", description="short")


def test_password_hashing():
    password = "test-only-long-passphrase"
    hashed, other = hash_password(password), hash_password(password)
    assert password not in hashed and hashed != other
    assert verify_password(password, hashed)
    assert not verify_password("incorrect-test-passphrase", hashed)
    for invalid in [None, "", "malformed", "scrypt$v1$%%%$%%%"]:
        assert not verify_password(password, invalid)
    with pytest.raises(ValueError):
        hash_password("short")


def test_auth_and_error_boundaries():
    app = FastAPI()
    register_error_handlers(app)

    @app.get("/protected")
    def protected(principal=Depends(require_roles(RoleName.STAFF))):
        return {"user_id": principal.user_id}

    @app.post("/validate")
    def validate(payload: BookingCreate):
        raise Conflict("internal detail must not leak")

    with TestClient(app) as client:
        assert client.get("/protected", headers={"X-Role": "staff"}).status_code == 401
        app.dependency_overrides[get_current_principal] = lambda: Principal("farmer", frozenset({RoleName.FARMER}))
        assert client.get("/protected").status_code == 403
        app.dependency_overrides[get_current_principal] = lambda: Principal("staff", frozenset({RoleName.STAFF}))
        assert client.get("/protected").status_code == 200
        response = client.post("/validate", json={"password": "do-not-echo"})
        assert response.status_code == 422 and "do-not-echo" not in response.text
        response = client.post("/validate", json=dict(centre_id="c", commodity_id="p", quantity=50,
                               appointment_date="2026-09-20", start_time="09:00"))
        assert response.status_code == 409 and "internal detail" not in response.text
