from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta, time
from decimal import Decimal
from pathlib import Path
import secrets

import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.base import utc_now
from app.db.seed import seed_development, seed_id
from app.db.session import get_db, make_engine
from app.main import app
from app.models import (AuthSession, Booking, Commodity, CentreResource, Disruption,
    OtpChallenge, ProcurementCentre, SlotPolicy, User)
from app.models.enums import BookingStatus, DisruptionStatus, ResourceType, Severity
from app.services.centre_service import local_today
from tests.test_foundation import migrate


@pytest.fixture
def api(tmp_path, monkeypatch):
    engine = make_engine("sqlite:///" + (tmp_path / "api.db").as_posix())
    migrate(engine)
    with Session(engine) as db:
        seed_development(db, "test")
        db.commit()
    monkeypatch.setattr(settings, "APP_ENV", "test")
    monkeypatch.setattr(settings, "AUTH_OTP_SECRET", SecretStr(secrets.token_urlsafe(48)))
    def isolated_db():
        with Session(engine) as db:
            yield db
    app.dependency_overrides[get_db] = isolated_db
    try:
        with TestClient(app) as client:
            yield client, engine
    finally:
        app.dependency_overrides.clear()
        engine.dispose()


def login(client, mobile="9000000001"):
    response = client.post("/api/auth/farmer/otp/request", json={"mobile": mobile})
    assert response.status_code == 200, response.text
    challenge = response.json()
    response = client.post("/api/auth/farmer/otp/verify", json={"challenge_id": challenge["challenge_id"], "otp": challenge["development_otp"]})
    assert response.status_code == 200, response.text
    return {"Authorization": "Bearer " + response.json()["access_token"]}, response.json()


def payload(**overrides):
    return dict(centre_id=seed_id("centre:kollam-east"), commodity_id=seed_id("commodity:paddy"),
        quantity=600, appointment_date=(local_today() + timedelta(days=1)).isoformat(), start_time="09:00:00") | overrides


def availability(client, quantity=50, centre="kollam-east"):
    return client.get(f"/api/centres/{seed_id('centre:' + centre)}/slots", params={
        "appointment_date": payload()["appointment_date"], "commodity": "paddy", "quantity": quantity})


def recommendations(client, quantity=600):
    response = client.get("/api/centres/recommendations", params={"commodity": "paddy", "quantity": quantity,
        "appointment_date": payload()["appointment_date"], "start_time": "09:00:00"})
    assert response.status_code == 200, response.text
    return response.json()


@pytest.mark.parametrize("mobile", ["", "123", "12345678901", "abcdefghij", " 9000000001", "+9000000001", 9000000001, "９００００００００１"])
def test_invalid_mobile(api, mobile):
    client, _ = api
    assert client.post("/api/auth/farmer/otp/request", json={"mobile": mobile}).status_code == 422


def test_session_identity_logout_and_storage(api):
    client, engine = api
    headers, session = login(client)
    assert client.get("/api/auth/me", headers=headers).json()["user"]["id"] == session["user"]["id"]
    assert session["farmer_profile"]["district"] == "Kollam"
    assert session["user"]["roles"] == [{"name": "farmer"}]
    with Session(engine) as db:
        persisted = db.scalars(select(AuthSession)).one()
        assert session["access_token"] != persisted.token_digest
        assert len(persisted.token_digest) == 64
        assert db.scalars(select(OtpChallenge)).one().consumed_at is not None
    assert client.post("/api/auth/logout", headers=headers).status_code == 204
    assert client.get("/api/auth/me", headers=headers).status_code == 401
    assert client.get("/api/auth/me", headers={"Authorization": "Bearer invalid", "X-Role": "super_admin"}).status_code == 401


