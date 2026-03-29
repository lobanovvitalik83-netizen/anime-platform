from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import AuthenticationError, ConflictError, NotFoundError, ValidationError
from app.core.security import generate_password, hash_password, verify_password
from app.models.admin import Admin
from app.repositories.admin_repository import AdminRepository
from app.services.audit_service import AuditService
from app.services.avatar_storage_service import AvatarStorageService


MANAGED_ROLES_BY_ACTOR = {
    "superadmin": {"admin", "editor"},
    "admin": {"editor"},
    "editor": set(),
}

CREATABLE_ROLES_BY_ACTOR = {
    "superadmin": {"admin", "editor"},
    "admin": {"editor"},
    "editor": set(),
}


class AuthService:
    def __init__(self, session: Session):
        self.session = session
        self.admins = AdminRepository(session)
        self.audit = AuditService(session)
        self.avatar_storage = AvatarStorageService()

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
            is_active=True,
            full_name="Owner",
            position="Owner",
            about=None,
            avatar_url=None,
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

    def list_admins_for_actor(self, actor: Admin) -> list[Admin]:
        if actor.role == "superadmin":
            return self.admins.list_all()
        if actor.role == "admin":
            return self.admins.list_by_roles(["editor"])
        return []

    def get_admin(self, admin_id: int) -> Admin:
        admin = self.admins.get_by_id(admin_id)
        if not admin:
            raise NotFoundError("Пользователь не найден.")
        return admin

    def get_manageable_admin(self, actor: Admin, target_admin_id: int) -> Admin:
        target = self.get_admin(target_admin_id)
        if actor.id == target.id:
            raise ValidationError("Этой операцией нельзя управлять самим собой.")
        if target.role not in MANAGED_ROLES_BY_ACTOR.get(actor.role, set()):
            raise ValidationError("У вас нет прав на управление этим пользователем.")
        return target

    def allowed_create_roles(self, actor: Admin) -> list[str]:
        roles = sorted(CREATABLE_ROLES_BY_ACTOR.get(actor.role, set()))
        return roles

    def create_admin(
        self,
        actor: Admin,
        *,
        username: str,
        role: str,
        password: str | None,
        generate_password_flag: bool,
        is_active: bool,
    ) -> tuple[Admin, str]:
        username = username.strip()
        role = role.strip().lower()

        if role not in CREATABLE_ROLES_BY_ACTOR.get(actor.role, set()):
            raise ValidationError("У вас нет прав создавать пользователя с этой ролью.")
        if not username:
            raise ValidationError("Логин обязателен.")
        if self.admins.get_by_username(username):
            raise ConflictError("Такой логин уже существует.")

        plain_password = password.strip() if password else ""
        if generate_password_flag or not plain_password:
            plain_password = generate_password()

        if len(plain_password) < 6:
            raise ValidationError("Пароль должен быть не короче 6 символов.")

        created = self.admins.create(
            username=username,
            password_hash=hash_password(plain_password),
            role=role,
            is_active=is_active,
            full_name=None,
            position=None,
            about=None,
            avatar_url=None,
        )
        self.audit.log(
            admin_id=actor.id,
            action="create_admin",
            entity_type="admin",
            entity_id=str(created.id),
            payload={"username": created.username, "role": created.role, "is_active": created.is_active},
        )
        self.session.commit()
        return created, plain_password

    def update_managed_admin(
        self,
        actor: Admin,
        target_admin_id: int,
        *,
        role: str,
        is_active: bool,
    ) -> Admin:
        target = self.get_manageable_admin(actor, target_admin_id)
        role = role.strip().lower()

        allowed_roles = CREATABLE_ROLES_BY_ACTOR.get(actor.role, set())
        if role not in allowed_roles:
            raise ValidationError("Нельзя назначить эту роль.")

        target = self.admins.update(
            target,
            role=role,
            is_active=is_active,
        )
        self.audit.log(
            admin_id=actor.id,
            action="update_admin",
            entity_type="admin",
            entity_id=str(target.id),
            payload={"username": target.username, "role": target.role, "is_active": target.is_active},
        )
        self.session.commit()
        return target

    def reset_managed_admin_password(self, actor: Admin, target_admin_id: int) -> tuple[Admin, str]:
        target = self.get_manageable_admin(actor, target_admin_id)
        new_password = generate_password()
        target = self.admins.update(target, password_hash=hash_password(new_password))
        self.audit.log(
            admin_id=actor.id,
            action="reset_admin_password",
            entity_type="admin",
            entity_id=str(target.id),
            payload={"username": target.username},
        )
        self.session.commit()
        return target, new_password

    def set_managed_admin_active(self, actor: Admin, target_admin_id: int, is_active: bool) -> Admin:
        target = self.get_manageable_admin(actor, target_admin_id)
        target = self.admins.update(target, is_active=is_active)
        self.audit.log(
            admin_id=actor.id,
            action="activate_admin" if is_active else "deactivate_admin",
            entity_type="admin",
            entity_id=str(target.id),
            payload={"username": target.username, "is_active": target.is_active},
        )
        self.session.commit()
        return target

    def update_profile(
        self,
        admin_id: int,
        *,
        full_name: str | None,
        position: str | None,
        about: str | None,
        avatar_url: str | None,
    ) -> Admin:
        admin = self.get_admin(admin_id)
        admin = self.admins.update(
            admin,
            full_name=(full_name or "").strip() or None,
            position=(position or "").strip() or None,
            about=(about or "").strip() or None,
            avatar_url=(avatar_url or "").strip() or None,
        )
        self.audit.log(
            admin_id=admin.id,
            action="update_profile",
            entity_type="admin",
            entity_id=str(admin.id),
            payload={"username": admin.username},
        )
        self.session.commit()
        return admin

    def upload_profile_avatar(
        self,
        admin_id: int,
        *,
        file_bytes: bytes,
        file_name: str,
        content_type: str | None,
    ) -> Admin:
        admin = self.get_admin(admin_id)
        new_avatar_url = self.avatar_storage.save_avatar(
            admin_id=admin.id,
            file_bytes=file_bytes,
            file_name=file_name,
            content_type=content_type,
            old_avatar_url=admin.avatar_url,
        )
        admin = self.admins.update(admin, avatar_url=new_avatar_url)
        self.audit.log(
            admin_id=admin.id,
            action="upload_profile_avatar",
            entity_type="admin",
            entity_id=str(admin.id),
            payload={"avatar_url": admin.avatar_url},
        )
        self.session.commit()
        return admin

    def change_own_password(self, admin_id: int, current_password: str, new_password: str) -> Admin:
        admin = self.get_admin(admin_id)
        if not verify_password(current_password, admin.password_hash):
            raise ValidationError("Текущий пароль указан неверно.")
        new_password = new_password.strip()
        if len(new_password) < 6:
            raise ValidationError("Новый пароль должен быть не короче 6 символов.")

        admin = self.admins.update(admin, password_hash=hash_password(new_password))
        self.audit.log(
            admin_id=admin.id,
            action="change_own_password",
            entity_type="admin",
            entity_id=str(admin.id),
            payload={"username": admin.username},
        )
        self.session.commit()
        return admin
