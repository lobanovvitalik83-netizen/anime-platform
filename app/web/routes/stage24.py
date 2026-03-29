from datetime import datetime
import io
import zipfile

from fastapi import APIRouter, Body, Depends, File, Request, UploadFile
from fastapi.responses import JSONResponse, Response, RedirectResponse
from sqlalchemy.orm import Session

from app.core.database import get_db_session
from app.repositories.admin_repository import AdminRepository
from app.services.analytics_service import AnalyticsService
from app.services.auth_service import AuthService
from app.services.chat_service import ChatService
from app.services.import_export_service import ImportExportService
from app.services.media_card_service import MediaCardService
from app.services.permission_service import ALL_PERMISSIONS, PERMISSION_LABELS, PermissionService
from app.services.report_service import ReportService
from app.services.site_setting_service import SiteSettingService
from app.services.audit_service import AuditService
from app.repositories.audit_log_repository import AuditLogRepository
from app.web.auth import get_current_admin_from_request, redirect_to_login
from app.web.templates import templates

router = APIRouter(include_in_schema=False)

def render_template(name: str, request: Request, **context):
    return templates.TemplateResponse(name, {"request": request, **context})

def require_auth(request: Request, db: Session, permission: str | None = None):
    admin = get_current_admin_from_request(request, db)
    if not admin:
        return None, redirect_to_login()
    if permission and not PermissionService().has_permission(admin, permission) and admin.role != "superadmin":
        return None, render_template("forbidden.html", request, page_title="Доступ запрещён", current_admin=admin, error="Недостаточно прав.")
    return admin, None

@router.get("/admin/chats-live")
def chats_live_index(request: Request, db: Session = Depends(get_db_session), q: str = ""):
    current_admin, redirect = require_auth(request, db, permission="messages_manage")
    if redirect:
        return redirect
    service = ChatService(db)
    chats = service.list_chats_for_admin(current_admin)
    search = (q or "").strip().lower()
    if search:
        chats = [item for item in chats if search in item.title.lower()]
    return render_template("chat_live.html", request, page_title="Сообщения", current_admin=current_admin, chats=chats, selected_chat=None, messages_enabled=service.messages_enabled(), q=q, error=None)

@router.get("/admin/chats-live/{chat_id}")
def chats_live_room(chat_id: int, request: Request, db: Session = Depends(get_db_session), q: str = ""):
    current_admin, redirect = require_auth(request, db, permission="messages_manage")
    if redirect:
        return redirect
    service = ChatService(db)
    chats = service.list_chats_for_admin(current_admin)
    selected = service.get_chat_for_admin(current_admin, chat_id)
    search = (q or "").strip().lower()
    if search:
        chats = [item for item in chats if search in item.title.lower()]
    return render_template("chat_live.html", request, page_title="Сообщения", current_admin=current_admin, chats=chats, selected_chat=selected, messages_enabled=service.messages_enabled(), q=q, error=None)

@router.get("/admin/chats-live/{chat_id}/messages.json")
def chats_live_messages(chat_id: int, request: Request, db: Session = Depends(get_db_session), after_id: int = 0):
    current_admin, redirect = require_auth(request, db, permission="messages_manage")
    if redirect:
        return JSONResponse({"items": []}, status_code=403)
    items = ChatService(db).list_messages_after(current_admin, chat_id, after_id=after_id)
    return JSONResponse({"items": items})

@router.post("/admin/chats-live/{chat_id}/send.json")
def chats_live_send(chat_id: int, request: Request, db: Session = Depends(get_db_session), payload: dict = Body(default={})):
    current_admin, redirect = require_auth(request, db, permission="messages_manage")
    if redirect:
        return JSONResponse({"ok": False}, status_code=403)
    content = str(payload.get("content", "")).strip()
    try:
        message = ChatService(db).post_message(current_admin, chat_id, content)
        return JSONResponse({"ok": True, "id": message.id})
    except Exception as exc:
        db.rollback()
        return JSONResponse({"ok": False, "error": str(exc)}, status_code=400)

@router.get("/admin/reports")
def reports_page(request: Request, db: Session = Depends(get_db_session), status: str = ""):
    current_admin, redirect = require_auth(request, db, permission="reports_view")
    if redirect:
        return redirect
    tickets = ReportService(db).list_tickets()
    if status:
        tickets = [t for t in tickets if t.status == status]
    return render_template("reports_list.html", request, page_title="Репорты", current_admin=current_admin, tickets=tickets, error=None)

