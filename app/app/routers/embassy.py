from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Announcement
from app.schemas import AnnouncementCreate

router = APIRouter(prefix="/embassy", tags=["embassy"])

@router.post("/announcement")
def create_announcement(announcement: AnnouncementCreate, db: Session = Depends(get_db)):
    new_announcement = Announcement(
        embassy_country=announcement.embassy_country,
        title=announcement.title,
        content=announcement.content
    )

    db.add(new_announcement)
    db.commit()
    db.refresh(new_announcement)
    return {"message": "Announcement posted", "announcement_id": new_announcement.id}

@router.get("/announcements/{country}")
def get_announcements(country: str, db: Session = Depends(get_db)):
    announcements = db.query(Announcement).filter(
        Announcement.embassy_country == country
    ).all()
    return announcements

@router.get("/announcements")
def get_all_announcements(db: Session = Depends(get_db)):
    return db.query(Announcement).all()