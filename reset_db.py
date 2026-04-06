import sys
import os

# Add the current directory to the path so it finds the 'app' folder
sys.path.append(os.getcwd())

from app.database import engine
from app.models.models import Base

def reset_production_db():
    print("🚀 Connecting to Render PostgreSQL...")
    try:
        # This clears out the old version with the missing fcm_token
        print("🗑️  Dropping old tables...")
        Base.metadata.drop_all(bind=engine)
        
        # This builds the fresh version matching your current code
        print("🏗️  Creating fresh tables (including fcm_token)...")
        Base.metadata.create_all(bind=engine)
        
        print("✅ Database Reset Complete! Your JAPA link is ready.")
    except Exception as e:
        print(f"❌ Connection Failed: {e}")

if __name__ == "__main__":
    reset_production_db()