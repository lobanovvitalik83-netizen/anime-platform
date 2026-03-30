from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin
from app.core.database import get_db_session
from app.models.admin import Admin
from app.schemas.access_code import AccessCodeCreate, AccessCodeGenerateRequest, AccessCodeRead
from app.services.code_service import CodeService

router = APIRouter(prefix="/api/access-codes", tags=["access-codes"])


@router.get("", response_model=list[AccessCodeRead])
def list_access_codes(
    _: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db_session),
) -> list[AccessCodeRead]:
    items = CodeService(db).list_codes()
    return [AccessCodeRead.model_validate(item) for item in items]


@router.post("", response_model=AccessCodeRead)
def create_access_code(
    payload: AccessCodeCreate,
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db_session),
) -> AccessCodeRead:
    item = CodeService(db).create_code(current_admin.id, payload.model_dump())
    return AccessCodeRead.model_validate(item)


@router.post("/generate", response_model=list[AccessCodeRead])
def generate_access_codes(
    payload: AccessCodeGenerateRequest,
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db_session),
) -> list[AccessCodeRead]:
    items = CodeService(db).generate_codes(current_admin.id, payload.model_dump())
    return [AccessCodeRead.model_validate(item) for item in items]
