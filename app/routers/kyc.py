from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
import shutil
import os
import logging

from app import models, database
from app.auth import get_current_user

logger = logging.getLogger(__name__)

# No prefix here - main.py will add /kyc
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
    """User submits KYC documents"""

    if current_user.id != user_id and getattr(current_user, 'role', 'user') != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only submit KYC for your own account"
        )

    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    allowed = {".jpg", ".jpeg", ".png", ".pdf"}
    id_ext = os.path.splitext(id_document.filename)[1].lower()
    selfie_ext = os.path.splitext(selfie_image.filename)[1].lower()

    if id_ext not in allowed or selfie_ext not in allowed:
        raise HTTPException(status_code=400, detail="Invalid file type. Allowed: jpg, jpeg, png, pdf")

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    id_path = f"{UPLOAD_DIR}/id_{user_id}_{timestamp}{id_ext}"
    selfie_path = f"{UPLOAD_DIR}/selfie_{user_id}_{timestamp}{selfie_ext}"

    try:
        with open(id_path, "wb") as f:
            shutil.copyfileobj(id_document.file, f)

        with open(selfie_path, "wb") as f:
            shutil.copyfileobj(selfie_image.file, f)

        user.id_document = id_path
        user.selfie_image = selfie_path
        user.kyc_verified = False
        user.kyc_submitted_at = datetime.utcnow()
        user.kyc_verified_at = None

        db.commit()
        db.refresh(user)

        return {
            "message": "KYC submitted successfully. Verification is pending.",
            "user_id": user_id
        }

    except Exception as e:
        db.rollback()
        logger.error(f"KYC submission failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to process KYC")
    
    # ====================== VERIFY / APPROVE KYC (Embassy Dashboard) ======================
@router.post("/verify/{user_id}")
def verify_kyc(
    user_id: int,
    action: str = "approve",        # "approve" or "reject"
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(database.get_db)
):
    """Embassy staff approves or rejects a user's KYC"""

    # Only allow admin or embassy staff
    if getattr(current_user, 'role', 'user') not in ["admin", "embassy", "embassy_staff"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only embassy staff or admins can verify KYC"
        )

    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if action.lower() == "approve":
        user.kyc_verified = True
        user.kyc_verified_at = datetime.utcnow()
        message = "KYC has been successfully approved"
        status_msg = "verified"

    elif action.lower() == "reject":
        user.kyc_verified = False
        user.kyc_verified_at = None
        message = "KYC has been rejected"
        status_msg = "rejected"
    else:
        raise HTTPException(status_code=400, detail="Invalid action. Use 'approve' or 'reject'")

    db.commit()
    db.refresh(user)

    logger.info(f"KYC {action} for user {user_id} by {current_user.role} {current_user.id}")

    return {
        "message": message,
        "user_id": user_id,
        "fullname": user.fullname,
        "kyc_verified": user.kyc_verified,
        "status": status_msg,
        "verified_at": user.kyc_verified_at
    }