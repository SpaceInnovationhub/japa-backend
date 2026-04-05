from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
# Standardized Absolute Imports
from app import models, schemas
from app.database import get_db

router = APIRouter(prefix="/tickets", tags=["tickets"])

@router.post("/create/{user_id}", response_model=schemas.TicketResponse)
def create_ticket(user_id: int, ticket: schemas.TicketCreate, db: Session = Depends(get_db)):
    # 1. Verify User Exists
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # 2. Create the new ticket using the data from schemas.TicketCreate
    new_ticket = models.SupportTicket(
        user_id=user_id,
        embassy_country=ticket.embassy_country, # Added this to match your SQL schema
        subject=ticket.subject,
        description=ticket.description,
        status="Open"
    )

    db.add(new_ticket)
    db.commit()
    db.refresh(new_ticket)
    return new_ticket

@router.get("/user/{user_id}", response_model=List[schemas.TicketResponse])
def get_user_tickets(user_id: int, db: Session = Depends(get_db)):
    return db.query(models.SupportTicket).filter(models.SupportTicket.user_id == user_id).all()

@router.get("/embassy/{country}", response_model=List[schemas.TicketResponse])
def get_embassy_tickets(country: str, db: Session = Depends(get_db)):
    # Optimized query to find tickets assigned to a specific embassy country
    return db.query(models.SupportTicket).filter(models.SupportTicket.embassy_country == country).all()