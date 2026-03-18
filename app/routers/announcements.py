from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from .. import models, schemas
from ..database import get_db
from ..auth import get_current_user

router = APIRouter(prefix="/api/announcements", tags=["announcements"])

@router.get("/", response_model=List[schemas.Announcement])
def get_announcements(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    announcements = db.query(models.Announcement).all()
    return announcements

@router.post("/", response_model=schemas.Announcement)
def create_announcement(
    announcement: schemas.AnnouncementCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Fix for Pydantic v2 - use .model_dump() instead of .dict()
    db_announcement = models.Announcement(
        **announcement.model_dump(),
        created_by=current_user.id
    )
    db.add(db_announcement)
    db.commit()
    db.refresh(db_announcement)
    return db_announcement