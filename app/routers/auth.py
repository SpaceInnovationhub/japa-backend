from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app import models, database, schemas
# Ensure these helper functions exist in app/auth.py
from app.auth import hash_password, verify_password, create_access_token, get_current_user
from datetime import timedelta

# FIX: Remove prefix="/auth" here to avoid the /auth/auth/login error
router = APIRouter(tags=["authentication"])

@router.post("/register", response_model=schemas.UserResponse)
def register(user: schemas.UserCreate, db: Session = Depends(database.get_db)):
    # 1. Check if user already exists (Email, Passport, or NIN)
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

    # 2. Hash the password for security
    hashed_pass = hash_password(user.password)

    # 3. Create the new user object
    new_user = models.User(
        fullname=user.fullname,
        passport_number=user.passport_number,
        nin=user.nin,
        email=user.email,
        phone=user.phone,
        password=hashed_pass, # Storing the hash, not plain text
        country=user.country,
        fcm_token=user.fcm_token  # Now correctly mapping from the request
    )

    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user
    except Exception as e:
        db.rollback()
        print(f"❌ Registration Error: {e}")
        raise HTTPException(status_code=500, detail="Could not complete registration")

@router.post("/login", response_model=schemas.Token)
def login(user_data: schemas.UserLogin, db: Session = Depends(database.get_db)):
    # 1. Find user by email
    user = db.query(models.User).filter(models.User.email == user_data.email).first()

    # 2. Validate user and password hash
    if not user or not verify_password(user_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 3. Generate the JWT token
    access_token = create_access_token(data={"sub": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=schemas.UserResponse)
def read_users_me(current_user: models.User = Depends(get_current_user)):
    return current_user