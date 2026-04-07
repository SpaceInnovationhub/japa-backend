from datetime import datetime
from pydantic import BaseModel, EmailStr
from typing import Optional, List

# --- AUTH & TOKEN SCHEMAS ---
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    # Added these so your Flutter app can store user info locally upon login
    role: str
    user_id: int

class TokenData(BaseModel):
    user_id: Optional[str] = None

# --- USER SCHEMAS ---
class UserCreate(BaseModel):
    fullname: str
    email: EmailStr
    password: str
    passport_number: str
    nin: str
    phone: str
    country: str
    # CRITICAL FIX: Added fcm_token here so register() doesn't throw a 422 error
    fcm_token: Optional[str] = None 
    role: Optional[str] = "user"

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    fullname: str
    email: EmailStr
    phone: str
    country: str
    role: str
    is_active: bool
    # Added this to match your models.py
    created_at: Optional[datetime] = None 

    class Config:
        from_attributes = True

# --- INCIDENT REPORT SCHEMAS ---
class IncidentReportCreate(BaseModel):
    embassy_country: str
    description: str
    media_path: Optional[str] = None
    location_coords: Optional[str] = None

class IncidentReportResponse(BaseModel):
    id: int
    user_id: int
    embassy_country: str
    description: str
    media_path: Optional[str] = None
    status: str
    created_at: datetime

    class Config:
        from_attributes = True

# --- TICKET SCHEMAS ---
class TicketCreate(BaseModel):
    embassy_country: str
    subject: str
    description: str

class TicketStatusUpdate(BaseModel):
    status: str

class TicketResponse(BaseModel):
    id: int
    user_id: int
    embassy_country: str
    subject: str
    description: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True

# --- ANNOUNCEMENT SCHEMAS ---
class AnnouncementBase(BaseModel):
    embassy_country: str
    title: str
    content: str
    category: str = "Info"

class AnnouncementCreate(AnnouncementBase):
    pass

class AnnouncementResponse(AnnouncementBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True