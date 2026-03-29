from collections import Counter
from dataclasses import dataclass
from typing import Any

from sqlalchemy.orm import Session

from app.models.access_code import AccessCode
from app.models.media_asset import MediaAsset
from app.repositories.access_code_repository import AccessCodeRepository
from app.repositories.admin_repository import AdminRepository
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.chat_repository import ChatRepository
from app.repositories.code_lookup_event_repository import CodeLookupEventRepository
from app.repositories.media_asset_repository import MediaAssetRepository
from app.repositories.report_repository import ReportRepository
from app.services.media_service import MediaService


@dataclass
class CodeAnalyticsRow:
    code_value: str
    total_attempts: int
    found_attempts: int
    not_found_attempts: int
    last_seen: Any
    access_code_exists: bool
    access_code_status: str | None
    title_name: str | None


class AnalyticsService:
    def __init__(self, session: Session):
        self.session = session
        self.events = CodeLookupEventRepository(session)
        self.audit_logs = AuditLogRepository(session)
        self.access_codes = AccessCodeRepository(session)
        self.media = MediaService(session)
        self.assets = MediaAssetRepository(session)
        self.admins = AdminRepository(session)
        self.chats = ChatRepository(session)
        self.reports = ReportRepository(session)

    def record_lookup_attempt(self, *, code_value: str, is_found: bool, source: str, access_code: AccessCode | None = None, error_text: str | None = None) -> None:
        self.events.create(
            code_value=code_value,
            access_code_id=access_code.id if access_code else None,
            title_id=access_code.title_id if access_code else None,
            season_id=access_code.season_id if access_code else None,
            episode_id=access_code.episode_id if access_code else None,
            is_found=is_found,
            source=source,
            error_text=error_text,
        )
        self.session.commit()

    def get_summary(self) -> dict:
        items = self.events.list_all()
        reports = self.reports.list_tickets()
        chats = self.chats.list_chats()
        admins = self.admins.list_all()
        unique_codes = {item.code_value for item in items}
        return {
            "total_attempts": len(items),
            "found_attempts": sum(1 for item in items if item.is_found),
            "not_found_attempts": sum(1 for item in items if not item.is_found),
            "unique_codes": len(unique_codes),
            "chats_total": len(chats),
            "reports_total": len(reports),
            "reports_open": sum(1 for item in reports if item.status != "closed"),
            "admins_total": len(admins),
        }

    def list_recent_lookup_events(self, limit: int = 150):
        return self.events.list_recent(limit=limit)

    def list_recent_audit_logs(self, limit: int = 150):
        return self.audit_logs.list_recent(limit=limit)

    def get_staff_activity(self) -> list[dict]:
        counter = Counter()
        for log in self.audit_logs.list_recent(limit=2000):
            counter[log.admin_id] += 1
        rows = []
        for admin in self.admins.list_all():
            rows.append({
                "admin_id": admin.id,
                "username": admin.username,
                "role": admin.role,
                "actions_count": counter.get(admin.id, 0),
            })
        rows.sort(key=lambda x: x["actions_count"], reverse=True)
        return rows

    def list_code_rows(self, q: str = "", outcome: str = "") -> list[CodeAnalyticsRow]:
        items = self.events.list_all()
        grouped: dict[str, list] = {}
        for item in items:
            grouped.setdefault(item.code_value, []).append(item)

        rows: list[CodeAnalyticsRow] = []
        search = (q or "").strip().lower()
        normalized_outcome = (outcome or "").strip().lower()

        for code_value, events in grouped.items():
            events_sorted = sorted(events, key=lambda item: item.created_at, reverse=True)
            total_attempts = len(events_sorted)
            found_attempts = sum(1 for item in events_sorted if item.is_found)
            not_found_attempts = total_attempts - found_attempts
            last_seen = events_sorted[0].created_at

            access_code = self.access_codes.get_by_code(code_value)
            title_name = None
            if access_code and access_code.title_id:
                try:
                    title_name = self.media.get_title(access_code.title_id).title
                except Exception:
                    title_name = None

            row = CodeAnalyticsRow(code_value, total_attempts, found_attempts, not_found_attempts, last_seen, bool(access_code), access_code.status if access_code else None, title_name)

            haystack = " ".join([row.code_value, row.title_name or "", row.access_code_status or ""]).lower()
            if search and search not in haystack:
                continue
            if normalized_outcome == "found" and row.found_attempts <= 0:
                continue
            if normalized_outcome == "not_found" and row.not_found_attempts <= 0:
                continue
            rows.append(row)

        rows.sort(key=lambda item: item.last_seen, reverse=True)
        return rows

    def get_top_codes(self, *, kind: str = "found", limit: int = 10) -> list[CodeAnalyticsRow]:
        rows = self.list_code_rows()
        if kind == "found":
            rows = [row for row in rows if row.found_attempts > 0]
            rows.sort(key=lambda x: (x.found_attempts, x.total_attempts), reverse=True)
        else:
            rows = [row for row in rows if row.not_found_attempts > 0]
            rows.sort(key=lambda x: (x.not_found_attempts, x.total_attempts), reverse=True)
        return rows[:limit]

    def get_code_detail(self, code_value: str) -> dict:
        events = self.events.list_by_code_value(code_value)
        access_code = self.access_codes.get_by_code(code_value)
        card = self._resolve_card(access_code) if access_code else None
        return {
            "code_value": code_value,
            "events": events,
            "access_code": access_code,
            "card": card,
            "total_attempts": len(events),
            "found_attempts": sum(1 for item in events if item.is_found),
            "not_found_attempts": sum(1 for item in events if not item.is_found),
            "last_seen": events[0].created_at if events else None,
        }

    def export_summary_rows(self) -> list[dict]:
        rows = [{"metric": key, "value": value} for key, value in self.get_summary().items()]
        for row in self.get_staff_activity():
            rows.append({"metric": f"actions_{row['username']}", "value": row["actions_count"]})
        for row in self.get_top_codes(kind="found", limit=20):
            rows.append({"metric": f"top_found_{row.code_value}", "value": row.found_attempts})
        for row in self.get_top_codes(kind="not_found", limit=20):
            rows.append({"metric": f"top_not_found_{row.code_value}", "value": row.not_found_attempts})
        return rows


