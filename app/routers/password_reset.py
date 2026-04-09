from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
from app import models, database, schemas
from app.auth import hash_password, verify_password, get_current_user
from app.utils.email import send_password_reset_email, send_password_changed_notification
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/password", tags=["password management"])

@router.post("/reset-request", response_model=schemas.PasswordResetResponse)
def request_password_reset(
    request: schemas.PasswordResetRequest,
    db: Session = Depends(database.get_db)
):
    """Request a password reset email"""
    
    # Find user by email
    user = db.query(models.User).filter(models.User.email == request.email).first()
    
    # For security, don't reveal if user exists or not
    if not user:
        logger.info(f"Password reset requested for non-existent email: {request.email}")
        return {"message": "If the email exists, a reset link will be sent"}
    
    # Check if hash is corrupted and needs forced reset
    requires_reset = False
    if user.password and (len(user.password) != 60 or not user.password.startswith('$2')):
        requires_reset = True
        logger.warning(f"Corrupted hash detected for {request.email} - forcing reset")
    
    # Check for existing unused tokens and invalidate them
    existing_tokens = db.query(models.PasswordResetToken).filter(
        models.PasswordResetToken.user_id == user.id,
        models.PasswordResetToken.used == False,
        models.PasswordResetToken.expires_at > datetime.utcnow()
    ).all()
    
    # Mark existing tokens as used (invalidate them)
    for token in existing_tokens:
        token.used = True
    
    # Generate new token
    reset_token = models.PasswordResetToken.generate_token(user.id)
    db.add(reset_token)
    db.commit()
    
    # Send email with reset link
    email_sent = send_password_reset_email(user.email, reset_token.token, user.fullname)
    
    if not email_sent:
        logger.error(f"Failed to send reset email to {user.email}")
        # Still return success message for security
        return {"message": "If the email exists, a reset link will be sent"}
    
    logger.info(f"Password reset token generated for {user.email}")
    return {
        "message": "Password reset email sent",
        "requires_reset": requires_reset
    }

@router.post("/reset-confirm")
def confirm_password_reset(
    reset_data: schemas.PasswordResetConfirm,
    db: Session = Depends(database.get_db)
):
    """Confirm password reset with token"""
    
    # Validate passwords match
    if reset_data.new_password != reset_data.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passwords do not match"
        )
    
    # Validate password strength
    if len(reset_data.new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters long"
        )
    
    # Find the token
    token_record = db.query(models.PasswordResetToken).filter(
        models.PasswordResetToken.token == reset_data.token,
        models.PasswordResetToken.used == False
    ).first()
    
    if not token_record:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
    
    # Check if token is expired
    if not token_record.is_valid():
        token_record.used = True
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset token has expired. Please request a new one."
        )
    
    # Get the user
    user = db.query(models.User).filter(models.User.id == token_record.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Hash the new password
    try:
        hashed_password = hash_password(reset_data.new_password)
        
        # Validate the hash was created correctly
        if len(hashed_password) != 60 or not hashed_password.startswith('$2'):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error processing new password"
            )
        
        # Update user's password
        user.password = hashed_password
        
        # Mark token as used
        token_record.used = True
        
        db.commit()
        
        # Send confirmation email
        send_password_changed_notification(user.email, user.fullname)
        
        logger.info(f"Password reset successful for {user.email}")
        
        return {"message": "Password has been reset successfully"}
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error resetting password for {user.email}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error resetting password. Please try again."
        )

@router.post("/change")
def change_password(
    password_data: schemas.PasswordChange,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(database.get_db)
):
    """Change password for authenticated user"""
    
    # Validate passwords match
    if password_data.new_password != password_data.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New passwords do not match"
        )
    
    # Validate password strength
    if len(password_data.new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters long"
        )
    
    # Verify current password
    if not verify_password(password_data.current_password, current_user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Current password is incorrect"
        )
    
    # Hash the new password
    try:
        hashed_password = hash_password(password_data.new_password)
        
        # Validate the hash
        if len(hashed_password) != 60 or not hashed_password.startswith('$2'):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error processing new password"
            )
        
        # Update password
        current_user.password = hashed_password
        db.commit()
        
        # Send notification email
        send_password_changed_notification(current_user.email, current_user.fullname)
        
        logger.info(f"Password changed successfully for {current_user.email}")
        
        return {"message": "Password changed successfully"}
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error changing password for {current_user.email}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error changing password. Please try again."
        )

@router.get("/check-reset-token/{token}")
def check_reset_token_validity(
    token: str,
    db: Session = Depends(database.get_db)
):
    """Check if a reset token is valid (for frontend validation)"""
    
    token_record = db.query(models.PasswordResetToken).filter(
        models.PasswordResetToken.token == token,
        models.PasswordResetToken.used == False
    ).first()
    
    if not token_record or not token_record.is_valid():
        return {"valid": False}
    
    return {"valid": True}