from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import SessionLocal  # Fixed import
from app.models import User  # Fixed import
import shutil
import os

router = APIRouter(prefix="/kyc", tags=["kyc"])

UPLOAD_DIR = "uploads/kyc"
os.makedirs(UPLOAD_DIR, exist_ok=True)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/submit/{user_id}")
async def submit_kyc(
    user_id: int,
    id_document: UploadFile = File(...),
    selfie_image: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    # Check if user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Validate file types (optional but recommended)
    allowed_extensions = [".jpg", ".jpeg", ".png", ".pdf"]

    id_ext = os.path.splitext(id_document.filename)[1].lower()
    selfie_ext = os.path.splitext(selfie_image.filename)[1].lower()

    if id_ext not in allowed_extensions or selfie_ext not in allowed_extensions:
        raise HTTPException(status_code=400, detail="Invalid file type. Allowed: jpg, jpeg, png, pdf")

    # Save files
    id_path = f"{UPLOAD_DIR}/id_{user_id}_{id_document.filename}"
    selfie_path = f"{UPLOAD_DIR}/selfie_{user_id}_{selfie_image.filename}"

    with open(id_path, "wb") as buffer:
        shutil.copyfileobj(id_document.file, buffer)

    with open(selfie_path, "wb") as buffer:
        shutil.copyfileobj(selfie_image.file, buffer)

    # Update user with KYC info
    user.id_document = id_path
    user.selfie_image = selfie_path
    user.kyc_verified = False
    user.kyc_submitted_at = datetime.utcnow()  # You'll need to add this column to User model

    db.commit()

    return {"message": "KYC Submitted. Verification Pending", "user_id": user_id}