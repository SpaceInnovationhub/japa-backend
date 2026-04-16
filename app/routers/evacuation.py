from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import EvacuationRequest, User
from app.schemas import EvacuationCreate, EvacuationResponse   # Make sure EvacuationResponse exists

router = APIRouter(prefix="/evacuation", tags=["evacuation"])


@router.post("/request/{user_id}", response_model=EvacuationResponse)
def request_evacuation(
    user_id: int, 
    payload: EvacuationCreate, 
    db: Session = Depends(get_db)
):
    # Check if user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Optional: Prevent duplicate pending requests
    existing = db.query(EvacuationRequest).filter(
        EvacuationRequest.user_id == user_id,
        EvacuationRequest.status == "Pending"
    ).first()

    if existing:
        raise HTTPException(
            status_code=400,
            detail="You already have a pending evacuation request"
        )

    # Create new evacuation request
    new_request = EvacuationRequest(
        user_id=user_id,
        country=payload.country,
        location=payload.location,
        description=payload.description,
        status="Pending"
    )

    db.add(new_request)
    db.commit()
    db.refresh(new_request)

    return new_request   # This returns full data (better than just message)


@router.get("/user/{user_id}")
def get_user_requests(user_id: int, db: Session = Depends(get_db)):
    requests = db.query(EvacuationRequest).filter(
        EvacuationRequest.user_id == user_id
    ).order_by(EvacuationRequest.created_at.desc()).all()
    return requests


@router.get("/embassy/{country}")
def get_country_requests(country: str, db: Session = Depends(get_db)):
    requests = db.query(EvacuationRequest).filter(
        EvacuationRequest.country == country
    ).order_by(EvacuationRequest.created_at.desc()).all()
    return requests


@router.put("/update/{request_id}")
def update_request_status(
    request_id: int, 
    status: str, 
    db: Session = Depends(get_db)
):
    request_obj = db.query(EvacuationRequest).filter(
        EvacuationRequest.id == request_id
    ).first()

    if not request_obj:
        raise HTTPException(status_code=404, detail="Request not found")

    request_obj.status = status
    db.commit()
    db.refresh(request_obj)

    return {"message": f"Request status updated to {status}", "request": request_obj}