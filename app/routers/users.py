from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel   # ← This was missing
import logging

from app import models, schemas, database
from app.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["Users"])


class FcmUpdate(BaseModel):
    fcm_token: str


# ====================== PROFILE ENDPOINT (Fixes your 404) ======================
@router.get("/profile", response_model=schemas.UserResponse)
def get_user_profile(current_user: models.User = Depends(get_current_user)):
    """Get current logged-in user's profile"""
    return current_user


# ====================== UPDATE FCM TOKEN ======================
@router.put("/fcm", response_model=dict)
def update_fcm_token(
    data: FcmUpdate, 
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(database.get_db)
):
    """Update FCM token for the currently logged-in user"""
    try:
        current_user.fcm_token = data.fcm_token
        db.commit()
        logger.info(f"FCM token updated for user {current_user.id}")
        return {"message": "FCM token updated successfully"}
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating FCM token: {e}")
        raise HTTPException(status_code=500, detail="Failed to update FCM token")


# ====================== GET USER BY ID ======================
@router.get("/{user_id}", response_model=schemas.UserResponse)
def get_user_by_id(
    user_id: int, 
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)  # You can restrict this later
):
    """Get user by ID"""
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user