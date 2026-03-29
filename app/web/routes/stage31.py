from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from starlette.responses import Response

from app.core.database import get_db_session
from app.services.achievement_service import AchievementService
from app.services.auth_service import AuthService
from app.services.notification_service import NotificationService
from app.services.permission_service import PermissionService
from app.web.auth import get_current_admin_from_request, redirect_to, redirect_to_login
from app.web.templates import templates

router = APIRouter(include_in_schema=False)


def render_template(name: str, request: Request, **context):
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
    return render_template("forgot_password.html", request, page_title="Забыл пароль", current_admin=None, error=None, success=None)


@router.post("/admin/forgot-password")
async def forgot_password_submit(request: Request, db: Session = Depends(get_db_session)):
    form = await request.form()
    username = str(form.get("username", "")).strip()
    if not username:
        return render_template("forgot_password.html", request, page_title="Забыл пароль", current_admin=None, error="Укажи логин.", success=None)
    target = AuthService(db).admins.get_by_username(username)
    if target:
        NotificationService(db).notify_by_permission(
            "team_manage",
            kind="password_reset_request",
            title="Запрос на сброс пароля",
            body=f"Пользователь @{username} запросил сброс пароля.",
            link_url="/admin/team",
        )
        db.commit()
    return render_template("forgot_password.html", request, page_title="Забыл пароль", current_admin=None, error=None, success="Запрос отправлен. Администратор обработает его вручную.")


@router.get("/admin/achievements")
def achievements_page(request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = require_auth(request, db)
    if redirect:
        return redirect
    rows = AchievementService(db).list_achievements()
    return render_template("achievements_list.html", request, page_title="Ачивки", current_admin=current_admin, rows=rows, error=None)


@router.get("/admin/achievements/new")
def achievement_new_page(request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = require_auth(request, db, permission="team_manage")
    if redirect:
        return redirect
    return render_template("achievement_form.html", request, page_title="Новая ачивка", current_admin=current_admin, values={"icon_emoji":"🏆","color":"#4f7cff","is_active":True}, error=None, action_url="/admin/achievements/new", submit_label="Создать ачивку")


@router.post("/admin/achievements/new")
async def achievement_new_submit(request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = require_auth(request, db, permission="team_manage")
    if redirect:
        return redirect
    form = await request.form()
    values = {
        "title": str(form.get("title","")).strip(),
        "description": str(form.get("description","")).strip(),
        "icon_emoji": str(form.get("icon_emoji","")).strip(),
        "color": str(form.get("color","")).strip(),
        "is_active": form.get("is_active") == "on",
    }
    try:
        AchievementService(db).create_achievement(current_admin.id, **values)
        return redirect_to("/admin/achievements")
    except Exception as exc:
        db.rollback()
        return render_template("achievement_form.html", request, page_title="Новая ачивка", current_admin=current_admin, values=values, error=str(exc), action_url="/admin/achievements/new", submit_label="Создать ачивку")


@router.get("/admin/achievements/{achievement_id}/edit")
def achievement_edit_page(achievement_id: int, request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = require_auth(request, db, permission="team_manage")
    if redirect:
        return redirect
    item = AchievementService(db).get_achievement(achievement_id)
    values = {"title": item.title, "description": item.description or "", "icon_emoji": item.icon_emoji or "🏆", "color": item.color or "#4f7cff", "is_active": item.is_active}
    return render_template("achievement_form.html", request, page_title="Редактирование ачивки", current_admin=current_admin, values=values, error=None, action_url=f"/admin/achievements/{achievement_id}/edit", submit_label="Сохранить ачивку")


@router.post("/admin/achievements/{achievement_id}/edit")
async def achievement_edit_submit(achievement_id: int, request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = require_auth(request, db, permission="team_manage")
    if redirect:
        return redirect
    form = await request.form()
    values = {
        "title": str(form.get("title","")).strip(),
        "description": str(form.get("description","")).strip(),
        "icon_emoji": str(form.get("icon_emoji","")).strip(),
        "color": str(form.get("color","")).strip(),
        "is_active": form.get("is_active") == "on",
    }
    try:
        AchievementService(db).update_achievement(current_admin.id, achievement_id, **values)
        return redirect_to("/admin/achievements")
    except Exception as exc:
        db.rollback()
        return render_template("achievement_form.html", request, page_title="Редактирование ачивки", current_admin=current_admin, values=values, error=str(exc), action_url=f"/admin/achievements/{achievement_id}/edit", submit_label="Сохранить ачивку")


@router.post("/admin/achievements/{achievement_id}/delete")
def achievement_delete(achievement_id: int, request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = require_auth(request, db, permission="team_manage")
    if redirect:
        return redirect
    try:
        AchievementService(db).delete_achievement(current_admin.id, achievement_id)
        return redirect_to("/admin/achievements")
    except Exception as exc:
        db.rollback()
        rows = AchievementService(db).list_achievements()
        return render_template("achievements_list.html", request, page_title="Ачивки", current_admin=current_admin, rows=rows, error=str(exc))


@router.get("/admin/people/{admin_id}/achievements/grant")
def achievement_grant_page(admin_id: int, request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = require_auth(request, db, permission="team_manage")
    if redirect:
        return redirect
    person = AuthService(db).get_admin(admin_id)
    rows = AchievementService(db).list_active_achievements()
    current = AchievementService(db).list_admin_achievements(admin_id)
    granted_ids = {item.achievement_id for item in current}
    return render_template("achievement_grant.html", request, page_title="Выдать ачивку", current_admin=current_admin, person=person, rows=rows, current=current, granted_ids=granted_ids, error=None)


@router.post("/admin/people/{admin_id}/achievements/grant")
async def achievement_grant_submit(admin_id: int, request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = require_auth(request, db, permission="team_manage")
    if redirect:
        return redirect
    form = await request.form()
    achievement_id = int(str(form.get("achievement_id", "0")))
    note = str(form.get("note", "")).strip()
    try:
        AchievementService(db).grant_to_admin(current_admin.id, target_admin_id=admin_id, achievement_id=achievement_id, note=note)
        return redirect_to(f"/admin/people/{admin_id}")
    except Exception as exc:
        db.rollback()
        person = AuthService(db).get_admin(admin_id)
        rows = AchievementService(db).list_active_achievements()
        current = AchievementService(db).list_admin_achievements(admin_id)
        granted_ids = {item.achievement_id for item in current}
        return render_template("achievement_grant.html", request, page_title="Выдать ачивку", current_admin=current_admin, person=person, rows=rows, current=current, granted_ids=granted_ids, error=str(exc))


@router.post("/admin/people/{admin_id}/achievements/{grant_id}/revoke")
def achievement_revoke(admin_id: int, grant_id: int, request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = require_auth(request, db, permission="team_manage")
    if redirect:
        return redirect
    try:
        AchievementService(db).revoke_from_admin(current_admin.id, grant_id)
        return redirect_to(f"/admin/people/{admin_id}")
    except Exception:
        db.rollback()
        return redirect_to(f"/admin/people/{admin_id}")
