from datetime import datetime
from pydantic import BaseModel, EmailStr
from typing import Optional, List

# --- USER SCHEMAS ---
class UserCreate(BaseModel):
    fullname: str
    passport_number: str
    nin: str
    email: EmailStr
    phone: str
    password: str
    country: str
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
    media_path: Optional[str]
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

class Announcement(AnnouncementBase): # Changed from AnnouncementResponse to Announcement
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

# --- AUTH SCHEMAS ---
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str