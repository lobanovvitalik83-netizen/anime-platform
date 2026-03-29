from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db_session
from app.schemas.public_lookup import PublicLookupResponse
from app.services.public_lookup_service import PublicLookupService

router = APIRouter(prefix="/api/public", tags=["public-lookup"])


@router.get("/code-lookup/{code}", response_model=PublicLookupResponse)
def public_code_lookup(code: str, db: Session = Depends(get_db_session)) -> PublicLookupResponse:
    return PublicLookupService(db).lookup(code)
