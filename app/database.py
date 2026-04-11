# app/database.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv
from pathlib import Path

# Get the project root directory (where .env file is)
project_root = Path(__file__).parent.parent
env_path = project_root / ".env"

# Load .env file explicitly
load_dotenv(dotenv_path=env_path)

# Get database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL")

# Debug: Print what we found
print(f"Looking for .env at: {env_path}")
print(f".env file exists: {env_path.exists()}")
print(f"DATABASE_URL: {DATABASE_URL}")

# Check if DATABASE_URL is set
if not DATABASE_URL:
    raise ValueError(
        "DATABASE_URL environment variable is not set. "
        f"Checked path: {env_path}. "
        "Please create a .env file with DATABASE_URL=postgresql://..."
    )

# Configure engine based on database type
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False}
    )
    print("✅ Using SQLite database")
else:
    engine = create_engine(DATABASE_URL)
    print("✅ Using PostgreSQL database")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()