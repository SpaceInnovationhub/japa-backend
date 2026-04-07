from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
# Use absolute imports for Render/Cloud stability
from app import models, schemas
from app.database import get_db
# Ensure this matches your auth file location
from app.routers.auth import get_current_user 

router = APIRouter(prefix="/api/announcements", tags=["announcements"])

@router.get("/", response_model=List[schemas.AnnouncementResponse])
def get_announcements(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    return db.query(models.Announcement).all()

# FIXED: Changed from schemas.Announcement to schemas.AnnouncementResponse
@router.post("/", response_model=schemas.AnnouncementResponse)
def create_announcement(
    announcement: schemas.AnnouncementCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Only allow Admin or Embassy roles to post announcements
    if current_user.role not in ["admin", "embassy"]:
        raise HTTPException(status_code=403, detail="Not authorized to post announcements")

    db_announcement = models.Announcement(
        **announcement.model_dump()
    )
    db.add(db_announcement)
    db.commit()
    db.refresh(db_announcement)
    return db_announcement