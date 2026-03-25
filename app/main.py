from pydantic import BaseModel

# Add this class right after your imports
class SignupRequest(BaseModel):
    fullname: str
    email: str
    password: str
    passport_number: str = None
    nin: str = None
    phone: str = None
    country: str = None

# Then replace your existing signup function with this
@app.post("/signup")
async def signup(request: SignupRequest, db: Session = Depends(database.get_db)):
    # Check if user exists
    db_user = db.query(models.User).filter(models.User.email == request.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Create new user with all fields
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