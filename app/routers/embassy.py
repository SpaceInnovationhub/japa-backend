from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import SessionLocal
from models import Announcement
from schemas import AnnouncementCreate
from services.notification_service import send_push_to_country

@router.post("/announcement")
def create_announcement(data: AnnouncementCreate, db: Session = Depends(get_db)):
    new_announcement = Announcement(**data.dict())
    db.add(new_announcement)
    db.commit()

    # 🔔 Send push notification
    send_push_to_country(
        country=data.embassy_country,
        title=data.title,
        body=data.content[:100]  # short preview
    )

    return {"message": "Announcement published and notifications sent"}
router = APIRouter(prefix="/embassy")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Embassy creates announcement or warning
@router.post("/announcement")
def create_announcement(data: AnnouncementCreate, db: Session = Depends(get_db)):
    new_announcement = Announcement(**data.dict())
    db.add(new_announcement)
    db.commit()
    return {"message": "Announcement published"}

# Mobile app fetches announcements by country
@router.get("/announcements/{country}")
def get_announcements(country: str, db: Session = Depends(get_db)):
    return db.query(Announcement)\
             .filter(Announcement.embassy_country == country)\
             .order_by(Announcement.created_at.desc())\
             .all()