def test_wrong_otp_attempts_expiry_and_replay(api):
    client, engine = api
    challenge = client.post("/api/auth/farmer/otp/request", json={"mobile": "9000000001"}).json()
    wrong = "000000" if challenge["development_otp"] != "000000" else "000001"
    for _ in range(5):
        assert client.post("/api/auth/farmer/otp/verify", json={"challenge_id": challenge["challenge_id"], "otp": wrong}).status_code == 401
    assert client.post("/api/auth/farmer/otp/verify", json={"challenge_id": challenge["challenge_id"], "otp": challenge["development_otp"]}).status_code == 401
    with Session(engine) as db:
        assert db.get(OtpChallenge, challenge["challenge_id"]).attempts == 5
    expired = client.post("/api/auth/farmer/otp/request", json={"mobile": "9000000002"}).json()
    with Session(engine) as db:
        db.get(OtpChallenge, expired["challenge_id"]).expires_at = utc_now() - timedelta(seconds=1)
        db.commit()
    assert client.post("/api/auth/farmer/otp/verify", json={"challenge_id": expired["challenge_id"], "otp": expired["development_otp"]}).status_code == 401
    valid = client.post("/api/auth/farmer/otp/request", json={"mobile": "9000000003"}).json()
    verify = {"challenge_id": valid["challenge_id"], "otp": valid["development_otp"]}
    assert client.post("/api/auth/farmer/otp/verify", json=verify).status_code == 200
    assert client.post("/api/auth/farmer/otp/verify", json=verify).status_code == 401


def test_rate_limit_and_resend_invalidates_previous(api):
    client, engine = api
    first = client.post("/api/auth/farmer/otp/request", json={"mobile": "9000000001"}).json()
    limited = client.post("/api/auth/farmer/otp/request", json={"mobile": "9000000001"})
    assert limited.status_code == 429 and int(limited.headers["Retry-After"]) > 0
    with Session(engine) as db:
        db.get(OtpChallenge, first["challenge_id"]).created_at -= timedelta(seconds=61)
        db.commit()
    assert client.post("/api/auth/farmer/otp/request", json={"mobile": "9000000001"}).status_code == 200
    assert client.post("/api/auth/farmer/otp/verify", json={"challenge_id": first["challenge_id"], "otp": first["development_otp"]}).status_code == 401


def test_expired_session_and_disabled_user(api):
    client, engine = api
    headers, identity = login(client)
    with Session(engine) as db:
        db.scalars(select(AuthSession)).one().expires_at = utc_now() - timedelta(seconds=1)
        db.commit()
    assert client.get("/api/auth/me", headers=headers).status_code == 401
    headers, identity = login(client, "9000000002")
    with Session(engine) as db:
        db.get(User, identity["user"]["id"]).is_active = False
        db.commit()
    assert client.get("/api/auth/me", headers=headers).status_code == 401


@pytest.mark.parametrize("environment", ["production", "staging"])
def test_no_development_otp_outside_explicit_modes(api, monkeypatch, environment):
    client, engine = api
    monkeypatch.setattr(settings, "APP_ENV", environment)
    response = client.post("/api/auth/farmer/otp/request", json={"mobile": "9000000001"})
    assert response.status_code == 503 and "development_otp" not in response.text
    with Session(engine) as db:
        assert db.scalar(select(func.count()).select_from(OtpChallenge)) == 0


def test_development_otp_secret_required_and_no_role_spoofing(api, monkeypatch):
    client, _ = api
    assert client.post("/api/auth/farmer/otp/request", json={"mobile": "9000000001", "role": "super_admin"}).status_code == 422
    monkeypatch.setattr(settings, "APP_ENV", "development")
    response = client.post("/api/auth/farmer/otp/request", json={"mobile": "9000000002"})
    assert "development_otp" in response.json() and response.headers["Cache-Control"] == "no-store"
    monkeypatch.setattr(settings, "AUTH_OTP_SECRET", None)
    assert client.post("/api/auth/farmer/otp/request", json={"mobile": "9000000003"}).status_code == 503


