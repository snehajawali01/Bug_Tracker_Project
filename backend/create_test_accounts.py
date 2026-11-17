from getpass import getpass

from sqlalchemy import or_, select

from app.db.session import SessionLocal
from app.models import User, UserRole
from app.core.security import hash_password


db = SessionLocal()

try:
    accounts = [
        ("ADMIN", UserRole.ADMIN),
        ("DEVELOPER", UserRole.DEVELOPER),
    ]

    for label, role in accounts:
        print(f"\n--- Create {label} Account ---")

        full_name = input("Full name: ").strip()
        email = input("Email: ").strip().lower()
        username = input("Username: ").strip()
        password = getpass("Password (minimum 8 characters): ")
        confirm = getpass("Confirm password: ")

        if not full_name or not email or not username:
            raise ValueError("All account details are required.")

        if len(password) < 8:
            raise ValueError("Password must contain at least 8 characters.")

        if password != confirm:
            raise ValueError("Passwords do not match.")

        existing = db.scalar(
            select(User).where(
                or_(
                    User.email == email,
                    User.username == username,
                )
            )
        )

        if existing:
            raise ValueError(
                f"Email or username already exists: {username}"
            )

        user = User(
            full_name=full_name,
            email=email,
            username=username,
            password_hash=hash_password(password),
            role=role,
            is_active=True,
        )

        db.add(user)
        db.flush()

        print(f"{label} account prepared. User ID: {user.id}")

    db.commit()
    print("\nSUCCESS: Both accounts created!")

except Exception as error:
    db.rollback()
    print("\nACCOUNT CREATION FAILED:", error)

finally:
    db.close()
