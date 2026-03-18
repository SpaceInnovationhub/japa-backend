from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from app import models, database
from app.database import engine, SessionLocal
from app.routers import incidents, auth, users, kyc, announcements, tickets

app = FastAPI()

# Include your routers
app.include_router(incidents.router)
app.include_router(announcements.router)
app.include_router(tickets.router)
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(kyc.router)

# Create tables
models.Base.metadata.create_all(bind=database.engine)

@app.post("/signup")
def signup(fullname: str, email: str, password: str, db: Session = Depends(database.get_db)):
    db_user = db.query(models.User).filter(models.User.email == email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    new_user = models.User(fullname=fullname, email=email, password=password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "User created successfully", "user_id": new_user.id}
    db.refresh(new_user)
    return {"message": "User created successfully", "user_id": new_user.id}