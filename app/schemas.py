from datetime import date, datetime
from pydantic import BaseModel, ConfigDict, EmailStr
from typing import Optional, List

# --- AUTH & TOKEN SCHEMAS ---
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
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

# --- EVACUATION REQUEST SCHEMAS ---
class EvacuationCreate(BaseModel):
    country: str
    location: str
    description: str

class EvacuationResponse(BaseModel):   # Recommended - add this too
    id: int
    user_id: int
    country: str
    location: str
    description: str
    status: str = "pending"           # e.g. pending, approved, completed
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

# ====================== PASSWORD RESET SCHEMAS ======================

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str
    confirm_password: str

class PasswordChange(BaseModel):
    current_password: str
    new_password: str
    confirm_password: str

class PasswordResetResponse(BaseModel):
    message: str
    requires_reset: bool = False

# ====================== VISA INFORMATION SCHEMAS ======================
class VisaInformationUpsert(BaseModel):
    country: str
    visa_type: str
    visa_number: Optional[str] = None

    issue_date: Optional[date] = None
    arrival_date: date
    expiry_date: date
    departure_date: Optional[date] = None

    length_of_stay_days: Optional[int] = None
    entry_type: Optional[str] = None

class VisaInformationResponse(VisaInformationUpsert):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime