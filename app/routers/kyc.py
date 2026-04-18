from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
import shutil
import os
import logging

from app import models, database
from app.auth import get_current_user

logger = logging.getLogger(__name__)

# FIX: Removed prefix="/kyc" because it's already defined in main.py
router = APIRouter(tags=["KYC Verification"])

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
    """User submits KYC documents (ID + Selfie)"""

    if current_user.id != user_id and getattr(current_user, 'role', 'user') != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only submit KYC for your own account"
        )

    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Validate file types
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

        user.id_document = id_path
        user.selfie_image = selfie_path
        user.kyc_verified = False
        user.kyc_submitted_at = datetime.utcnow()
        user.kyc_verified_at = None

        db.commit()
        db.refresh(user)

        logger.info(f"KYC submitted for user {user_id}")
        return {
            "message": "KYC submitted successfully. Verification is pending.",
            "user_id": user_id,
            "status": "pending"
        }

    except Exception as e:
        db.rollback()
        logger.error(f"KYC submission failed for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to process KYC submission")


# ====================== VERIFY KYC (Embassy Dashboard) ======================
@router.post("/verify/{user_id}")
def verify_kyc(
    user_id: int,
    action: str,                    # "approve" or "reject"
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(database.get_db)
):
    """Embassy Admin / Staff verifies (approves or rejects) KYC"""

    if getattr(current_user, 'role', 'user') not in ["super_admin", "embassy", "admin"]:
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
        message = "KYC has been approved successfully"
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


# ====================== GET PENDING KYC (For Dashboard) ======================
@router.get("/pending")
def get_pending_kyc(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(database.get_db)
):
    """Get list of users with pending KYC verification filtered by Admin's country"""
    
    # Security check: Only Admins or Embassy Staff
    if getattr(current_user, 'role', 'user') not in ["super_admin", "embassy", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Only embassy staff can view pending KYC."
        )

    # Start the query for users who submitted KYC but aren't verified yet
    query = db.query(models.User).filter(
        models.User.kyc_submitted_at.isnot(None),
        models.User.kyc_verified == False
    )

    # DYNAMIC FILTER: 
    # If the user is an 'embassy' role, only show users from THEIR country
    if current_user.role == "embassy":
        query = query.filter(models.User.country == current_user.country)
        logger.info(f"Filtering pending KYC for country: {current_user.country}")

    pending_users = query.all()

    return pending_users