from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import AuthenticationError, ConflictError, NotFoundError, ValidationError
from app.core.security import hash_password, verify_password
from app.models.admin import Admin
from app.repositories.admin_repository import AdminRepository
from app.services.audit_service import AuditService


VALID_ADMIN_ROLES = {"superadmin", "admin", "editor"}


class AuthService:
    def __init__(self, session: Session):
        self.session = session
        self.admins = AdminRepository(session)
        self.audit = AuditService(session)

    def authenticate(self, username: str, password: str) -> Admin:
        admin = self.admins.get_by_username(username)
        if not admin or not admin.is_active:
            raise AuthenticationError("Invalid credentials")
        if not verify_password(password, admin.password_hash):
            raise AuthenticationError("Invalid credentials")

        self.audit.log(
            admin_id=admin.id,
            action="login",
            entity_type="admin",
            entity_id=str(admin.id),
            payload={"username": admin.username},
        )
        self.session.commit()
        return admin

    def list_admins(self) -> list[Admin]:
        return self.admins.list_all()

    def get_admin(self, admin_id: int) -> Admin:
        admin = self.admins.get_by_id(admin_id)
        if not admin:
            raise NotFoundError("Admin not found")
        return admin

    def ensure_default_admin(self) -> Admin | None:
        username = settings.admin_default_username
        password = settings.admin_default_password

        if not username or not password:
            return None

        existing = self.admins.get_by_username(username)
        if existing:
            return existing

        created = self.admins.create(
            username=username,
            password_hash=hash_password(password),
            role="superadmin",
        )
        self.audit.log(
            admin_id=created.id,
            action="bootstrap_admin",
            entity_type="admin",
            entity_id=str(created.id),
            payload={"username": created.username},
        )
        self.session.commit()
        return created

    def create_admin(self, creator_admin_id: int, username: str, password: str, role: str = "editor") -> Admin:
        username = username.strip()
        password = password.strip()
        role = role.strip().lower()

        if role not in VALID_ADMIN_ROLES:
            raise ValidationError("Role must be superadmin, admin or editor")
        if not username:
            raise ValidationError("Username is required")
        if len(password) < 6:
            raise ValidationError("Password must be at least 6 characters")

        existing = self.admins.get_by_username(username)
        if existing:
            raise ConflictError("Admin already exists")

        created = self.admins.create(
            username=username,
            password_hash=hash_password(password),
            role=role,
        )
        self.audit.log(
            admin_id=creator_admin_id,
            action="create_admin",
            entity_type="admin",
            entity_id=str(created.id),
            payload={"username": created.username, "role": created.role},
        )
        self.session.commit()
        return created

    def update_admin(
        self,
        actor_admin_id: int,
        target_admin_id: int,
        *,
        username: str,
        role: str,
        is_active: bool,
        new_password: str | None = None,
    ) -> Admin:
        admin = self.get_admin(target_admin_id)
        username = username.strip()
        role = role.strip().lower()

        if role not in VALID_ADMIN_ROLES:
            raise ValidationError("Role must be superadmin, admin or editor")
        if not username:
            raise ValidationError("Username is required")

        existing = self.admins.get_by_username(username)
        if existing and existing.id != admin.id:
            raise ConflictError("Username already exists")

        payload = {
            "username": username,
            "role": role,
            "is_active": is_active,
        }
        if new_password and new_password.strip():
            if len(new_password.strip()) < 6:
                raise ValidationError("Password must be at least 6 characters")
            payload["password_hash"] = hash_password(new_password.strip())

        admin = self.admins.update(admin, **payload)
        self.audit.log(
            admin_id=actor_admin_id,
            action="update_admin",
            entity_type="admin",
            entity_id=str(admin.id),
            payload={"username": admin.username, "role": admin.role, "is_active": admin.is_active},
        )
        self.session.commit()
        return admin

    def set_admin_active(self, actor_admin_id: int, target_admin_id: int, is_active: bool) -> Admin:
        admin = self.get_admin(target_admin_id)
        admin = self.admins.update(admin, is_active=is_active)
        self.audit.log(
            admin_id=actor_admin_id,
            action="activate_admin" if is_active else "deactivate_admin",
            entity_type="admin",
            entity_id=str(admin.id),
            payload={"username": admin.username, "is_active": admin.is_active},
        )
        self.session.commit()
        return admin
