from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.access_code import AccessCode


class AccessCodeRepository:
    def __init__(self, session: Session):
        self.session = session

    def list_all(self) -> list[AccessCode]:
        statement = select(AccessCode).order_by(AccessCode.id.desc())
        return list(self.session.scalars(statement))

    def get_by_id(self, code_id: int) -> AccessCode | None:
        return self.session.get(AccessCode, code_id)

    def get_by_code(self, code: str) -> AccessCode | None:
        statement = select(AccessCode).where(AccessCode.code == code)
        return self.session.scalar(statement)

    def create(self, **kwargs) -> AccessCode:
        entity = AccessCode(**kwargs)
        self.session.add(entity)
        self.session.flush()
        return entity

    def update(self, entity: AccessCode, **kwargs) -> AccessCode:
        for key, value in kwargs.items():
            setattr(entity, key, value)
        self.session.flush()
        return entity

    def delete(self, entity: AccessCode) -> None:
        self.session.delete(entity)
        self.session.flush()
