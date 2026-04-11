from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
import shutil
import os
import logging

from app import models, database
from app.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(tags=["KYC Verification"])

UPLOAD_DIR = "uploads/kyc"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/submit/{user_id}")
async def submit_kyc(
    user_id: int,
    id_document: UploadFile = File(...),
    selfie_image: UploadFile = File(...),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(database.get_db)
):
    """Submit KYC documents"""

    # Security: Only owner or admin
    if current_user.id != user_id and getattr(current_user, 'role', 'user') != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only submit KYC for your own account"
        )

    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Validate file extensions
    allowed = {".jpg", ".jpeg", ".png", ".pdf"}
    id_ext = os.path.splitext(id_document.filename)[1].lower()
    selfie_ext = os.path.splitext(selfie_image.filename)[1].lower()

    if id_ext not in allowed or selfie_ext not in allowed:
        raise HTTPException(status_code=400, detail="Invalid file type. Allowed: jpg, jpeg, png, pdf")

    # Safe filenames
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    id_path = f"{UPLOAD_DIR}/id_{user_id}_{timestamp}{id_ext}"
    selfie_path = f"{UPLOAD_DIR}/selfie_{user_id}_{timestamp}{selfie_ext}"

    try:
        with open(id_path, "wb") as f:
            shutil.copyfileobj(id_document.file, f)

        with open(selfie_path, "wb") as f:
            shutil.copyfileobj(selfie_image.file, f)

        # Update user
        user.id_document = id_path
        user.selfie_image = selfie_path
        user.kyc_verified = False
        user.kyc_submitted_at = datetime.utcnow()

        db.commit()

        logger.info(f"KYC submitted for user {user_id}")
        return {
            "message": "KYC submitted successfully. Verification is pending.",
            "user_id": user_id
        }

    except Exception as e:
        db.rollback()
        logger.error(f"KYC error for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to process KYC submission")
