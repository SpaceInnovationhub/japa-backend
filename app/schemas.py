from pydantic import BaseModel, EmailStr
from typing import Optional

class UserCreate(BaseModel):
    fullname: str
    passport_number: str
    nin: str
    email: EmailStr
    phone: str
    password: str
    country: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    fullname: str
    email: EmailStr
    phone: str
    country: str

    class Config:
        from_attributes = True

class TicketCreate(BaseModel):
    subject: str
    description: str

class TicketResponse(BaseModel):
    id: int
    subject: str
    description: str
    status: str

    class Config:
        from_attributes = True

class AnnouncementBase(BaseModel):
    title: str
    content: str
    category: str = "Info"

class AnnouncementCreate(AnnouncementBase):
    pass

class Announcement(AnnouncementBase):
    id: int
    created_by: int
    created_at: datetime

    class Config:
        orm_mode = True

# Similar for Ticket and Incident schemas

class EvacuationRequestCreate(BaseModel):
    country: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

    class TicketCreate(BaseModel):
        embassy_country: str
        subject: str
        description: str

    class TicketStatusUpdate(BaseModel):
        status: str


        class AnnouncementCreate(BaseModel):
            embassy_country: str
            title: str
            content: str
            category: str   # Info, Warning, Critical
