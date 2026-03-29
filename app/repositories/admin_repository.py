from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.admin import Admin


class AdminRepository:
    def __init__(self, session: Session):
        self.session = session

    def list_all(self) -> list[Admin]:
        statement = select(Admin).order_by(Admin.id.asc())
        return list(self.session.scalars(statement))

    def list_by_roles(self, roles: list[str]) -> list[Admin]:
        statement = select(Admin).where(Admin.role.in_(roles)).order_by(Admin.id.asc())
        return list(self.session.scalars(statement))

    def get_by_id(self, admin_id: int) -> Admin | None:
        return self.session.get(Admin, admin_id)

    def get_by_username(self, username: str) -> Admin | None:
        statement = select(Admin).where(Admin.username == username)
        return self.session.scalar(statement)

    def create(self, **kwargs) -> Admin:
        entity = Admin(**kwargs)
        self.session.add(entity)
        self.session.flush()
        return entity

    def update(self, entity: Admin, **kwargs) -> Admin:
        for key, value in kwargs.items():
            setattr(entity, key, value)
        self.session.flush()
        return entity

    def delete(self, entity: Admin) -> None:
        self.session.delete(entity)
        self.session.flush()
