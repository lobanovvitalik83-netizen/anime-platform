from sqlalchemy import select
from sqlalchemy.orm import Session

from config import settings
from crud.permission import seed_permissions
from crud.role import create_role, get_role_by_slug
from crud.user import create_user
from models import Permission, User

OWNER_ROLE_SLUG = "owner"


def init_database(db: Session) -> None:
    seed_permissions(db)

    owner_role = get_role_by_slug(db, OWNER_ROLE_SLUG)
    if owner_role is None:
        owner_role = create_role(
            db,
            name="Owner",
            slug=OWNER_ROLE_SLUG,
            description="Full access role",
            permission_keys=[],
        )
        owner_role.permissions = list(db.scalars(select(Permission)).all())
        db.add(owner_role)
        db.commit()
        db.refresh(owner_role)

    owner_exists = db.scalar(select(User).where(User.email == settings.FIRST_OWNER_EMAIL))
    if owner_exists is None:
        create_user(
            db,
            email=settings.FIRST_OWNER_EMAIL,
            username=settings.FIRST_OWNER_USERNAME,
            password=settings.FIRST_OWNER_PASSWORD,
            role_slugs=[OWNER_ROLE_SLUG],
            permission_keys=[],
            is_superuser=True,
        )
