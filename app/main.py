from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

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

@app.get("/")
def root():
    return {"message": "JAPA API Running!"}

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.post("/signup")
def signup(request: SignupRequest):
    return {
        "message": "User created successfully",
        "user": {
            "id": 1,
            "fullname": request.fullname,
            "email": request.email
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000)