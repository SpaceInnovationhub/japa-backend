import sys
import os

# Add current directory to path so it sees the 'app' folder
sys.path.append(os.getcwd())

try:
    from app.database import engine
    from app.models import Base  # Since you have app/models.py
    print("✅ Imports successful!")
except ImportError as e:
    print(f"❌ Import Error: {e}")
    print("Check if you are running this from the 'backend_api' folder.")
    sys.exit(1)

def reset_production_db():
    print("🚀 Connecting to Render PostgreSQL...")
    try:
        print("🗑️  Dropping old tables...")
        Base.metadata.drop_all(bind=engine)
        
        print("🏗️  Creating fresh tables (including fcm_token)...")
        Base.metadata.create_all(bind=engine)
        
        print("✅ Database Reset Complete! Your JAPA link is ready.")
    except Exception as e:
        print(f"❌ Connection Failed: {e}")

if __name__ == "__main__":
    reset_production_db()