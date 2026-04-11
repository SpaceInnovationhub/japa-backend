from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import logging

from app import models, schemas, database
from app.auth import verify_password, create_access_token

logger = logging.getLogger(__name__)

router = APIRouter(tags=["authentication"])


@router.post("/register", response_model=schemas.UserResponse)
def register(user: schemas.UserCreate, db: Session = Depends(database.get_db)):
    """Register new user"""
    # Check duplicates
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

    try:
        hashed_pass = hash_password(user.password)   # Make sure hash_password is imported
        if not hashed_pass or len(hashed_pass) < 50:
            raise HTTPException(status_code=500, detail="Password hashing failed")
    except Exception as e:
        logger.error(f"Password hashing error for {user.email}: {e}")
        raise HTTPException(status_code=500, detail="Error processing password")

    new_user = models.User(
        fullname=user.fullname,
        email=user.email,
        password=hashed_pass,
        passport_number=user.passport_number,
        nin=user.nin,
        phone=user.phone,
        country=user.country,
        fcm_token=user.fcm_token,
        role="user",
        is_active=True
    )

    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        logger.info(f"User registered successfully: {user.email}")
        return new_user
    except Exception as e:
        db.rollback()
        logger.error(f"Registration database error for {user.email}: {e}")
        raise HTTPException(status_code=500, detail="Could not complete registration")


@router.post("/login", response_model=schemas.Token)
def login(user_data: schemas.UserLogin, db: Session = Depends(database.get_db)):
    """Login user"""
    try:
        # Find user
        user = db.query(models.User).filter(models.User.email == user_data.email).first()

        if not user:
            logger.warning(f"Login failed - user not found: {user_data.email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Handle corrupted / old password hashes gracefully
        if not user.password or len(user.password) < 50 or not user.password.startswith("$2"):
            logger.error(f"Corrupted password hash detected for {user.email} (length: {len(user.password) if user.password else 0})")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Your password is corrupted. Please use 'Forgot Password' to reset it.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Verify password
        if not verify_password(user_data.password, user.password):
            logger.warning(f"Invalid password attempt for {user.email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Check account status
        if not getattr(user, 'is_active', True):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account is inactive. Contact support.",
            )

        # Generate token
        access_token = create_access_token(data={"sub": str(user.id)})

        logger.info(f"Login successful for {user.email}")
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "role": getattr(user, 'role', 'user'),
            "user_id": user.id
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected login error for {user_data.email}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred during login. Please try again later."
        )


@router.get("/me", response_model=schemas.UserResponse)
def read_users_me(current_user: models.User = Depends(get_current_user)):
    return current_user