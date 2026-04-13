from app.database import SessionLocal
from app.models import User
from app.auth import hash_password
import sys

def create_initial_admins():
    db = SessionLocal()
    try:
        # Check if super admin already exists
        existing_super = db.query(User).filter(User.email == "admin@japa.ng").first()
        if existing_super:
            print("✅ Super Admin already exists")
        else:
            super_admin = User(
                fullname="Nigeria HQ Super Admin",
                email="admin@japa.ng",
                password=hash_password("JapaAdmin2025!"),   # Change this password after first login
                country="Nigeria",
                role="super_admin",
                is_active=True,
                phone="+2349012345678"
            )
            db.add(super_admin)
            print("✅ Created Super Admin (Nigeria HQ)")

        # Embassy Admins
        embassies = [
            {
                "fullname": "United States Embassy Admin",
                "email": "admin@japa.us",
                "country": "United States of America",
                "password": "JapaUS2025!"
            },
            {
                "fullname": "United Kingdom Embassy Admin",
                "email": "admin@japa.uk",
                "country": "United Kingdom",
                "password": "JapaUK2025!"
            },
            {
                "fullname": "France Embassy Admin",
                "email": "admin@japa.fr",
                "country": "France",
                "password": "JapaFR2025!"
            },
            {
                "fullname": "Canada Embassy Admin",
                "email": "admin@japa.ca",
                "country": "Canada",
                "password": "JapaCA2025!"
            },
        ]

        for embassy in embassies:
            existing = db.query(User).filter(User.email == embassy["email"]).first()
            if existing:
                print(f"✅ {embassy['country']} Admin already exists")
                continue

            admin = User(
                fullname=embassy["fullname"],
                email=embassy["email"],
                password=hash_password(embassy["password"]),
                country=embassy["country"],
                role="embassy",
                is_active=True,
                phone="+1234567890"   # You can update later
            )
            db.add(admin)
            print(f"✅ Created Admin for {embassy['country']}")

        db.commit()
        print("\n🎉 All initial admin accounts created successfully!")

    except Exception as e:
        db.rollback()
        print(f"❌ Error creating admins: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    create_initial_admins()