def test_catalog_filters_inactive_and_missing(api):
    client, engine = api
    assert len(client.get("/api/commodities").json()) == 3
    assert len(client.get("/api/centres").json()) == 3
    assert len(client.get("/api/centres", params={"commodity": "copra"}).json()) == 2
    assert client.get("/api/centres", params={"district": "unknown"}).json() == []
    detail = client.get("/api/centres/" + seed_id("centre:kollam-east")).json()
    assert len(detail["resources"]) == 4 and detail["commodities"]
    assert client.get("/api/centres/missing").status_code == 404
    with Session(engine) as db:
        db.get(ProcurementCentre, seed_id("centre:kollam-east")).is_active = False
        db.get(Commodity, seed_id("commodity:maize")).is_active = False
        db.commit()
    assert len(client.get("/api/centres").json()) == 2
    assert len(client.get("/api/centres", params={"active": False}).json()) == 1
    assert len(client.get("/api/commodities").json()) == 2
    assert not any(s["available"] for s in availability(client).json())
    headers, _ = login(client)
    assert client.post("/api/bookings", json=payload(), headers=headers).status_code == 409


def test_booking_group_ownership_cancellation_and_rebook(api):
    client, engine = api
    headers, who = login(client)
    other, other_who = login(client, "9000000002")
    assert client.post("/api/bookings", json=payload()).status_code == 401
    assert client.post("/api/bookings", json=payload(farmer_id=other_who["user"]["id"]), headers=headers).status_code == 422
    response = client.post("/api/bookings", json=payload(group_metadata={"group_name": "Test group", "farmer_count": 2, "contact_name": "Test contact"}), headers=headers)
    assert response.status_code == 201, response.text
    booking = response.json()
    assert booking["farmer_id"] == who["user"]["id"] and booking["version"] == 1
    path = "/api/bookings/" + booking["id"]
    assert client.get(path, headers=headers).json()["group_metadata"]["farmer_count"] == 2
    assert client.get(path, headers=other).status_code == 404
    assert client.post(path + "/cancel", headers=other, json={"expected_version": 1}).status_code == 404
    assert client.get("/api/bookings", headers=other, params={"farmer_id": who["user"]["id"]}).json() == []
    assert len(client.get("/api/bookings?active=true&group=true", headers=headers).json()) == 1
    assert client.get("/api/bookings?history=true", headers=headers).json() == []
    assert Decimal(availability(client).json()[0]["remaining_capacity"]) == 2400
    assert client.post(path + "/cancel", headers=headers, json={"expected_version": 2}).status_code == 409
    cancelled = client.post(path + "/cancel", headers=headers, json={"expected_version": 1, "reason": "Change of plan"})
    assert cancelled.status_code == 200 and cancelled.json()["version"] == 2
    assert cancelled.json()["cancelled_at"] and cancelled.json()["status"] == "cancelled"
    assert client.post(path + "/cancel", headers=headers, json={"expected_version": 2}).status_code == 409
    assert len(client.get("/api/bookings?history=true&status=cancelled", headers=headers).json()) == 1
    assert Decimal(availability(client).json()[0]["remaining_capacity"]) == 3000
    rebooked = client.post("/api/bookings", json=payload(), headers=headers).json()
    assert rebooked["token"] != booking["token"]
    engine.dispose()
    with Session(engine) as db:
        assert db.get(Booking, rebooked["id"]).farmer_id == who["user"]["id"]


@pytest.mark.parametrize("changes,code", [
    ({"quantity": 0}, 422), ({"quantity": 49}, 400), ({"quantity": 50.5}, 400),
    ({"quantity": 4000}, 409), ({"centre_id": "missing"}, 404),
    ({"commodity_id": seed_id("commodity:maize")}, 400), ({"start_time": "08:00"}, 400),
    ({"appointment_date": "2000-01-01"}, 400), ({"status": "completed"}, 422),
    ({"group_metadata": {"group_name": "x", "contact_name": "x", "farmer_count": 21}}, 422),
])
def test_booking_failures(api, changes, code):
    client, _ = api
    headers, _ = login(client)
    assert client.post("/api/bookings", headers=headers, json=payload(**changes)).status_code == code