@router.get("/admin/reports/{ticket_id}")
def report_detail(ticket_id: int, request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = require_auth(request, db, permission="reports_view")
    if redirect:
        return redirect
    ticket = ReportService(db).get_ticket(ticket_id)
    return render_template("report_detail.html", request, page_title=f"Репорт #{ticket_id}", current_admin=current_admin, ticket=ticket, error=None, success=None)

@router.post("/admin/reports/{ticket_id}/reply")
async def report_reply(ticket_id: int, request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = require_auth(request, db, permission="reports_reply")
    if redirect:
        return redirect
    form = await request.form()
    body = str(form.get("body", "")).strip()
    service = ReportService(db)
    try:
        ticket = await service.reply_from_admin(current_admin, ticket_id, body)
        return render_template("report_detail.html", request, page_title=f"Репорт #{ticket_id}", current_admin=current_admin, ticket=ticket, error=None, success="Ответ отправлен в Telegram.")
    except Exception as exc:
        db.rollback()
        ticket = service.get_ticket(ticket_id)
        return render_template("report_detail.html", request, page_title=f"Репорт #{ticket_id}", current_admin=current_admin, ticket=ticket, error=str(exc), success=None)

@router.post("/admin/reports/{ticket_id}/close")
def report_close(ticket_id: int, request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = require_auth(request, db, permission="reports_reply")
    if redirect:
        return redirect
    ReportService(db).close_ticket(current_admin, ticket_id)
    return RedirectResponse(url=f"/admin/reports/{ticket_id}", status_code=303)

@router.get("/admin/editor-tools")
def editor_tools_page(request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = require_auth(request, db, permission="editor_tools")
    if redirect:
        return redirect
    recent_cards = MediaCardService(db).list_cards()[:10]
    return render_template("editor_tools.html", request, page_title="Инструменты редактора", current_admin=current_admin, recent_cards=recent_cards)

@router.get("/admin/settings/advanced")
def settings_advanced(request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = require_auth(request, db, permission="settings_manage")
    if redirect:
        return redirect
    settings_service = SiteSettingService(db)
    return render_template("settings_advanced.html", request, page_title="Настройки+", current_admin=current_admin, messages_enabled=settings_service.is_messages_enabled(), reports_enabled=settings_service.is_reports_enabled(), maintenance_mode=settings_service.is_maintenance_mode(), site_title=settings_service.get_str("site_title", "Media Bridge"), logo_url=settings_service.get_str("logo_url", ""), help_contact=settings_service.get_str("telegram_help_contact", ""), error=None, success=None)

@router.post("/admin/settings/advanced")
async def settings_advanced_submit(request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = require_auth(request, db, permission="settings_manage")
    if redirect:
        return redirect
    form = await request.form()
    settings_service = SiteSettingService(db)
    settings_service.set_messages_enabled(form.get("messages_enabled") == "on")
    settings_service.set_reports_enabled(form.get("reports_enabled") == "on")
    settings_service.set_maintenance_mode(form.get("maintenance_mode") == "on")
    settings_service.set_str("site_title", str(form.get("site_title", "")).strip() or "Media Bridge")
    settings_service.set_str("logo_url", str(form.get("logo_url", "")).strip())
    settings_service.set_str("telegram_help_contact", str(form.get("help_contact", "")).strip())
    return render_template("settings_advanced.html", request, page_title="Настройки+", current_admin=current_admin, messages_enabled=settings_service.is_messages_enabled(), reports_enabled=settings_service.is_reports_enabled(), maintenance_mode=settings_service.is_maintenance_mode(), site_title=settings_service.get_str("site_title", "Media Bridge"), logo_url=settings_service.get_str("logo_url", ""), help_contact=settings_service.get_str("telegram_help_contact", ""), error=None, success="Настройки сохранены.")

@router.get("/admin/analytics/advanced")
def analytics_advanced(request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = require_auth(request, db, permission="analytics_view")
    if redirect:
        return redirect
    service = AnalyticsService(db)
    return render_template("analytics_advanced.html", request, page_title="Аналитика+", current_admin=current_admin, summary=service.get_summary(), staff_activity=service.get_staff_activity(), top_found=service.get_top_codes(kind="found", limit=10), top_not_found=service.get_top_codes(kind="not_found", limit=10))

@router.get("/admin/admin-actions")
def admin_actions_page(
    request: Request,
    db: Session = Depends(get_db_session),
    admin_id: int | None = None,
    action: str = "",
    date_from: str = "",
    date_to: str = "",
    sort: str = "desc",
):
    current_admin, redirect = require_auth(request, db, permission="admin_actions_view")
    if redirect:
        return redirect
    repo = AuditLogRepository(db)
    actions = repo.list_filtered(admin_id=admin_id, action=action, date_from=date_from, date_to=date_to, sort=sort)
    admins = AdminRepository(db).list_all()
    return render_template(
        "admin_actions.html",
        request,
        page_title="Действия админов",
        current_admin=current_admin,
        rows=actions,
        admins=admins,
        action_options=repo.list_actions(),
        filters={"admin_id": admin_id, "action": action, "date_from": date_from, "date_to": date_to, "sort": sort},
    )

@router.get("/admin/import-export/advanced")
def import_export_advanced(request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = require_auth(request, db, permission="import_export")
    if redirect:
        return redirect
    return render_template("import_export_advanced.html", request, page_title="Импорт / экспорт+", current_admin=current_admin)

@router.get("/admin/export/everything.zip")
def export_everything_zip(request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = require_auth(request, db, permission="import_export")
    if redirect:
        return redirect
    payload = ImportExportService(db).export_everything_zip()
    return Response(content=payload, media_type="application/zip", headers={"Content-Disposition": "attachment; filename=everything_export.zip"})

@router.get("/admin/export/users.csv")
def export_users_csv(request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = require_auth(request, db, permission="import_export")
    if redirect:
        return redirect
    return Response(content=ImportExportService(db).export_users_csv(), media_type="text/csv; charset=utf-8", headers={"Content-Disposition": "attachment; filename=users.csv"})

@router.get("/admin/export/reports.csv")
def export_reports_csv(request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = require_auth(request, db, permission="import_export")
    if redirect:
        return redirect
    return Response(content=ImportExportService(db).export_reports_csv(), media_type="text/csv; charset=utf-8", headers={"Content-Disposition": "attachment; filename=reports.csv"})

@router.get("/admin/export/analytics.csv")
def export_analytics_csv(request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = require_auth(request, db, permission="analytics_export")
    if redirect:
        return redirect
    return Response(content=ImportExportService(db).export_analytics_csv(), media_type="text/csv; charset=utf-8", headers={"Content-Disposition": "attachment; filename=analytics.csv"})

@router.get("/admin/templates/titles.csv")
def template_titles_csv(request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = require_auth(request, db, permission="import_export")
    if redirect:
        return redirect
    return Response(content=ImportExportService(db).template_titles_csv(), media_type="text/csv; charset=utf-8", headers={"Content-Disposition": "attachment; filename=titles_template.csv"})

@router.get("/admin/templates/codes.csv")
def template_codes_csv(request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = require_auth(request, db, permission="import_export")
    if redirect:
        return redirect
    return Response(content=ImportExportService(db).template_codes_csv(), media_type="text/csv; charset=utf-8", headers={"Content-Disposition": "attachment; filename=codes_template.csv"})

@router.get("/admin/team/{admin_id}/permissions")
def user_permissions_page(admin_id: int, request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = require_auth(request, db, permission="team_manage")
    if redirect:
        return redirect
    service = AuthService(db)
    target = service.get_manageable_admin(current_admin, admin_id)
    selected = PermissionService().parse_permissions(target.extra_permissions)
    return render_template("permissions_form.html", request, page_title="Разрешения", current_admin=current_admin, target=target, all_permissions=ALL_PERMISSIONS, permission_labels=PERMISSION_LABELS, selected_permissions=selected, error=None, success=None)

@router.post("/admin/team/{admin_id}/permissions")
async def user_permissions_submit(admin_id: int, request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = require_auth(request, db, permission="team_manage")
    if redirect:
        return redirect
    service = AuthService(db)
    target = service.get_manageable_admin(current_admin, admin_id)
    form = await request.form()
    selected = [str(v) for v in form.getlist("extra_permissions")]
    admins_repo = AdminRepository(db)
    target = admins_repo.update(target, extra_permissions=PermissionService().serialize_permissions(selected))
    db.commit()
    return render_template("permissions_form.html", request, page_title="Разрешения", current_admin=current_admin, target=target, all_permissions=ALL_PERMISSIONS, permission_labels=PERMISSION_LABELS, selected_permissions=selected, error=None, success="Разрешения обновлены.")
