from pydantic import BaseModel, EmailStr

class SettingsOut(BaseModel):
    project_name: str
    support_email: EmailStr
    telegram_bot_enabled: bool
    telegram_bot_username: str
    telegram_admin_chat_id: str

class SettingsUpdate(BaseModel):
    project_name: str
    support_email: EmailStr
    telegram_bot_enabled: bool
    telegram_bot_username: str = ""
    telegram_admin_chat_id: str = ""
