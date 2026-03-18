import firebase_admin
from firebase_admin import credentials, messaging
from sqlalchemy.orm import Session
from app.models import User
import logging

# Initialize Firebase only once
try:
    cred = credentials.Certificate("firebase_key.json")
    firebase_admin.initialize_app(cred)
except ValueError:
    # Prevent re-initialization error
    pass


# 🔹 Send notification to a single device
def send_push_to_user(fcm_token: str, title: str, body: str, data: dict = None):
    try:
        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body
            ),
            token=fcm_token,
            data=data or {}
        )

        response = messaging.send(message)
        return response

    except Exception as e:
        logging.error(f"Push error (single user): {e}")
        return None


# 🔹 Send notification to all users in a country
def send_push_to_country(db: Session, country: str, title: str, body: str):

    users = db.query(User).filter(
        User.country == country,
        User.fcm_token != None
    ).all()

    tokens = [u.fcm_token for u in users if u.fcm_token]

    if not tokens:
        return {"message": "No devices found"}

    # Firebase allows max 500 tokens per batch
    batch_size = 500
    responses = []

    for i in range(0, len(tokens), batch_size):

        batch = tokens[i:i + batch_size]

        message = messaging.MulticastMessage(
            notification=messaging.Notification(
                title=title,
                body=body
            ),
            tokens=batch
        )

        try:
            response = messaging.send_multicast(message)
            responses.append(response)
        except Exception as e:
            logging.error(f"Push error (batch): {e}")

    return {"message": "Notifications sent", "batches": len(responses)}


# 🔹 Send emergency alert (high priority)
def send_emergency_alert(db: Session, country: str, message_text: str):

    title = "🚨 Emergency Alert"
    body = message_text

    users = db.query(User).filter(
        User.country == country,
        User.fcm_token != None
    ).all()

    tokens = [u.fcm_token for u in users if u.fcm_token]

    if not tokens:
        return {"message": "No users to notify"}

    multicast_message = messaging.MulticastMessage(
        notification=messaging.Notification(
            title=title,
            body=body
        ),
        android=messaging.AndroidConfig(priority="high"),
        apns=messaging.APNSConfig(
            headers={"apns-priority": "10"}
        ),
        tokens=tokens
    )

    try:
        response = messaging.send_multicast(multicast_message)
        return {
            "success": response.success_count,
            "failure": response.failure_count
        }

    except Exception as e:
        logging.error(f"Emergency push error: {e}")
        return None
