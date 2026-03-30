from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.site_setting import SiteSetting


class SiteSettingRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_by_key(self, key: str) -> SiteSetting | None:
        statement = select(SiteSetting).where(SiteSetting.key == key)
        return self.session.scalar(statement)

    def create(self, key: str, value: str | None) -> SiteSetting:
        entity = SiteSetting(key=key, value=value)
        self.session.add(entity)
        self.session.flush()
        return entity

    def update(self, entity: SiteSetting, value: str | None) -> SiteSetting:
        entity.value = value
        self.session.flush()
        return entity