def get_code_status_summary(self) -> dict:
    codes = self.access_codes.list_all()
    return {
        "total_codes": len(codes),
        "active_codes": sum(1 for item in codes if item.status == "active"),
        "inactive_codes": sum(1 for item in codes if item.status == "inactive"),
        "archived_codes": sum(1 for item in codes if item.status == "archived"),
    }

def get_personal_activity(self, admin_id: int) -> dict:
    rows = self.audit_logs.list_filtered(admin_id=admin_id, limit=1000)
    return {
        "actions_count": len(rows),
        "recent_actions": rows[:15],
    }

    def _resolve_card(self, access_code: AccessCode | None) -> dict | None:
        if not access_code:
            return None
        title = season = episode = None
        if access_code.title_id:
            try: title = self.media.get_title(access_code.title_id)
            except Exception: title = None
        if access_code.season_id:
            try: season = self.media.get_season(access_code.season_id)
            except Exception: season = None
        if access_code.episode_id:
            try: episode = self.media.get_episode(access_code.episode_id)
            except Exception: episode = None
        if episode and not title:
            try: title = self.media.get_title(episode.title_id)
            except Exception: title = None
        if episode and not season and episode.season_id:
            try: season = self.media.get_season(episode.season_id)
            except Exception: season = None
        if season and not title:
            try: title = self.media.get_title(season.title_id)
            except Exception: title = None
        asset = self._pick_best_asset(title.id if title else None, season.id if season else None, episode.id if episode else None)
        return {
            "access_code_status": access_code.status,
            "title": title.title if title else None,
            "genre": title.type if title else None,
            "season_number": season.season_number if season else None,
            "episode_number": episode.episode_number if episode else None,
            "asset_type": asset.asset_type if asset else None,
            "storage_kind": asset.storage_kind if asset else None,
            "external_url": asset.external_url if asset else None,
        }

    def _pick_best_asset(self, title_id: int | None, season_id: int | None, episode_id: int | None) -> MediaAsset | None:
        candidates = self.assets.list_lookup_candidates(title_id=title_id, season_id=season_id, episode_id=episode_id)
        if not candidates:
            return None

        def scope_priority(asset: MediaAsset) -> int:
            if episode_id and asset.episode_id == episode_id:
                return 0
            if season_id and asset.season_id == season_id:
                return 1
            if title_id and asset.title_id == title_id:
                return 2
            return 3

        def primary_priority(asset: MediaAsset) -> int:
            return 0 if asset.is_primary else 1

        return sorted(candidates, key=lambda item: (scope_priority(item), primary_priority(item), -item.id))[0]
