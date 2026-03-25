from sqlalchemy.orm import Session
from app.models.user import Permission, Role, User, AppSetting
from app.services.security import hash_password
from app.core.config import settings

PERMISSION_KEYS = [
    "users.view","users.create","users.update","users.block",
    "roles.view","permissions.view","settings.view","settings.update",
    "content.view","content.create","content.update","content.delete"
]

def ensure_seed_data(db: Session) -> None:
    permissions = []
    for key in PERMISSION_KEYS:
        item = db.query(Permission).filter(Permission.key == key).first()
        if not item:
            item = Permission(key=key, description=key)
            db.add(item)
            db.flush()
        permissions.append(item)

    owner_role = db.query(Role).filter(Role.slug == "owner").first()
    if not owner_role:
        owner_role = Role(name="Owner", slug="owner", description="Full access role")
        owner_role.permissions = permissions
        db.add(owner_role)
        db.flush()

    creator_role = db.query(Role).filter(Role.slug == "creator").first()
    if not creator_role:
        creator_role = Role(name="Creator", slug="creator", description="Content creator role")
        creator_role.permissions = [p for p in permissions if p.key.startswith("content.") or p.key == "users.view"]
        db.add(creator_role)
        db.flush()

    owner = db.query(User).filter(User.username == settings.owner_username).first()
    if not owner:
        owner = User(
            email=settings.owner_email,
            username=settings.owner_username,
            password_hash=hash_password(settings.owner_password),
            is_active=True,
            is_superuser=True,
            roles=[owner_role],
        )
        db.add(owner)

    defaults = {
        "project_name": "Anime Platform",
        "support_email": settings.owner_email,
        "telegram_bot_enabled": "true" if settings.telegram_bot_enabled else "false",
        "telegram_bot_username": settings.telegram_bot_username,
        "telegram_admin_chat_id": settings.telegram_admin_chat_id,
    }
    for key, value in defaults.items():
        row = db.query(AppSetting).filter(AppSetting.key == key).first()
        if not row:
            db.add(AppSetting(key=key, value=value))
    db.commit()
