from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from crud.permission import get_permissions_by_keys
from models import Role


def list_roles(db: Session) -> list[Role]:
    return list(db.scalars(select(Role).order_by(Role.id.asc())).all())


def get_role_by_slug(db: Session, slug: str) -> Role | None:
    return db.scalar(select(Role).where(Role.slug == slug))


def get_roles_by_slugs(db: Session, slugs: list[str]) -> list[Role]:
    if not slugs:
        return []
    return list(db.scalars(select(Role).where(Role.slug.in_(slugs))).all())


def create_role(db: Session, *, name: str, slug: str, description: str | None, permission_keys: list[str]) -> Role:
    existing = get_role_by_slug(db, slug)
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Role slug already exists")

    role = Role(name=name, slug=slug, description=description)
    role.permissions = get_permissions_by_keys(db, permission_keys)
    db.add(role)
    db.commit()
    db.refresh(role)
    return role


def update_role(
    db: Session,
    *,
    role: Role,
    name: str | None = None,
    slug: str | None = None,
    description: str | None = None,
    permission_keys: list[str] | None = None,
) -> Role:
    if slug and slug != role.slug:
        existing = get_role_by_slug(db, slug)
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Role slug already exists")
        role.slug = slug

    if name is not None:
        role.name = name
    if description is not None:
        role.description = description
    if permission_keys is not None:
        role.permissions = get_permissions_by_keys(db, permission_keys)

    db.add(role)
    db.commit()
    db.refresh(role)
    return role
