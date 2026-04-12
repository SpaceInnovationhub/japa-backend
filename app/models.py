from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base
from datetime import datetime

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    fullname = Column(String(100), nullable=False)
    passport_number = Column(String(50), unique=True, index=True)
    nin = Column(String(50), unique=True, index=True)
    email = Column(String(100), unique=True, index=True, nullable=False)
    phone = Column(String(20))
    password = Column(String(255), nullable=False)
    country = Column(String(50))
    fcm_token = Column(Text, nullable=True)

    role = Column(String(20), default="user")          # 'user', 'admin', 'embassy'
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # ==================== KYC FIELDS (Newly Added) ====================
    id_document = Column(String(500), nullable=True)       # Path to ID document
    selfie_image = Column(String(500), nullable=True)      # Path to selfie
    kyc_verified = Column(Boolean, default=False)
    kyc_submitted_at = Column(DateTime(timezone=True), nullable=True)
    kyc_verified_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    tickets = relationship("SupportTicket", back_populates="user", cascade="all, delete-orphan")
    evacuation_requests = relationship("EvacuationRequest", back_populates="user", cascade="all, delete-orphan")
    incident_reports = relationship("IncidentReport", back_populates="user", cascade="all, delete-orphan")

    # Optional: Add a method for easier KYC status
    @property
    def kyc_status(self):
        if self.kyc_verified:
            return "Verified"
        elif self.kyc_submitted_at:
            return "Pending Review"
        return "Not Submitted"


class SupportTicket(Base):
    __tablename__ = "support_tickets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    embassy_country = Column(String(50))
    subject = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    status = Column(String(30), default="Open")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="tickets")


class Announcement(Base):
    __tablename__ = "announcements"

    id = Column(Integer, primary_key=True, index=True)
    embassy_country = Column(String(50))
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    category = Column(String(20)) 
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class IncidentReport(Base):
    __tablename__ = "incident_reports"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    embassy_country = Column(String(100))
    description = Column(Text, nullable=False)
    media_path = Column(String(500)) 
    location_coords = Column(String(100)) 
    status = Column(String(50), default="Pending")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", back_populates="incident_reports")


class EvacuationRequest(Base):
    __tablename__ = "evacuation_requests"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    country = Column(String(50), nullable=False)
    status = Column(String(30), default="Pending")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="evacuation_requests")