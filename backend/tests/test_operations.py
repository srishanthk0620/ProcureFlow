from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from decimal import Decimal
import pytest
from pydantic import SecretStr
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.errors import Conflict
from app.core.security import hash_password
from app.db.base import utc_now
from app.db.seed import seed_id
from app.models import (AuthSession, Booking, FarmerProfile, Notification, QueueEntry,
    Role, StaffAuthAttempt, StaffProfile, User)
from app.models.enums import BookingStatus, QueueStage, RoleName
from app.services.centre_service import local_today
from tests.test_farmer_api import api, login, payload

PASSWORD = "isolated-test-staff-passphrase"


@pytest.fixture(scope="module")
def stored_password():
    return hash_password(PASSWORD)


@pytest.fixture
def staff_account(api, stored_password):
    client, engine = api
    with Session(engine) as db:
        user = db.get(User, seed_id("user:staff"))
        user.is_active, user.password_hash = True, stored_password
        db.commit()
    return "DEV-STAFF-001"


def staff_login(client, identifier="DEV-STAFF-001"):
    request = client.post("/api/auth/staff/login", json={"identifier": identifier, "password": PASSWORD})
    assert request.status_code == 200, request.text
    challenge = request.json()
    verify = client.post("/api/auth/staff/otp/verify", json={"challenge_id": challenge["challenge_id"], "otp": challenge["development_otp"]})
    assert verify.status_code == 200, verify.text
    return {"Authorization": "Bearer " + verify.json()["access_token"]}, verify.json()


@pytest.fixture
def operator(api, staff_account):
    return staff_login(api[0])[0]


def due_booking(client, engine, farmer, **changes):
    response = client.post("/api/bookings", headers=farmer, json=payload(**changes))
    assert response.status_code == 201, response.text
    identifier = response.json()["id"]
    # Simulate arrival of the appointment day without changing the production clock.
    with Session(engine) as db:
        booking = db.get(Booking, identifier)
        booking.appointment_date = local_today()
        db.commit()
        return identifier, booking.version


def arrive(client, operator, identifier, version):
    response = client.post(f"/api/bookings/{identifier}/check-in", headers=operator, json={"expected_version": version})
    assert response.status_code == 201, response.text
    return response.json()


def act(client, operator, snapshot, action, expected=200):
    response = client.patch("/api/queue/" + snapshot["queue_id"], headers=operator,
        json={"action": action, "expected_version": snapshot["version"]})
    assert response.status_code == expected, response.text
    return response.json()


def notice_count(engine):
    with Session(engine) as db:
        return db.scalar(select(func.count()).select_from(Notification))


def test_staff_login_session_me_logout(api, staff_account):
    client, engine = api
    headers, session = staff_login(client)
    assert session["user"]["roles"] == [{"name": "staff"}]
    assert session["permitted_centre_ids"] == [seed_id("centre:kollam-east")]
    me = client.get("/api/auth/me", headers=headers).json()
    assert me["staff_profile"]["employee_code"] == staff_account
    assert "password" not in str(me) and "credential_digest" not in str(me)
    with Session(engine) as db:
        assert db.scalars(select(AuthSession)).one().auth_method == "staff_otp"
        assert db.scalars(select(StaffAuthAttempt)).one().consumed_at is not None
    assert client.post("/api/auth/logout", headers=headers).status_code == 204
    assert client.get("/api/queue", headers=headers).status_code == 401


def test_password_failure_rate_limit_and_spoofing(api, staff_account):
    client, engine = api
    for _ in range(5):
        assert client.post("/api/auth/staff/login", json={"identifier": staff_account, "password": "wrong-password-long"}).status_code == 401
    limited = client.post("/api/auth/staff/login", json={"identifier": staff_account, "password": PASSWORD})
    assert limited.status_code == 429 and limited.headers["Retry-After"]
    assert client.post("/api/auth/staff/login", json={"identifier": staff_account, "password": PASSWORD, "role": "super_admin"}).status_code == 422
    with Session(engine) as db:
        assert db.scalar(select(func.count()).select_from(StaffAuthAttempt)) == 5
        assert db.scalar(select(func.count()).select_from(AuthSession)) == 0


