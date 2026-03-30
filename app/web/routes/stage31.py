from fastapi import APIRouter, Depends, File, Request, UploadFile
from sqlalchemy.orm import Session
from starlette.responses import RedirectResponse

from app.core.database import get_db_session
from app.repositories.admin_repository import AdminRepository
from app.services.achievement_service import AchievementService
from app.services.notification_service import NotificationService
from app.services.permission_service import PermissionService
from app.web.auth import get_current_admin_from_request, redirect_to_login
from app.web.templates import templates

router = APIRouter(include_in_schema=False)


def render_template(name: str, request: Request, **context):
    current_admin = context.get("current_admin")
    if current_admin:
        context.setdefault("current_permissions", sorted(PermissionService().get_permissions(current_admin)))
    return templates.TemplateResponse(name, {"request": request, **context})


def require_auth(request: Request, db: Session, permission: str | None = None):
    admin = get_current_admin_from_request(request, db)
    if not admin:
        return None, redirect_to_login()
    if permission and admin.role != "superadmin" and not PermissionService().has_permission(admin, permission):
        return None, render_template("forbidden.html", request, page_title="Доступ запрещён", current_admin=admin, error="Недостаточно прав для этого раздела.")
    return admin, None


@router.get("/admin/forgot-password")
def forgot_password_page(request: Request):
    return render_template("forgot_password.html", request, page_title="Восстановление доступа", error=None, success=None)


@router.post("/admin/forgot-password")
async def forgot_password_submit(request: Request, db: Session = Depends(get_db_session)):
    form = await request.form()
    username = str(form.get("username", "")).strip()
    if not username:
        return render_template("forgot_password.html", request, page_title="Восстановление доступа", error="Укажи логин.", success=None)
    target = AdminRepository(db).get_by_username(username)
    if target:
        NotificationService(db).notify_by_permission(
            "team_manage",
            kind="password_reset_request",
            title=f"Запрос на сброс пароля для {target.username}",
            body=f"Пользователь {target.username} запросил восстановление доступа через форму входа.",
            link_url=f"/admin/team/{target.id}/edit",
        )
        db.commit()
    return render_template("forgot_password.html", request, page_title="Восстановление доступа", error=None, success="Запрос принят. Администратор увидит уведомление и сможет сбросить пароль.")

