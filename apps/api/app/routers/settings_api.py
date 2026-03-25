from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import require_permission
from app.models import SettingKV
from app.schemas import SettingItem, SettingUpdate

router = APIRouter()


@router.get("")
def list_settings(db: Session = Depends(get_db), _=Depends(require_permission("settings.view"))):
    return [{"key": item.key, "value": item.value} for item in db.scalars(select(SettingKV).order_by(SettingKV.key)).all()]


@router.patch("")
def update_settings(payload: SettingUpdate, db: Session = Depends(get_db), _=Depends(require_permission("settings.update"))):
    for incoming in payload.items:
        setting = db.scalar(select(SettingKV).where(SettingKV.key == incoming.key))
        if not setting:
            setting = SettingKV(key=incoming.key, value=incoming.value)
        else:
            setting.value = incoming.value
        db.add(setting)
    db.commit()
    return {"status": "updated"}
