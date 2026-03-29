from sqlalchemy.orm import Session

from app.repositories.site_setting_repository import SiteSettingRepository


class SiteSettingService:
    MESSAGES_ENABLED_KEY = "messages_enabled"

    def __init__(self, session: Session):
        self.session = session
        self.settings = SiteSettingRepository(session)

    def get_bool(self, key: str, default: bool = False) -> bool:
        item = self.settings.get_by_key(key)
        if not item or item.value is None:
            return default
        return item.value.strip().lower() in {"1", "true", "yes", "on"}

    def set_bool(self, key: str, value: bool) -> None:
        item = self.settings.get_by_key(key)
        raw_value = "true" if value else "false"
        if item:
            self.settings.update(item, raw_value)
        else:
            self.settings.create(key, raw_value)
        self.session.commit()

    def is_messages_enabled(self) -> bool:
        return self.get_bool(self.MESSAGES_ENABLED_KEY, default=True)

    def set_messages_enabled(self, value: bool) -> None:
        self.set_bool(self.MESSAGES_ENABLED_KEY, value)
