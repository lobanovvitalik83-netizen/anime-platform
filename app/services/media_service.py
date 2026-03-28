from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.models.media_title import MediaTitle
from app.repositories.media_title_repository import MediaTitleRepository
from app.services.audit_service import AuditService


class MediaService:
    def __init__(self, session: Session):
        self.session = session
        self.titles = MediaTitleRepository(session)
        self.audit = AuditService(session)

    def list_titles(self) -> list[MediaTitle]:
        return self.titles.list_all()

    def get_title(self, title_id: int) -> MediaTitle:
        entity = self.titles.get_by_id(title_id)
        if not entity:
            raise NotFoundError("Media title not found")
        return entity

    def create_title(self, admin_id: int, payload: dict) -> MediaTitle:
        entity = self.titles.create(**payload)
        self.audit.log(
            admin_id=admin_id,
            action="create_media_title",
            entity_type="media_title",
            entity_id=str(entity.id),
            payload={"title": entity.title},
        )
        self.session.commit()
        self.session.refresh(entity)
        return entity

    def update_title(self, admin_id: int, title_id: int, payload: dict) -> MediaTitle:
        entity = self.get_title(title_id)
        entity = self.titles.update(entity, **payload)
        self.audit.log(
            admin_id=admin_id,
            action="update_media_title",
            entity_type="media_title",
            entity_id=str(entity.id),
            payload=payload,
        )
        self.session.commit()
        self.session.refresh(entity)
        return entity
