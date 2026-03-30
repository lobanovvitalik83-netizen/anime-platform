from fastapi import APIRouter, Depends, File, Request, Response, UploadFile
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db_session
from app.services.achievement_service import AchievementService
from app.services.auth_service import AuthService
from app.services.import_export_service import ImportExportService
from app.services.notification_service import NotificationService
from app.services.permission_service import PERMISSION_LABELS, PermissionService
from app.services.site_setting_service import SiteSettingService
from app.web.auth import get_current_admin_from_request, has_required_role, redirect_to, redirect_to_login
from app.web.templates import templates

router = APIRouter(include_in_schema=False)
permissions_service = PermissionService()


def render_template(name: str, request: Request, **context):
    current_admin = context.get("current_admin")
    current_permissions = []
    unread_notifications = 0
    if current_admin:
        current_permissions = sorted(permissions_service.get_permissions(current_admin))
        try:
            unread_notifications = NotificationService(context.get("db") or request.state.db).unread_count(current_admin)
        except Exception:
            unread_notifications = 0
    merged = {
        "request": request,
        "current_permissions": current_permissions,
        "permission_labels": PERMISSION_LABELS,
        "unread_notifications": unread_notifications,
        **context,
    }
    return templates.TemplateResponse(name, merged)


def require_admin(request: Request, db: Session, min_role: str = "editor"):
    request.state.db = db
    admin = get_current_admin_from_request(request, db)
    if not admin:
        return None, redirect_to_login()
    if not has_required_role(admin, min_role):
        return None, render_template("forbidden.html", request, page_title="Доступ запрещён", current_admin=admin, db=db, error="Недостаточно прав.")
    return admin, None


def _has_permission(admin, code: str) -> bool:
    return admin.role == "superadmin" or permissions_service.has_permission(admin, code)


