from sqlalchemy.orm import Session

from app.core.exceptions import AuthenticationError, ConflictError
from app.core.security import hash_password, verify_password
from app.models.admin import Admin
from app.repositories.admin_repository import AdminRepository
from app.services.audit_service import AuditService


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

    def ensure_default_admin(self, username: str, password: str) -> Admin | None:
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

    def create_admin(self, username: str, password: str, role: str = "admin") -> Admin:
        existing = self.admins.get_by_username(username)
        if existing:
            raise ConflictError("Admin already exists")

        created = self.admins.create(
            username=username,
            password_hash=hash_password(password),
            role=role,
        )
        self.audit.log(
            admin_id=created.id,
            action="create_admin",
            entity_type="admin",
            entity_id=str(created.id),
            payload={"username": created.username, "role": created.role},
        )
        self.session.commit()
        return created
