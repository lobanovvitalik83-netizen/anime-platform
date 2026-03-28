import secrets

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import ConflictError, NotFoundError
from app.models.access_code import AccessCode
from app.repositories.access_code_repository import AccessCodeRepository
from app.services.audit_service import AuditService


class CodeService:
    def __init__(self, session: Session):
        self.session = session
        self.codes = AccessCodeRepository(session)
        self.audit = AuditService(session)

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
        existing = self.codes.get_by_code(payload["code"])
        if existing:
            raise ConflictError("Code already exists")

        entity = self.codes.create(
            **payload,
            created_by_admin_id=admin_id,
        )
        self.audit.log(
            admin_id=admin_id,
            action="create_access_code",
            entity_type="access_code",
            entity_id=str(entity.id),
            payload={"code": entity.code},
        )
        self.session.commit()
        self.session.refresh(entity)
        return entity

    def generate_codes(self, admin_id: int, payload: dict) -> list[AccessCode]:
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
            admin_id=admin_id,
            action="bulk_generate_access_codes",
            entity_type="access_code",
            entity_id="batch",
            payload={"quantity": len(generated)},
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
