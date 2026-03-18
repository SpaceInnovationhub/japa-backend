from sqlalchemy import Column, Integer, String, Date, ForeignKey, Text
from sqlalchemy.orm import relationship
from .database import Base
from sqlalchemy import DateTime
from datetime import datetime

class Announcement(Base):
    __tablename__ = "announcements"
    id = Column(Integer, primary_key=True, index=True)
    embassy_country = Column(String(50))
    title = Column(String(200))
    content = Column(Text)
    category = Column(String)   # Info, Warning, Critical
    created_at = Column(DateTime, default=datetime.utcnow)

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    fullname = Column(String(100))
    passport_number = Column(String(50), unique=True, index=True)
    nin = Column(String(50), unique=True, index=True)
    email = Column(String(100), unique=True, index=True)
    phone = Column(String(20))
    password = Column(String(255))
    country = Column(String(50))
    fcm_token = Column(String, nullable=True)

    # Relationships
    tickets = relationship("SupportTicket", back_populates="user")
    evacuation_requests = relationship("EvacuationRequest", back_populates="user")

class SupportTicket(Base):
    __tablename__ = "support_tickets"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    subject = Column(String(200))
    description = Column(Text)
    status = Column(String(30), default="Open")

    # Relationship
    user = relationship("User", back_populates="tickets")

class EvacuationRequest(Base):
    __tablename__ = "evacuation_requests"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    country = Column(String(50))
    status = Column(String(30), default="Pending")

    # Relationship
    user = relationship("User", back_populates="evacuation_requests")

# ADD THIS NEW MODEL
class IncidentReport(Base):
    __tablename__ = "incident_reports"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    embassy_country = Column(String(100))
    description = Column(Text)
    media_path = Column(String(500))
    status = Column(String(50), default="Pending")  # Pending, Reviewed, Resolved
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship
    user = relationship("User", backref="incident_reports")