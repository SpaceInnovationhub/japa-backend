from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
import shutil
import os
import logging

from app import models, database
from app.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/kyc", tags=["KYC Verification"])

UPLOAD_DIR = "uploads/kyc"
os.makedirs(UPLOAD_DIR, exist_ok=True)


# ====================== SUBMIT KYC ======================
@router.post("/submit/{user_id}")
async def submit_kyc(
    user_id: int,
    id_document: UploadFile = File(...),
    selfie_image: UploadFile = File(...),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(database.get_db)
):
    """User submits KYC documents"""
    # ... (keep your existing submit_kyc function as is)
    # I'll keep it short here — just add the pending one below


# ====================== VERIFY KYC ======================
@router.post("/verify/{user_id}")
def verify_kyc(
    user_id: int,
    action: str,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(database.get_db)
):
    # ... (keep your existing verify_kyc function)


# ====================== GET PENDING KYC ======================
@router.get("/pending")
def get_pending_kyc(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(database.get_db)
):
    """Get list of pending KYC for dashboard"""
    if getattr(current_user, 'role', 'user') not in ["admin", "embassy", "embassy_staff"]:
        raise HTTPException(status_code=403, detail="Access denied")

    pending_users = db.query(models.User).filter(
        models.User.kyc_submitted_at.isnot(None),
        models.User.kyc_verified == False
    ).all()

    return pending_users