from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
import os

# Local imports - adjust paths based on your structure
try:
    from app import models, database
    from app.database import engine, SessionLocal
    from app.routers import incidents, auth, users, kyc, announcements, tickets
except ImportError:
    # Alternative import structure if app is not a package
    import models, database
    from database import engine, SessionLocal
    from routers import incidents, auth, users, kyc, announcements, tickets

# ========== CREATE APP ==========
app = FastAPI(title="JAPA Backend API", version="1.0.0")

# ========== CORS MIDDLEWARE ==========
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ========== INCLUDE ROUTERS ==========
app.include_router(incidents.router)
app.include_router(announcements.router)
app.include_router(tickets.router)
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(kyc.router)

# ========== CREATE TABLES ==========
models.Base.metadata.create_all(bind=database.engine)

# ========== REQUEST MODEL ==========
class SignupRequest(BaseModel):
    fullname: str
    email: str
    password: str
    passport_number: str = None
    nin: str = None
    phone: str = None
    country: str = None

# ========== ROOT ENDPOINTS ==========
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

# ========== SIGNUP ENDPOINT ==========
@app.post("/signup")
def signup(request: SignupRequest, db: Session = Depends(database.get_db)):
    # Check if user exists
    db_user = db.query(models.User).filter(models.User.email == request.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Create new user
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
        "user_id": new_user.id,
        "user": {
            "id": new_user.id,
            "fullname": new_user.fullname,
            "email": new_user.email
        }
    }

# ========== RUN SERVER ==========
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)