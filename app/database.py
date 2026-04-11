# app/database.py

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import os
import logging

logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL")

# Fix old postgres:// prefix if present
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,           # Critical: checks if connection is alive before using it
    pool_recycle=300,             # Recycle connections every 5 minutes (Neon suspends fast)
    pool_size=5,
    max_overflow=10,
    echo=False,                   # Set to True only for debugging
    connect_args={
        "sslmode": "require",     # Already in your URL but good to reinforce
    }
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Optional: Test connection on startup
@app.on_event("startup")   # Add this in your main.py if not already present
async def startup_event():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("✅ Successfully connected to Neon PostgreSQL")
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")