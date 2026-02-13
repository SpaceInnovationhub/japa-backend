from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import EvacuationRequest, User
from app.schemas import EvacuationRequestCreate

router = APIRouter(prefix="/evacuation", tags=["evacuation"])

@router.post("/request/{user_id}")
def request_evacuation(user_id: int, request: EvacuationRequestCreate, db: Session = Depends(get_db)):
    # Check if user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Check if user already has pending request
    existing_request = db.query(EvacuationRequest).filter(
        EvacuationRequest.user_id == user_id,
        EvacuationRequest.status == "Pending"
    ).first()

    if existing_request:
        raise HTTPException(
            status_code=400,
            detail="You already have a pending evacuation request"
        )

    new_request = EvacuationRequest(
        user_id=user_id,
        country=request.country
    )

    db.add(new_request)
    db.commit()
    db.refresh(new_request)
    return {"message": "Evacuation request submitted", "request_id": new_request.id}

@router.get("/user/{user_id}")
def get_user_requests(user_id: int, db: Session = Depends(get_db)):
    requests = db.query(EvacuationRequest).filter(
        EvacuationRequest.user_id == user_id
    ).all()
    return requests

@router.get("/embassy/{country}")
def view_requests(country: str, db: Session = Depends(get_db)):
    requests = db.query(EvacuationRequest).filter(
        EvacuationRequest.country == country
    ).all()
    return requests

@router.put("/update/{request_id}")
def update_request_status(request_id: int, status: str, db: Session = Depends(get_db)):
    request = db.query(EvacuationRequest).filter(EvacuationRequest.id == request_id).first()
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")

    request.status = status
    db.commit()
    return {"message": f"Request status updated to {status}"}