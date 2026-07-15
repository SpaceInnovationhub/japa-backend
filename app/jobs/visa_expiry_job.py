import logging
from datetime import date

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import User, VisaInformation, VisaReminderLog
from app.services.notification_service import send_push_to_user

logger = logging.getLogger(__name__)

REMINDER_DAYS = {
    180,
    90,
    60,
    30,
    14,
    7,
    1,
    0,
}


def check_visa_expiries() -> None:
    db: Session = SessionLocal()

    try:
        today = date.today()

        visas = (
            db.query(VisaInformation)
            .join(User, User.id == VisaInformation.user_id)
            .filter(VisaInformation.expiry_date.isnot(None))
            .all()
        )

        for visa in visas:
            try:
                _process_visa(db, visa, today)
            except Exception:
                logger.exception(
                    "Failed processing visa reminder for visa_id=%s",
                    visa.id,
                )

    finally:
        db.close()


def _process_visa(
    db: Session,
    visa: VisaInformation,
    today: date,
) -> None:
    days_remaining = (visa.expiry_date - today).days

    if days_remaining in REMINDER_DAYS:
        reminder_type = _reminder_type(days_remaining)

        if _already_sent(
            db=db,
            visa_id=visa.id,
            reminder_type=reminder_type,
            reminder_date=today,
        ):
            return

        _send_standard_reminder(
            db=db,
            visa=visa,
            days_remaining=days_remaining,
            reminder_type=reminder_type,
            reminder_date=today,
        )

        return

    if days_remaining < 0:
        _send_expired_reminder_if_due(
            db=db,
            visa=visa,
            days_overstayed=abs(days_remaining),
            reminder_date=today,
        )


def _send_standard_reminder(
    db: Session,
    visa: VisaInformation,
    days_remaining: int,
    reminder_type: str,
    reminder_date: date,
) -> None:
    user = db.query(User).filter(User.id == visa.user_id).first()

    if user is None:
        return

    if not user.fcm_token:
        logger.info(
            "Skipping visa reminder because user %s has no FCM token",
            user.id,
        )
        return

    if days_remaining == 0:
        title = "Visa Expires Today"
        body = (
            f"Your {visa.visa_type} expires today. "
            "Please take immediate action."
        )
    elif days_remaining == 1:
        title = "Visa Expiry Reminder"
        body = (
            f"Your {visa.visa_type} expires tomorrow. "
            "Please review your immigration status immediately."
        )
    else:
        title = "Visa Expiry Reminder"
        body = (
            f"Your {visa.visa_type} expires in "
            f"{days_remaining} days."
        )

    response = send_push_to_user(
        fcm_token=user.fcm_token,
        title=title,
        body=body,
        data={
            "type": "visa_expiry",
            "visa_id": str(visa.id),
            "days_remaining": str(days_remaining),
        },
    )

    if response is None:
        logger.warning(
            "Firebase did not confirm visa reminder for user_id=%s",
            user.id,
        )
        return

    _save_reminder_log(
        db=db,
        visa=visa,
        reminder_type=reminder_type,
        reminder_date=reminder_date,
    )


def _send_expired_reminder_if_due(
    db: Session,
    visa: VisaInformation,
    days_overstayed: int,
    reminder_date: date,
) -> None:
    # Do not send an expired notification every day.
    # Send on selected overstay milestones only.
    overstay_milestones = {
        1,
        3,
        7,
        14,
        30,
        60,
        90,
    }

    if days_overstayed not in overstay_milestones:
        return

    reminder_type = f"expired_{days_overstayed}_days"

    if _already_sent(
        db=db,
        visa_id=visa.id,
        reminder_type=reminder_type,
        reminder_date=reminder_date,
    ):
        return

    user = db.query(User).filter(User.id == visa.user_id).first()

    if user is None or not user.fcm_token:
        return

    response = send_push_to_user(
        fcm_token=user.fcm_token,
        title="Visa Expired",
        body=(
            f"Your {visa.visa_type} expired "
            f"{days_overstayed} day"
            f"{'' if days_overstayed == 1 else 's'} ago. "
            "Please contact the relevant immigration authority "
            "or seek qualified legal guidance."
        ),
        data={
            "type": "visa_expired",
            "visa_id": str(visa.id),
            "days_overstayed": str(days_overstayed),
        },
    )

    if response is None:
        return

    _save_reminder_log(
        db=db,
        visa=visa,
        reminder_type=reminder_type,
        reminder_date=reminder_date,
    )


def _already_sent(
    db: Session,
    visa_id: int,
    reminder_type: str,
    reminder_date: date,
) -> bool:
    existing = (
        db.query(VisaReminderLog)
        .filter(
            VisaReminderLog.visa_id == visa_id,
            VisaReminderLog.reminder_type == reminder_type,
            VisaReminderLog.reminder_date == reminder_date,
        )
        .first()
    )

    return existing is not None


def _save_reminder_log(
    db: Session,
    visa: VisaInformation,
    reminder_type: str,
    reminder_date: date,
) -> None:
    log = VisaReminderLog(
        visa_id=visa.id,
        user_id=visa.user_id,
        reminder_type=reminder_type,
        reminder_date=reminder_date,
    )

    db.add(log)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()


def _reminder_type(days_remaining: int) -> str:
    if days_remaining == 0:
        return "expires_today"

    if days_remaining == 1:
        return "1_day"

    return f"{days_remaining}_days"