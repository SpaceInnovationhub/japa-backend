from fastapi import APIRouter, UploadFile, File, Form, Depends
from sqlalchemy.orm import Session
from database import SessionLocal
from models import IncidentReport
import shutil, os

router = APIRouter(prefix="/incidents")

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
    file_path = f"{UPLOAD_DIR}/{user_id}_{media.filename}"
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(media.file, buffer)

    incident = IncidentReport(
        user_id=user_id,
        embassy_country=embassy_country,
        description=description,
        media_path=file_path
    )
    db.add(incident)
    db.commit()

    return {"message": "Incident report submitted"}


# Embassy fetch incidents by country
@router.get("/embassy/{country}")
def get_incidents(country: str, db: Session = Depends(get_db)):
    return db.query(IncidentReport)\
             .filter(IncidentReport.embassy_country == country)\
             .order_by(IncidentReport.created_at.desc())\
             .all()