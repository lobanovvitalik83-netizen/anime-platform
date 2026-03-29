from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.code_lookup_event import CodeLookupEvent


class CodeLookupEventRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, **kwargs) -> CodeLookupEvent:
        entity = CodeLookupEvent(**kwargs)
        self.session.add(entity)
        self.session.flush()
        return entity

    def list_all(self) -> list[CodeLookupEvent]:
        statement = select(CodeLookupEvent).order_by(CodeLookupEvent.id.desc())
        return list(self.session.scalars(statement))

    def list_recent(self, limit: int = 200) -> list[CodeLookupEvent]:
        statement = select(CodeLookupEvent).order_by(CodeLookupEvent.id.desc()).limit(limit)
        return list(self.session.scalars(statement))

    def list_by_code_value(self, code_value: str) -> list[CodeLookupEvent]:
        statement = select(CodeLookupEvent).where(CodeLookupEvent.code_value == code_value).order_by(CodeLookupEvent.id.desc())
        return list(self.session.scalars(statement))
