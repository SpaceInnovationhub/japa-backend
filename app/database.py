import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

load_dotenv()

# 1. Fetch the URL from environment variables
DATABASE_URL = os.getenv("DATABASE_URL")

# 2. Fix the "postgres://" vs "postgresql://" issue for Render/Railway
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# 3. Fallback to local if no environment variable is found
if not DATABASE_URL:
    DATABASE_URL = "postgresql://japa_user:password12345@localhost:5432/japa_db"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()