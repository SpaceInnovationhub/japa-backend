from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db, SessionLocal  # Fixed import
from app.models import Announcement
from app.schemas import AnnouncementCreate, Announcement
from app.services.notification_service import send_push_to_country
from typing import List

# Define router
router = APIRouter(prefix="/embassy", tags=["embassy"])

@router.post("/announcement", response_model=dict)
def create_announcement(data: AnnouncementCreate, db: Session = Depends(get_db)):
    # Create new announcement
    new_announcement = Announcement(
        embassy_country=data.embassy_country,
        title=data.title,
        content=data.content,
        category=data.category
    )
    db.add(new_announcement)
    db.commit()
    db.refresh(new_announcement)

    # Send push notification
    try:
        send_push_to_country(
            country=data.embassy_country,
            title=data.title,
            body=data.content[:100]
        )
    except Exception as e:
        print(f"Notification failed: {e}")

    return {"message": "Announcement published and notifications sent"}

@router.get("/announcements/{country}", response_model=List[Announcement])
def get_announcements(country: str, db: Session = Depends(get_db)):
    announcements = db.query(Announcement)\
        .filter(Announcement.embassy_country == country)\
        .order_by(Announcement.created_at.desc())\
        .all()
    return announcements