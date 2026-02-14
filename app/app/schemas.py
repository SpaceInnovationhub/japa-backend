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

class AnnouncementCreate(BaseModel):
    embassy_country: str
    title: str
    content: str

class EvacuationRequestCreate(BaseModel):
    country: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"