from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from datetime import datetime
from app import models, database, schemas
from app.auth import hash_password, verify_password, get_current_user
from app.utils.email import send_password_reset_email, send_password_changed_notification
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/password", tags=["password management"])


@router.post("/reset-request")
def request_password_reset(
    request: schemas.PasswordResetRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(database.get_db)
):
    """Request a password reset email"""
    
    user = db.query(models.User).filter(models.User.email == request.email).first()
    
    # Security: Never reveal if email exists
    if not user:
        logger.info(f"Password reset requested for non-existent email: {request.email}")
        return {"message": "If the email exists, a reset link has been sent."}
    
    # Check for corrupted hash
    requires_reset = False
    if user.password and (len(user.password) != 60 or not user.password.startswith('$2')):
        requires_reset = True
        logger.warning(f"Corrupted hash detected for {request.email}")

    # Invalidate old tokens
    existing_tokens = db.query(models.PasswordResetToken).filter(
        models.PasswordResetToken.user_id == user.id,
        models.PasswordResetToken.used == False,
        models.PasswordResetToken.expires_at > datetime.utcnow()
    ).all()

    for token in existing_tokens:
        token.used = True

    # Create new token
    reset_token = models.PasswordResetToken.generate_token(user.id)
    db.add(reset_token)
    db.commit()
    db.refresh(reset_token)

    # Queue email in background
    background_tasks.add_task(
        send_password_reset_email,
        user.email,
        reset_token.token,
        user.fullname or "User"
    )

    logger.info(f"Password reset token generated for {user.email}")

    return {
        "message": "If the email exists, a reset link has been sent.",
        "requires_reset": requires_reset
    }


# Keep the rest of your routes (reset-confirm, change, check-reset-token) unchanged
# ... (paste your existing confirm_password_reset, change_password, and check_reset_token_validity here)