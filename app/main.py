from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware  # Add this import
from sqlalchemy.orm import Session
from app import models, database
from app.database import engine, SessionLocal
from app.routers import incidents, auth, users, kyc, announcements, tickets
import os

app = FastAPI(title="JAPA Backend API", version="1.0.0")

# Add CORS middleware - ADD THIS BLOCK RIGHT AFTER CREATING THE APP
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://japa-mobile.onrender.com",  # Your Flutter mobile app
        "https://japa-backend.onrender.com",  # Your backend itself
        "http://localhost:3000",  # Local React development
        "http://localhost:8000",  # Local backend development
        "http://127.0.0.1:8000",  # Alternative localhost
        "*"  # For development - REMOVE IN PRODUCTION
    ],
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],  # Allows all headers
)

# Include your routers
app.include_router(incidents.router)
app.include_router(announcements.router)
app.include_router(tickets.router)
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(kyc.router)

# Create tables
models.Base.metadata.create_all(bind=database.engine)

@app.get("/")
def read_root():
    return {
        "message": "JAPA Backend API is running!",
        "status": "active",
        "version": "1.0.0",
        "endpoints": [
            "/signup",
            "/auth/login",
            "/users/profile",
            "/kyc/submit",
            "/tickets/create",
            "/announcements",
            "/incidents/report"
        ]
    }

@app.get("/health")
def health_check():
    return {"status": "healthy", "database": "connected"}

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

# Add this at the bottom for Render deployment
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=False)