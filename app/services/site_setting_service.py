from sqlalchemy.orm import Session
from app.repositories.site_setting_repository import SiteSettingRepository

class SiteSettingService:
    MESSAGES_ENABLED_KEY = "messages_enabled"
    REPORTS_ENABLED_KEY = "reports_enabled"
    MAINTENANCE_MODE_KEY = "maintenance_mode"
    SITE_TITLE_KEY = "site_title"
    LOGO_URL_KEY = "logo_url"

    def __init__(self, session: Session):
        self.session = session
        self.settings = SiteSettingRepository(session)

    def get_bool(self, key: str, default: bool = False) -> bool:
        item = self.settings.get_by_key(key)
        if not item or item.value is None:
            return default
        return item.value.strip().lower() in {"1", "true", "yes", "on"}

    def get_str(self, key: str, default: str = "") -> str:
        item = self.settings.get_by_key(key)
        if not item or item.value is None:
            return default
        return item.value

    def set_str(self, key: str, value: str | None):
        item = self.settings.get_by_key(key)
        if item:
            self.settings.update(item, value)
        else:
            self.settings.create(key, value)
        self.session.commit()

    def set_bool(self, key: str, value: bool):
        self.set_str(key, "true" if value else "false")

    def is_messages_enabled(self) -> bool:
        return self.get_bool(self.MESSAGES_ENABLED_KEY, True)

    def is_reports_enabled(self) -> bool:
        return self.get_bool(self.REPORTS_ENABLED_KEY, True)

    def is_maintenance_mode(self) -> bool:
        return self.get_bool(self.MAINTENANCE_MODE_KEY, False)

    def set_messages_enabled(self, value: bool):
        self.set_bool(self.MESSAGES_ENABLED_KEY, value)

    def set_reports_enabled(self, value: bool):
        self.set_bool(self.REPORTS_ENABLED_KEY, value)

    def set_maintenance_mode(self, value: bool):
        self.set_bool(self.MAINTENANCE_MODE_KEY, value)
