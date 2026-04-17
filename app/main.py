import os
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from sqlalchemy import text
from sqlalchemy.orm import Session

# Import your modules
import os
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel, EmailStr

# Import local modules
from app.database import engine, get_db, test_db_connection
from app import models
from app.auth import hash_password

# Import routers
from app.routers.auth import router as auth_router
from app.routers.users import router as users_router
from app.routers.kyc import router as kyc_router
from app.routers.announcements import router as announcements_router
from app.routers.tickets import router as tickets_router
from app.routers.incidents import router as incidents_router
from app.routers.password_reset import router as password_reset_router

# Create FastAPI app
app = FastAPI(
    title="JAPA Backend API",
    version="1.0.0",
    description="JAPA Application Backend API",
    docs_url="/docs",
    redoc_url="/redoc"
)

# ====================== CORRECTED CORS CONFIGURATION ======================
# Ensure your EXACT frontend URL is in this list
allowed_origins = [
    "https://frontend-kegw.onrender.com",  # Your actual frontend
    "https://japa-backend.onrender.com",   # Your backend (for self-calls)
    "http://localhost:3000",               # For local React development
    "http://localhost:5173",               # For local Vite development
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
app.include_router(users_router, prefix="/users", tags=["Users"])
app.include_router(kyc_router, prefix="/kyc", tags=["KYC Verification"])
app.include_router(announcements_router, prefix="/announcements", tags=["Announcements"])
app.include_router(tickets_router, prefix="/tickets", tags=["Support Tickets"])
app.include_router(incidents_router, prefix="/incidents", tags=["Incidents"])
app.include_router(password_reset_router, prefix="/password", tags=["Password Management"])

# ====================== STARTUP EVENT ======================
@app.on_event("startup")
def startup_event():
    print("🚀 JAPA API is starting up...")
    print(f"📊 Environment: {os.getenv('ENVIRONMENT', 'development')}")
    print(f"🔗 CORS Origins: {allowed_origins}")

    # Test database connection
    if test_db_connection():
        print("✅ Successfully connected to Neon PostgreSQL")
    else:
        print("⚠️ Database connection test failed - check DATABASE_URL")

    # Create/verify tables
    try:
        models.Base.metadata.create_all(bind=engine)
        print("✅ Database tables created/verified successfully")
    except Exception as e:
        print(f"❌ Error creating tables: {e}")


@app.on_event("shutdown")
def shutdown_event():
    print("🛑 JAPA API is shutting down...")


# ====================== HEALTH & ROOT ROUTES ======================
@app.get("/")
def read_root():
    return {
        "status": "online",
        "project": "JAPA Backend API",
        "version": "1.0.0",
        "message": "Welcome to the JAPA API. Documentation is available at /docs",
        "environment": os.getenv("ENVIRONMENT", "development")
    }


@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    """Health check with real DB test"""
    try:
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception:
        db_status = "disconnected"

    return {
        "status": "healthy",
        "environment": os.getenv("ENVIRONMENT", "development"),
        "database": db_status
    }


# ====================== SIGNUP ENDPOINT ======================
class SignupRequest(BaseModel):
    fullname: str
    email: EmailStr
    password: str
    passport_number: str | None = None
    nin: str | None = None
    phone: str | None = None
    country: str | None = None
    fcm_token: str | None = None


@app.post("/signup")
def signup(request: SignupRequest, db: Session = Depends(get_db)):
    # Check for duplicates
    existing = db.query(models.User).filter(
        (models.User.email == request.email) |
        (models.User.passport_number == request.passport_number) |
        (models.User.nin == request.nin)
    ).first()

    if existing:
        if existing.email == request.email:
            raise HTTPException(status_code=400, detail="Email already registered")
        elif existing.passport_number == request.passport_number:
            raise HTTPException(status_code=400, detail="Passport number already registered")
        else:
            raise HTTPException(status_code=400, detail="NIN already registered")

    if len(request.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters long")

    try:
        hashed_password = hash_password(request.password)
        if not hashed_password or len(hashed_password) < 50:
            raise HTTPException(status_code=500, detail="Password processing failed")
    except Exception as e:
        print(f"❌ Password hashing error: {e}")
        raise HTTPException(status_code=500, detail="Error creating account")

    new_user = models.User(
        fullname=request.fullname,
        email=request.email,
        password=hashed_password,
        passport_number=request.passport_number,
        nin=request.nin,
        phone=request.phone,
        country=request.country,
        fcm_token=request.fcm_token,
        role="user",
        is_active=True
    )

    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        return {
            "message": "User registered successfully",
            "user_id": new_user.id,
            "email": new_user.email,
            "fullname": new_user.fullname
        }
    except Exception as e:
        db.rollback()
        print(f"❌ Database insertion error: {e}")
        raise HTTPException(status_code=500, detail="Failed to create user. Please try again.")

# ====================== ONE-TIME ADMIN SEEDER ======================
@app.post("/seed-admins")
def seed_admins():
    """Create initial admin accounts - Call this via POST in Postman"""
    try:
        from app.auth import hash_password
        from app.models import User
        
        db = next(get_db()) 

        created = []

        # 1. Super Admin - Nigeria HQ
        if not db.query(User).filter(User.email == "admin@japa.ng").first():
            super_admin = User(
                fullname="Nigeria HQ Super Admin",
                email="admin@japa.ng",
                password=hash_password("JapaAdmin2025!"),
                country="Nigeria",
                role="super_admin",
                is_active=True,
                phone="+2349012345678"
            )
            db.add(super_admin)
            created.append("Super Admin (Nigeria)")

        # 2. Embassy Admins
        embassies = [
            ("United States of America", "admin@japa.us", "JapaUS2025!", "🇺🇸 United States Embassy Admin"),
            ("United Kingdom", "admin@japa.uk", "JapaUK2025!", "🇬🇧 United Kingdom Embassy Admin"),
            ("France", "admin@japa.fr", "JapaFR2025!", "🇫🇷 France Embassy Admin"),
            ("Canada", "admin@japa.ca", "JapaCA2025!", "🇨🇦 Canada Embassy Admin"),
        ]

        for country, email, password, fullname in embassies:
            if not db.query(User).filter(User.email == email).first():
                admin = User(
                    fullname=fullname,
                    email=email,
                    password=hash_password(password),
                    country=country,
                    role="embassy",
                    is_active=True,
                    phone="+1234567890"
                )
                db.add(admin)
                created.append(f"Admin for {country}")

        db.commit()

        return {
            "status": "success",
            "message": "Initial admin accounts created successfully!",
            "created": created,
            "credentials": {
                "super_admin": {"email": "admin@japa.ng", "password": "JapaAdmin2025!"},
                "usa": {"email": "admin@japa.us", "password": "JapaUS2025!"},
                "uk": {"email": "admin@japa.uk", "password": "JapaUK2025!"},
                "france": {"email": "admin@japa.fr", "password": "JapaFR2025!"},
                "canada": {"email": "admin@japa.ca", "password": "JapaCA2025!"}
            }
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}
    
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, log_level="info")