def test_staff_otp_wrong_expired_replay_and_cross_flow(api, staff_account):
    client, engine = api
    challenge = client.post("/api/auth/staff/login", json={"identifier": staff_account, "password": PASSWORD}).json()
    verify = {"challenge_id": challenge["challenge_id"], "otp": challenge["development_otp"]}
    assert client.post("/api/auth/farmer/otp/verify", json=verify).status_code == 401
    wrong = "000000" if verify["otp"] != "000000" else "000001"
    assert client.post("/api/auth/staff/otp/verify", json=verify | {"otp": wrong}).status_code == 401
    assert client.post("/api/auth/staff/otp/verify", json=verify).status_code == 200
    assert client.post("/api/auth/staff/otp/verify", json=verify).status_code == 401
    with Session(engine) as db:
        attempt = db.get(StaffAuthAttempt, verify["challenge_id"])
        attempt.created_at -= timedelta(seconds=61)
        db.commit()
    newer = client.post("/api/auth/staff/login", json={"identifier": staff_account, "password": PASSWORD}).json()
    with Session(engine) as db:
        db.get(StaffAuthAttempt, newer["challenge_id"]).expires_at = utc_now() - timedelta(seconds=1)
        db.commit()
    assert client.post("/api/auth/staff/otp/verify", json={"challenge_id": newer["challenge_id"], "otp": newer["development_otp"]}).status_code == 401


def test_staff_otp_attempt_limit_and_production_disabled(api, staff_account, monkeypatch):
    client, _ = api
    challenge = client.post("/api/auth/staff/login", json={"identifier": staff_account, "password": PASSWORD}).json()
    verify = {"challenge_id": challenge["challenge_id"], "otp": challenge["development_otp"]}
    for _ in range(5):
        wrong = "000000" if verify["otp"] != "000000" else "000001"
        assert client.post("/api/auth/staff/otp/verify", json=verify | {"otp": wrong}).status_code == 401
    assert client.post("/api/auth/staff/otp/verify", json=verify).status_code == 401
    monkeypatch.setattr(settings, "APP_ENV", "production")
    result = client.post("/api/auth/staff/login", json={"identifier": staff_account, "password": PASSWORD})
    assert result.status_code == 503 and "development_otp" not in result.text
    assert client.post("/api/auth/staff/otp/verify", json=verify).status_code == 503


def test_password_change_invalidates_challenge(api, staff_account, stored_password):
    client, engine = api
    challenge = client.post("/api/auth/staff/login", json={"identifier": staff_account, "password": PASSWORD}).json()
    with Session(engine) as db:
        db.get(User, seed_id("user:staff")).password_hash = None
        db.commit()
    assert client.post("/api/auth/staff/otp/verify", json={"challenge_id": challenge["challenge_id"], "otp": challenge["development_otp"]}).status_code == 401


def test_farmer_session_never_gains_staff_scope(api, staff_account):
    client, engine = api
    farmer, who = login(client)
    with Session(engine) as db:
        user = db.get(User, who["user"]["id"])
        user.roles.append(db.scalar(select(Role).where(Role.name == RoleName.STAFF)))
        user.staff_profile = StaffProfile(employee_code="DUAL-ROLE", centre_id=seed_id("centre:kollam-east"))
        db.commit()
    assert client.get("/api/queue", headers=farmer).status_code == 403
    me = client.get("/api/auth/me", headers=farmer).json()
    assert me["permitted_centre_ids"] == [] and me["user"]["roles"] == [{"name": "farmer"}]


