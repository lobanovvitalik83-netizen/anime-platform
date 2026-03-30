from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from starlette.responses import RedirectResponse

from app.core.database import get_db_session
from app.services.notification_service import NotificationService
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


@router.get("/admin/notifications")
def notifications_page(request: Request, db: Session = Depends(get_db_session), only_unread: bool = False):
    current_admin, redirect = require_auth(request, db)
    if redirect:
        return redirect
    service = NotificationService(db)
    return render_template(
        "notifications_list.html",
        request,
        page_title="Уведомления",
        current_admin=current_admin,
        rows=service.list_for_admin(current_admin, only_unread=only_unread),
        only_unread=only_unread,
    )


@router.post("/admin/notifications/{notification_id}/read")
def notification_mark_read(notification_id: int, request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = require_auth(request, db)
    if redirect:
        return redirect
    NotificationService(db).mark_read(current_admin, notification_id)
    db.commit()
    return RedirectResponse(url="/admin/notifications", status_code=303)
