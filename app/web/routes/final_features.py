from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from starlette.responses import RedirectResponse

from app.core.database import get_db_session
from app.services.achievement_service import AchievementService
from app.services.auth_service import AuthService
from app.services.password_reset_service import PasswordResetService
from app.web.auth import get_current_admin_from_request, redirect_to_login
from app.web.templates import templates

router = APIRouter(include_in_schema=False)


def render_template(name: str, request: Request, **context):
    return templates.TemplateResponse(name, {"request": request, **context})


def require_auth(request: Request, db: Session):
    admin = get_current_admin_from_request(request, db)
    if not admin:
        return None, redirect_to_login()
    return admin, None


@router.get("/admin/achievements")
def achievements_index(request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = require_auth(request, db)
    if redirect:
        return redirect
    rows = AchievementService(db).list_achievements()
    return render_template("achievements_list.html", request, page_title="Ачивки", current_admin=current_admin, rows=rows, error=None)


@router.get("/admin/achievements/new")
def achievements_new(request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = require_auth(request, db)
    if redirect:
        return redirect
    return render_template("achievement_form.html", request, page_title="Создать ачивку", current_admin=current_admin, values={"name": "", "description": "", "icon_url": "", "is_active": True}, action_url="/admin/achievements/new", submit_label="Создать ачивку", error=None, success=None)


@router.post("/admin/achievements/new")
async def achievements_new_submit(request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = require_auth(request, db)
    if redirect:
        return redirect
    form = await request.form()
    values = {
        "name": str(form.get("name", "")).strip(),
        "description": str(form.get("description", "")).strip(),
        "icon_url": str(form.get("icon_url", "")).strip(),
        "is_active": form.get("is_active") == "on",
    }
    try:
        AchievementService(db).create_achievement(current_admin.id, **values)
        return render_template("achievement_form.html", request, page_title="Создать ачивку", current_admin=current_admin, values={"name": "", "description": "", "icon_url": "", "is_active": True}, action_url="/admin/achievements/new", submit_label="Создать ачивку", error=None, success="Ачивка создана.")
    except Exception as exc:
        db.rollback()
        return render_template("achievement_form.html", request, page_title="Создать ачивку", current_admin=current_admin, values=values, action_url="/admin/achievements/new", submit_label="Создать ачивку", error=str(exc), success=None)


@router.get("/admin/achievements/{achievement_id}/edit")
def achievements_edit(achievement_id: int, request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = require_auth(request, db)
    if redirect:
        return redirect
    item = AchievementService(db).get_achievement(achievement_id)
    return render_template("achievement_form.html", request, page_title=f"Редактировать ачивку #{achievement_id}", current_admin=current_admin, values={"name": item.name, "description": item.description or "", "icon_url": item.icon_url or "", "is_active": item.is_active}, action_url=f"/admin/achievements/{achievement_id}/edit", submit_label="Сохранить ачивку", error=None, success=None)


@router.post("/admin/achievements/{achievement_id}/edit")
async def achievements_edit_submit(achievement_id: int, request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = require_auth(request, db)
    if redirect:
        return redirect
    form = await request.form()
    values = {
        "name": str(form.get("name", "")).strip(),
        "description": str(form.get("description", "")).strip(),
        "icon_url": str(form.get("icon_url", "")).strip(),
        "is_active": form.get("is_active") == "on",
    }
    try:
        AchievementService(db).update_achievement(current_admin.id, achievement_id, **values)
        return render_template("achievement_form.html", request, page_title=f"Редактировать ачивку #{achievement_id}", current_admin=current_admin, values=values, action_url=f"/admin/achievements/{achievement_id}/edit", submit_label="Сохранить ачивку", error=None, success="Ачивка обновлена.")
    except Exception as exc:
        db.rollback()
        return render_template("achievement_form.html", request, page_title=f"Редактировать ачивку #{achievement_id}", current_admin=current_admin, values=values, action_url=f"/admin/achievements/{achievement_id}/edit", submit_label="Сохранить ачивку", error=str(exc), success=None)


@router.post("/admin/achievements/{achievement_id}/delete")
def achievements_delete(achievement_id: int, request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = require_auth(request, db)
    if redirect:
        return redirect
    AchievementService(db).delete_achievement(current_admin.id, achievement_id)
    return RedirectResponse(url="/admin/achievements", status_code=303)


@router.get("/admin/people/{admin_id}/achievements/grant")
def achievements_grant_page(admin_id: int, request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = require_auth(request, db)
    if redirect:
        return redirect
    target = AuthService(db).get_admin(admin_id)
    rows = AchievementService(db).list_achievements()
    grants = AchievementService(db).list_admin_grants(admin_id)
    return render_template("achievement_grant_form.html", request, page_title=f"Ачивки сотрудника {target.full_name or target.username}", current_admin=current_admin, target=target, achievements=rows, grants=grants, error=None, success=None)


@router.post("/admin/people/{admin_id}/achievements/grant")
async def achievements_grant_submit(admin_id: int, request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = require_auth(request, db)
    if redirect:
        return redirect
    form = await request.form()
    achievement_id = int(str(form.get("achievement_id", "")).strip())
    reason = str(form.get("reason", "")).strip()
    target = AuthService(db).get_admin(admin_id)
    rows = AchievementService(db).list_achievements()
    try:
        AchievementService(db).grant(current_admin.id, admin_id=admin_id, achievement_id=achievement_id, reason=reason)
        grants = AchievementService(db).list_admin_grants(admin_id)
        return render_template("achievement_grant_form.html", request, page_title=f"Ачивки сотрудника {target.full_name or target.username}", current_admin=current_admin, target=target, achievements=rows, grants=grants, error=None, success="Ачивка выдана.")
    except Exception as exc:
        db.rollback()
        grants = AchievementService(db).list_admin_grants(admin_id)
        return render_template("achievement_grant_form.html", request, page_title=f"Ачивки сотрудника {target.full_name or target.username}", current_admin=current_admin, target=target, achievements=rows, grants=grants, error=str(exc), success=None)


@router.post("/admin/people/{admin_id}/achievements/{grant_id}/revoke")
def achievements_revoke(admin_id: int, grant_id: int, request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = require_auth(request, db)
    if redirect:
        return redirect
    AchievementService(db).revoke(current_admin.id, grant_id)
    return RedirectResponse(url=f"/admin/people/{admin_id}/achievements/grant", status_code=303)


@router.post("/admin/team/{admin_id}/create-reset-link")
def create_reset_link(admin_id: int, request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = require_auth(request, db)
    if redirect:
        return redirect
    auth = AuthService(db)
    item = auth.get_manageable_admin(current_admin, admin_id)
    allowed_roles = auth.allowed_create_roles(current_admin)
    reset_link, _token = PasswordResetService(db).create_reset_link(current_admin, admin_id, request.base_url._url.rstrip("/"))
    return render_template(
        "team_form.html",
        request,
        page_title=f"Редактировать пользователя #{admin_id}",
        current_admin=current_admin,
        error=None,
        success="Ссылка сброса создана.",
        credentials=None,
        reset_link=reset_link,
        values={"username": item.username, "role": item.role, "is_active": item.is_active},
        allowed_roles=allowed_roles,
        action_url=f"/admin/team/{admin_id}/edit",
        submit_label="Сохранить пользователя",
        is_edit=True,
        reset_password_url=f"/admin/team/{admin_id}/reset-password",
        create_reset_link_url=f"/admin/team/{admin_id}/create-reset-link",
    )


@router.get("/admin/reset-password/{token}")
def reset_password_page(token: str, request: Request, db: Session = Depends(get_db_session)):
    try:
        entity = PasswordResetService(db).get_valid_token(token)
        return render_template("reset_password.html", request, page_title="Сброс пароля", token=token, username=entity.admin.username, error=None, success=None)
    except Exception as exc:
        return render_template("reset_password.html", request, page_title="Сброс пароля", token=token, username=None, error=str(exc), success=None)


@router.post("/admin/reset-password/{token}")
async def reset_password_submit(token: str, request: Request, db: Session = Depends(get_db_session)):
    form = await request.form()
    password = str(form.get("password", "")).strip()
    password2 = str(form.get("password_confirm", "")).strip()
    if password != password2:
        return render_template("reset_password.html", request, page_title="Сброс пароля", token=token, username=None, error="Пароли не совпадают.", success=None)
    try:
        entity = PasswordResetService(db).get_valid_token(token)
        PasswordResetService(db).consume(token, password)
        return render_template("reset_password.html", request, page_title="Сброс пароля", token=token, username=entity.admin.username, error=None, success="Пароль успешно обновлён.")
    except Exception as exc:
        db.rollback()
        return render_template("reset_password.html", request, page_title="Сброс пароля", token=token, username=None, error=str(exc), success=None)