def test_prearrival_and_cross_centre_authorization(api, operator):
    client, engine = api
    farmer, _ = login(client)
    other, _ = login(client, "9000000002")
    booking = client.post("/api/bookings", headers=farmer, json=payload()).json()
    status = client.get("/api/queue/" + booking["id"], headers=farmer).json()
    assert status["queue_id"] is None and not status["checked_in"] and status["position"] is None
    assert status["eta"]["travel_eta_minutes"] == 18
    assert client.get("/api/queue", headers=operator).json() == []
    assert client.get("/api/queue/" + booking["id"], headers=other).status_code == 404
    assert client.get("/api/queue", headers=farmer).status_code == 403
    assert client.post("/api/bookings/" + booking["id"] + "/check-in", headers=farmer, json={"expected_version": 1}).status_code == 403
    assert client.post("/api/bookings/" + booking["id"] + "/check-in", headers=operator, json={"expected_version": 1}).status_code == 409
    assert client.get("/api/queue?centre_id=" + seed_id("centre:kollam-town"), headers=operator).status_code == 403
    foreign, version = due_booking(client, engine, farmer, centre_id=seed_id("centre:kollam-town"))
    assert client.post(f"/api/bookings/{foreign}/check-in", headers=operator, json={"expected_version": version}).status_code == 403
    assert client.get("/api/queue/" + foreign, headers=operator).status_code == 403


def test_checkin_transitions_hold_resume_and_completion(api, operator):
    client, engine = api
    farmer, _ = login(client)
    identifier, version = due_booking(client, engine, farmer)
    checked = arrive(client, operator, identifier, version)
    assert checked["current_stage"] == "checked_in" and checked["position"] == 1
    assert checked["eta"]["travel_eta_minutes"] == 0
    assert client.post(f"/api/bookings/{identifier}/check-in", headers=operator, json={"expected_version": version}).status_code == 409
    act(client, operator, checked, "complete", 409)
    held = act(client, operator, checked, "hold")
    assert held["held"] and held["position"] is None and held["eta"]["expected_completion_minutes"] is None
    act(client, operator, held, "hold", 409)
    act(client, operator, held, "advance", 409)
    resumed = act(client, operator, held, "resume")
    act(client, operator, resumed, "resume", 409)
    act(client, operator, checked, "advance", 409)
    quality = act(client, operator, resumed, "advance")
    weighing = act(client, operator, quality, "advance")
    act(client, operator, weighing, "advance", 409)
    completed = act(client, operator, weighing, "complete")
    assert quality["quality_started_at"] and weighing["weighing_started_at"] and completed["completed_at"]
    assert checked["eta"]["processing_eta_minutes"] > quality["eta"]["processing_eta_minutes"] > weighing["eta"]["processing_eta_minutes"] > completed["eta"]["processing_eta_minutes"]
    assert completed["eta"]["expected_completion_minutes"] == 0
    act(client, operator, completed, "hold", 409)
    with Session(engine) as db:
        booking = db.get(Booking, identifier)
        assert booking.status.value == booking.queue_entry.current_stage.value == "completed"
        assert db.scalar(select(func.count()).select_from(QueueEntry)) == 1
    assert client.get("/api/queue", headers=operator).json() == []
    assert len(client.get("/api/queue?stage=completed", headers=operator).json()) == 1
    notices = client.get("/api/notifications", headers=farmer).json()
    assert len(notices) == 6 and any(n["category"] == "completed" for n in notices)


def test_queue_order_and_shared_eta(api, operator):
    client, engine = api
    farmer, _ = login(client)
    ids = [due_booking(client, engine, farmer) for _ in range(2)]
    first, second = [arrive(client, operator, identifier, version) for identifier, version in ids]
    assert second["position"] == 2 and second["bookings_ahead"] == 1
    assert second["eta"]["queue_eta_minutes"] == 10
    farmer_status = client.get("/api/queue/" + ids[1][0], headers=farmer).json()
    staff_status = next(r for r in client.get("/api/queue", headers=operator).json() if r["booking_id"] == ids[1][0])
    for key in farmer_status["eta"]:
        if key != "calculated_at":
            assert farmer_status["eta"][key] == staff_status["eta"][key]
    detail = client.get("/api/bookings/" + ids[1][0], headers=farmer).json()
    assert detail["eta"]["expected_completion_minutes"] == farmer_status["eta"]["expected_completion_minutes"]
    held = act(client, operator, first, "hold")
    updated = client.get("/api/queue/" + ids[1][0], headers=farmer).json()
    assert updated["position"] == 1 and updated["eta"]["queue_eta_minutes"] == 0
    first = act(client, operator, held, "resume")
    first = act(client, operator, first, "advance")
    assert client.get("/api/queue/" + ids[1][0], headers=farmer).json()["eta"]["queue_eta_minutes"] == 7
    first = act(client, operator, first, "advance")
    first = act(client, operator, first, "complete")
    assert client.get("/api/queue/" + ids[1][0], headers=farmer).json()["position"] == 1


