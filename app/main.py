from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from . import models, database
from .database import engine, SessionLocal  # The dot means "look in this same folder"
from . import models
app = FastAPI()
from routers import incidents
app.include_router(incidents.router)

FirebaseMessaging.onMessage.listen((RemoteMessage message) {
  if (message.notification != null) {
    print("Notification: ${message.notification!.title}");
  }
}
# Create tables in Neon
models.Base.metadata.create_all(bind=database.engine)

@app.post("/signup")
def signup(fullname: str, email: str, password: str, db: Session = Depends(database.get_db)):
    # Check if user exists
    db_user = db.query(models.User).filter(models.User.email == email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Create new user (For now, storing plain text—we will hash it later!)
    new_user = models.User(fullname=fullname, email=email, password=password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "User created successfully", "user_id": new_user.id}
    backend_api/firebase_key.json