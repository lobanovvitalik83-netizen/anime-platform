from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.import_job import ImportJob


class ImportJobRepository:
    def __init__(self, session: Session):
        self.session = session

    def list_all(self) -> list[ImportJob]:
        statement = select(ImportJob).order_by(ImportJob.id.desc())
        return list(self.session.scalars(statement))

    def create(self, **kwargs) -> ImportJob:
        entity = ImportJob(**kwargs)
        self.session.add(entity)
        self.session.flush()
        return entity

    def update(self, entity: ImportJob, **kwargs) -> ImportJob:
        for key, value in kwargs.items():
            setattr(entity, key, value)
        self.session.flush()
        return entity
