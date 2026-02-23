from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User
from app.schemas import UserCreate, UserLogin, UserResponse, Token
from app.auth import hash_password, verify_password, create_access_token
from pydantic import BaseModel

class FcmUpdate(BaseModel):
    fcm_token: str

@router.put("/fcm/{user_id}")
def update_fcm(user_id: int, data: FcmUpdate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    user.fcm_token = data.fcm_token
    db.commit()
    return {"message": "FCM token updated"}

router = APIRouter(prefix="/user", tags=["users"])

@router.post("/register", response_model=UserResponse)
def register(user: UserCreate, db: Session = Depends(get_db)):
    # Check if user already exists
    db_user = db.query(User).filter(
        (User.email == user.email) |
        (User.passport_number == user.passport_number) |
        (User.nin == user.nin)
    ).first()

    if db_user:
        raise HTTPException(
            status_code=400,
            detail="Email, passport number, or NIN already registered"
        )

    # Create new user
    hashed_password = hash_password(user.password)
    new_user = User(
        fullname=user.fullname,
        passport_number=user.passport_number,
        nin=user.nin,
        email=user.email,
        phone=user.phone,
        password=hashed_password,
        country=user.country
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.post("/login", response_model=Token)
def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()

    if not db_user or not verify_password(user.password, db_user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": str(db_user.id)})
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user