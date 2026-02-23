from fastapi import APIRouter, UploadFile, File, Depends
from sqlalchemy.orm import Session
from database import SessionLocal
from models import User
import shutil
import os

router = APIRouter(prefix="/kyc")

UPLOAD_DIR = "uploads"
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
    id_path = f"{UPLOAD_DIR}/id_{user_id}_{id_document.filename}"
    selfie_path = f"{UPLOAD_DIR}/selfie_{user_id}_{selfie_image.filename}"

    with open(id_path, "wb") as buffer:
        shutil.copyfileobj(id_document.file, buffer)

    with open(selfie_path, "wb") as buffer:
        shutil.copyfileobj(selfie_image.file, buffer)

    user = db.query(User).filter(User.id == user_id).first()
    user.id_document = id_path
    user.selfie_image = selfie_path
    user.kyc_verified = False

    db.commit()

    return {"message": "KYC Submitted. Verification Pending"}
