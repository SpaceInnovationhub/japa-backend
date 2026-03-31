from fastapi import FastAPI, HTTPException
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
    
    users_db[request.email] = {
        "fullname": request.fullname,
        "email": request.email,
        "password": request.password,
        "id": len(users_db) + 1
    }
    
    return {
        "message": "User created successfully",
        "user": {
            "id": users_db[request.email]["id"],
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
    
    return {
        "message": "Login successful",
        "access_token": f"token_{users_db[request.email]['id']}",
        "token_type": "bearer",
        "user": users_db[request.email]
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=False)