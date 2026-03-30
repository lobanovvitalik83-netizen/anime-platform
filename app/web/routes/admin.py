from fastapi import APIRouter, Depends, File, Request, Response, UploadFile
from sqlalchemy.orm import Session
from starlette.responses import RedirectResponse

from app.core.config import settings
from app.core.database import get_db_session
from app.core.exceptions import AuthenticationError, ValidationError
from app.services.analytics_service import AnalyticsService
from app.services.achievement_service import AchievementService
from app.services.password_reset_service import PasswordResetService
from app.services.asset_service import AssetService
from app.services.auth_service import AuthService
from app.services.chat_service import ChatService
from app.services.code_service import CodeService
from app.services.import_export_service import ImportExportService
from app.services.media_card_service import MediaCardService
from app.services.media_service import MediaService
from app.services.public_lookup_service import PublicLookupService
from app.services.site_setting_service import SiteSettingService
from app.services.report_service import ReportService
from app.services.permission_service import PERMISSION_LABELS, PermissionService
from app.web.auth import clear_auth_cookie, get_current_admin_from_request, has_required_role, redirect_to, redirect_to_login, set_auth_cookie
from app.core.security import get_client_identifier, login_rate_limiter
from app.web.templates import templates

router = APIRouter(include_in_schema=False)
permission_service = PermissionService()


def to_int(value: str | None) -> int | None:
    if value is None or value == "":
        return None
    return int(value)


def render_template(name: str, request: Request, **context):
    current_admin = context.get("current_admin")
    db = context.get("db")
    current_permissions = []
    unread_notifications = 0
    if current_admin:
        try:
            current_permissions = sorted(permission_service.get_permissions(current_admin))
        except Exception:
            current_permissions = []
        if db is not None:
            try:
                unread_notifications = NotificationService(db).unread_count(current_admin)
            except Exception:
                unread_notifications = 0
    payload = {
        "request": request,
        "current_permissions": current_permissions,
        "permission_labels": PERMISSION_LABELS,
        "unread_notifications": unread_notifications,
        **context,
    }
    return templates.TemplateResponse(name, payload)


def get_admin_or_redirect(request: Request, db: Session, min_role: str = "editor"):
    admin = get_current_admin_from_request(request, db)
    if not admin:
        return None, redirect_to_login()
    if not has_required_role(admin, min_role):
        return None, render_template(
            "forbidden.html",
            request,
            page_title="Доступ запрещён",
            current_admin=admin,
            error="У вас недостаточно прав для этого раздела.",
        )
    return admin, None


def _render_media_cards(request: Request, current_admin, db: Session, q: str = "", genre: str = "", status: str = "", error: str | None = None):
    cards = MediaCardService(db).list_cards(q=q, genre=genre, status=status)
    return render_template(
        "media_cards_list.html",
        request,
        page_title="Медиа",
        current_admin=current_admin,
        cards=cards,
        filters={"q": q, "genre": genre, "status": status},
        error=error,
    )


def _team_manageable_ids(current_admin, admins):
    if current_admin.role == "superadmin":
        return {item.id for item in admins if item.id != current_admin.id and item.role in {"admin", "editor", "support"}}
    if current_admin.role == "admin":
        return {item.id for item in admins if item.role in {"editor", "support"}}
    return set()


def _messages_enabled(db: Session) -> bool:
    return SiteSettingService(db).is_messages_enabled()


@router.get("/")
def root_redirect() -> RedirectResponse:
    return redirect_to("/admin")


@router.get("/admin/login")
def admin_login_page(request: Request, db: Session = Depends(get_db_session)):
    admin = get_current_admin_from_request(request, db)
    if admin:
        return redirect_to("/admin")
    return render_template("login.html", request, page_title="Вход", error=None)


@router.post("/admin/login")
async def admin_login_submit(request: Request, db: Session = Depends(get_db_session)):
    form = await request.form()
    username = str(form.get("username", "")).strip()
    password = str(form.get("password", "")).strip()

    limiter_key = f"login:{get_client_identifier(request)}:{username.lower()}"
    allowed, retry_after = login_rate_limiter.is_allowed(
        limiter_key,
        attempts=settings.login_rate_limit_attempts,
        window_seconds=settings.login_rate_limit_window_seconds,
    )
    if not allowed:
        return render_template("login.html", request, db=db, page_title="Вход", error=f"Слишком много попыток входа. Повтори через {retry_after} сек.")

    try:
        admin = AuthService(db).authenticate(username=username, password=password)
    except AuthenticationError as exc:
        return render_template("login.html", request, db=db, page_title="Вход", error=str(exc))

    response = redirect_to("/admin")
    set_auth_cookie(response, admin.id)
    return response


@router.get("/admin/logout")
def admin_logout():
    response = redirect_to("/admin/login")
    clear_auth_cookie(response)
    return response


