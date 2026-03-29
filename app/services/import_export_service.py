import csv
import io
import json
import zipfile

from sqlalchemy.orm import Session

from app.core.exceptions import ValidationError
from app.repositories.admin_repository import AdminRepository
from app.repositories.import_job_repository import ImportJobRepository
from app.repositories.report_repository import ReportRepository
from app.services.analytics_service import AnalyticsService
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
        self.admins = AdminRepository(session)
        self.reports = ReportRepository(session)
        self.analytics = AnalyticsService(session)

    def list_jobs(self):
        return self.jobs.list_all()

    def export_titles_csv(self) -> str:
        rows = []
        for item in self.media.list_titles():
            rows.append({"id": item.id, "type": item.type, "title": item.title, "status": item.status, "created_at": item.created_at.isoformat() if item.created_at else ""})
        return self._render_csv(rows)

    def export_seasons_csv(self) -> str:
        rows = []
        for item in self.media.list_seasons():
            rows.append({"id": item.id, "title_id": item.title_id, "season_number": item.season_number, "created_at": item.created_at.isoformat() if item.created_at else ""})
        return self._render_csv(rows)

    def export_episodes_csv(self) -> str:
        rows = []
        for item in self.media.list_episodes():
            rows.append({"id": item.id, "title_id": item.title_id, "season_id": item.season_id or "", "episode_number": item.episode_number, "status": item.status, "created_at": item.created_at.isoformat() if item.created_at else ""})
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
                "storage_provider": getattr(item, "storage_provider", "") or "",
                "storage_object_key": getattr(item, "storage_object_key", "") or "",
                "source_label": getattr(item, "source_label", "") or "",
                "source_url": getattr(item, "source_url", "") or "",
                "external_url": item.external_url or "",
                "mime_type": item.mime_type or "",
                "is_primary": item.is_primary,
                "created_at": item.created_at.isoformat() if item.created_at else "",
            })
        return self._render_csv(rows)

    def export_codes_csv(self) -> str:
        rows = []
        for item in self.codes.list_codes():
            rows.append({"id": item.id, "code": item.code, "title_id": item.title_id or "", "season_id": item.season_id or "", "episode_id": item.episode_id or "", "status": item.status, "created_at": item.created_at.isoformat() if item.created_at else ""})
        return self._render_csv(rows)

    def export_users_csv(self) -> str:
        rows = []
        for item in self.admins.list_all():
            rows.append({"id": item.id, "username": item.username, "role": item.role, "is_active": item.is_active, "full_name": item.full_name or "", "position": item.position or "", "extra_permissions": item.extra_permissions or "", "created_at": item.created_at.isoformat() if item.created_at else ""})
        return self._render_csv(rows)

    def export_reports_csv(self) -> str:
        rows = []
        for item in self.reports.list_tickets():
            rows.append({"id": item.id, "status": item.status, "tg_user_id": item.tg_user_id, "tg_username": item.tg_username or "", "tg_full_name": item.tg_full_name or "", "assigned_admin_id": item.assigned_admin_id or "", "last_message_preview": item.last_message_preview or "", "created_at": item.created_at.isoformat() if item.created_at else "", "updated_at": item.updated_at.isoformat() if item.updated_at else ""})
        return self._render_csv(rows)

    def export_analytics_csv(self) -> str:
        return self._render_csv(self.analytics.export_summary_rows())

    def export_everything_zip(self) -> bytes:
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            files = {
                "titles.csv": self.export_titles_csv(),
                "seasons.csv": self.export_seasons_csv(),
                "episodes.csv": self.export_episodes_csv(),
                "assets.csv": self.export_assets_csv(),
                "codes.csv": self.export_codes_csv(),
                "users.csv": self.export_users_csv(),
                "reports.csv": self.export_reports_csv(),
                "analytics.csv": self.export_analytics_csv(),
            }
            for name, content in files.items():
                zf.writestr(name, content)
        return buffer.getvalue()

    def template_titles_csv(self) -> str:
        return "type,title,status\nanime,Naruto,draft\n"

    def template_codes_csv(self) -> str:
        return "code,title_id,season_id,episode_id,status\n12345678,1,1,1,active\n"

    def import_titles_csv(self, admin_id: int, filename: str, content: bytes):
        decoded = self._decode(content)
        reader = csv.DictReader(io.StringIO(decoded))
        required_columns = {"type", "title"}
        missing = required_columns - set(reader.fieldnames or [])
        if missing:
            raise ValidationError(f"Missing CSV columns: {', '.join(sorted(missing))}")
        success_rows = 0
        failed_rows = 0
        errors: list[dict] = []
        for index, row in enumerate(reader, start=2):
            try:
                self.media.create_title({"type": (row.get("type") or "").strip(), "title": (row.get("title") or "").strip(), "original_title": None, "description": None, "year": None, "status": (row.get("status") or "draft").strip()})
                success_rows += 1
            except Exception as exc:
                failed_rows += 1
                errors.append({"row": index, "error": str(exc), "data": row})
        job = self.jobs.create_job(admin_id=admin_id, job_type="import_titles_csv", file_name=filename, status="completed" if failed_rows == 0 else "completed_with_errors", success_rows=success_rows, failed_rows=failed_rows, payload_json=json.dumps(errors[:100], ensure_ascii=False))
        self.session.commit()
        return job

    def import_codes_csv(self, admin_id: int, filename: str, content: bytes):
        decoded = self._decode(content)
        reader = csv.DictReader(io.StringIO(decoded))
        required_columns = {"code"}
        missing = required_columns - set(reader.fieldnames or [])
        if missing:
            raise ValidationError(f"Missing CSV columns: {', '.join(sorted(missing))}")
        success_rows = 0
        failed_rows = 0
        errors: list[dict] = []
        for index, row in enumerate(reader, start=2):
            try:
                self.codes.create_code(admin_id, {"code": (row.get("code") or "").strip(), "title_id": int(row["title_id"]) if (row.get("title_id") or "").strip() else None, "season_id": int(row["season_id"]) if (row.get("season_id") or "").strip() else None, "episode_id": int(row["episode_id"]) if (row.get("episode_id") or "").strip() else None, "status": (row.get("status") or "active").strip()})
                success_rows += 1
            except Exception as exc:
                failed_rows += 1
                errors.append({"row": index, "error": str(exc), "data": row})
        job = self.jobs.create_job(admin_id=admin_id, job_type="import_codes_csv", file_name=filename, status="completed" if failed_rows == 0 else "completed_with_errors", success_rows=success_rows, failed_rows=failed_rows, payload_json=json.dumps(errors[:100], ensure_ascii=False))
        self.session.commit()
        return job

    def _decode(self, content: bytes) -> str:
        for encoding in ("utf-8-sig", "utf-8", "cp1251"):
            try:
                return content.decode(encoding)
            except UnicodeDecodeError:
                continue
        raise ValidationError("Не удалось прочитать CSV. Используй UTF-8 или CP1251.")

    def _render_csv(self, rows: list[dict]) -> str:
        if not rows:
            return ""
        buffer = io.StringIO()
        writer = csv.DictWriter(buffer, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
        return buffer.getvalue()
