from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
import os
import sys

# Add current directory to Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Corrected imports
from app.models import models          # ← This was the main fix
from app.database import engine, get_db

# Import routers
from app.routers.auth import router as auth_router
from app.routers.users import router as users_router
from app.routers.kyc import router as kyc_router
from app.routers.announcements import router as announcements_router
from app.routers.tickets import router as tickets_router
from app.routers.incidents import router as incidents_router

app = FastAPI(title="JAPA Backend API", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(users_router, prefix="/users", tags=["users"])
app.include_router(kyc_router, prefix="/kyc", tags=["kyc"])
app.include_router(announcements_router, prefix="/announcements", tags=["announcements"])
app.include_router(tickets_router, prefix="/tickets", tags=["support"])
app.include_router(incidents_router, prefix="/incidents", tags=["incidents"])

# Create tables
models.Base.metadata.create_all(bind=engine)

# Signup Model
class SignupRequest(BaseModel):
    fullname: str
    email: str
    password: str
    passport_number: str | None = None
    nin: str | None = None
    phone: str | None = None
    country: str | None = None


@app.get("/")
def read_root():
    return {"message": "✅ JAPA Backend API is running"}

@app.post("/signup")
def signup(request: SignupRequest, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == request.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    new_user = models.User(
        fullname=request.fullname,
        email=request.email,
        password=request.password,
        passport_number=request.passport_number,
        nin=request.nin,
        phone=request.phone,
        country=request.country
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {
        "message": "User created successfully",
        "user_id": new_user.id
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)