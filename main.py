ffrom fastapi import FastAPI, Depends, HTTPException
 from fastapi.middleware.cors import CORSMiddleware
 from pydantic import BaseModel
 from sqlalchemy.orm import Session
 import os

 # Local imports
 from app import models, database
 from app.database import engine
 from app.routers import incidents, auth, users, kyc, announcements, tickets

 # ========== CREATE APP ==========
 app = FastAPI(title="JAPA Backend API", version="1.0.0")

 # ========== CORS MIDDLEWARE - FIXED ==========
 app.add_middleware(
     CORSMiddleware,
     allow_origins=[
         "http://localhost:49239",  # Your current Flutter app port
         "http://localhost:3000",
         "http://localhost:8000",
         "https://japa-backend.onrender.com",
         "*"  # Allow all for testing
     ],
     allow_credentials=True,
     allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],  # Explicitly allow POST
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
         "version": "1.0.0"
     }

 @app.get("/health")
 def health_check():
     return {"status": "healthy"}

 @app.options("/signup")
 async def signup_options():
     """Handle OPTIONS preflight request"""
     return {"message": "OK"}

 # ========== SIGNUP ENDPOINT - FIXED ==========
 @app.post("/signup")
 async def signup(request: SignupRequest, db: Session = Depends(database.get_db)):
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