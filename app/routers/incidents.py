from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import SessionLocal  # Fixed import
from app.models import IncidentReport  # Fixed import
import shutil, os

router = APIRouter(prefix="/incidents", tags=["incidents"])

UPLOAD_DIR = "uploads/incidents"
os.makedirs(UPLOAD_DIR, exist_ok=True)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# User submits incident
@router.post("/report/{user_id}")
async def report_incident(
    user_id: int,
    embassy_country: str = Form(...),
    description: str = Form(...),
    media: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    # Validate file type (optional but recommended)
    allowed_extensions = [".jpg", ".jpeg", ".png", ".mp4", ".mov", ".pdf"]
    file_ext = os.path.splitext(media.filename)[1].lower()
    if file_ext not in allowed_extensions:
        raise HTTPException(status_code=400, detail="File type not allowed")

    # Save file
    file_path = f"{UPLOAD_DIR}/{user_id}_{media.filename}"
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(media.file, buffer)

    # Create incident record
    incident = IncidentReport(
        user_id=user_id,
        embassy_country=embassy_country,
        description=description,
        media_path=file_path
    )
    db.add(incident)
    db.commit()
    db.refresh(incident)

    return {"message": "Incident report submitted", "incident_id": incident.id}


# Embassy fetch incidents by country
@router.get("/embassy/{country}")
def get_incidents(country: str, db: Session = Depends(get_db)):
    incidents = db.query(IncidentReport)\
        .filter(IncidentReport.embassy_country == country)\
        .order_by(IncidentReport.created_at.desc())\
        .all()

    return incidents