def test_concurrent_duplicate_checkin_and_cancellation(api, operator):
    client, engine = api
    farmer, _ = login(client)
    identifier, version = due_booking(client, engine, farmer)
    with ThreadPoolExecutor(max_workers=2) as pool:
        codes = list(pool.map(lambda _: client.post(f"/api/bookings/{identifier}/check-in", headers=operator,
            json={"expected_version": version}).status_code, range(2)))
    assert sorted(codes) == [201, 409]
    cancelled, version = due_booking(client, engine, farmer)
    assert client.post(f"/api/bookings/{cancelled}/cancel", headers=farmer, json={"expected_version": version}).status_code == 200
    assert client.post(f"/api/bookings/{cancelled}/check-in", headers=operator, json={"expected_version": version + 1}).status_code == 409


def test_queue_event_failure_rolls_back_everything(api, operator, monkeypatch):
    client, engine = api
    farmer, _ = login(client)
    identifier, version = due_booking(client, engine, farmer)
    import app.services.queue_service as service
    original = service.notify_booking
    def failure(db, *args, **kwargs):
        original(db, *args, **kwargs)
        db.flush()
        raise Conflict()
    monkeypatch.setattr(service, "notify_booking", failure)
    assert client.post(f"/api/bookings/{identifier}/check-in", headers=operator, json={"expected_version": version}).status_code == 409
    with Session(engine) as db:
        booking = db.get(Booking, identifier)
        assert booking.status == BookingStatus.BOOKED and booking.version == version
        assert booking.queue_entry is None
        assert db.scalar(select(func.count()).select_from(Notification)) == 0


def test_disruption_effects_resolution_notifications_and_zero(api, operator):
    client, engine = api
    farmer, _ = login(client)
    identifier, version = due_booking(client, engine, farmer)
    arrive(client, operator, identifier, version)
    report = {"resource_type": "quality_desk", "severity": "medium", "note": "Distinct desk one", "expected_recovery_minutes": 30}
    assert client.post("/api/disruptions", headers=farmer, json=report).status_code == 403
    assert client.post("/api/disruptions", headers=operator, json=report | {"centre_id": seed_id("centre:kollam-town")}).status_code == 403
    first = client.post("/api/disruptions", headers=operator, json=report)
    assert first.status_code == 201, first.text
    assert client.post("/api/disruptions", headers=operator, json=report).status_code == 409
    status = client.get("/api/queue/" + identifier, headers=farmer).json()
    assert Decimal(status["eta"]["resource_factor"]) == Decimal("0.5")
    assert status["eta"]["processing_eta_minutes"] == 20 and status["eta"]["disruption_penalty_minutes"] == 15
    assert status["eta"]["expected_completion_minutes"] == 35
    second = client.post("/api/disruptions", headers=operator, json=report | {"note": "Distinct desk two"})
    assert second.status_code == 201
    zero = client.get("/api/queue/" + identifier, headers=farmer).json()["eta"]
    assert Decimal(zero["resource_factor"]) == 0 and zero["expected_completion_minutes"] is None
    assert client.post("/api/disruptions", headers=operator, json=report | {"note": "No third working desk"}).status_code == 409
    assert client.patch("/api/disruptions/" + first.json()["id"] + "/resolve", headers=farmer).status_code == 403
    for incident in [first.json(), second.json()]:
        response = client.patch("/api/disruptions/" + incident["id"] + "/resolve", headers=operator)
        assert response.status_code == 200 and response.json()["resolved_at"]
        before = notice_count(engine)
        assert client.patch("/api/disruptions/" + incident["id"] + "/resolve", headers=operator).status_code == 409
        assert notice_count(engine) == before
    restored = client.get("/api/queue/" + identifier, headers=farmer).json()["eta"]
    assert restored["processing_eta_minutes"] == 10 and restored["disruption_penalty_minutes"] == 0
    assert len(client.get("/api/disruptions?status=resolved", headers=operator).json()) == 2
    assert len(client.get("/api/notifications", headers=farmer).json()) == 5


