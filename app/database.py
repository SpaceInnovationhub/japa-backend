import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import logging

logger = logging.getLogger(__name__)

# Get DATABASE_URL from Render environment variables
DATABASE_URL = os.getenv("DATABASE_URL")

# Fix old 'postgres://' prefix (some providers still use it)
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Optimized engine for Neon PostgreSQL (serverless)
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,        # Prevents "SSL connection closed" errors
    pool_recycle=300,          # Recycle every 5 minutes (Neon suspends idle connections)
    pool_size=5,
    max_overflow=10,
    echo=False,                # Change to True only when debugging
    connect_args={
        "sslmode": "require",
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


# Optional helper to test connection (call from main.py)
def test_db_connection():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error(f"Database connection test failed: {e}")
        return False