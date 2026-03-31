from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class SignupRequest(BaseModel):
    fullname: str
    email: str
    password: str

class LoginRequest(BaseModel):
    email: str
    password: str

# Simple in-memory storage
users_db = {}
tokens_db = {}

@app.get("/")
def root():
    return {"message": "JAPA API Running!"}

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.post("/signup")
def signup(request: SignupRequest):
    if request.email in users_db:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user_id = len(users_db) + 1
    users_db[request.email] = {
        "id": user_id,
        "fullname": request.fullname,
        "email": request.email,
        "password": request.password
    }
    
    return {
        "message": "User created successfully",
        "user": {
            "id": user_id,
            "fullname": request.fullname,
            "email": request.email
        }
    }

@app.post("/auth/login")
def login(request: LoginRequest):
    if request.email not in users_db:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if users_db[request.email]["password"] != request.password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = f"token_{users_db[request.email]['id']}"
    tokens_db[token] = users_db[request.email]["email"]
    
    return {
        "message": "Login successful",
        "access_token": token,
        "token_type": "bearer",
        "user": users_db[request.email]
    }

@app.get("/users/profile")
def get_profile(authorization: str = Header(None)):
    # Extract token from Authorization header
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    token = authorization.replace("Bearer ", "")
    
    if token not in tokens_db:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    email = tokens_db[token]
    user = users_db.get(email)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=False)