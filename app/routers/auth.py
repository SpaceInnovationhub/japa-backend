from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app import models, database, schemas
from app.auth import hash_password, verify_password, create_access_token, get_current_user
from datetime import timedelta
import logging

# Set up logging
logger = logging.getLogger(__name__)

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

    # 2. Hash the password for security with validation
    try:
        hashed_pass = hash_password(user.password)
        
        # Validate the hash was created correctly
        if not hashed_pass or len(hashed_pass) < 50:
            raise HTTPException(
                status_code=500,
                detail="Password hashing failed - invalid hash generated"
            )
        
        logger.info(f"✅ Password hashed successfully for user: {user.email}")
        
    except Exception as e:
        logger.error(f"❌ Password hashing error for {user.email}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Error processing password. Please try again."
        )

    # 3. Create the new user object
    new_user = models.User(
        fullname=user.fullname,
        passport_number=user.passport_number,
        nin=user.nin,
        email=user.email,
        phone=user.phone,
        password=hashed_pass,
        country=user.country,
        fcm_token=user.fcm_token
    )

    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        logger.info(f"✅ User registered successfully: {user.email}")
        return new_user
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Registration Error for {user.email}: {str(e)}")
        raise HTTPException(status_code=500, detail="Could not complete registration")

@router.post("/login", response_model=schemas.Token)
def login(user_data: schemas.UserLogin, db: Session = Depends(database.get_db)):
    # 1. Find user by email
    user = db.query(models.User).filter(models.User.email == user_data.email).first()
    
    # 2. Check if user exists
    if not user:
        logger.warning(f"❌ Login failed - user not found: {user_data.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 3. Validate the password with error handling for corrupted hashes
    try:
        # Debug: Log hash info (without exposing the actual hash)
        if user.password:
            hash_length = len(user.password)
            hash_prefix = user.password[:10] if user.password else "None"
            logger.info(f"🔐 Verifying password for {user.email} - Hash length: {hash_length}, Prefix: {hash_prefix}")
            
            # Check if the hash looks corrupted
            if hash_length < 50:
                logger.error(f"⚠️ Corrupted password hash detected for user {user.email} (length: {hash_length})")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Account authentication error. Please reset your password.",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            # Check for proper bcrypt format
            if not user.password.startswith('$2'):
                logger.error(f"⚠️ Invalid bcrypt format for user {user.email} (starts with: {user.password[:2]})")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Account authentication error. Please contact support.",
                    headers={"WWW-Authenticate": "Bearer"},
                )
        
        # Perform the password verification
        is_valid_password = verify_password(user_data.password, user.password)
        
        if not is_valid_password:
            logger.warning(f"❌ Login failed - invalid password for user: {user_data.email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        logger.info(f"✅ Login successful for user: {user.email}")
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except ValueError as e:
        # Handle bcrypt salt errors specifically
        logger.error(f"❌ Bcrypt error for user {user.email}: {str(e)}")
        
        # Check if it's the salt error we're seeing
        if "salt" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Password hash is corrupted. Please reset your password.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication error. Please try again.",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except Exception as e:
        logger.error(f"❌ Unexpected error during login for {user.email}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during login. Please try again.",
        )

    # 4. Generate the JWT token
    try:
        access_token = create_access_token(data={"sub": str(user.id)})
        logger.info(f"🔑 Token generated successfully for user: {user.email}")
        return {"access_token": access_token, "token_type": "bearer"}
    except Exception as e:
        logger.error(f"❌ Token generation error for {user.email}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not generate access token.",
        )

@router.get("/me", response_model=schemas.UserResponse)
def read_users_me(current_user: models.User = Depends(get_current_user)):
    return current_user

# Optional: Add an endpoint for users to reset their password if hash is corrupted
@router.post("/reset-password-request")
def request_password_reset(email: str, db: Session = Depends(database.get_db)):
    """Endpoint to request password reset for users with corrupted hashes"""
    user = db.query(models.User).filter(models.User.email == email).first()
    
    if not user:
        # Don't reveal if user exists or not for security
        return {"message": "If the email exists, a reset link will be sent"}
    
    # Check if hash is corrupted
    if user.password and (len(user.password) < 50 or not user.password.startswith('$2')):
        logger.warning(f"⚠️ Corrupted hash detected for {email} - forcing password reset")
        # Here you would send a password reset email
        # For now, just log it
        return {"message": "Password reset link sent", "requires_reset": True}
    
    # Normal password reset flow
    return {"message": "Password reset link sent"}