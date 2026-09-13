"""Explicit, additive development seed. Requires migrations to have run first."""
from datetime import date, time
from decimal import Decimal
from uuid import NAMESPACE_URL, uuid5

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import SessionLocal
from app.models import (CentreResource, Commodity, FarmerProfile, PriceRecord,
                        ProcurementCentre, Role, SlotPolicy, StaffProfile, User)
from app.models.enums import ResourceType, RoleName


def seed_id(label: str) -> str:
    return str(uuid5(NAMESPACE_URL, "procureflow:development:" + label))


def seed_development(session: Session, environment: str) -> None:
    if environment not in {"development", "test"}:
        raise RuntimeError("Development seed is disabled in this environment")
    # Caller owns commit/rollback. Existing rows are never overwritten.
    roles = {}
    for name in RoleName:
        role = session.scalar(select(Role).where(Role.name == name))
        if role is None:
            role = Role(id=seed_id("role:" + name), name=name)
            session.add(role)
        roles[name] = role
    commodities = {}
    for code, name in [("paddy", "Paddy"), ("copra", "Copra"), ("maize", "Maize")]:
        commodity = session.scalar(select(Commodity).where(Commodity.code == code))
        if commodity is None:
            commodity = Commodity(id=seed_id("commodity:" + code), code=code, name=name, unit="kg")
            session.add(commodity)
        commodities[code] = commodity
    centres = {}
    for code, name, district, travel, distance in [
        ("kollam-east", "Kollam East Development Centre", "Kollam", 18, "8.4"),
        ("kollam-town", "Kollam Town Development Centre", "Kollam", 12, "5"),
        ("karunagappally", "Karunagappally Development Centre", "Kollam", 38, "22"),
    ]:
        centre = session.scalar(select(ProcurementCentre).where(ProcurementCentre.code == code))
        if centre is None:
            centre = ProcurementCentre(id=seed_id("centre:" + code), code=code, name=name,
                district=district, state="Kerala", reference_travel_minutes=travel,
                reference_distance_km=Decimal(distance), commodities=[commodities["paddy"]])
            if code != "karunagappally":
                centre.commodities.append(commodities["copra"])
            session.add(centre)
        centres[code] = centre
        session.flush()
        for hour in (9, 11, 14):
            policy = session.scalar(select(SlotPolicy).where(SlotPolicy.centre_id == centre.id, SlotPolicy.start_time == time(hour)))
            if policy is None:
                session.add(SlotPolicy(id=seed_id(code + ":slot:" + str(hour)), centre_id=centre.id,
                    start_time=time(hour), end_time=time(hour + 2), capacity=Decimal(3000), unit="kg"))
        for resource_type, total in [(ResourceType.GATE, 3), (ResourceType.QUALITY_DESK, 2),
                                     (ResourceType.WEIGHBRIDGE, 2), (ResourceType.STAFF, 7)]:
            exists = session.scalar(select(CentreResource).where(
                CentreResource.centre_id == centre.id, CentreResource.resource_type == resource_type))
            if exists is None:
                session.add(CentreResource(id=seed_id(code + ":" + resource_type), centre_id=centre.id,
                    resource_type=resource_type, total_count=total, active_count=total))
    for label, role_name in [("farmer", RoleName.FARMER), ("staff", RoleName.STAFF)]:
        user_id = seed_id("user:" + label)
        if session.get(User, user_id) is None:
            # No mobile number, password or usable default login. Explicitly inactive.
            user = User(id=user_id, display_name="Development " + label.title(),
                        is_active=False, roles=[roles[role_name]])
            session.add(user)
            session.flush()
            if label == "farmer":
                session.add(FarmerProfile(user_id=user_id, district="Kollam", state="Kerala"))
            else:
                session.add(StaffProfile(user_id=user_id, employee_code="DEV-STAFF-001",
                                         centre_id=centres["kollam-east"].id))
    for code, rate in [("paddy", "28.50"), ("copra", "112.00"), ("maize", "20.00")]:
        price_id = seed_id("price:" + code)
        if session.get(PriceRecord, price_id) is None:
            session.add(PriceRecord(id=price_id, commodity_id=commodities[code].id,
                rate=Decimal(rate), unit="kg", effective_date=date(2026, 1, 1),
                source_label="Development fixture; not an official/live quotation", illustrative=True))
    session.flush()


def main() -> None:
    with SessionLocal.begin() as session:
        seed_development(session, settings.APP_ENV)
    print("Development seed complete; existing data preserved.")


if __name__ == "__main__":
    main()
