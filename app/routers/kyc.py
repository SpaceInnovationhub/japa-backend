from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
import shutil
import os
import logging

from app import models, schemas, database
from app.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/kyc", tags=["KYC Verification"])

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
    """Submit KYC documents (ID + Selfie)"""

    # Security check: Only the user themselves or admin can submit
    if current_user.id != user_id and getattr(current_user, "role", "user") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only submit KYC for your own account"
        )

    # Check if user exists
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Validate file types
    allowed_extensions = {".jpg", ".jpeg", ".png", ".pdf"}
    
    id_ext = os.path.splitext(id_document.filename)[1].lower()
    selfie_ext = os.path.splitext(selfie_image.filename)[1].lower()

    if id_ext not in allowed_extensions or selfie_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400, 
            detail="Invalid file type. Allowed: jpg, jpeg, png, pdf"
        )

    # Create safe filenames
    id_path = f"{UPLOAD_DIR}/id_{user_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}{id_ext}"
    selfie_path = f"{UPLOAD_DIR}/selfie_{user_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}{selfie_ext}"

    try:
        # Save files
        with open(id_path, "wb") as buffer:
            shutil.copyfileobj(id_document.file, buffer)

        with open(selfie_path, "wb") as buffer:
            shutil.copyfileobj(selfie_image.file, buffer)

        # Update user KYC fields (make sure these columns exist in your User model)
        user.id_document = id_path
        user.selfie_image = selfie_path
        user.kyc_verified = False
        user.kyc_submitted_at = datetime.utcnow()

        db.commit()

        logger.info(f"KYC submitted successfully for user {user_id}")
        return {
            "message": "KYC submitted successfully. Verification is pending.",
            "user_id": user_id,
            "id_document_path": id_path,
            "selfie_path": selfie_path
        }

    except Exception as e:
        db.rollback()
        logger.error(f"KYC submission failed for user {user_id}: {e}")
        # Clean up files if saving failed (optional)
        for path in [id_path, selfie_path]:
            if os.path.exists(path):
                try:
                    os.remove(path)
                except:
                    pass
        raise HTTPException(status_code=500, detail="Failed to save KYC documents")
