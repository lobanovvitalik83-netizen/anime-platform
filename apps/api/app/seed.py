import os
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.models import ContentCard, Permission, Role, SettingKV, User
from app.security import hash_password

DEFAULT_PERMISSIONS = [
    "users.view",
    "users.create",
    "users.update",
    "roles.view",
    "roles.create",
    "roles.update",
    "permissions.view",
    "content.view",
    "content.create",
    "content.update",
    "content.delete",
    "media.upload",
    "settings.view",
    "settings.update",
    "analytics.view",
]

DEFAULT_SETTINGS = {
    "platform_name": "Anime Platform",
    "support_email": "support@example.com",
    "telegram_bot_enabled": "false",
}


def seed_database(db: Session) -> None:
    for key in DEFAULT_PERMISSIONS:
        permission = db.scalar(select(Permission).where(Permission.key == key))
        if not permission:
            db.add(Permission(key=key, description=key))
    db.commit()

    owner_role = db.scalar(select(Role).where(Role.slug == "owner"))
    if not owner_role:
        owner_role = Role(name="Owner", slug="owner", description="Full access role")
        owner_role.permissions = list(db.scalars(select(Permission)).all())
        db.add(owner_role)
        db.commit()
        db.refresh(owner_role)

    owner_user = db.scalar(select(User).where(User.username == settings.owner_username))
    if not owner_user:
        owner_user = User(
            email=settings.owner_email,
            username=settings.owner_username,
            password_hash=hash_password(settings.owner_password),
            is_active=True,
            is_superuser=True,
        )
        owner_user.roles = [owner_role]
        db.add(owner_user)
        db.commit()

    creator_role = db.scalar(select(Role).where(Role.slug == "creator"))
    if not creator_role:
        creator_permissions = list(
            db.scalars(select(Permission).where(Permission.key.in_(["content.view", "content.create", "content.update", "media.upload"]))).all()
        )
        creator_role = Role(name="Creator", slug="creator", description="Content creator")
        creator_role.permissions = creator_permissions
        db.add(creator_role)
        db.commit()

    for key, value in DEFAULT_SETTINGS.items():
        existing = db.scalar(select(SettingKV).where(SettingKV.key == key))
        if not existing:
            db.add(SettingKV(key=key, value=value))
    db.commit()

    media_root = Path(settings.media_root)
    media_root.mkdir(parents=True, exist_ok=True)
