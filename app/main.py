from fastapi import FastAPI, HTTPException, Depends, Header
from sqlalchemy.orm import Session
from .database import engine, Base, get_db
from . import models
import os

# Create the tables in PostgreSQL automatically
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# ... (Keep your CORSMiddleware here) ...

# --- CITIZEN ROUTES (FLUTTER) ---

@app.post("/signup")
def signup(request: models.UserCreate, db: Session = Depends(get_db)):
    # Check if user exists in REAL database
    db_user = db.query(models.User).filter(models.User.email == request.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    new_user = models.User(
        fullname=request.fullname,
        email=request.email,
        password=request.password, # Note: Use Bcrypt here later!
        country=request.country,
        role="user"
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "User created in DB", "user_id": new_user.id}

# --- EMBASSY ROUTES (REACT DASHBOARD) ---

@app.get("/incidents")
def get_all_incidents(db: Session = Depends(get_db)):
    # This is what your React Dashboard calls!
    return db.query(models.IncidentReport).all()

@app.get("/tickets")
def get_all_tickets(db: Session = Depends(get_db)):
    return db.query(models.SupportTicket).all()

@app.put("/incidents/{incident_id}")
def update_incident_status(incident_id: int, status: str, db: Session = Depends(get_db)):
    incident = db.query(models.IncidentReport).filter(models.IncidentReport.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Not found")
    incident.status = status
    db.commit()
    return {"message": "Status updated"}