@router.get("/admin")
def admin_dashboard(request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = get_admin_or_redirect(request, db)
    if redirect:
        return redirect

    media_service = MediaService(db)
    asset_service = AssetService(db)
    code_service = CodeService(db)

    def _safe_count(fn):
        try:
            return len(fn())
        except Exception:
            return 0

    try:
        recent_notifications = NotificationService(db).list_for_admin(current_admin, limit=8)
    except Exception:
        recent_notifications = []

    return render_template(
        "dashboard.html",
        request,
        db=db,
        page_title="Панель",
        current_admin=current_admin,
        recent_notifications=recent_notifications,
        counts={
            "titles": _safe_count(media_service.list_titles),
            "assets": _safe_count(asset_service.list_assets),
            "codes": _safe_count(code_service.list_codes),
            "reports": _safe_count(ReportService(db).list_tickets),
            "chats": _safe_count(lambda: ChatService(db).list_chats_for_admin(current_admin)),
        },
    )


@router.get("/admin/media")
def admin_media_cards(request: Request, db: Session = Depends(get_db_session), q: str = "", genre: str = "", status: str = ""):
    current_admin, redirect = get_admin_or_redirect(request, db)
    if redirect:
        return redirect
    return _render_media_cards(request, current_admin, db, q=q, genre=genre, status=status)


@router.post("/admin/media/bulk-delete")
async def admin_media_bulk_delete(request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = get_admin_or_redirect(request, db, min_role="admin")
    if redirect:
        return redirect
    form = await request.form()
    selected_ids = [int(item) for item in form.getlist("selected_ids")]
    if len(selected_ids) > settings.max_bulk_delete_items:
        return _render_media_cards(request, current_admin, db, error=f"За один раз можно удалить не больше {settings.max_bulk_delete_items} карточек.")
    service = MediaCardService(db)
    if not selected_ids:
        return _render_media_cards(request, current_admin, db, error="Не выбраны карточки.")
    try:
        for item_id in selected_ids:
            service.delete_card(current_admin.id, item_id)
    except Exception as exc:
        db.rollback()
        return _render_media_cards(request, current_admin, db, error=str(exc))
    return redirect_to("/admin/media")


@router.post("/admin/media/{title_id}/delete")
def admin_media_delete(title_id: int, request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = get_admin_or_redirect(request, db, min_role="admin")
    if redirect:
        return redirect
    try:
        MediaCardService(db).delete_card(current_admin.id, title_id)
    except Exception as exc:
        db.rollback()
        return _render_media_cards(request, current_admin, db, error=str(exc))
    return redirect_to("/admin/media")


@router.get("/admin/media/{title_id}/edit")
def admin_media_edit_page(title_id: int, request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = get_admin_or_redirect(request, db)
    if redirect:
        return redirect

    card = MediaCardService(db).get_card(title_id)
    values = {
        "genre": card["title"].type,
        "title": card["title"].title,
        "season_number": card["season"].season_number if card["season"] else "",
        "episode_number": card["episode"].episode_number if card["episode"] else "",
        "asset_type": card["asset"].asset_type if card["asset"] else "image",
        "external_url": card["asset"].external_url if card["asset"] and getattr(card["asset"], "storage_provider", None) == "external_reference" else "",
        "import_url": getattr(card["asset"], "source_url", "") if card["asset"] and getattr(card["asset"], "uploaded_by_system", False) else "",
        "source_label": getattr(card["asset"], "source_label", "") if card["asset"] else "",
        "mime_type": card["asset"].mime_type if card["asset"] else "",
        "is_primary": card["asset"].is_primary if card["asset"] else True,
        "generate_code": True,
        "status": card["title"].status,
    }

    return render_template(
        "card_builder.html",
        request,
        page_title=f"Редактирование карточки #{title_id}",
        current_admin=current_admin,
        error=None,
        success=None,
        values=values,
        result=None,
        action_url=f"/admin/media/{title_id}/edit",
        submit_label="Сохранить карточку",
        upload_ready=settings.media_upload_enabled,
        upload_help_text=settings.media_upload_help_text,
        upload_backend_label=settings.media_storage_backend_label,
    )

@router.post("/admin/media/{title_id}/edit")
async def admin_media_edit_submit(title_id: int, request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = get_admin_or_redirect(request, db)
    if redirect:
        return redirect
    form = await request.form()
    upload = form.get("media_file")

    def _text(name: str) -> str:
        return str(form.get(name, "")).strip()

    def _optional_int(name: str):
        raw = _text(name)
        if not raw:
            return None
        return int(raw)

    values = {
        "genre": _text("genre"),
        "title": _text("title"),
        "season_number": _optional_int("season_number"),
        "episode_number": _optional_int("episode_number"),
        "asset_type": _text("asset_type") or "image",
        "external_url": _text("external_url"),
        "import_url": _text("import_url"),
        "source_label": _text("source_label"),
        "mime_type": _text("mime_type"),
        "is_primary": form.get("is_primary") == "on",
        "generate_code": form.get("generate_code") == "on",
        "status": _text("status") or "draft",
    }

    file_name = None
    file_content_type = None
    file_bytes = None
    if upload and getattr(upload, "filename", ""):
        file_name = upload.filename
        file_content_type = getattr(upload, "content_type", None)
        file_bytes = await upload.read()

    try:
        result = await MediaCardService(db).update_card(
            current_admin.id,
            title_id,
            values,
            upload_file_name=file_name,
            upload_file_content_type=file_content_type,
            upload_file_bytes=file_bytes,
        )
        return render_template(
            "card_builder.html",
            request,
            page_title=f"Редактирование карточки #{title_id}",
            current_admin=current_admin,
            error=None,
            success="Карточка обновлена.",
            values=values,
            result=result,
            action_url=f"/admin/media/{title_id}/edit",
            submit_label="Сохранить карточку",
            upload_ready=settings.media_upload_enabled,
            upload_help_text=settings.media_upload_help_text,
            upload_backend_label=settings.media_storage_backend_label,
        )
    except Exception as exc:
        db.rollback()
        return render_template(
            "card_builder.html",
            request,
            page_title=f"Редактирование карточки #{title_id}",
            current_admin=current_admin,
            error=str(exc),
            success=None,
            values=values,
            result=None,
            action_url=f"/admin/media/{title_id}/edit",
            submit_label="Сохранить карточку",
            upload_ready=settings.media_upload_enabled,
            upload_help_text=settings.media_upload_help_text,
            upload_backend_label=settings.media_storage_backend_label,
        )

@router.get("/admin/card-builder")
def admin_card_builder_page(request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = get_admin_or_redirect(request, db)
    if redirect:
        return redirect

    return render_template(
        "card_builder.html",
        request,
        page_title="Создание карточки",
        current_admin=current_admin,
        error=None,
        success=None,
        values={
            "generate_code": True,
            "status": "active",
            "asset_type": "image",
            "genre": "anime",
            "external_url": "",
            "import_url": "",
            "source_label": "",
        },
        result=None,
        action_url="/admin/card-builder",
        submit_label="Создать карточку",
        upload_ready=settings.media_upload_enabled,
        upload_help_text=settings.media_upload_help_text,
        upload_backend_label=settings.media_storage_backend_label,
    )

@router.post("/admin/card-builder")
async def admin_card_builder_submit(request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = get_admin_or_redirect(request, db)
    if redirect:
        return redirect
    form = await request.form()
    upload = form.get("media_file")

    def _text(name: str) -> str:
        return str(form.get(name, "")).strip()

    def _optional_int(name: str):
        raw = _text(name)
        if not raw:
            return None
        return int(raw)

    values = {
        "genre": _text("genre"),
        "title": _text("title"),
        "season_number": _optional_int("season_number"),
        "episode_number": _optional_int("episode_number"),
        "asset_type": _text("asset_type") or "image",
        "external_url": _text("external_url"),
        "import_url": _text("import_url"),
        "source_label": _text("source_label"),
        "mime_type": _text("mime_type"),
        "is_primary": form.get("is_primary") == "on",
        "generate_code": form.get("generate_code") == "on",
        "status": _text("status") or "active",
    }

    file_name = None
    file_content_type = None
    file_bytes = None

    if upload and getattr(upload, "filename", ""):
        file_name = upload.filename
        file_content_type = getattr(upload, "content_type", None)
        file_bytes = await upload.read()

    try:
        result = await MediaCardService(db).create_card(
            admin_id=current_admin.id,
            payload=values,
            upload_file_name=file_name,
            upload_file_content_type=file_content_type,
            upload_file_bytes=file_bytes,
        )
        return render_template(
            "card_builder.html",
            request,
            page_title="Создание карточки",
            current_admin=current_admin,
            error=None,
            success="Карточка успешно создана.",
            values={
                "generate_code": True,
                "status": "active",
                "asset_type": "image",
                "genre": "anime",
                "external_url": "",
                "import_url": "",
                "source_label": "",
            },
            result=result,
            action_url="/admin/card-builder",
            submit_label="Создать карточку",
            upload_ready=settings.media_upload_enabled,
            upload_help_text=settings.media_upload_help_text,
            upload_backend_label=settings.media_storage_backend_label,
        )
    except Exception as exc:
        db.rollback()
        return render_template(
            "card_builder.html",
            request,
            page_title="Создание карточки",
            current_admin=current_admin,
            error=str(exc),
            success=None,
            values=values,
            result=None,
            action_url="/admin/card-builder",
            submit_label="Создать карточку",
            upload_ready=settings.media_upload_enabled,
            upload_help_text=settings.media_upload_help_text,
            upload_backend_label=settings.media_storage_backend_label,
        )

@router.get("/admin/codes")
def admin_codes(request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = get_admin_or_redirect(request, db, min_role="admin")
    if redirect:
        return redirect
    analytics = AnalyticsService(db)
    return render_template(
        "codes_list.html",
        request,
        page_title="Коды доступа",
        current_admin=current_admin,
        codes=CodeService(db).list_codes(),
        top_found=analytics.get_top_codes(kind="found", limit=8),
        top_not_found=analytics.get_top_codes(kind="not_found", limit=8),
        error=None,
    )



@router.get("/admin/codes/generate")
def admin_codes_generate_page(request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = get_admin_or_redirect(request, db, min_role="admin")
    if redirect:
        return redirect
    media_service = MediaService(db)
    return render_template("code_generate.html", request, page_title="Генерация кодов", current_admin=current_admin, titles=media_service.list_titles(), seasons=media_service.list_seasons(), episodes=media_service.list_episodes(), error=None, values={}, generated_codes=None)


@router.post("/admin/codes/generate")
async def admin_codes_generate_submit(request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = get_admin_or_redirect(request, db, min_role="admin")
    if redirect:
        return redirect

    media_service = MediaService(db)
    form = await request.form()
    payload = {
        "quantity": int(str(form.get("quantity")).strip()),
        "title_id": to_int(str(form.get("title_id", "")).strip() or None),
        "season_id": to_int(str(form.get("season_id", "")).strip() or None),
        "episode_id": to_int(str(form.get("episode_id", "")).strip() or None),
        "status": str(form.get("status", "active")).strip(),
    }

    try:
        generated_codes = CodeService(db).generate_codes(current_admin.id, payload)
    except Exception as exc:
        db.rollback()
        return render_template("code_generate.html", request, page_title="Генерация кодов", current_admin=current_admin, titles=media_service.list_titles(), seasons=media_service.list_seasons(), episodes=media_service.list_episodes(), error=str(exc), values=payload, generated_codes=None)

    return render_template("code_generate.html", request, page_title="Генерация кодов", current_admin=current_admin, titles=media_service.list_titles(), seasons=media_service.list_seasons(), episodes=media_service.list_episodes(), error=None, values=payload, generated_codes=generated_codes)


@router.get("/admin/codes/{code_id}/edit")
def admin_code_edit_page(code_id: int, request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = get_admin_or_redirect(request, db, min_role="admin")
    if redirect:
        return redirect
    code_service = CodeService(db)
    media_service = MediaService(db)
    item = code_service.get_code(code_id)
    values = {"code": item.code, "title_id": item.title_id or "", "season_id": item.season_id or "", "episode_id": item.episode_id or "", "status": item.status}
    return render_template("code_form.html", request, page_title=f"Редактировать код #{item.id}", current_admin=current_admin, titles=media_service.list_titles(), seasons=media_service.list_seasons(), episodes=media_service.list_episodes(), error=None, values=values, action_url=f"/admin/codes/{item.id}/edit", submit_label="Сохранить изменения")


@router.post("/admin/codes/{code_id}/edit")
async def admin_code_edit_submit(code_id: int, request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = get_admin_or_redirect(request, db, min_role="admin")
    if redirect:
        return redirect
    media_service = MediaService(db)
    form = await request.form()
    payload = {"code": str(form.get("code", "")).strip(), "title_id": to_int(str(form.get("title_id", "")).strip() or None), "season_id": to_int(str(form.get("season_id", "")).strip() or None), "episode_id": to_int(str(form.get("episode_id", "")).strip() or None), "status": str(form.get("status", "active")).strip()}
    try:
        CodeService(db).update_code(current_admin.id, code_id, payload)
    except Exception as exc:
        db.rollback()
        return render_template("code_form.html", request, page_title=f"Редактировать код #{code_id}", current_admin=current_admin, titles=media_service.list_titles(), seasons=media_service.list_seasons(), episodes=media_service.list_episodes(), error=str(exc), values=payload, action_url=f"/admin/codes/{code_id}/edit", submit_label="Сохранить изменения")
    return redirect_to("/admin/codes")


@router.post("/admin/codes/{code_id}/activate")
def admin_code_activate(code_id: int, request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = get_admin_or_redirect(request, db, min_role="admin")
    if redirect:
        return redirect
    CodeService(db).activate_code(current_admin.id, code_id)
    return redirect_to("/admin/codes")


@router.post("/admin/codes/{code_id}/deactivate")
def admin_code_deactivate(code_id: int, request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = get_admin_or_redirect(request, db, min_role="admin")
    if redirect:
        return redirect
    CodeService(db).deactivate_code(current_admin.id, code_id)
    return redirect_to("/admin/codes")


@router.post("/admin/codes/{code_id}/delete")
def admin_code_delete(code_id: int, request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = get_admin_or_redirect(request, db, min_role="admin")
    if redirect:
        return redirect
    CodeService(db).delete_code(current_admin.id, code_id)
    return redirect_to("/admin/codes")


@router.post("/admin/codes/bulk-action")
async def admin_codes_bulk_action(request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = get_admin_or_redirect(request, db, min_role="admin")
    if redirect:
        return redirect
    form = await request.form()
    action = str(form.get("bulk_action", "")).strip()
    selected_values = form.getlist("selected_ids")
    if not action:
        return render_template("codes_list.html", request, page_title="Коды", current_admin=current_admin, codes=CodeService(db).list_codes(), error="Не выбрано массовое действие.")
    if not selected_values:
        return render_template("codes_list.html", request, page_title="Коды", current_admin=current_admin, codes=CodeService(db).list_codes(), error="Не выбраны коды.")

    code_service = CodeService(db)
    try:
        for raw_id in selected_values:
            code_id = int(str(raw_id))
            if action == "activate":
                code_service.activate_code(current_admin.id, code_id)
            elif action == "deactivate":
                code_service.deactivate_code(current_admin.id, code_id)
            elif action == "delete":
                code_service.delete_code(current_admin.id, code_id)
            else:
                raise ValueError("Unknown bulk action")
    except Exception as exc:
        db.rollback()
        return render_template("codes_list.html", request, page_title="Коды", current_admin=current_admin, codes=CodeService(db).list_codes(), error=str(exc))
    return redirect_to("/admin/codes")


@router.get("/admin/import-export")
def admin_import_export_page(request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = get_admin_or_redirect(request, db, min_role="admin")
    if redirect:
        return redirect
    return render_template("import_export.html", request, page_title="Импорт / экспорт", current_admin=current_admin, error=None, success=None)


@router.get("/admin/import-jobs")
def admin_import_jobs_page(request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = get_admin_or_redirect(request, db, min_role="admin")
    if redirect:
        return redirect
    jobs = ImportExportService(db).list_jobs()
    return render_template("import_jobs_list.html", request, page_title="Import jobs", current_admin=current_admin, jobs=jobs)


@router.get("/admin/export/titles.csv")
def admin_export_titles_csv(request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = get_admin_or_redirect(request, db, min_role="admin")
    if redirect:
        return redirect
    content = ImportExportService(db).export_titles_csv()
    return Response(content=content, media_type="text/csv; charset=utf-8", headers={"Content-Disposition": "attachment; filename=titles.csv"})


@router.get("/admin/export/seasons.csv")
def admin_export_seasons_csv(request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = get_admin_or_redirect(request, db, min_role="admin")
    if redirect:
        return redirect
    content = ImportExportService(db).export_seasons_csv()
    return Response(content=content, media_type="text/csv; charset=utf-8", headers={"Content-Disposition": "attachment; filename=seasons.csv"})


@router.get("/admin/export/episodes.csv")
def admin_export_episodes_csv(request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = get_admin_or_redirect(request, db, min_role="admin")
    if redirect:
        return redirect
    content = ImportExportService(db).export_episodes_csv()
    return Response(content=content, media_type="text/csv; charset=utf-8", headers={"Content-Disposition": "attachment; filename=episodes.csv"})


@router.get("/admin/export/assets.csv")
def admin_export_assets_csv(request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = get_admin_or_redirect(request, db, min_role="admin")
    if redirect:
        return redirect
    content = ImportExportService(db).export_assets_csv()
    return Response(content=content, media_type="text/csv; charset=utf-8", headers={"Content-Disposition": "attachment; filename=assets.csv"})


@router.get("/admin/export/codes.csv")
def admin_export_codes_csv(request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = get_admin_or_redirect(request, db, min_role="admin")
    if redirect:
        return redirect
    content = ImportExportService(db).export_codes_csv()
    return Response(content=content, media_type="text/csv; charset=utf-8", headers={"Content-Disposition": "attachment; filename=codes.csv"})


@router.post("/admin/import/titles/csv")
async def admin_import_titles_csv(request: Request, file: UploadFile = File(...), db: Session = Depends(get_db_session)):
    current_admin, redirect = get_admin_or_redirect(request, db, min_role="admin")
    if redirect:
        return redirect
    try:
        content = await file.read()
        job = ImportExportService(db).import_titles_csv(current_admin.id, file.filename or "titles.csv", content)
        success = f"Импорт titles завершён. Успешно: {job.success_rows}, ошибок: {job.failed_rows}."
        return render_template("import_export.html", request, page_title="Импорт / экспорт", current_admin=current_admin, error=None, success=success)
    except Exception as exc:
        db.rollback()
        return render_template("import_export.html", request, page_title="Импорт / экспорт", current_admin=current_admin, error=str(exc), success=None)


@router.post("/admin/import/codes/csv")
async def admin_import_codes_csv(request: Request, file: UploadFile = File(...), db: Session = Depends(get_db_session)):
    current_admin, redirect = get_admin_or_redirect(request, db, min_role="admin")
    if redirect:
        return redirect
    try:
        content = await file.read()
        job = ImportExportService(db).import_codes_csv(current_admin.id, file.filename or "codes.csv", content)
        success = f"Импорт codes завершён. Успешно: {job.success_rows}, ошибок: {job.failed_rows}."
        return render_template("import_export.html", request, page_title="Импорт / экспорт", current_admin=current_admin, error=None, success=success)
    except Exception as exc:
        db.rollback()
        return render_template("import_export.html", request, page_title="Импорт / экспорт", current_admin=current_admin, error=str(exc), success=None)


@router.get("/admin/lookup-test")
def admin_lookup_test(request: Request, db: Session = Depends(get_db_session), code: str | None = None):
    current_admin, redirect = get_admin_or_redirect(request, db)
    if redirect:
        return redirect
    result = None
    error = None
    if code:
        try:
            result = PublicLookupService(db).lookup(code, source="admin_lookup")
        except Exception as exc:
            db.rollback()
            error = str(exc)
    return render_template("lookup_test.html", request, page_title="Тест lookup", current_admin=current_admin, code=code or "", result=result, error=error)


@router.get("/admin/profile")
def admin_profile_page(request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = get_admin_or_redirect(request, db)
    if redirect:
        return redirect
    return render_template("profile.html", request, db=db, page_title="Мой профиль", current_admin=current_admin, achievements=AchievementService(db).list_for_admin(current_admin.id), error=None, success=None, password_error=None, password_success=None)


@router.post("/admin/profile")
async def admin_profile_submit(request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = get_admin_or_redirect(request, db)
    if redirect:
        return redirect
    form = await request.form()
    avatar_file = form.get("avatar_file")
    service = AuthService(db)
    try:
        service.update_profile(
            current_admin,
            username=str(form.get("username", "")).strip() or None,
            full_name=str(form.get("full_name", "")).strip() or None,
            position=str(form.get("position", "")).strip() or None,
            about=str(form.get("about", "")).strip() or None,
            avatar_url=str(form.get("avatar_url", "")).strip() or None,
        )
        if avatar_file and getattr(avatar_file, "filename", ""):
            content = await avatar_file.read()
            service.upload_profile_avatar(current_admin.id, file_bytes=content, file_name=avatar_file.filename, content_type=getattr(avatar_file, "content_type", None))
        refreshed = AuthService(db).get_admin(current_admin.id)
        return render_template("profile.html", request, db=db, page_title="Мой профиль", current_admin=refreshed, achievements=AchievementService(db).list_for_admin(refreshed.id), error=None, success="Профиль обновлён.", password_error=None, password_success=None)
    except Exception as exc:
        db.rollback()
        refreshed = AuthService(db).get_admin(current_admin.id)
        return render_template("profile.html", request, db=db, page_title="Мой профиль", current_admin=refreshed, achievements=AchievementService(db).list_for_admin(refreshed.id), error=str(exc), success=None, password_error=None, password_success=None)


@router.post("/admin/profile/password")
async def admin_profile_password_submit(request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = get_admin_or_redirect(request, db)
    if redirect:
        return redirect
    form = await request.form()
    current_password = str(form.get("current_password", "")).strip()
    new_password = str(form.get("new_password", "")).strip()
    try:
        AuthService(db).change_own_password(current_admin.id, current_password, new_password)
        refreshed = AuthService(db).get_admin(current_admin.id)
        return render_template("profile.html", request, db=db, page_title="Мой профиль", current_admin=refreshed, achievements=AchievementService(db).list_for_admin(refreshed.id), error=None, success=None, password_error=None, password_success="Пароль изменён.")
    except Exception as exc:
        db.rollback()
        refreshed = AuthService(db).get_admin(current_admin.id)
        return render_template("profile.html", request, db=db, page_title="Мой профиль", current_admin=refreshed, achievements=AchievementService(db).list_for_admin(refreshed.id), error=None, success=None, password_error=str(exc), password_success=None)


@router.get("/admin/people")
def admin_people_page(request: Request, db: Session = Depends(get_db_session), q: str = ""):
    current_admin, redirect = get_admin_or_redirect(request, db)
    if redirect:
        return redirect

    service = AuthService(db)
    people = service.list_active_admins()
    search = (q or "").strip().lower()
    if search:
        def _match(item):
            blob = " ".join([
                item.username or "",
                item.full_name or "",
                item.position or "",
                item.about or "",
            ]).lower()
            return search in blob
        people = [item for item in people if _match(item)]

    return render_template("people_list.html", request, page_title="Сотрудники", current_admin=current_admin, people=people, q=q, messages_enabled=_messages_enabled(db))


@router.get("/admin/people/{admin_id}")
def admin_person_profile(admin_id: int, request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = get_admin_or_redirect(request, db)
    if redirect:
        return redirect

    person = AuthService(db).get_admin(admin_id)
    if not person.is_active:
        return render_template("forbidden.html", request, page_title="Профиль скрыт", current_admin=current_admin, error="Этот профиль недоступен.")
    return render_template("person_profile.html", request, db=db, page_title=person.full_name or person.username, current_admin=current_admin, person=person, achievements=AchievementService(db).list_for_admin(person.id), messages_enabled=_messages_enabled(db))


@router.post("/admin/people/{admin_id}/message")
def admin_person_message(admin_id: int, request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = get_admin_or_redirect(request, db)
    if redirect:
        return redirect
    try:
        chat = ChatService(db).get_or_create_direct_chat(current_admin, admin_id)
        return redirect_to(f"/admin/chats/{chat.id}")
    except Exception as exc:
        db.rollback()
        person = AuthService(db).get_admin(admin_id)
        return render_template("person_profile.html", request, db=db, page_title=person.full_name or person.username, current_admin=current_admin, person=person, achievements=AchievementService(db).list_for_admin(person.id), messages_enabled=_messages_enabled(db), error=str(exc))


@router.get("/admin/team")
def admin_team_page(request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = get_admin_or_redirect(request, db, min_role="admin")
    if redirect:
        return redirect
    service = AuthService(db)
    admins = service.list_admins_for_actor(current_admin)
    manageable_ids = _team_manageable_ids(current_admin, admins)
    return render_template("team_list.html", request, page_title="Пользователи", current_admin=current_admin, admins=admins, manageable_ids=manageable_ids, error=None)


@router.get("/admin/team/new")
def admin_team_new_page(request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = get_admin_or_redirect(request, db, min_role="admin")
    if redirect:
        return redirect
    allowed_roles = AuthService(db).allowed_create_roles(current_admin)
    return render_template("team_form.html", request, page_title="Создать пользователя", current_admin=current_admin, error=None, success=None, credentials=None, values={"role": allowed_roles[0] if allowed_roles else "editor", "is_active": True, "generate_password": True}, allowed_roles=allowed_roles, action_url="/admin/team/new", submit_label="Создать пользователя", is_edit=False, reset_password_url=None, reset_link_url=None)


@router.post("/admin/team/new")
async def admin_team_new_submit(request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = get_admin_or_redirect(request, db, min_role="admin")
    if redirect:
        return redirect
    form = await request.form()
    values = {"username": str(form.get("username", "")).strip(), "role": str(form.get("role", "editor")).strip(), "is_active": form.get("is_active") == "on", "generate_password": form.get("generate_password") == "on", "password": str(form.get("password", "")).strip()}
    service = AuthService(db)
    allowed_roles = service.allowed_create_roles(current_admin)
    try:
        created, plain_password = service.create_admin(current_admin, username=values["username"], role=values["role"], password=values["password"], generate_password_flag=values["generate_password"], is_active=values["is_active"])
        return render_template("team_form.html", request, page_title="Создать пользователя", current_admin=current_admin, error=None, success="Пользователь создан.", credentials={"username": created.username, "password": plain_password}, values={"role": allowed_roles[0] if allowed_roles else "editor", "is_active": True, "generate_password": True}, allowed_roles=allowed_roles, action_url="/admin/team/new", submit_label="Создать пользователя", is_edit=False, reset_password_url=None, reset_link_url=None)
    except Exception as exc:
        db.rollback()
        return render_template("team_form.html", request, page_title="Создать пользователя", current_admin=current_admin, error=str(exc), success=None, credentials=None, values=values, allowed_roles=allowed_roles, action_url="/admin/team/new", submit_label="Создать пользователя", is_edit=False, reset_password_url=None, reset_link_url=None)


@router.get("/admin/team/{admin_id}/edit")
def admin_team_edit_page(admin_id: int, request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = get_admin_or_redirect(request, db, min_role="admin")
    if redirect:
        return redirect
    service = AuthService(db)
    item = service.get_manageable_admin(current_admin, admin_id)
    allowed_roles = service.allowed_create_roles(current_admin)
    return render_template("team_form.html", request, page_title=f"Редактировать пользователя #{admin_id}", current_admin=current_admin, error=None, success=None, credentials=None, values={"username": item.username, "role": item.role, "is_active": item.is_active}, allowed_roles=allowed_roles, action_url=f"/admin/team/{admin_id}/edit", submit_label="Сохранить пользователя", is_edit=True, reset_password_url=f"/admin/team/{admin_id}/reset-password", reset_link_url=f"/admin/team/{admin_id}/reset-link")


@router.post("/admin/team/{admin_id}/edit")
async def admin_team_edit_submit(admin_id: int, request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = get_admin_or_redirect(request, db, min_role="admin")
    if redirect:
        return redirect
    service = AuthService(db)
    allowed_roles = service.allowed_create_roles(current_admin)
    form = await request.form()
    values = {"username": str(form.get("username", "")).strip(), "role": str(form.get("role", "editor")).strip(), "is_active": form.get("is_active") == "on"}
    try:
        managed = service.update_managed_admin(current_admin, admin_id, username=values["username"], role=values["role"], is_active=values["is_active"])
        return render_template("team_form.html", request, page_title=f"Редактировать пользователя #{admin_id}", current_admin=current_admin, error=None, success="Пользователь обновлён.", credentials=None, values={"username": managed.username, "role": managed.role, "is_active": managed.is_active}, allowed_roles=allowed_roles, action_url=f"/admin/team/{admin_id}/edit", submit_label="Сохранить пользователя", is_edit=True, reset_password_url=f"/admin/team/{admin_id}/reset-password", reset_link_url=f"/admin/team/{admin_id}/reset-link")
    except Exception as exc:
        db.rollback()
        target = service.get_admin(admin_id)
        return render_template("team_form.html", request, page_title=f"Редактировать пользователя #{admin_id}", current_admin=current_admin, error=str(exc), success=None, credentials=None, values={"username": target.username, "role": values["role"], "is_active": values["is_active"]}, allowed_roles=allowed_roles, action_url=f"/admin/team/{admin_id}/edit", submit_label="Сохранить пользователя", is_edit=True, reset_password_url=f"/admin/team/{admin_id}/reset-password", reset_link_url=f"/admin/team/{admin_id}/reset-link")


@router.post("/admin/team/{admin_id}/reset-password")
def admin_team_reset_password(admin_id: int, request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = get_admin_or_redirect(request, db, min_role="admin")
    if redirect:
        return redirect
    service = AuthService(db)
    allowed_roles = service.allowed_create_roles(current_admin)
    try:
        target, plain_password = service.reset_managed_admin_password(current_admin, admin_id)
        return render_template("team_form.html", request, page_title=f"Редактировать пользователя #{admin_id}", current_admin=current_admin, error=None, success="Пароль сброшен.", credentials={"username": target.username, "password": plain_password}, values={"username": target.username, "role": target.role, "is_active": target.is_active}, allowed_roles=allowed_roles, action_url=f"/admin/team/{admin_id}/edit", submit_label="Сохранить пользователя", is_edit=True, reset_password_url=f"/admin/team/{admin_id}/reset-password", reset_link_url=f"/admin/team/{admin_id}/reset-link")
    except Exception as exc:
        db.rollback()
        target = service.get_admin(admin_id)
        return render_template("team_form.html", request, page_title=f"Редактировать пользователя #{admin_id}", current_admin=current_admin, error=str(exc), success=None, credentials=None, values={"username": target.username, "role": target.role, "is_active": target.is_active}, allowed_roles=allowed_roles, action_url=f"/admin/team/{admin_id}/edit", submit_label="Сохранить пользователя", is_edit=True, reset_password_url=f"/admin/team/{admin_id}/reset-password", reset_link_url=f"/admin/team/{admin_id}/reset-link")


@router.post("/admin/team/{admin_id}/deactivate")
def admin_team_deactivate(admin_id: int, request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = get_admin_or_redirect(request, db, min_role="admin")
    if redirect:
        return redirect
    service = AuthService(db)
    try:
        service.set_managed_admin_active(current_admin, admin_id, False)
        return redirect_to("/admin/team")
    except Exception as exc:
        db.rollback()
        admins = service.list_admins_for_actor(current_admin)
        return render_template("team_list.html", request, page_title="Пользователи", current_admin=current_admin, admins=admins, manageable_ids=_team_manageable_ids(current_admin, admins), error=str(exc))


@router.post("/admin/team/{admin_id}/activate")
def admin_team_activate(admin_id: int, request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = get_admin_or_redirect(request, db, min_role="admin")
    if redirect:
        return redirect
    service = AuthService(db)
    try:
        service.set_managed_admin_active(current_admin, admin_id, True)
        return redirect_to("/admin/team")
    except Exception as exc:
        db.rollback()
        admins = service.list_admins_for_actor(current_admin)
        return render_template("team_list.html", request, page_title="Пользователи", current_admin=current_admin, admins=admins, manageable_ids=_team_manageable_ids(current_admin, admins), error=str(exc))


@router.post("/admin/team/{admin_id}/delete")
def admin_team_delete(admin_id: int, request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = get_admin_or_redirect(request, db, min_role="superadmin")
    if redirect:
        return redirect
    service = AuthService(db)
    try:
        service.delete_managed_admin(current_admin, admin_id)
        return redirect_to("/admin/team")
    except Exception as exc:
        db.rollback()
        admins = service.list_admins_for_actor(current_admin)
        return render_template("team_list.html", request, page_title="Пользователи", current_admin=current_admin, admins=admins, manageable_ids=_team_manageable_ids(current_admin, admins), error=str(exc))



@router.post("/admin/team/{admin_id}/reset-link")
def admin_team_reset_link(admin_id: int, request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = get_admin_or_redirect(request, db, min_role="admin")
    if redirect:
        return redirect
    service = AuthService(db)
    allowed_roles = service.allowed_create_roles(current_admin)
    try:
        target = service.get_manageable_admin(current_admin, admin_id)
        reset_link = PasswordResetService(db).create_reset_link(current_admin, target.id)
        return render_template("team_form.html", request, db=db, page_title=f"Редактировать пользователя #{admin_id}", current_admin=current_admin, error=None, success="Одноразовая ссылка сброса создана.", credentials={"reset_link": reset_link}, values={"username": target.username, "role": target.role, "is_active": target.is_active}, allowed_roles=allowed_roles, action_url=f"/admin/team/{admin_id}/edit", submit_label="Сохранить пользователя", is_edit=True, reset_password_url=f"/admin/team/{admin_id}/reset-password", reset_link_url=f"/admin/team/{admin_id}/reset-link")
    except Exception as exc:
        db.rollback()
        target = service.get_admin(admin_id)
        return render_template("team_form.html", request, db=db, page_title=f"Редактировать пользователя #{admin_id}", current_admin=current_admin, error=str(exc), success=None, credentials=None, values={"username": target.username, "role": target.role, "is_active": target.is_active}, allowed_roles=allowed_roles, action_url=f"/admin/team/{admin_id}/edit", submit_label="Сохранить пользователя", is_edit=True, reset_password_url=f"/admin/team/{admin_id}/reset-password", reset_link_url=f"/admin/team/{admin_id}/reset-link")

@router.get("/admin/reset-password/{token}")
def admin_reset_password_page(token: str, request: Request, db: Session = Depends(get_db_session)):
    try:
        token_entity = PasswordResetService(db).validate_token(token)
        return render_template("reset_password_form.html", request, db=db, page_title="Сброс пароля", current_admin=None, target_username=token_entity.admin.username, error=None, success=None)
    except Exception as exc:
        return render_template("reset_password_form.html", request, db=db, page_title="Сброс пароля", current_admin=None, target_username="", error=str(exc), success=None)

@router.post("/admin/reset-password/{token}")
async def admin_reset_password_submit(token: str, request: Request, db: Session = Depends(get_db_session)):
    form = await request.form()
    new_password = str(form.get("new_password", "")).strip()
    new_password_repeat = str(form.get("new_password_repeat", "")).strip()
    if new_password != new_password_repeat:
        try:
            token_entity = PasswordResetService(db).validate_token(token)
            username = token_entity.admin.username
        except Exception:
            username = ""
        return render_template("reset_password_form.html", request, db=db, page_title="Сброс пароля", current_admin=None, target_username=username, error="Пароли не совпадают.", success=None)
    try:
        PasswordResetService(db).reset_by_token(token, new_password)
        return render_template("reset_password_form.html", request, db=db, page_title="Сброс пароля", current_admin=None, target_username="", error=None, success="Пароль успешно обновлён.")
    except Exception as exc:
        try:
            token_entity = PasswordResetService(db).validate_token(token)
            username = token_entity.admin.username
        except Exception:
            username = ""
        db.rollback()
        return render_template("reset_password_form.html", request, db=db, page_title="Сброс пароля", current_admin=None, target_username=username, error=str(exc), success=None)

@router.get("/admin/chats")
def admin_chats_page(request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = get_admin_or_redirect(request, db)
    if redirect:
        return redirect
    chat_service = ChatService(db)
    chats = chat_service.list_chats_for_admin(current_admin)
    return render_template("chat_list.html", request, page_title="Чаты", current_admin=current_admin, chats=chats, error=None, messages_enabled=chat_service.messages_enabled())


@router.get("/admin/chats/new")
def admin_chat_new_page(request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = get_admin_or_redirect(request, db)
    if redirect:
        return redirect
    chat_service = ChatService(db)
    admins = [item for item in chat_service.list_active_admins() if item.id != current_admin.id]
    return render_template("chat_new.html", request, page_title="Создать чат", current_admin=current_admin, admins=admins, error=None, values={}, selected_ids=[], messages_enabled=chat_service.messages_enabled())


@router.post("/admin/chats/new")
async def admin_chat_new_submit(request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = get_admin_or_redirect(request, db)
    if redirect:
        return redirect
    form = await request.form()
    title = str(form.get("title", "")).strip()
    selected_ids = [int(item) for item in form.getlist("participant_ids")]
    service = ChatService(db)
    admins = [item for item in service.list_active_admins() if item.id != current_admin.id]
    try:
        chat = service.create_chat(current_admin, title=title, participant_ids=selected_ids)
        return redirect_to(f"/admin/chats/{chat.id}")
    except Exception as exc:
        db.rollback()
        return render_template("chat_new.html", request, page_title="Создать чат", current_admin=current_admin, admins=admins, error=str(exc), values={"title": title}, selected_ids=selected_ids, messages_enabled=service.messages_enabled())


@router.get("/admin/chats/{chat_id}")
def admin_chat_room(chat_id: int, request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = get_admin_or_redirect(request, db)
    if redirect:
        return redirect
    service = ChatService(db)
    try:
        chat = service.get_chat_for_admin(current_admin, chat_id)
        return render_template("chat_room.html", request, page_title=chat.title, current_admin=current_admin, chat=chat, error=None, messages_enabled=service.messages_enabled())
    except Exception as exc:
        db.rollback()
        chats = service.list_chats_for_admin(current_admin)
        return render_template("chat_list.html", request, page_title="Чаты", current_admin=current_admin, chats=chats, error=str(exc), messages_enabled=service.messages_enabled())


@router.post("/admin/chats/{chat_id}/message")
async def admin_chat_send_message(chat_id: int, request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = get_admin_or_redirect(request, db)
    if redirect:
        return redirect
    form = await request.form()
    content = str(form.get("content", "")).strip()
    service = ChatService(db)
    try:
        chat = service.post_message(current_admin, chat_id, content)
        return render_template("chat_room.html", request, page_title=chat.title, current_admin=current_admin, chat=chat, error=None, messages_enabled=service.messages_enabled())
    except Exception as exc:
        db.rollback()
        try:
            chat = service.get_chat_for_admin(current_admin, chat_id)
            return render_template("chat_room.html", request, page_title=chat.title, current_admin=current_admin, chat=chat, error=str(exc), messages_enabled=service.messages_enabled())
        except Exception:
            chats = service.list_chats_for_admin(current_admin)
            return render_template("chat_list.html", request, page_title="Чаты", current_admin=current_admin, chats=chats, error=str(exc), messages_enabled=service.messages_enabled())


@router.get("/admin/settings/general")
def admin_settings_general_page(request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = get_admin_or_redirect(request, db, min_role="superadmin")
    if redirect:
        return redirect
    service = SiteSettingService(db)
    return render_template("settings_general.html", request, page_title="Общие настройки", current_admin=current_admin, messages_enabled=service.is_messages_enabled(), error=None, success=None)


@router.post("/admin/settings/general")
async def admin_settings_general_submit(request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = get_admin_or_redirect(request, db, min_role="superadmin")
    if redirect:
        return redirect
    form = await request.form()
    enabled = form.get("messages_enabled") == "on"
    service = SiteSettingService(db)
    service.set_messages_enabled(enabled)
    return render_template("settings_general.html", request, page_title="Общие настройки", current_admin=current_admin, messages_enabled=service.is_messages_enabled(), error=None, success="Настройки обновлены.")


@router.get("/admin/analytics")
def admin_analytics_page(
    request: Request,
    db: Session = Depends(get_db_session),
    q: str = "",
    outcome: str = "",
):
    current_admin, redirect = get_admin_or_redirect(request, db, min_role="admin")
    if redirect:
        return redirect

    service = AnalyticsService(db)
    return render_template(
        "analytics_dashboard.html",
        request,
        page_title="Аналитика и аудит",
        current_admin=current_admin,
        summary=service.get_summary(),
        code_rows=service.list_code_rows(q=q, outcome=outcome),
        recent_lookup_events=service.list_recent_lookup_events(limit=120),
        recent_audit_logs=service.list_recent_audit_logs(limit=120),
        filters={"q": q, "outcome": outcome},
    )


@router.get("/admin/analytics/codes/{code_value}")
def admin_analytics_code_detail(
    code_value: str,
    request: Request,
    db: Session = Depends(get_db_session),
):
    current_admin, redirect = get_admin_or_redirect(request, db, min_role="admin")
    if redirect:
        return redirect

    detail = AnalyticsService(db).get_code_detail(code_value)
    return render_template(
        "code_analytics_detail.html",
        request,
        page_title=f"Аналитика кода {code_value}",
        current_admin=current_admin,
        detail=detail,
    )
