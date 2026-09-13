from datetime import date, time
from decimal import Decimal
from typing import Annotated
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models import Commodity
from app.schemas.core import CentreRead, CommodityRead
from app.schemas.farmer_api import RecommendationRead, SlotRead
from app.services.centre_service import get_centre, list_centres, slots
from app.services.recommendation_service import recommendations

router = APIRouter(prefix="/api", tags=["catalog"])
Amount = Annotated[Decimal, Query(gt=0, le=20000, max_digits=12, decimal_places=3)]


@router.get("/commodities", response_model=list[CommodityRead])
def commodities(db: Session = Depends(get_db)):
    return list(db.scalars(select(Commodity).where(Commodity.is_active.is_(True)).order_by(Commodity.code)))


@router.get("/centres", response_model=list[CentreRead])
def centres(commodity: str | None = None, district: str | None = None, active: bool | None = True, db: Session = Depends(get_db)):
    return list_centres(db, commodity, district, active)


@router.get("/centres/recommendations", response_model=list[RecommendationRead])
def recommend(commodity: str, quantity: Amount, appointment_date: date, start_time: time | None = None, db: Session = Depends(get_db)):
    return recommendations(db, commodity, quantity, appointment_date, start_time)


@router.get("/centres/{centre_id}", response_model=CentreRead)
def centre(centre_id: str, db: Session = Depends(get_db)):
    return get_centre(db, centre_id)


@router.get("/centres/{centre_id}/slots", response_model=list[SlotRead])
def availability(centre_id: str, appointment_date: date, commodity: str, quantity: Amount = Decimal(50), db: Session = Depends(get_db)):
    return slots(db, centre_id, appointment_date, commodity, quantity)