def test_notification_isolation_and_read(api, operator):
    client, engine = api
    farmer, _ = login(client)
    other, _ = login(client, "9000000002")
    identifier, version = due_booking(client, engine, farmer)
    arrive(client, operator, identifier, version)
    assert client.get("/api/notifications", headers=other).json() == []
    notice = client.get("/api/notifications?unread=true", headers=farmer).json()[0]
    url = "/api/notifications/" + notice["id"] + "/read"
    assert client.patch(url, headers=other, json={"read": True}).status_code == 404
    assert client.patch(url, headers=farmer, json={"read": True}).json()["is_read"]
    assert client.get("/api/notifications?unread=true", headers=farmer).json() == []
    assert not client.patch(url, headers=farmer, json={"read": False}).json()["is_read"]


def test_manager_scope_and_no_admin_shortcut(api, staff_account):
    client, engine = api
    with Session(engine) as db:
        user = db.get(User, seed_id("user:staff"))
        user.roles = [db.scalar(select(Role).where(Role.name == RoleName.CENTRE_MANAGER))]
        db.commit()
    manager, _ = staff_login(client)
    assert client.get("/api/queue", headers=manager).status_code == 200
    assert client.get("/api/disruptions?centre_id=" + seed_id("centre:kollam-town"), headers=manager).status_code == 403
    with Session(engine) as db:
        user = db.get(User, seed_id("user:staff"))
        user.roles = [db.scalar(select(Role).where(Role.name == RoleName.SUPER_ADMIN))]
        db.commit()
    assert client.get("/api/queue", headers=manager).status_code == 401


def test_migration_preserves_existing_session(api):
    from alembic import command
    from alembic.config import Config
    from pathlib import Path
    client, engine = api
    farmer, who = login(client)
    with engine.begin() as connection:
        config = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
        config.attributes["connection"] = connection
        command.downgrade(config, "0002")
        command.upgrade(config, "head")
        row = connection.execute(text("SELECT user_id, auth_method FROM auth_sessions")).one()
        assert row.user_id == who["user"]["id"] and row.auth_method == "farmer_otp"
    assert client.get("/api/auth/me", headers=farmer).status_code == 200


def test_other_centre_cannot_mutate_queue_or_resolve_incident(api, operator, stored_password):
    client, engine = api
    farmer, _ = login(client)
    identifier, version = due_booking(client, engine, farmer)
    checked = arrive(client, operator, identifier, version)
    incident = client.post("/api/disruptions", headers=operator, json={"resource_type": "other",
        "severity": "medium", "note": "Local operational delay", "expected_recovery_minutes": 30}).json()
    with Session(engine) as db:
        user = User(display_name="Other test operator", is_active=True, password_hash=stored_password,
            roles=[db.scalar(select(Role).where(Role.name == RoleName.STAFF))])
        user.staff_profile = StaffProfile(employee_code="OTHER-STAFF", centre_id=seed_id("centre:kollam-town"))
        db.add(user)
        db.commit()
    other, _ = staff_login(client, "OTHER-STAFF")
    assert client.get("/api/queue", headers=other).json() == []
    act(client, other, checked, "hold", 403)
    assert client.patch("/api/disruptions/" + incident["id"] + "/resolve", headers=other).status_code == 403


def test_disruption_transaction_rolls_back_on_notification_failure(api, operator, monkeypatch):
    from app.models import Disruption
    import app.services.disruption_service as service
    client, engine = api
    farmer, _ = login(client)
    due_booking(client, engine, farmer)
    original = service.notify_booking
    def failure(db, *args, **kwargs):
        original(db, *args, **kwargs)
        db.flush()
        raise Conflict()
    monkeypatch.setattr(service, "notify_booking", failure)
    result = client.post("/api/disruptions", headers=operator, json={"resource_type": "quality_desk",
        "severity": "high", "note": "Test rollback", "expected_recovery_minutes": 30})
    assert result.status_code == 409
    with Session(engine) as db:
        assert db.scalar(select(func.count()).select_from(Disruption)) == 0
        assert db.scalar(select(func.count()).select_from(Notification)) == 0
