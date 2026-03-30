import getpass

from sqlalchemy import select

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.admin import Admin


def main() -> None:
    username = input("Admin username: ").strip()
    if not username:
        raise SystemExit("Username is required")

    password = getpass.getpass("Admin password: ").strip()
    if not password:
        raise SystemExit("Password is required")

    with SessionLocal() as session:
        existing = session.scalar(select(Admin).where(Admin.username == username))
        if existing:
            raise SystemExit("Admin already exists")

        admin = Admin(
            username=username,
            password_hash=hash_password(password),
            role="superadmin",
            is_active=True,
        )
        session.add(admin)
        session.commit()

    print("Admin created successfully")


if __name__ == "__main__":
    main()
