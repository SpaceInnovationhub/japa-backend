from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app import models, database, schemas
from app.auth import hash_password, verify_password, create_access_token, get_current_user
from datetime import timedelta

# THIS IS THE CRITICAL LINE - Create the router instance
router = APIRouter(prefix="/auth", tags=["authentication"])

@router.post("/register", response_model=schemas.UserResponse)
def register(user: schemas.UserCreate, db: Session = Depends(database.get_db)):
    # Check if user exists
    db_user = db.query(models.User).filter(
        (models.User.email == user.email) |
        (models.User.passport_number == user.passport_number) |
        (models.User.nin == user.nin)
    ).first()

    if db_user:
        raise HTTPException(
            status_code=400,
            detail="Email, passport number, or NIN already registered"
        )

    # Create new user
    hashed_password = hash_password(user.password)
    new_user = models.User(
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

@router.post("/login", response_model=schemas.Token)
def login(user_data: schemas.UserLogin, db: Session = Depends(database.get_db)):
    user = db.query(models.User).filter(models.User.email == user_data.email).first()

    if not user or not verify_password(user_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=schemas.UserResponse)
def read_users_me(current_user: models.User = Depends(get_current_user)):
    return current_user