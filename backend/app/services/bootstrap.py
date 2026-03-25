from sqlalchemy.orm import Session
from app.models.user import Permission, Role, User, AppSetting
from app.services.security import hash_password
from app.core.config import settings

PERMISSION_KEYS = [
    "users.view","users.create","users.update","users.block",
    "roles.view","roles.create","roles.update","roles.assign",
    "permissions.view","permissions.assign","settings.view","settings.update"
]

def ensure_seed_data(db: Session) -> None:
    permissions = []
    for key in PERMISSION_KEYS:
        existing = db.query(Permission).filter(Permission.key == key).first()
        if not existing:
            existing = Permission(key=key, description=key)
            db.add(existing)
            db.flush()
        permissions.append(existing)

    owner_role = db.query(Role).filter(Role.slug == "owner").first()
    if not owner_role:
        owner_role = Role(name="Owner", slug="owner", description="Full access role")
        owner_role.permissions = permissions
        db.add(owner_role)
        db.flush()

    creator_role = db.query(Role).filter(Role.slug == "creator").first()
    if not creator_role:
        creator_perms = [p for p in permissions if p.key in {"users.view","roles.view","permissions.view"}]
        creator_role = Role(name="Creator", slug="creator", description="Content creator role")
        creator_role.permissions = creator_perms
        db.add(creator_role)
        db.flush()

    owner = db.query(User).filter(User.username == settings.owner_username).first()
    if not owner:
        owner = User(
            email=settings.owner_email,
            username=settings.owner_username,
            password_hash=hash_password(settings.owner_password[:72]),
            is_active=True,
            is_superuser=True,
            roles=[owner_role],
        )
        db.add(owner)

    defaults = {
        "project_name": "Anime Platform",
        "support_email": settings.owner_email,
        "telegram_bot_enabled": "true",
    }
    for key, value in defaults.items():
        existing = db.query(AppSetting).filter(AppSetting.key == key).first()
        if not existing:
            db.add(AppSetting(key=key, value=value))
    db.commit()
