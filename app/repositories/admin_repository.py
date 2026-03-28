from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.admin import Admin


class AdminRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, admin_id: int) -> Admin | None:
        return self.session.get(Admin, admin_id)

    def get_by_username(self, username: str) -> Admin | None:
        statement = select(Admin).where(Admin.username == username)
        return self.session.scalar(statement)

    def list_all(self) -> list[Admin]:
        statement = select(Admin).order_by(Admin.id.asc())
        return list(self.session.scalars(statement))

    def create(self, username: str, password_hash: str, role: str = "admin") -> Admin:
        admin = Admin(
            username=username,
            password_hash=password_hash,
            role=role,
            is_active=True,
        )
        self.session.add(admin)
        self.session.flush()
        return admin
