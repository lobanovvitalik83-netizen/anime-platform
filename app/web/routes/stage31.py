from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from starlette.responses import RedirectResponse

from app.core.database import get_db_session
from app.repositories.admin_repository import AdminRepository
from app.services.achievement_service import AchievementService
from app.services.notification_service import NotificationService
from app.web.auth import get_current_admin_from_request, redirect_to, redirect_to_login
from app.web.templates import templates

router = APIRouter(include_in_schema=False)


def render_template(name: str, request: Request, **context):
    return templates.TemplateResponse(name, {"request": request, **context})


def require_auth(request: Request, db: Session):
    admin = get_current_admin_from_request(request, db)
    if not admin:
        return None, redirect_to_login()
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

    target = AdminRepository(db).get_by_username(username)
    if target:
        NotificationService(db).notify_by_permission(
            "team_manage",
            kind="password_reset_request",
            title=f"Запрос на сброс пароля: {target.username}",
            body=f"Пользователь {target.username} запросил сброс пароля через страницу входа.",
            link_url=f"/admin/team/{target.id}/edit",
        )
        db.commit()

    return render_template(
        "forgot_password.html",
        request,
        page_title="Забыл пароль",
        current_admin=None,
        error=None,
        success="Если такой логин существует, запрос на сброс передан администрации.",
    )


@router.get("/admin/achievements")
def achievements_page(request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = require_auth(request, db)
    if redirect:
        return redirect
    service = AchievementService(db)
    return render_template(
        "achievements_list.html",
        request,
        page_title="Ачивки",
        current_admin=current_admin,
        rows=service.list_achievements(),
        error=None,
    )


@router.get("/admin/achievements/new")
def achievements_new_page(request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = require_auth(request, db)
    if redirect:
        return redirect
    return render_template(
        "achievement_form.html",
        request,
        page_title="Создать ачивку",
        current_admin=current_admin,
        values={"icon": "🏆", "color": "#4c8bf5", "is_active": True},
        error=None,
        action_url="/admin/achievements/new",
        submit_label="Создать",
    )


@router.post("/admin/achievements/new")
async def achievements_new_submit(request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = require_auth(request, db)
    if redirect:
        return redirect
    form = await request.form()
    values = {
        "name": str(form.get("name", "")).strip(),
        "description": str(form.get("description", "")).strip(),
        "icon": str(form.get("icon", "🏆")).strip(),
        "color": str(form.get("color", "#4c8bf5")).strip(),
        "is_active": form.get("is_active") == "on",
    }
    try:
        AchievementService(db).create_achievement(current_admin, values)
        return redirect_to("/admin/achievements")
    except Exception as exc:
        db.rollback()
        return render_template(
            "achievement_form.html",
            request,
            page_title="Создать ачивку",
            current_admin=current_admin,
            values=values,
            error=str(exc),
            action_url="/admin/achievements/new",
            submit_label="Создать",
        )


@router.get("/admin/achievements/{achievement_id}/edit")
def achievements_edit_page(achievement_id: int, request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = require_auth(request, db)
    if redirect:
        return redirect
    item = AchievementService(db).get_achievement(achievement_id)
    return render_template(
        "achievement_form.html",
        request,
        page_title=f"Редактировать ачивку #{achievement_id}",
        current_admin=current_admin,
        values={"name": item.name, "description": item.description or "", "icon": item.icon or "🏆", "color": item.color or "#4c8bf5", "is_active": item.is_active},
        error=None,
        action_url=f"/admin/achievements/{achievement_id}/edit",
        submit_label="Сохранить",
    )


@router.post("/admin/achievements/{achievement_id}/edit")
async def achievements_edit_submit(achievement_id: int, request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = require_auth(request, db)
    if redirect:
        return redirect
    form = await request.form()
    values = {
        "name": str(form.get("name", "")).strip(),
        "description": str(form.get("description", "")).strip(),
        "icon": str(form.get("icon", "🏆")).strip(),
        "color": str(form.get("color", "#4c8bf5")).strip(),
        "is_active": form.get("is_active") == "on",
    }
    try:
        AchievementService(db).update_achievement(current_admin, achievement_id, values)
        return redirect_to("/admin/achievements")
    except Exception as exc:
        db.rollback()
        return render_template(
            "achievement_form.html",
            request,
            page_title=f"Редактировать ачивку #{achievement_id}",
            current_admin=current_admin,
            values=values,
            error=str(exc),
            action_url=f"/admin/achievements/{achievement_id}/edit",
            submit_label="Сохранить",
        )


@router.post("/admin/achievements/{achievement_id}/delete")
def achievements_delete(achievement_id: int, request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = require_auth(request, db)
    if redirect:
        return redirect
    try:
        AchievementService(db).delete_achievement(current_admin, achievement_id)
    except Exception:
        db.rollback()
    return redirect_to("/admin/achievements")


@router.get("/admin/people/{admin_id}/achievements/grant")
def achievements_grant_page(admin_id: int, request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = require_auth(request, db)
    if redirect:
        return redirect
    target = AdminRepository(db).get_by_id(admin_id)
    rows = AchievementService(db).list_active_achievements()
    return render_template(
        "achievement_grant.html",
        request,
        page_title=f"Выдать ачивку пользователю #{admin_id}",
        current_admin=current_admin,
        person=target,
        rows=rows,
        error=None,
    )


@router.post("/admin/people/{admin_id}/achievements/grant")
async def achievements_grant_submit(admin_id: int, request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = require_auth(request, db)
    if redirect:
        return redirect
    form = await request.form()
    achievement_id = int(str(form.get("achievement_id", "0")).strip() or "0")
    note = str(form.get("note", "")).strip()
    try:
        AchievementService(db).grant_to_admin(current_admin, admin_id, achievement_id, note)
        return redirect_to(f"/admin/people/{admin_id}")
    except Exception as exc:
        db.rollback()
        target = AdminRepository(db).get_by_id(admin_id)
        rows = AchievementService(db).list_active_achievements()
        return render_template(
            "achievement_grant.html",
            request,
            page_title=f"Выдать ачивку пользователю #{admin_id}",
            current_admin=current_admin,
            person=target,
            rows=rows,
            error=str(exc),
        )


@router.post("/admin/people/{admin_id}/achievements/{grant_id}/delete")
def achievements_revoke(admin_id: int, grant_id: int, request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = require_auth(request, db)
    if redirect:
        return redirect
    try:
        AchievementService(db).revoke_grant(current_admin, grant_id)
    except Exception:
        db.rollback()
    return redirect_to(f"/admin/people/{admin_id}")
