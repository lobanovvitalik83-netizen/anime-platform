import secrets

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.models.access_code import AccessCode
from app.repositories.access_code_repository import AccessCodeRepository
from app.services.audit_service import AuditService
from app.services.media_service import MediaService


class CodeService:
    def __init__(self, session: Session):
        self.session = session
        self.codes = AccessCodeRepository(session)
        self.audit = AuditService(session)
        self.media = MediaService(session)

    def list_codes(self) -> list[AccessCode]:
        return self.codes.list_all()

    def get_code(self, code_id: int) -> AccessCode:
        entity = self.codes.get_by_id(code_id)
        if not entity:
            raise NotFoundError("Access code not found")
        return entity

    def lookup_active_code(self, code: str) -> AccessCode:
        entity = self.codes.get_by_code(code)
        if not entity or entity.status != "active":
            raise NotFoundError("Active access code not found")
        return entity

    def create_code(self, admin_id: int, payload: dict) -> AccessCode:
        if self.codes.get_by_code(payload["code"]):
            raise ConflictError("Code already exists")
        self._validate_target(payload)
        entity = self.codes.create(**payload, created_by_admin_id=admin_id)
        self.audit.log(admin_id, "create_access_code", "access_code", str(entity.id), {"code": entity.code})
        self.session.commit()
        self.session.refresh(entity)
        return entity

    def update_code(self, admin_id: int, code_id: int, payload: dict) -> AccessCode:
        entity = self.get_code(code_id)

        new_code = payload.get("code", entity.code)
        if not str(new_code).isdigit():
            raise ValidationError("Code must contain digits only")

        existing = self.codes.get_by_code(str(new_code))
        if existing and existing.id != entity.id:
            raise ConflictError("Code already exists")

        target_payload = {
            "title_id": payload.get("title_id", entity.title_id),
            "season_id": payload.get("season_id", entity.season_id),
            "episode_id": payload.get("episode_id", entity.episode_id),
        }
        self._validate_target(target_payload)

        entity = self.codes.update(
            entity,
            code=str(new_code),
            title_id=target_payload["title_id"],
            season_id=target_payload["season_id"],
            episode_id=target_payload["episode_id"],
            status=payload.get("status", entity.status),
        )
        self.audit.log(admin_id, "update_access_code", "access_code", str(entity.id), payload)
        self.session.commit()
        self.session.refresh(entity)
        return entity


    def activate_code(self, admin_id: int, code_id: int) -> AccessCode:
        entity = self.get_code(code_id)
        entity = self.codes.update(entity, status="active")
        self.audit.log(admin_id, "activate_access_code", "access_code", str(entity.id), {"code": entity.code})
        self.session.commit()
        self.session.refresh(entity)
        return entity

    def deactivate_code(self, admin_id: int, code_id: int) -> AccessCode:
        entity = self.get_code(code_id)
        entity = self.codes.update(entity, status="inactive")
        self.audit.log(admin_id, "deactivate_access_code", "access_code", str(entity.id), {"code": entity.code})
        self.session.commit()
        self.session.refresh(entity)
        return entity

    def delete_code(self, admin_id: int, code_id: int) -> None:
        entity = self.get_code(code_id)
        self.audit.log(admin_id, "delete_access_code", "access_code", str(entity.id), {"code": entity.code})
        self.codes.delete(entity)
        self.session.commit()

    def generate_codes(self, admin_id: int, payload: dict) -> list[AccessCode]:
        self._validate_target(payload)
        quantity = payload["quantity"]
        generated: list[AccessCode] = []
        used_in_batch: set[str] = set()

        while len(generated) < quantity:
            candidate = self._generate_code_candidate()
            if candidate in used_in_batch:
                continue
            if self.codes.get_by_code(candidate):
                continue

            entity = self.codes.create(
                code=candidate,
                title_id=payload.get("title_id"),
                season_id=payload.get("season_id"),
                episode_id=payload.get("episode_id"),
                status=payload.get("status", "active"),
                created_by_admin_id=admin_id,
            )
            used_in_batch.add(candidate)
            generated.append(entity)

        self.audit.log(
            admin_id,
            "bulk_generate_access_codes",
            "access_code",
            "batch",
            {"quantity": len(generated)},
        )
        self.session.commit()
        for entity in generated:
            self.session.refresh(entity)
        return generated

    def _generate_code_candidate(self) -> str:
        digits = "".join(str(secrets.randbelow(10)) for _ in range(settings.code_length))
        if digits[0] == "0":
            digits = str(secrets.randbelow(9) + 1) + digits[1:]
        return digits

    def _validate_target(self, payload: dict) -> None:
        if not any(payload.get(key) is not None for key in ("title_id", "season_id", "episode_id")):
            raise ValidationError("At least one owner must be provided")

        if payload.get("title_id") is not None:
            self.media.get_title(payload["title_id"])
        if payload.get("season_id") is not None:
            self.media.get_season(payload["season_id"])
        if payload.get("episode_id") is not None:
            self.media.get_episode(payload["episode_id"])
