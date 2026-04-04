from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
import os

# Imports
import models
from database import engine, get_db
from routers import auth, users, kyc, announcements, tickets, incidents

app = FastAPI(title="JAPA Backend API", version="1.0.0")

# CORS Middleware - MUST be right after creating the app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(kyc.router, prefix="/kyc", tags=["kyc"])
app.include_router(announcements.router, prefix="/announcements", tags=["announcements"])
app.include_router(tickets.router, prefix="/tickets", tags=["support"])
app.include_router(incidents.router, prefix="/incidents", tags=["incidents"])

# Create tables on startup (development only)
models.Base.metadata.create_all(bind=engine)

# Request model for signup
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
    return {"message": "JAPA Backend API is running ✅"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.post("/signup")
def signup(request: SignupRequest, db: Session = Depends(get_db)):
    # Check if email already exists
    db_user = db.query(models.User).filter(models.User.email == request.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Create new user (TODO: Hash the password!)
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


# For running locally
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)