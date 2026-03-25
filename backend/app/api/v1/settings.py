from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api.deps import require_permission
from app.db.session import get_db
from app.models.user import AppSetting, User
from app.schemas.settings import SettingsUpdate

router = APIRouter(prefix="/settings", tags=["settings"])

def read_settings(db: Session):
    rows = {item.key: item.value for item in db.query(AppSetting).all()}
    return {
        "project_name": rows.get("project_name", "Anime Platform"),
        "support_email": rows.get("support_email", "owner@example.com"),
        "telegram_bot_enabled": rows.get("telegram_bot_enabled", "true") == "true",
        "telegram_bot_username": rows.get("telegram_bot_username", ""),
        "telegram_admin_chat_id": rows.get("telegram_admin_chat_id", ""),
    }

@router.get("")
def get_settings(db: Session = Depends(get_db), _: User = Depends(require_permission("settings.view"))):
    return read_settings(db)

@router.patch("")
def update_settings(payload: SettingsUpdate, db: Session = Depends(get_db), _: User = Depends(require_permission("settings.update"))):
    values = {
        "project_name": payload.project_name,
        "support_email": payload.support_email,
        "telegram_bot_enabled": "true" if payload.telegram_bot_enabled else "false",
        "telegram_bot_username": payload.telegram_bot_username,
        "telegram_admin_chat_id": payload.telegram_admin_chat_id,
    }
    for key, value in values.items():
        row = db.query(AppSetting).filter(AppSetting.key == key).first()
        if row:
            row.value = str(value)
        else:
            db.add(AppSetting(key=key, value=str(value)))
    db.commit()
    return read_settings(db)
