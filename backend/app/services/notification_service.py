from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.errors import NotFound
from app.db.transactions import serialized_write
from app.models import Booking, Notification
from app.models.enums import NoticeType
from app.schemas.core import NotificationRead
from app.services.auth_service import Principal, validate_actor


def notify_booking(db: Session, booking: Booking, category: NoticeType, title: str, message: str):
    """Called in the same transaction as the event; never commits independently."""
    db.add(Notification(recipient_id=booking.farmer_id, booking_id=booking.id,
        category=category, title=title, message=message))


def list_notifications(db: Session, actor: Principal, unread: bool | None, limit: int, offset: int):
    validate_actor(db, actor)
    query = select(Notification).where(Notification.recipient_id == actor.user_id)
    if unread is not None:
        query = query.where(Notification.is_read.is_(not unread))
    return [NotificationRead.model_validate(n) for n in db.scalars(query.order_by(
        Notification.created_at.desc(), Notification.id).offset(offset).limit(limit))]


def mark_notification(db: Session, actor: Principal, identifier: str, read: bool):
    with serialized_write(db):
        validate_actor(db, actor)
        notice = db.scalar(select(Notification).where(Notification.id == identifier, Notification.recipient_id == actor.user_id))
        if notice is None:
            raise NotFound()
        notice.is_read = read
        db.flush()
        result = NotificationRead.model_validate(notice)
    return result
