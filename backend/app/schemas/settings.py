from pydantic import BaseModel

class SettingsOut(BaseModel):
    project_name: str
    support_email: str
    telegram_bot_enabled: bool

class SettingsUpdate(BaseModel):
    project_name: str
    support_email: str
    telegram_bot_enabled: bool