def test_completed_bookings_release_active_capacity_and_cannot_cancel(api):
    client, engine = api
    headers, _ = login(client)
    booking = client.post("/api/bookings", headers=headers, json=payload(quantity=3000)).json()
    assert not availability(client).json()[0]["available"]
    with Session(engine) as db:
        db.get(Booking, booking["id"]).status = BookingStatus.COMPLETED
        db.commit()
    assert availability(client).json()[0]["available"]
    assert client.post("/api/bookings/" + booking["id"] + "/cancel", headers=headers, json={"expected_version": 2}).status_code == 409


def test_concurrent_capacity_requests_are_serialized(api):
    client, engine = api
    first, _ = login(client)
    second, _ = login(client, "9000000002")
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda headers: client.post("/api/bookings", headers=headers, json=payload(quantity=2000)).status_code, [first, second]))
    assert sorted(results) == [201, 409]
    with Session(engine) as db:
        assert db.scalar(select(func.sum(Booking.quantity))) == 2000


def test_recommendation_ranking_scoping_and_components(api):
    client, engine = api
    headers, _ = login(client)
    assert client.post("/api/bookings", headers=headers, json=payload(centre_id=seed_id("centre:kollam-town"), quantity=1800)).status_code == 201
    ranked = recommendations(client)
    assert ranked[0]["centre"]["code"] == "kollam-east" and ranked[0]["recommended"]
    assert sum(item["recommended"] for item in ranked) == 1
    for row in ranked:
        assert row["reason"] and "no live GPS" in row["travel_source"]
        assert row["expected_completion_minutes"] == sum(row[k] for k in ["travel_eta_minutes", "queue_eta_minutes", "processing_eta_minutes", "disruption_penalty_minutes"])
    baseline = ranked
    assert client.post("/api/bookings", headers=headers, json=payload(centre_id=seed_id("centre:kollam-east"), start_time="11:00", quantity=2000)).status_code == 201
    assert client.post("/api/bookings", headers=headers, json=payload(appointment_date=(local_today()+timedelta(days=2)).isoformat(), quantity=2000)).status_code == 201
    assert recommendations(client) == baseline


def test_disruption_zero_resource_and_slot_feasibility(api):
    client, engine = api
    with Session(engine) as db:
        db.add(Disruption(centre_id=seed_id("centre:kollam-east"), resource_type=ResourceType.QUALITY_DESK,
            severity=Severity.MEDIUM, note="Test outage", expected_recovery_minutes=30, reported_by=seed_id("user:staff")))
        db.commit()
    rows = {r["centre"]["code"]: r for r in recommendations(client)}
    east = rows["kollam-east"]
    assert east["disruption_penalty_minutes"] == 15 and east["processing_eta_minutes"] == 20
    assert east["expected_completion_minutes"] == 18 + 0 + 20 + 15
    assert not {r["centre"]["code"]: r for r in recommendations(client, 2000)}["kollam-east"]["capacity_available"]
    with Session(engine) as db:
        resource = db.scalar(select(CentreResource).where(CentreResource.centre_id == seed_id("centre:kollam-east"), CentreResource.resource_type == ResourceType.QUALITY_DESK))
        resource.active_count = 0
        db.commit()
    east = {r["centre"]["code"]: r for r in recommendations(client)}["kollam-east"]
    assert not east["capacity_available"] and east["expected_completion_minutes"] is None
    assert not east["recommended"] and east["queue_eta_minutes"] is None


def test_openapi_health_and_cors(api):
    client, _ = api
    response = client.get("/openapi.json")
    assert response.status_code == 200
    assert "/api/centres/recommendations" in response.json()["paths"]
    assert "/api/auth/staff/login" not in response.json()["paths"]
    assert client.get("/api/health").json()["status"] == "ok"
    response = client.options("/api/bookings", headers={"Origin": "http://localhost:5173", "Access-Control-Request-Method": "POST", "Access-Control-Request-Headers": "authorization,content-type"})
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"
    response = client.options("/api/bookings", headers={"Origin": "https://untrusted.example", "Access-Control-Request-Method": "POST"})
    assert "access-control-allow-origin" not in response.headers
