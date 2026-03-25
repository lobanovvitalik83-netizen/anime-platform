from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import require_permission
from app.models import ContentCard, Permission, Role, User
from app.schemas import AnalyticsSummary

router = APIRouter()


@router.get("/summary", response_model=AnalyticsSummary)
def summary(db: Session = Depends(get_db), _=Depends(require_permission("analytics.view"))):
    users_total = db.scalar(select(func.count(User.id))) or 0
    roles_total = db.scalar(select(func.count(Role.id))) or 0
    permissions_total = db.scalar(select(func.count(Permission.id))) or 0
    content_total = db.scalar(select(func.count(ContentCard.id))) or 0
    content_published = db.scalar(select(func.count(ContentCard.id)).where(ContentCard.status == "published")) or 0
    content_draft = db.scalar(select(func.count(ContentCard.id)).where(ContentCard.status == "draft")) or 0
    content_archived = db.scalar(select(func.count(ContentCard.id)).where(ContentCard.status == "archived")) or 0

    return AnalyticsSummary(
        users_total=users_total,
        roles_total=roles_total,
        permissions_total=permissions_total,
        content_total=content_total,
        content_published=content_published,
        content_draft=content_draft,
        content_archived=content_archived,
    )
