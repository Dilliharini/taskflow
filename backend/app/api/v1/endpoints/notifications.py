import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select, update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from app.api.dependencies import get_current_user
from app.core.database import get_db
from app.core.realtime import publish_user_event
from app.models import Notification, User
from app.schemas.notification import NotificationRead, UnreadCountRead

router = APIRouter()


@router.get("", response_model=list[NotificationRead])
def list_notifications(
    limit: int = Query(default=30, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    unread_only: bool = False,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[Notification]:
    stmt = select(Notification).where(Notification.user_id == user.id)
    if unread_only:
        stmt = stmt.where(Notification.is_read.is_(False))
    return list(db.scalars(stmt.order_by(Notification.created_at.desc()).limit(limit).offset(offset)).all())


@router.get("/unread-count", response_model=UnreadCountRead)
def unread_count(db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> UnreadCountRead:
    count = db.scalar(select(func.count(Notification.id)).where(
        Notification.user_id == user.id, Notification.is_read.is_(False)
    )) or 0
    return UnreadCountRead(count=count)


@router.patch("/read-all", response_model=UnreadCountRead)
def mark_all_read(db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> UnreadCountRead:
    try:
        db.execute(
            update(Notification)
            .where(Notification.user_id == user.id, Notification.is_read.is_(False))
            .values(is_read=True, read_at=datetime.now(timezone.utc))
        )
        db.commit()
        remaining = db.scalar(select(func.count(Notification.id)).where(
            Notification.user_id == user.id, Notification.is_read.is_(False)
        )) or 0
        return UnreadCountRead(count=remaining)
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Unable to update notifications.") from None


@router.patch("/{notification_id}/read", response_model=NotificationRead)
def mark_read(notification_id: uuid.UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> Notification:
    try:
        notification = db.scalar(select(Notification).where(
            Notification.id == notification_id, Notification.user_id == user.id
        ))
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Unable to load notification.") from None
    if notification is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found.")
    if not notification.is_read:
        try:
            notification.is_read = True
            notification.read_at = datetime.now(timezone.utc)
            db.commit()
            db.refresh(notification)
        except SQLAlchemyError:
            db.rollback()
            raise HTTPException(status_code=500, detail="Unable to update notification.") from None
    return notification