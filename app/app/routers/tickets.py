from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import SupportTicket, User
from app.schemas import TicketCreate, TicketResponse

router = APIRouter(prefix="/tickets", tags=["tickets"])

@router.post("/create/{user_id}", response_model=TicketResponse)
def create_ticket(user_id: int, ticket: TicketCreate, db: Session = Depends(get_db)):
    # Check if user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    new_ticket = SupportTicket(
        user_id=user_id,
        subject=ticket.subject,
        description=ticket.description
    )

    db.add(new_ticket)
    db.commit()
    db.refresh(new_ticket)
    return new_ticket

@router.get("/user/{user_id}", response_model=list[TicketResponse])
def get_user_tickets(user_id: int, db: Session = Depends(get_db)):
    tickets = db.query(SupportTicket).filter(SupportTicket.user_id == user_id).all()
    return tickets

@router.get("/embassy/{country}", response_model=list[TicketResponse])
def embassy_tickets(country: str, db: Session = Depends(get_db)):
    # Get all tickets for users from this country
    tickets = db.query(SupportTicket).join(User).filter(User.country == country).all()
    return tickets