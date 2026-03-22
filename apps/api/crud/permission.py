from sqlalchemy import select
from sqlalchemy.orm import Session

from constants import DEFAULT_PERMISSIONS
from models import Permission


def seed_permissions(db: Session) -> None:
    existing_keys = set(db.scalars(select(Permission.key)).all())
    missing = [key for key in DEFAULT_PERMISSIONS if key not in existing_keys]

    for key in missing:
        db.add(Permission(key=key, description=key))

    if missing:
        db.commit()


def get_permissions_by_keys(db: Session, keys: list[str]) -> list[Permission]:
    if not keys:
        return []
    return list(db.scalars(select(Permission).where(Permission.key.in_(keys))).all())


def list_permissions(db: Session) -> list[Permission]:
    return list(db.scalars(select(Permission).order_by(Permission.key.asc())).all())
