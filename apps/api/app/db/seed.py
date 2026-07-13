"""
Seed database with initial admin accounts.
Run this script after database is created.
"""
import os
import sys

from dotenv import load_dotenv

# Load .env from project root
load_dotenv(os.path.join(os.path.dirname(__file__), "../../../../.env"))

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.db.database import SessionLocal, engine, Base
from app.models.user import User, UserRole, UserTier
from app.auth.password import hash_password


# Read admin credentials from environment
ADMIN_ACCOUNTS = [
    {
        "email": os.getenv("ADMIN_EMAIL"),
        "password": os.getenv("ADMIN_PASSWORD"),
        "display_name": os.getenv("ADMIN_DISPLAY_NAME"),
    },
]


def seed_admins():
    """Create admin accounts if they don't exist."""
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        for admin_data in ADMIN_ACCOUNTS:
            existing = db.query(User).filter(User.email == admin_data["email"]).first()
            if existing:
                print(f"Admin {admin_data['email']} already exists, skipping...")
                continue

            admin = User(
                email=admin_data["email"],
                password_hash=hash_password(admin_data["password"]),
                display_name=admin_data["display_name"],
                role=UserRole.ADMIN,
                tier=UserTier.PREMIUM,
            )
            db.add(admin)
            print(f"Created admin: {admin_data['email']}")

        db.commit()
        print("Admin seeding complete!")

    except Exception as e:
        db.rollback()
        print(f"Error seeding admins: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_admins()
