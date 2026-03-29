import csv
import io
import json

from sqlalchemy.orm import Session

from app.core.exceptions import ValidationError
from app.repositories.import_job_repository import ImportJobRepository
from app.services.asset_service import AssetService
from app.services.code_service import CodeService
from app.services.media_service import MediaService


class ImportExportService:
    def __init__(self, session: Session):
        self.session = session
        self.jobs = ImportJobRepository(session)
        self.media = MediaService(session)
        self.assets = AssetService(session)
        self.codes = CodeService(session)

    def list_jobs(self):
        return self.jobs.list_all()

    def export_titles_csv(self) -> str:
        rows = []
        for item in self.media.list_titles():
            rows.append({
                "id": item.id,
                "type": item.type,
                "title": item.title,
                "original_title": item.original_title or "",
                "description": item.description or "",
                "year": item.year or "",
                "status": item.status,
                "created_at": item.created_at.isoformat() if item.created_at else "",
            })
        return self._render_csv(rows)

    def export_seasons_csv(self) -> str:
        rows = []
        for item in self.media.list_seasons():
            rows.append({
                "id": item.id,
                "title_id": item.title_id,
                "season_number": item.season_number,
                "name": item.name or "",
                "description": item.description or "",
                "created_at": item.created_at.isoformat() if item.created_at else "",
            })
        return self._render_csv(rows)

    def export_episodes_csv(self) -> str:
        rows = []
        for item in self.media.list_episodes():
            rows.append({
                "id": item.id,
                "title_id": item.title_id,
                "season_id": item.season_id or "",
                "episode_number": item.episode_number,
                "name": item.name or "",
                "synopsis": item.synopsis or "",
                "status": item.status,
                "created_at": item.created_at.isoformat() if item.created_at else "",
            })
        return self._render_csv(rows)

    def export_assets_csv(self) -> str:
        rows = []
        for item in self.assets.list_assets():
            rows.append({
                "id": item.id,
                "title_id": item.title_id or "",
                "season_id": item.season_id or "",
                "episode_id": item.episode_id or "",
                "asset_type": item.asset_type,
                "storage_kind": item.storage_kind,
                "telegram_file_id": item.telegram_file_id or "",
                "external_url": item.external_url or "",
                "mime_type": item.mime_type or "",
                "is_primary": item.is_primary,
                "created_at": item.created_at.isoformat() if item.created_at else "",
            })
        return self._render_csv(rows)

    def export_codes_csv(self) -> str:
        rows = []
        for item in self.codes.list_codes():
            rows.append({
                "id": item.id,
                "code": item.code,
                "title_id": item.title_id or "",
                "season_id": item.season_id or "",
                "episode_id": item.episode_id or "",
                "status": item.status,
                "created_by_admin_id": item.created_by_admin_id or "",
                "created_at": item.created_at.isoformat() if item.created_at else "",
            })
        return self._render_csv(rows)

    def import_titles_csv(self, admin_id: int, file_name: str, content: bytes):
        job = self.jobs.create(
            admin_id=admin_id,
            source_type="titles_csv",
            file_name=file_name,
            status="running",
            total_rows=0,
            success_rows=0,
            failed_rows=0,
            report_json=None,
        )
        self.session.commit()
        self.session.refresh(job)

        report = []
        success_rows = 0
        failed_rows = 0
        total_rows = 0

        text = self._decode_csv(content)
        reader = csv.DictReader(io.StringIO(text))

        required = {"type", "title"}
        if not reader.fieldnames or not required.issubset(set(reader.fieldnames)):
            raise ValidationError("CSV titles import requires columns: type,title")

        for index, row in enumerate(reader, start=2):
            total_rows += 1
            payload = {
                "type": (row.get("type") or "").strip(),
                "title": (row.get("title") or "").strip(),
                "original_title": (row.get("original_title") or "").strip() or None,
                "description": (row.get("description") or "").strip() or None,
                "year": self._to_int(row.get("year")),
                "status": (row.get("status") or "draft").strip(),
            }
            try:
                self.media.create_title(admin_id, payload)
                success_rows += 1
            except Exception as exc:
                self.session.rollback()
                failed_rows += 1
                report.append({"row": index, "error": str(exc), "payload": payload})

        job = self.jobs.update(
            job,
            status="completed" if failed_rows == 0 else "completed_with_errors",
            total_rows=total_rows,
            success_rows=success_rows,
            failed_rows=failed_rows,
            report_json=json.dumps(report, ensure_ascii=False),
        )
        self.session.commit()
        self.session.refresh(job)
        return job

    def import_codes_csv(self, admin_id: int, file_name: str, content: bytes):
        job = self.jobs.create(
            admin_id=admin_id,
            source_type="codes_csv",
            file_name=file_name,
            status="running",
            total_rows=0,
            success_rows=0,
            failed_rows=0,
            report_json=None,
        )
        self.session.commit()
        self.session.refresh(job)

        report = []
        success_rows = 0
        failed_rows = 0
        total_rows = 0

        text = self._decode_csv(content)
        reader = csv.DictReader(io.StringIO(text))

        required = {"code"}
        if not reader.fieldnames or not required.issubset(set(reader.fieldnames)):
            raise ValidationError("CSV codes import requires column: code")

        for index, row in enumerate(reader, start=2):
            total_rows += 1
            payload = {
                "code": (row.get("code") or "").strip(),
                "title_id": self._to_int(row.get("title_id")),
                "season_id": self._to_int(row.get("season_id")),
                "episode_id": self._to_int(row.get("episode_id")),
                "status": (row.get("status") or "active").strip(),
            }
            try:
                self.codes.create_code(admin_id, payload)
                success_rows += 1
            except Exception as exc:
                self.session.rollback()
                failed_rows += 1
                report.append({"row": index, "error": str(exc), "payload": payload})

        job = self.jobs.update(
            job,
            status="completed" if failed_rows == 0 else "completed_with_errors",
            total_rows=total_rows,
            success_rows=success_rows,
            failed_rows=failed_rows,
            report_json=json.dumps(report, ensure_ascii=False),
        )
        self.session.commit()
        self.session.refresh(job)
        return job

    def _render_csv(self, rows: list[dict]) -> str:
        output = io.StringIO()
        fieldnames = list(rows[0].keys()) if rows else []
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        if fieldnames:
            writer.writeheader()
            writer.writerows(rows)
        return output.getvalue()

    def _decode_csv(self, content: bytes) -> str:
        for encoding in ("utf-8", "utf-8-sig", "cp1251"):
            try:
                return content.decode(encoding)
            except UnicodeDecodeError:
                continue
        raise ValidationError("Cannot decode CSV file")

    def _to_int(self, value):
        value = (value or "").strip()
        if not value:
            return None
        return int(value)
