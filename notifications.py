from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
import models, schemas, auth
from database import get_db

router = APIRouter(prefix="/api/v1/notifications", tags=["Notifications"])

def create_notification(db: Session, user_id: int, message: str):
    """Helper function to log system events."""
    notif = models.Notification(user_id=user_id, message=message)
    db.add(notif)
    db.commit()

@router.get("/", response_model=schemas.APIResponse)
def get_notifications(is_read: Optional[bool] = None, current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    """Paginated list of notifications, filterable by read status."""
    query = db.query(models.Notification).filter(models.Notification.user_id == current_user.id)
    if is_read is not None:
        query = query.filter(models.Notification.is_read == is_read)
    
    # Basic pagination (Limit to 50 for hackathon scale)
    results = query.order_by(models.Notification.created_at.desc()).limit(50).all()
    
    return schemas.APIResponse(data=[{"id": n.id, "message": n.message, "is_read": n.is_read, "created_at": n.created_at} for n in results])

@router.patch("/{notif_id}/read", response_model=schemas.APIResponse)
def mark_as_read(notif_id: int, current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    notif = db.query(models.Notification).filter(models.Notification.id == notif_id, models.Notification.user_id == current_user.id).first()
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")
    notif.is_read = True
    db.commit()
    return schemas.APIResponse(message="Notification marked as read.")