@router.get("/admin/achievements")
def achievements_page(request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = require_auth(request, db, permission="achievement_manage")
    if redirect:
        return redirect
    rows = AchievementService(db).list_achievements()
    return render_template("achievements_list.html", request, page_title="Ачивки", current_admin=current_admin, rows=rows, error=None)

@router.get("/admin/achievements/new")
def achievements_new_page(request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = require_auth(request, db, permission="achievement_manage")
    if redirect:
        return redirect
    return render_template("achievement_form.html", request, page_title="Создать ачивку", current_admin=current_admin, values={}, error=None, success=None, action_url="/admin/achievements/new", submit_label="Создать ачивку")

@router.post("/admin/achievements/new")
async def achievements_new_submit(request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = require_auth(request, db, permission="achievement_manage")
    if redirect:
        return redirect
    form = await request.form()
    service = AchievementService(db)
    image_url = str(form.get("image_url", "")).strip()
    upload = form.get("image_file")
    try:
        if upload and getattr(upload, "filename", ""):
            image_url = service.save_achievement_image(file_bytes=await upload.read(), file_name=upload.filename)
        service.create_achievement(current_admin.id, title=str(form.get("title", "")).strip(), description=str(form.get("description", "")).strip(), image_url=image_url)
        return RedirectResponse(url="/admin/achievements", status_code=303)
    except Exception as exc:
        db.rollback()
        return render_template("achievement_form.html", request, page_title="Создать ачивку", current_admin=current_admin, values={"title": str(form.get("title","")), "description": str(form.get("description","")), "image_url": str(form.get("image_url",""))}, error=str(exc), success=None, action_url="/admin/achievements/new", submit_label="Создать ачивку")

@router.get("/admin/achievements/{achievement_id}/edit")
def achievements_edit_page(achievement_id: int, request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = require_auth(request, db, permission="achievement_manage")
    if redirect:
        return redirect
    item = AchievementService(db).get_achievement(achievement_id)
    return render_template("achievement_form.html", request, page_title=f"Редактировать ачивку #{achievement_id}", current_admin=current_admin, values={"title": item.title, "description": item.description or "", "image_url": item.image_url or ""}, error=None, success=None, action_url=f"/admin/achievements/{achievement_id}/edit", submit_label="Сохранить ачивку")

@router.post("/admin/achievements/{achievement_id}/edit")
async def achievements_edit_submit(achievement_id: int, request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = require_auth(request, db, permission="achievement_manage")
    if redirect:
        return redirect
    form = await request.form()
    service = AchievementService(db)
    image_url = str(form.get("image_url", "")).strip()
    upload = form.get("image_file")
    try:
        if upload and getattr(upload, "filename", ""):
            image_url = service.save_achievement_image(file_bytes=await upload.read(), file_name=upload.filename)
        service.update_achievement(current_admin.id, achievement_id, title=str(form.get("title", "")).strip(), description=str(form.get("description", "")).strip(), image_url=image_url)
        return RedirectResponse(url="/admin/achievements", status_code=303)
    except Exception as exc:
        db.rollback()
        return render_template("achievement_form.html", request, page_title=f"Редактировать ачивку #{achievement_id}", current_admin=current_admin, values={"title": str(form.get("title","")), "description": str(form.get("description","")), "image_url": str(form.get("image_url",""))}, error=str(exc), success=None, action_url=f"/admin/achievements/{achievement_id}/edit", submit_label="Сохранить ачивку")

@router.post("/admin/achievements/{achievement_id}/delete")
def achievements_delete(achievement_id: int, request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = require_auth(request, db, permission="achievement_manage")
    if redirect:
        return redirect
    try:
        AchievementService(db).delete_achievement(current_admin.id, achievement_id)
    except Exception as exc:
        db.rollback()
        rows = AchievementService(db).list_achievements()
        return render_template("achievements_list.html", request, page_title="Ачивки", current_admin=current_admin, rows=rows, error=str(exc))
    return RedirectResponse(url="/admin/achievements", status_code=303)

@router.get("/admin/people/{admin_id}/achievements/grant")
def achievement_grant_page(admin_id: int, request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = require_auth(request, db, permission="achievement_manage")
    if redirect:
        return redirect
    person = AdminRepository(db).get_by_id(admin_id)
    if not person:
        return render_template("forbidden.html", request, page_title="Ошибка", current_admin=current_admin, error="Сотрудник не найден.")
    rows = AchievementService(db).list_achievements()
    existing = {grant.achievement_id for grant in AchievementService(db).list_admin_achievements(admin_id)}
    return render_template("achievement_grant.html", request, page_title="Выдать ачивку", current_admin=current_admin, person=person, rows=rows, existing=existing, error=None, success=None)

@router.post("/admin/people/{admin_id}/achievements/grant")
async def achievement_grant_submit(admin_id: int, request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = require_auth(request, db, permission="achievement_manage")
    if redirect:
        return redirect
    person = AdminRepository(db).get_by_id(admin_id)
    form = await request.form()
    achievement_id = int(str(form.get("achievement_id", "0")).strip() or "0")
    note = str(form.get("note", "")).strip()
    try:
        AchievementService(db).grant_achievement(current_admin, admin_id=admin_id, achievement_id=achievement_id, note=note)
        return RedirectResponse(url=f"/admin/people/{admin_id}", status_code=303)
    except Exception as exc:
        db.rollback()
        rows = AchievementService(db).list_achievements()
        existing = {grant.achievement_id for grant in AchievementService(db).list_admin_achievements(admin_id)}
        return render_template("achievement_grant.html", request, page_title="Выдать ачивку", current_admin=current_admin, person=person, rows=rows, existing=existing, error=str(exc), success=None)

@router.post("/admin/people/{admin_id}/achievements/{grant_id}/revoke")
def achievement_revoke(admin_id: int, grant_id: int, request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = require_auth(request, db, permission="achievement_manage")
    if redirect:
        return redirect
    AchievementService(db).revoke_grant(current_admin.id, grant_id)
    return RedirectResponse(url=f"/admin/people/{admin_id}", status_code=303)
