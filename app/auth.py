# app/auth.py
from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app import database, models
import os
import logging

logger = logging.getLogger(__name__)

# Configure bcrypt with proper settings
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12,  # Add this for consistency
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# JWT Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

def hash_password(password: str) -> str:
    """
    Hash a password with bcrypt.
    Handles password length limits (bcrypt max 72 bytes).
    """
    if not password:
        raise ValueError("Password cannot be empty")
    
    # Truncate password to 72 bytes if necessary (bcrypt limitation)
    if len(password.encode('utf-8')) > 72:
        logger.warning(f"Password truncated from {len(password)} to 72 bytes")
        password = password[:72]  # Truncate to 72 characters
    
    try:
        hashed = pwd_context.hash(password)
        
        # Validate the hash was created correctly
        if not hashed or len(hashed) < 50:
            raise ValueError("Generated hash is invalid")
        
        return hashed
        
    except Exception as e:
        logger.error(f"Password hashing error: {str(e)}")
        raise ValueError(f"Could not hash password: {str(e)}")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain text password against a hashed password.
    Handles various error cases gracefully.
    """
    if not plain_password or not hashed_password:
        logger.warning("Missing password or hash for verification")
        return False
    
    # Check if hash is corrupted (too short)
    if len(hashed_password) < 20:
        logger.warning(f"Corrupted password hash detected (length: {len(hashed_password)})")
        return False
    
    # Check if hash has bcrypt format
    if not hashed_password.startswith('$2'):
        logger.warning(f"Invalid bcrypt format: {hashed_password[:10]}...")
        return False
    
    # Truncate plain password to 72 bytes if necessary
    if len(plain_password.encode('utf-8')) > 72:
        logger.warning(f"Plain password truncated from {len(plain_password)} to 72 bytes")
        plain_password = plain_password[:72]
    
    try:
        # Try to verify with normal context
        return pwd_context.verify(plain_password, hashed_password)
        
    except ValueError as e:
        # Handle specific bcrypt errors
        error_msg = str(e).lower()
        
        if "salt" in error_msg:
            logger.error(f"Invalid salt in hash: {hashed_password[:20]}...")
        elif "hash" in error_msg:
            logger.error(f"Invalid hash format: {hashed_password[:20]}...")
        else:
            logger.error(f"Password verification error: {str(e)}")
        
        return False
        
    except Exception as e:
        logger.error(f"Unexpected error in verify_password: {str(e)}")
        return False

def create_access_token(data: dict, expires_delta: timedelta = None):
    """Create JWT access token"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    return encoded_jwt

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(database.get_db)):
    """Get current user from JWT token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        
        user = db.query(models.User).filter(models.User.id == int(user_id)).first()
        if user is None:
            raise credentials_exception
        
        return user
        
    except JWTError:
        raise credentials_exception