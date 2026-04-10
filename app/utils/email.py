# app/utils/email.py
import os
import logging

logger = logging.getLogger(__name__)

# Email configuration (use environment variables)
SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
FROM_EMAIL = os.getenv("FROM_EMAIL", SMTP_USER)
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

def send_password_reset_email(to_email: str, reset_token: str, user_name: str) -> bool:
    """Send password reset email to user"""
    # For development, just log the reset link
    reset_link = f"{FRONTEND_URL}/reset-password?token={reset_token}"
    print(f"\n{'='*60}")
    print(f"🔐 PASSWORD RESET LINK (Development Mode)")
    print(f"User: {user_name} ({to_email})")
    print(f"Reset link: {reset_link}")
    print(f"{'='*60}\n")
    return True

def send_password_changed_notification(to_email: str, user_name: str) -> bool:
    """Send notification email when password is changed"""
    print(f"\n📧 Password changed notification for {user_name} ({to_email})\n")
    return True