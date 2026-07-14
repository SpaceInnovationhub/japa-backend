from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, VisaInformation
from app.schemas import (
    VisaInformationResponse,
    VisaInformationUpsert,
)

router = APIRouter(
    prefix="/visa",
    tags=["Visa Information"],
)

@router.get(
    "/user/{user_id}",
    response_model=VisaInformationResponse,
)
def get_user_visa_information(
    user_id: int,
    db: Session = Depends(get_db),
):
    visa = (
        db.query(VisaInformation)
        .filter(VisaInformation.user_id == user_id)
        .first()
    )

    if not visa:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Visa information not found",
        )

    return visa

@router.put(
    "/user/{user_id}",
    response_model=VisaInformationResponse,
)
def create_or_update_visa_information(
    user_id: int,
    payload: VisaInformationUpsert,
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if payload.expiry_date < payload.arrival_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Expiry date cannot be earlier than arrival date",
        )

    visa = (
        db.query(VisaInformation)
        .filter(VisaInformation.user_id == user_id)
        .first()
    )

    values = payload.model_dump()

    if visa:
        for field, value in values.items():
            setattr(visa, field, value)
    else:
        visa = VisaInformation(
            user_id=user_id,
            **values,
        )
        db.add(visa)

    db.commit()
    db.refresh(visa)

    return visa