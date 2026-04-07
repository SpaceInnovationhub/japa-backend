import os
import sys
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session

# Absolute path setup
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database import engine, get_db
from app import models

# Import routers
from app.routers.auth import router as auth_router
from app.routers.users import router as users_router
from app.routers.kyc import router as kyc_router
from app.routers.announcements import router as announcements_router
from app.routers.tickets import router as tickets_router
from app.routers.incidents import router as incidents_router

app = FastAPI(title="JAPA Backend API", version="1.0.0")

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True, # Changed to True for better cross-origin support
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(users_router, prefix="/users", tags=["users"])
app.include_router(kyc_router, prefix="/kyc", tags=["kyc"])
app.include_router(announcements_router, prefix="/announcements", tags=["announcements"])
app.include_router(tickets_router, prefix="/tickets", tags=["support"])
app.include_router(incidents_router, prefix="/incidents", tags=["incidents"])

# Create tables
models.Base.metadata.create_all(bind=engine)

# Pydantic Model for Signup
class SignupRequest(BaseModel):
    fullname: str
    email: str
    password: str
    passport_number: str | None = None
    nin: str | None = None
    phone: str | None = None
    country: str | None = None
    fcm_token: str | None = None

@app.post("/signup")
def signup(request: SignupRequest, db: Session = Depends(get_db)):
    # 1. Check for duplicate Email, NIN, or Passport
    existing_user = db.query(models.User).filter(
        (models.User.email == request.email) | 
        (models.User.passport_number == request.passport_number) |
        (models.User.nin == request.nin)
    ).first()

    if existing_user:
        # Check which one specifically is the duplicate for a better error message
        if existing_user.email == request.email:
            detail = "Email already registered"
        elif existing_user.passport_number == request.passport_number:
            detail = "Passport number already registered"
        else:
            detail = "NIN already registered"
            
        raise HTTPException(status_code=400, detail=detail)

    # 2. Proceed with registration if no duplicates found

    # 2. Map data to SQLAlchemy Model
    new_user = models.User(
        fullname=request.fullname,
        email=request.email,
        password=request.password,   # Note: Implement hashing later
        passport_number=request.passport_number,
        nin=request.nin,
        phone=request.phone,
        country=request.country,
        fcm_token=request.fcm_token  # <--- CRITICAL FIX: Mapping the token
    )

    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return {
            "message": "User registered successfully",
            "user_id": new_user.id
        }
    except Exception as e:
        db.rollback()
        print(f"❌ DATABASE ERROR: {e}")
        raise HTTPException(status_code=500, detail="Database insertion failed")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)