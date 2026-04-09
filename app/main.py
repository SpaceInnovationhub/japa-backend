import os
import sys
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Absolute path setup
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database import engine, get_db
from app import models
from app.auth import hash_password 

# Import routers
from app.routers.auth import router as auth_router
from app.routers.users import router as users_router
from app.routers.kyc import router as kyc_router
from app.routers.announcements import router as announcements_router
from app.routers.tickets import router as tickets_router
from app.routers.incidents import router as incidents_router
from app.routers import password_reset

# Create FastAPI app
app = FastAPI(
    title="JAPA Backend API", 
    version="1.0.0",
    description="JAPA Application Backend API",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Configuration - Use environment variables for production
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS if ALLOWED_ORIGINS != ["*"] else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers with proper prefixes
app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
app.include_router(users_router, prefix="/users", tags=["Users"])
app.include_router(kyc_router, prefix="/kyc", tags=["KYC Verification"])
app.include_router(announcements_router, prefix="/announcements", tags=["Announcements"])
app.include_router(tickets_router, prefix="/tickets", tags=["Support Tickets"])
app.include_router(incidents_router, prefix="/incidents", tags=["Incidents"])
app.include_router(password_reset.router, prefix="/password-reset", tags=["Password Management"])

# Create tables (with error handling)
try:
    models.Base.metadata.create_all(bind=engine)
    print("✅ Database tables created/verified successfully")
except Exception as e:
    print(f"❌ Error creating database tables: {e}")

# Pydantic Model for Signup
class SignupRequest(BaseModel):
    fullname: str
    email: EmailStr
    password: str
    passport_number: str | None = None
    nin: str | None = None
    phone: str | None = None
    country: str | None = None
    fcm_token: str | None = None

# --- HEALTH CHECK / ROOT ROUTE ---
@app.get("/")
def read_root():
    return {
        "status": "online",
        "project": "JAPA Backend API",
        "version": "1.0.0",
        "message": "Welcome to the JAPA API. Documentation is available at /docs",
        "endpoints": {
            "auth": "/auth",
            "users": "/users",
            "kyc": "/kyc",
            "password_reset": "/password-reset",
            "docs": "/docs"
        }
    }

@app.get("/health")
def health_check():
    """Health check endpoint for monitoring"""
    return {
        "status": "healthy",
        "environment": os.getenv("ENVIRONMENT", "development"),
        "database": "connected"  # You could add actual DB check here
    }

@app.post("/signup")
def signup(request: SignupRequest, db: Session = Depends(get_db)):
    # 1. Check for duplicate Email, NIN, or Passport
    existing_user = db.query(models.User).filter(
        (models.User.email == request.email) | 
        (models.User.passport_number == request.passport_number) |
        (models.User.nin == request.nin)
    ).first()

    if existing_user:
        if existing_user.email == request.email:
            detail = "Email already registered"
        elif existing_user.passport_number == request.passport_number:
            detail = "Passport number already registered"
        else:
            detail = "NIN already registered"
            
        raise HTTPException(status_code=400, detail=detail)

    # 2. Validate password strength
    if len(request.password) < 8:
        raise HTTPException(
            status_code=400, 
            detail="Password must be at least 8 characters long"
        )

    # 3. Hash the password with error handling
    try:
        hashed_password = hash_password(request.password)
        
        # Validate the hash was created correctly
        if not hashed_password or len(hashed_password) < 50:
            raise HTTPException(
                status_code=500,
                detail="Error processing password. Please try again."
            )
            
    except Exception as e:
        print(f"❌ Password hashing error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error creating account. Please try again."
        )

    # 4. Create new user
    new_user = models.User(
        fullname=request.fullname,
        email=request.email,
        password=hashed_password,
        passport_number=request.passport_number,
        nin=request.nin,
        phone=request.phone,
        country=request.country,
        fcm_token=request.fcm_token
    )

    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        # Don't return sensitive data
        return {
            "message": "User registered successfully",
            "user_id": new_user.id,
            "email": new_user.email,
            "fullname": new_user.fullname
        }
    except Exception as e:
        db.rollback()
        print(f"❌ DATABASE ERROR: {e}")
        raise HTTPException(status_code=500, detail="Database insertion failed")

# Optional: Add a shutdown event handler
@app.on_event("shutdown")
def shutdown_event():
    """Cleanup on application shutdown"""
    print("🛑 JAPA API is shutting down...")

# Optional: Add startup event
@app.on_event("startup")
def startup_event():
    """Initialize on application startup"""
    print("🚀 JAPA API is starting up...")
    print(f"📊 Environment: {os.getenv('ENVIRONMENT', 'development')}")
    print(f"🔗 CORS Origins: {ALLOWED_ORIGINS}")
    print("✅ All routers registered successfully")

if __name__ == "__main__":
    import uvicorn
    
    # Get port from environment variable or default to 8000
    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0")
    reload = os.environ.get("ENVIRONMENT", "development") == "development"
    
    print(f"🚀 Starting JAPA API on {host}:{port}")
    print(f"🔄 Auto-reload: {reload}")
    print(f"📚 API Documentation: http://{host}:{port}/docs")
    
    uvicorn.run(
        "app.main:app", 
        host=host, 
        port=port, 
        reload=reload,
        log_level="info"
    )