@router.get("/admin/achievements")
def achievements_page(request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = require_admin(request, db)
    if redirect:
        return redirect
    if not _has_permission(current_admin, "achievement_manage"):
        return render_template("forbidden.html", request, page_title="Ачивки", current_admin=current_admin, db=db, error="Нет доступа к управлению ачивками.")
    items = AchievementService(db).list_achievements()
    return render_template("achievements_list.html", request, page_title="Ачивки", current_admin=current_admin, db=db, achievements=items)


@router.get("/admin/achievements/new")
def achievement_new_page(request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = require_admin(request, db)
    if redirect:
        return redirect
    if not _has_permission(current_admin, "achievement_manage"):
        return render_template("forbidden.html", request, page_title="Ачивки", current_admin=current_admin, db=db, error="Нет доступа к управлению ачивками.")
    return render_template("achievement_form.html", request, page_title="Создать ачивку", current_admin=current_admin, db=db, values={"is_active": True}, action_url="/admin/achievements/new", submit_label="Создать ачивку", error=None, success=None)


@router.post("/admin/achievements/new")
async def achievement_new_submit(request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = require_admin(request, db)
    if redirect:
        return redirect
    if not _has_permission(current_admin, "achievement_manage"):
        return render_template("forbidden.html", request, page_title="Ачивки", current_admin=current_admin, db=db, error="Нет доступа к управлению ачивками.")
    form = await request.form()
    values = {
        "title": str(form.get("title", "")).strip(),
        "slug": str(form.get("slug", "")).strip(),
        "description": str(form.get("description", "")).strip(),
        "icon_url": str(form.get("icon_url", "")).strip(),
        "is_active": form.get("is_active") == "on",
    }
    try:
        AchievementService(db).create_achievement(current_admin.id, values)
        return redirect_to("/admin/achievements")
    except Exception as exc:
        db.rollback()
        return render_template("achievement_form.html", request, page_title="Создать ачивку", current_admin=current_admin, db=db, values=values, action_url="/admin/achievements/new", submit_label="Создать ачивку", error=str(exc), success=None)


@router.get("/admin/achievements/{achievement_id}/edit")
def achievement_edit_page(achievement_id: int, request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = require_admin(request, db)
    if redirect:
        return redirect
    if not _has_permission(current_admin, "achievement_manage"):
        return render_template("forbidden.html", request, page_title="Ачивки", current_admin=current_admin, db=db, error="Нет доступа к управлению ачивками.")
    item = AchievementService(db).get_achievement(achievement_id)
    values = {"title": item.title, "slug": item.slug, "description": item.description or "", "icon_url": item.icon_url or "", "is_active": item.is_active}
    return render_template("achievement_form.html", request, page_title=f"Редактировать ачивку #{achievement_id}", current_admin=current_admin, db=db, values=values, action_url=f"/admin/achievements/{achievement_id}/edit", submit_label="Сохранить ачивку", error=None, success=None)


@router.post("/admin/achievements/{achievement_id}/edit")
async def achievement_edit_submit(achievement_id: int, request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = require_admin(request, db)
    if redirect:
        return redirect
    if not _has_permission(current_admin, "achievement_manage"):
        return render_template("forbidden.html", request, page_title="Ачивки", current_admin=current_admin, db=db, error="Нет доступа к управлению ачивками.")
    form = await request.form()
    values = {"title": str(form.get("title", "")).strip(), "slug": str(form.get("slug", "")).strip(), "description": str(form.get("description", "")).strip(), "icon_url": str(form.get("icon_url", "")).strip(), "is_active": form.get("is_active") == "on"}
    try:
        AchievementService(db).update_achievement(current_admin.id, achievement_id, values)
        return redirect_to("/admin/achievements")
    except Exception as exc:
        db.rollback()
        return render_template("achievement_form.html", request, page_title=f"Редактировать ачивку #{achievement_id}", current_admin=current_admin, db=db, values=values, action_url=f"/admin/achievements/{achievement_id}/edit", submit_label="Сохранить ачивку", error=str(exc), success=None)


@router.post("/admin/achievements/{achievement_id}/delete")
def achievement_delete(achievement_id: int, request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = require_admin(request, db)
    if redirect:
        return redirect
    if not _has_permission(current_admin, "achievement_manage"):
        return render_template("forbidden.html", request, page_title="Ачивки", current_admin=current_admin, db=db, error="Нет доступа к управлению ачивками.")
    try:
        AchievementService(db).delete_achievement(current_admin.id, achievement_id)
        return redirect_to("/admin/achievements")
    except Exception as exc:
        db.rollback()
        items = AchievementService(db).list_achievements()
        return render_template("achievements_list.html", request, page_title="Ачивки", current_admin=current_admin, db=db, achievements=items, error=str(exc))


@router.get("/admin/people/{admin_id}/achievements/grant")
def grant_achievement_page(admin_id: int, request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = require_admin(request, db)
    if redirect:
        return redirect
    if not _has_permission(current_admin, "achievement_manage"):
        return render_template("forbidden.html", request, page_title="Ачивки", current_admin=current_admin, db=db, error="Нет доступа к управлению ачивками.")
    person = AuthService(db).get_admin(admin_id)
    service = AchievementService(db)
    return render_template("grant_achievement.html", request, page_title="Выдать ачивку", current_admin=current_admin, db=db, person=person, achievements=service.list_achievements(active_only=True), grants=service.list_admin_achievements(admin_id), error=None, success=None)


@router.post("/admin/people/{admin_id}/achievements/grant")
async def grant_achievement_submit(admin_id: int, request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = require_admin(request, db)
    if redirect:
        return redirect
    if not _has_permission(current_admin, "achievement_manage"):
        return render_template("forbidden.html", request, page_title="Ачивки", current_admin=current_admin, db=db, error="Нет доступа к управлению ачивками.")
    form = await request.form()
    achievement_id = int(form.get("achievement_id"))
    reason = str(form.get("grant_reason", "")).strip()
    service = AchievementService(db)
    person = AuthService(db).get_admin(admin_id)
    try:
        service.grant_achievement(current_admin.id, admin_id, achievement_id, reason)
        return redirect_to(f"/admin/people/{admin_id}/achievements/grant")
    except Exception as exc:
        db.rollback()
        return render_template("grant_achievement.html", request, page_title="Выдать ачивку", current_admin=current_admin, db=db, person=person, achievements=service.list_achievements(active_only=True), grants=service.list_admin_achievements(admin_id), error=str(exc), success=None)


@router.post("/admin/people/{admin_id}/achievements/{grant_id}/revoke")
def revoke_achievement(admin_id: int, grant_id: int, request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = require_admin(request, db)
    if redirect:
        return redirect
    if not _has_permission(current_admin, "achievement_manage"):
        return render_template("forbidden.html", request, page_title="Ачивки", current_admin=current_admin, db=db, error="Нет доступа к управлению ачивками.")
    try:
        AchievementService(db).revoke_grant(current_admin.id, grant_id)
        return redirect_to(f"/admin/people/{admin_id}/achievements/grant")
    except Exception as exc:
        db.rollback()
        person = AuthService(db).get_admin(admin_id)
        service = AchievementService(db)
        return render_template("grant_achievement.html", request, page_title="Выдать ачивку", current_admin=current_admin, db=db, person=person, achievements=service.list_achievements(active_only=True), grants=service.list_admin_achievements(admin_id), error=str(exc), success=None)


@router.get("/admin/settings/site")
def site_settings_page(request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = require_admin(request, db, min_role="admin")
    if redirect:
        return redirect
    if not _has_permission(current_admin, "settings_manage"):
        return render_template("forbidden.html", request, page_title="Настройки", current_admin=current_admin, db=db, error="Нет доступа к настройкам.")
    service = SiteSettingService(db)
    return render_template(
        "settings_site.html",
        request,
        page_title="Настройки сайта",
        current_admin=current_admin,
        db=db,
        messages_enabled=service.is_messages_enabled(),
        reports_enabled=service.is_reports_enabled(),
        site_title=service.get_str(service.SITE_TITLE_KEY, settings.app_name),
        help_contact=settings.telegram_help_contact_text,
        upload_backend_label=settings.media_storage_backend_label,
        yandex_disk_base_path=settings.yandex_disk_base_path,
        error=None,
        success=None,
    )


@router.post("/admin/settings/site")
async def site_settings_submit(request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = require_admin(request, db, min_role="admin")
    if redirect:
        return redirect
    if not _has_permission(current_admin, "settings_manage"):
        return render_template("forbidden.html", request, page_title="Настройки", current_admin=current_admin, db=db, error="Нет доступа к настройкам.")
    form = await request.form()
    service = SiteSettingService(db)
    service.set_messages_enabled(form.get("messages_enabled") == "on")
    service.set_reports_enabled(form.get("reports_enabled") == "on")
    service.set_str(service.SITE_TITLE_KEY, str(form.get("site_title", "")).strip() or settings.app_name)
    service.set_str("telegram_help_contact", str(form.get("help_contact", "")).strip())
    return render_template(
        "settings_site.html",
        request,
        page_title="Настройки сайта",
        current_admin=current_admin,
        db=db,
        messages_enabled=service.is_messages_enabled(),
        reports_enabled=service.is_reports_enabled(),
        site_title=service.get_str(service.SITE_TITLE_KEY, settings.app_name),
        help_contact=service.get_str("telegram_help_contact", settings.telegram_help_contact_text),
        upload_backend_label=settings.media_storage_backend_label,
        yandex_disk_base_path=settings.yandex_disk_base_path,
        error=None,
        success="Настройки сохранены.",
    )


@router.get("/admin/export/cards.csv")
def export_cards_csv(request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = require_admin(request, db, min_role="admin")
    if redirect:
        return redirect
    return Response(content=ImportExportService(db).export_cards_csv(), media_type="text/csv; charset=utf-8", headers={"Content-Disposition": "attachment; filename=cards.csv"})


@router.get("/admin/templates/cards.csv")
def template_cards_csv(request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = require_admin(request, db, min_role="admin")
    if redirect:
        return redirect
    return Response(content=ImportExportService(db).template_cards_csv(), media_type="text/csv; charset=utf-8", headers={"Content-Disposition": "attachment; filename=cards_template.csv"})


@router.post("/admin/import/cards/csv")
async def import_cards_csv(request: Request, file: UploadFile = File(...), db: Session = Depends(get_db_session)):
    current_admin, redirect = require_admin(request, db, min_role="admin")
    if redirect:
        return redirect
    try:
        content = await file.read()
        job = ImportExportService(db).import_cards_csv(current_admin.id, file.filename or "cards.csv", content)
        return render_template("import_export.html", request, page_title="Импорт / экспорт", current_admin=current_admin, db=db, error=None, success=f"Импорт cards завершён. Успешно: {job.success_rows}, ошибок: {job.failed_rows}.")
    except Exception as exc:
        db.rollback()
        return render_template("import_export.html", request, page_title="Импорт / экспорт", current_admin=current_admin, db=db, error=str(exc), success=None)


@router.get("/admin/export/everything.zip")
def export_everything_zip(request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = require_admin(request, db, min_role="admin")
    if redirect:
        return redirect
    content = ImportExportService(db).export_everything_zip()
    return Response(content=content, media_type="application/zip", headers={"Content-Disposition": "attachment; filename=everything.zip"})
