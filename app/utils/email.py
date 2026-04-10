import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Email configuration from environment variables
SMTP_HOST: str = os.getenv("SMTP_HOST", "").strip()
SMTP_PORT_STR: str = os.getenv("SMTP_PORT", "587").strip()
SMTP_USER: str = os.getenv("SMTP_USER", "").strip()
SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "").strip()
FROM_EMAIL: str = os.getenv("FROM_EMAIL", "").strip() or SMTP_USER or "noreply@yourapp.com"
FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:3000").strip()

# Safely convert SMTP_PORT to int with fallback
try:
    SMTP_PORT: int = int(SMTP_PORT_STR)
except ValueError:
    logger.warning(f"Invalid SMTP_PORT value '{SMTP_PORT_STR}' in environment variables. Using default 587.")
    SMTP_PORT: int = 587

# Check if email sending is properly configured
EMAIL_CONFIGURED = bool(SMTP_HOST and SMTP_USER and SMTP_PASSWORD)

def send_password_reset_email(
    to_email: str, 
    reset_token: str, 
    user_name: str = "User"
) -> bool:
    """Send password reset email. Returns True on success or graceful fallback."""
    
    if not EMAIL_CONFIGURED:
        reset_link = f"{FRONTEND_URL}/reset-password?token={reset_token}"
        
        logger.warning(f"Email not fully configured. Would send reset email to {to_email}")
        
        print("\n" + "="*70)
        print("🔐 PASSWORD RESET LINK (Email sending disabled)")
        print(f"User      : {user_name} ({to_email})")
        print(f"Reset Link: {reset_link}")
        print("This link expires in 24 hours.")
        print("="*70 + "\n")
        
        return True

    try:
        import smtplib
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText

        reset_link = f"{FRONTEND_URL}/reset-password?token={reset_token}"
        subject = "Password Reset Request - JAPA App"

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .button {{
                    display: inline-block;
                    padding: 14px 28px;
                    background-color: #4CAF50;
                    color: white;
                    text-decoration: none;
                    border-radius: 5px;
                    font-weight: bold;
                    margin: 20px 0;
                }}
                .footer {{ margin-top: 40px; font-size: 12px; color: #666; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h2>Password Reset Request</h2>
                <p>Hello {user_name},</p>
                <p>We received a request to reset your password for your JAPA account.</p>
                <p>Click the button below to set a new password:</p>
                <a href="{reset_link}" class="button">Reset My Password</a>
                <p>Or copy this link:</p>
                <p><strong>{reset_link}</strong></p>
                <p><small>This link will expire in 24 hours for security reasons.</small></p>
                <p>If you didn't request this, please ignore this email.</p>
                <div class="footer">
                    <p>Best regards,<br>The JAPA Team</p>
                </div>
            </div>
        </body>
        </html>
        """

        text_content = f"""
        Password Reset Request - JAPA App

        Hello {user_name},

        We received a request to reset your password.
        Click the link below to create a new password:

        {reset_link}

        This link will expire in 24 hours.

        If you didn't request this, please ignore this email.

        Best regards,
        The JAPA Team
        """

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = FROM_EMAIL
        msg["To"] = to_email

        msg.attach(MIMEText(text_content, "plain"))
        msg.attach(MIMEText(html_content, "html"))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)

        logger.info(f"Password reset email successfully sent to {to_email}")
        return True

    except Exception as e:
        logger.error(f"Failed to send password reset email to {to_email}: {str(e)}", exc_info=True)
        return False


def send_password_changed_notification(
    to_email: str, 
    user_name: str = "User"
) -> bool:
    """Send notification after successful password change."""
    
    if not EMAIL_CONFIGURED:
        logger.info(f"Password changed notification would be sent to {to_email} ({user_name})")
        return True

    try:
        import smtplib
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText

        subject = "Your Password Has Been Changed - JAPA App"

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .footer {{ margin-top: 40px; font-size: 12px; color: #666; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h2>Password Changed Successfully</h2>
                <p>Hello {user_name},</p>
                <p>Your JAPA account password has been successfully updated.</p>
                <p><strong>If you did not make this change, please contact support immediately.</strong></p>
                <div class="footer">
                    <p>Best regards,<br>The JAPA Team</p>
                </div>
            </div>
        </body>
        </html>
        """

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = FROM_EMAIL
        msg["To"] = to_email
        msg.attach(MIMEText(html_content, "html"))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)

        logger.info(f"Password changed notification sent to {to_email}")
        return True

    except Exception as e:
        logger.error(f"Failed to send password changed notification to {to_email}: {str(e)}", exc_info=True)
        return False