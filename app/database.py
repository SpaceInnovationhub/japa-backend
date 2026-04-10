# app/database.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Get database URL from environment
DATABASE_URL = os.getenv("postgresql://japa_user:password12345@localhost:5432/japa_db")

# Configure engine with connection pool settings
engine = create_engine(
    DATABASE_URL,
    pool_size=20,           # Number of permanent connections
    max_overflow=40,        # Extra connections during peak
    pool_timeout=30,        # Seconds to wait for connection
    pool_pre_ping=True,     # Verify connection before using
    pool_recycle=3600       # Recycle connections after 1 hour
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()