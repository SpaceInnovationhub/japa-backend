import os
import shutil
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db # Use the central one we defined
from app.models import IncidentReport
from datetime import datetime

router = APIRouter(prefix="/api/incidents", tags=["incidents"])

UPLOAD_DIR = "uploads/incidents"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/report/{user_id}")
async def report_incident(
    user_id: int,
    embassy_country: str = Form(...),
    description: str = Form(...),
    media: UploadFile = File(None), # Made optional in case user has no media
    db: Session = Depends(get_db)
):
    file_path = None
    
    if media:
        allowed_extensions = [".jpg", ".jpeg", ".png", ".mp4", ".mov", ".pdf"]
        file_ext = os.path.splitext(media.filename)[1].lower()
        if file_ext not in allowed_extensions:
            raise HTTPException(status_code=400, detail="File type not allowed")

        # Create unique filename to avoid overwriting
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{user_id}_{timestamp}_{media.filename}"
        file_path = os.path.join(UPLOAD_DIR, filename)

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(media.file, buffer)

    new_incident = IncidentReport(
        user_id=user_id,
        embassy_country=embassy_country,
        description=description,
        media_path=file_path,
        status="Pending"
    )
    
    db.add(new_incident)
    db.commit()
    db.refresh(new_incident)

    return {"message": "Incident reported", "incident": new_incident.id}