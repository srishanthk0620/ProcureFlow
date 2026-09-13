from datetime import date
from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session
from app.api.dependencies import get_current_principal, require_staff_or_manager
from app.db.session import get_db
from app.models.enums import DisruptionStatus, QueueStage
from app.schemas.core import NotificationRead
from app.schemas.operations import IncidentInput, IncidentRead, NotificationUpdate, QueueActionInput, QueueStatus, VersionAction
from app.services.auth_service import Principal
from app.services.disruption_service import list_disruptions, report_disruption, resolve_disruption
from app.services.notification_service import list_notifications, mark_notification
from app.services.queue_service import check_in, get_status, list_queue, transition_queue


def no_store(response: Response):
    response.headers["Cache-Control"] = "no-store"


router = APIRouter(prefix="/api", tags=["operations"], dependencies=[Depends(no_store)])


@router.post("/bookings/{booking_id}/check-in", response_model=QueueStatus, status_code=201)
def arrival(booking_id: str, payload: VersionAction,
            actor: Principal = Depends(require_staff_or_manager), db: Session = Depends(get_db)):
    return check_in(db, actor, booking_id, payload)


@router.get("/queue", response_model=list[QueueStatus])
def queue(centre_id: str | None = None, appointment_date: date | None = Query(default=None, alias="date"),
          stage: QueueStage | None = None, held: bool | None = None, commodity: str | None = None,
          limit: int = Query(default=100, ge=1, le=200), offset: int = Query(default=0, ge=0),
          actor: Principal = Depends(require_staff_or_manager), db: Session = Depends(get_db)):
    return list_queue(db, actor, centre_id, appointment_date, stage, held, commodity, limit, offset)


@router.get("/queue/{booking_id}", response_model=QueueStatus)
def status(booking_id: str, actor: Principal = Depends(get_current_principal), db: Session = Depends(get_db)):
    return get_status(db, actor, booking_id)


@router.patch("/queue/{queue_id}", response_model=QueueStatus)
def action(queue_id: str, payload: QueueActionInput,
           actor: Principal = Depends(require_staff_or_manager), db: Session = Depends(get_db)):
    return transition_queue(db, actor, queue_id, payload)


@router.get("/disruptions", response_model=list[IncidentRead])
def incidents(centre_id: str | None = None, status: DisruptionStatus | None = None,
              limit: int = Query(default=100, ge=1, le=200), offset: int = Query(default=0, ge=0),
              actor: Principal = Depends(require_staff_or_manager), db: Session = Depends(get_db)):
    return list_disruptions(db, actor, centre_id, status, limit, offset)


@router.post("/disruptions", response_model=IncidentRead, status_code=201)
def report(payload: IncidentInput, actor: Principal = Depends(require_staff_or_manager), db: Session = Depends(get_db)):
    return report_disruption(db, actor, payload)


@router.patch("/disruptions/{incident_id}/resolve", response_model=IncidentRead)
def resolve(incident_id: str, actor: Principal = Depends(require_staff_or_manager), db: Session = Depends(get_db)):
    return resolve_disruption(db, actor, incident_id)


@router.get("/notifications", response_model=list[NotificationRead])
def notifications(unread: bool | None = None, limit: int = Query(default=100, ge=1, le=200),
                  offset: int = Query(default=0, ge=0), actor: Principal = Depends(get_current_principal),
                  db: Session = Depends(get_db)):
    return list_notifications(db, actor, unread, limit, offset)


@router.patch("/notifications/{notification_id}/read", response_model=NotificationRead)
def read(notification_id: str, payload: NotificationUpdate,
         actor: Principal = Depends(get_current_principal), db: Session = Depends(get_db)):
    return mark_notification(db, actor, notification_id, payload.read)
