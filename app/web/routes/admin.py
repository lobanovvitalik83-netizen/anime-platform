from fastapi import APIRouter, Depends, File, Request, Response, UploadFile
from sqlalchemy.orm import Session
from starlette.responses import RedirectResponse

from app.core.database import get_db_session
from app.core.exceptions import AuthenticationError
from app.services.asset_service import AssetService
from app.services.auth_service import AuthService
from app.services.code_service import CodeService
from app.services.media_card_service import MediaCardService
from app.services.import_export_service import ImportExportService
from app.services.media_service import MediaService
from app.services.public_lookup_service import PublicLookupService
from app.web.auth import clear_auth_cookie, get_current_admin_from_request, redirect_to, redirect_to_login, set_auth_cookie
from app.web.templates import templates

router = APIRouter(include_in_schema=False)


def to_int(value: str | None) -> int | None:
    if value is None or value == "":
        return None
    return int(value)


def get_admin_or_redirect(request: Request, db: Session):
    admin = get_current_admin_from_request(request, db)
    if not admin:
        return None, redirect_to_login()
    return admin, None


def render_template(name: str, request: Request, **context):
    return templates.TemplateResponse(name, {"request": request, **context})


def _render_error(name: str, request: Request, current_admin, error: str, **context):
    return render_template(name, request, current_admin=current_admin, error=error, **context)


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

    try:
        admin = AuthService(db).authenticate(username=username, password=password)
    except AuthenticationError as exc:
        return render_template("login.html", request, page_title="Вход", error=str(exc))

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

    return render_template(
        "dashboard.html",
        request,
        page_title="Панель",
        current_admin=current_admin,
        counts={
            "titles": len(media_service.list_titles()),
            "seasons": len(media_service.list_seasons()),
            "episodes": len(media_service.list_episodes()),
            "assets": len(asset_service.list_assets()),
            "codes": len(code_service.list_codes()),
        },
    )


@router.get("/admin/titles")
def admin_titles(request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = get_admin_or_redirect(request, db)
    if redirect:
        return redirect

    return render_template(
        "titles_list.html",
        request,
        page_title="Тайтлы",
        current_admin=current_admin,
        titles=MediaService(db).list_titles(),
    )


@router.get("/admin/titles/new")
def admin_title_new_page(request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = get_admin_or_redirect(request, db)
    if redirect:
        return redirect

    return render_template(
        "title_form.html",
        request,
        page_title="Новый тайтл",
        current_admin=current_admin,
        error=None,
        values={},
        action_url="/admin/titles/new",
        submit_label="Сохранить",
    )


@router.post("/admin/titles/new")
async def admin_title_new_submit(request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = get_admin_or_redirect(request, db)
    if redirect:
        return redirect

    form = await request.form()
    payload = {
        "type": str(form.get("type", "")).strip(),
        "title": str(form.get("title", "")).strip(),
        "original_title": str(form.get("original_title", "")).strip() or None,
        "description": str(form.get("description", "")).strip() or None,
        "year": to_int(str(form.get("year", "")).strip() or None),
        "status": str(form.get("status", "draft")).strip(),
    }

    try:
        MediaService(db).create_title(current_admin.id, payload)
    except Exception as exc:
        db.rollback()
        return _render_error(
            "title_form.html",
            request,
            current_admin,
            str(exc),
            page_title="Новый тайтл",
            values=payload,
            action_url="/admin/titles/new",
            submit_label="Сохранить",
        )

    return redirect_to("/admin/titles")


@router.get("/admin/titles/{title_id}/edit")
def admin_title_edit_page(title_id: int, request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = get_admin_or_redirect(request, db)
    if redirect:
        return redirect

    item = MediaService(db).get_title(title_id)
    values = {
        "type": item.type,
        "title": item.title,
        "original_title": item.original_title or "",
        "description": item.description or "",
        "year": item.year or "",
        "status": item.status,
    }
    return render_template(
        "title_form.html",
        request,
        page_title=f"Редактировать тайтл #{item.id}",
        current_admin=current_admin,
        error=None,
        values=values,
        action_url=f"/admin/titles/{item.id}/edit",
        submit_label="Сохранить изменения",
    )


@router.post("/admin/titles/{title_id}/edit")
async def admin_title_edit_submit(title_id: int, request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = get_admin_or_redirect(request, db)
    if redirect:
        return redirect

    form = await request.form()
    payload = {
        "type": str(form.get("type", "")).strip(),
        "title": str(form.get("title", "")).strip(),
        "original_title": str(form.get("original_title", "")).strip() or None,
        "description": str(form.get("description", "")).strip() or None,
        "year": to_int(str(form.get("year", "")).strip() or None),
        "status": str(form.get("status", "draft")).strip(),
    }

    try:
        MediaService(db).update_title(current_admin.id, title_id, payload)
    except Exception as exc:
        db.rollback()
        return _render_error(
            "title_form.html",
            request,
            current_admin,
            str(exc),
            page_title=f"Редактировать тайтл #{title_id}",
            values=payload,
            action_url=f"/admin/titles/{title_id}/edit",
            submit_label="Сохранить изменения",
        )

    return redirect_to("/admin/titles")


@router.post("/admin/titles/{title_id}/delete")
def admin_title_delete(title_id: int, request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = get_admin_or_redirect(request, db)
    if redirect:
        return redirect
    MediaService(db).delete_title(current_admin.id, title_id)
    return redirect_to("/admin/titles")


@router.get("/admin/seasons")
def admin_seasons(request: Request, db: Session = Depends(get_db_session), title_id: int | None = None):
    current_admin, redirect = get_admin_or_redirect(request, db)
    if redirect:
        return redirect

    media_service = MediaService(db)
    return render_template(
        "seasons_list.html",
        request,
        page_title="Сезоны",
        current_admin=current_admin,
        seasons=media_service.list_seasons(title_id=title_id),
        titles=media_service.list_titles(),
        selected_title_id=title_id,
    )


@router.get("/admin/seasons/new")
def admin_season_new_page(request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = get_admin_or_redirect(request, db)
    if redirect:
        return redirect

    return render_template(
        "season_form.html",
        request,
        page_title="Новый сезон",
        current_admin=current_admin,
        titles=MediaService(db).list_titles(),
        error=None,
        values={},
        action_url="/admin/seasons/new",
        submit_label="Сохранить",
    )


@router.post("/admin/seasons/new")
async def admin_season_new_submit(request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = get_admin_or_redirect(request, db)
    if redirect:
        return redirect

    titles = MediaService(db).list_titles()
    form = await request.form()
    payload = {
        "title_id": int(str(form.get("title_id")).strip()),
        "season_number": int(str(form.get("season_number")).strip()),
        "name": str(form.get("name", "")).strip() or None,
        "description": str(form.get("description", "")).strip() or None,
    }

    try:
        MediaService(db).create_season(current_admin.id, payload)
    except Exception as exc:
        db.rollback()
        return _render_error(
            "season_form.html",
            request,
            current_admin,
            str(exc),
            page_title="Новый сезон",
            titles=titles,
            values=payload,
            action_url="/admin/seasons/new",
            submit_label="Сохранить",
        )

    return redirect_to("/admin/seasons")


@router.get("/admin/seasons/{season_id}/edit")
def admin_season_edit_page(season_id: int, request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = get_admin_or_redirect(request, db)
    if redirect:
        return redirect

    item = MediaService(db).get_season(season_id)
    values = {
        "title_id": item.title_id,
        "season_number": item.season_number,
        "name": item.name or "",
        "description": item.description or "",
    }
    return render_template(
        "season_form.html",
        request,
        page_title=f"Редактировать сезон #{item.id}",
        current_admin=current_admin,
        titles=MediaService(db).list_titles(),
        error=None,
        values=values,
        action_url=f"/admin/seasons/{item.id}/edit",
        submit_label="Сохранить изменения",
    )


@router.post("/admin/seasons/{season_id}/edit")
async def admin_season_edit_submit(season_id: int, request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = get_admin_or_redirect(request, db)
    if redirect:
        return redirect

    titles = MediaService(db).list_titles()
    form = await request.form()
    payload = {
        "title_id": int(str(form.get("title_id")).strip()),
        "season_number": int(str(form.get("season_number")).strip()),
        "name": str(form.get("name", "")).strip() or None,
        "description": str(form.get("description", "")).strip() or None,
    }

    try:
        MediaService(db).update_season(current_admin.id, season_id, payload)
    except Exception as exc:
        db.rollback()
        return _render_error(
            "season_form.html",
            request,
            current_admin,
            str(exc),
            page_title=f"Редактировать сезон #{season_id}",
            titles=titles,
            values=payload,
            action_url=f"/admin/seasons/{season_id}/edit",
            submit_label="Сохранить изменения",
        )

    return redirect_to("/admin/seasons")


@router.post("/admin/seasons/{season_id}/delete")
def admin_season_delete(season_id: int, request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = get_admin_or_redirect(request, db)
    if redirect:
        return redirect
    MediaService(db).delete_season(current_admin.id, season_id)
    return redirect_to("/admin/seasons")


@router.get("/admin/episodes")
def admin_episodes(
    request: Request,
    db: Session = Depends(get_db_session),
    title_id: int | None = None,
    season_id: int | None = None,
):
    current_admin, redirect = get_admin_or_redirect(request, db)
    if redirect:
        return redirect

    media_service = MediaService(db)
    return render_template(
        "episodes_list.html",
        request,
        page_title="Эпизоды",
        current_admin=current_admin,
        episodes=media_service.list_episodes(title_id=title_id, season_id=season_id),
        titles=media_service.list_titles(),
        seasons=media_service.list_seasons(title_id=title_id),
        selected_title_id=title_id,
        selected_season_id=season_id,
    )


@router.get("/admin/episodes/new")
def admin_episode_new_page(request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = get_admin_or_redirect(request, db)
    if redirect:
        return redirect

    media_service = MediaService(db)
    return render_template(
        "episode_form.html",
        request,
        page_title="Новый эпизод",
        current_admin=current_admin,
        titles=media_service.list_titles(),
        seasons=media_service.list_seasons(),
        error=None,
        values={},
        action_url="/admin/episodes/new",
        submit_label="Сохранить",
    )


@router.post("/admin/episodes/new")
async def admin_episode_new_submit(request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = get_admin_or_redirect(request, db)
    if redirect:
        return redirect

    media_service = MediaService(db)
    titles = media_service.list_titles()
    seasons = media_service.list_seasons()

    form = await request.form()
    payload = {
        "title_id": int(str(form.get("title_id")).strip()),
        "season_id": to_int(str(form.get("season_id", "")).strip() or None),
        "episode_number": int(str(form.get("episode_number")).strip()),
        "name": str(form.get("name", "")).strip() or None,
        "synopsis": str(form.get("synopsis", "")).strip() or None,
        "status": str(form.get("status", "draft")).strip(),
    }

    try:
        MediaService(db).create_episode(current_admin.id, payload)
    except Exception as exc:
        db.rollback()
        return _render_error(
            "episode_form.html",
            request,
            current_admin,
            str(exc),
            page_title="Новый эпизод",
            titles=titles,
            seasons=seasons,
            values=payload,
            action_url="/admin/episodes/new",
            submit_label="Сохранить",
        )

    return redirect_to("/admin/episodes")


@router.get("/admin/episodes/{episode_id}/edit")
def admin_episode_edit_page(episode_id: int, request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = get_admin_or_redirect(request, db)
    if redirect:
        return redirect

    item = MediaService(db).get_episode(episode_id)
    media_service = MediaService(db)
    values = {
        "title_id": item.title_id,
        "season_id": item.season_id or "",
        "episode_number": item.episode_number,
        "name": item.name or "",
        "synopsis": item.synopsis or "",
        "status": item.status,
    }
    return render_template(
        "episode_form.html",
        request,
        page_title=f"Редактировать эпизод #{item.id}",
        current_admin=current_admin,
        titles=media_service.list_titles(),
        seasons=media_service.list_seasons(),
        error=None,
        values=values,
        action_url=f"/admin/episodes/{item.id}/edit",
        submit_label="Сохранить изменения",
    )


@router.post("/admin/episodes/{episode_id}/edit")
async def admin_episode_edit_submit(episode_id: int, request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = get_admin_or_redirect(request, db)
    if redirect:
        return redirect

    media_service = MediaService(db)
    titles = media_service.list_titles()
    seasons = media_service.list_seasons()

    form = await request.form()
    payload = {
        "title_id": int(str(form.get("title_id")).strip()),
        "season_id": to_int(str(form.get("season_id", "")).strip() or None),
        "episode_number": int(str(form.get("episode_number")).strip()),
        "name": str(form.get("name", "")).strip() or None,
        "synopsis": str(form.get("synopsis", "")).strip() or None,
        "status": str(form.get("status", "draft")).strip(),
    }

    try:
        MediaService(db).update_episode(current_admin.id, episode_id, payload)
    except Exception as exc:
        db.rollback()
        return _render_error(
            "episode_form.html",
            request,
            current_admin,
            str(exc),
            page_title=f"Редактировать эпизод #{episode_id}",
            titles=titles,
            seasons=seasons,
            values=payload,
            action_url=f"/admin/episodes/{episode_id}/edit",
            submit_label="Сохранить изменения",
        )

    return redirect_to("/admin/episodes")


@router.post("/admin/episodes/{episode_id}/delete")
def admin_episode_delete(episode_id: int, request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = get_admin_or_redirect(request, db)
    if redirect:
        return redirect
    MediaService(db).delete_episode(current_admin.id, episode_id)
    return redirect_to("/admin/episodes")


@router.get("/admin/assets")
def admin_assets(
    request: Request,
    db: Session = Depends(get_db_session),
    title_id: int | None = None,
    season_id: int | None = None,
    episode_id: int | None = None,
):
    current_admin, redirect = get_admin_or_redirect(request, db)
    if redirect:
        return redirect

    asset_service = AssetService(db)
    return render_template(
        "assets_list.html",
        request,
        page_title="Ассеты",
        current_admin=current_admin,
        assets=asset_service.list_assets(title_id=title_id, season_id=season_id, episode_id=episode_id),
    )


@router.get("/admin/assets/new")
def admin_asset_new_page(request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = get_admin_or_redirect(request, db)
    if redirect:
        return redirect

    return render_template(
        "asset_form_simple.html",
        request,
        page_title="Новый ассет",
        current_admin=current_admin,
        error=None,
        values={},
        action_url="/admin/assets/new",
        submit_label="Сохранить",
    )


@router.post("/admin/assets/new")
async def admin_asset_new_submit(request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = get_admin_or_redirect(request, db)
    if redirect:
        return redirect

    form = await request.form()
    payload = {
        "title_id": to_int(str(form.get("title_id", "")).strip() or None),
        "season_id": to_int(str(form.get("season_id", "")).strip() or None),
        "episode_id": to_int(str(form.get("episode_id", "")).strip() or None),
        "asset_type": str(form.get("asset_type", "")).strip(),
        "storage_kind": str(form.get("storage_kind", "")).strip(),
        "telegram_file_id": str(form.get("telegram_file_id", "")).strip() or None,
        "external_url": str(form.get("external_url", "")).strip() or None,
        "mime_type": str(form.get("mime_type", "")).strip() or None,
        "is_primary": form.get("is_primary") == "on",
    }

    try:
        AssetService(db).create_asset(current_admin.id, payload)
    except Exception as exc:
        db.rollback()
        return _render_error(
            "asset_form_simple.html",
            request,
            current_admin,
            str(exc),
            page_title="Новый ассет",
            values=payload,
            action_url="/admin/assets/new",
            submit_label="Сохранить",
        )

    return redirect_to("/admin/assets")


@router.get("/admin/assets/{asset_id}/edit")
def admin_asset_edit_page(asset_id: int, request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = get_admin_or_redirect(request, db)
    if redirect:
        return redirect

    item = AssetService(db).get_asset(asset_id)
    values = {
        "title_id": item.title_id or "",
        "season_id": item.season_id or "",
        "episode_id": item.episode_id or "",
        "asset_type": item.asset_type,
        "storage_kind": item.storage_kind,
        "telegram_file_id": item.telegram_file_id or "",
        "external_url": item.external_url or "",
        "mime_type": item.mime_type or "",
        "is_primary": item.is_primary,
    }
    return render_template(
        "asset_form_simple.html",
        request,
        page_title=f"Редактировать ассет #{item.id}",
        current_admin=current_admin,
        error=None,
        values=values,
        action_url=f"/admin/assets/{item.id}/edit",
        submit_label="Сохранить изменения",
    )


@router.post("/admin/assets/{asset_id}/edit")
async def admin_asset_edit_submit(asset_id: int, request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = get_admin_or_redirect(request, db)
    if redirect:
        return redirect

    form = await request.form()
    payload = {
        "title_id": to_int(str(form.get("title_id", "")).strip() or None),
        "season_id": to_int(str(form.get("season_id", "")).strip() or None),
        "episode_id": to_int(str(form.get("episode_id", "")).strip() or None),
        "asset_type": str(form.get("asset_type", "")).strip(),
        "storage_kind": str(form.get("storage_kind", "")).strip(),
        "telegram_file_id": str(form.get("telegram_file_id", "")).strip() or None,
        "external_url": str(form.get("external_url", "")).strip() or None,
        "mime_type": str(form.get("mime_type", "")).strip() or None,
        "is_primary": form.get("is_primary") == "on",
    }

    try:
        AssetService(db).update_asset(current_admin.id, asset_id, payload)
    except Exception as exc:
        db.rollback()
        return _render_error(
            "asset_form_simple.html",
            request,
            current_admin,
            str(exc),
            page_title=f"Редактировать ассет #{asset_id}",
            values=payload,
            action_url=f"/admin/assets/{asset_id}/edit",
            submit_label="Сохранить изменения",
        )

    return redirect_to("/admin/assets")


@router.post("/admin/assets/{asset_id}/delete")
def admin_asset_delete(asset_id: int, request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = get_admin_or_redirect(request, db)
    if redirect:
        return redirect
    AssetService(db).delete_asset(current_admin.id, asset_id)
    return redirect_to("/admin/assets")


@router.get("/admin/codes")
def admin_codes(request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = get_admin_or_redirect(request, db)
    if redirect:
        return redirect

    return render_template(
        "codes_list.html",
        request,
        page_title="Коды",
        current_admin=current_admin,
        codes=CodeService(db).list_codes(),
    )


@router.get("/admin/codes/generate")
def admin_codes_generate_page(request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = get_admin_or_redirect(request, db)
    if redirect:
        return redirect

    media_service = MediaService(db)
    return render_template(
        "code_generate.html",
        request,
        page_title="Генерация кодов",
        current_admin=current_admin,
        titles=media_service.list_titles(),
        seasons=media_service.list_seasons(),
        episodes=media_service.list_episodes(),
        error=None,
        values={},
        generated_codes=None,
    )


@router.post("/admin/codes/generate")
async def admin_codes_generate_submit(request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = get_admin_or_redirect(request, db)
    if redirect:
        return redirect

    media_service = MediaService(db)
    titles = media_service.list_titles()
    seasons = media_service.list_seasons()
    episodes = media_service.list_episodes()

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
        return _render_error(
            "code_generate.html",
            request,
            current_admin,
            str(exc),
            page_title="Генерация кодов",
            titles=titles,
            seasons=seasons,
            episodes=episodes,
            values=payload,
            generated_codes=None,
        )

    return render_template(
        "code_generate.html",
        request,
        page_title="Генерация кодов",
        current_admin=current_admin,
        titles=titles,
        seasons=seasons,
        episodes=episodes,
        error=None,
        values=payload,
        generated_codes=generated_codes,
    )


@router.get("/admin/codes/{code_id}/edit")
def admin_code_edit_page(code_id: int, request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = get_admin_or_redirect(request, db)
    if redirect:
        return redirect

    code_service = CodeService(db)
    media_service = MediaService(db)
    item = code_service.get_code(code_id)
    values = {
        "code": item.code,
        "title_id": item.title_id or "",
        "season_id": item.season_id or "",
        "episode_id": item.episode_id or "",
        "status": item.status,
    }
    return render_template(
        "code_form.html",
        request,
        page_title=f"Редактировать код #{item.id}",
        current_admin=current_admin,
        titles=media_service.list_titles(),
        seasons=media_service.list_seasons(),
        episodes=media_service.list_episodes(),
        error=None,
        values=values,
        action_url=f"/admin/codes/{item.id}/edit",
        submit_label="Сохранить изменения",
    )


@router.post("/admin/codes/{code_id}/edit")
async def admin_code_edit_submit(code_id: int, request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = get_admin_or_redirect(request, db)
    if redirect:
        return redirect

    media_service = MediaService(db)
    form = await request.form()
    payload = {
        "code": str(form.get("code", "")).strip(),
        "title_id": to_int(str(form.get("title_id", "")).strip() or None),
        "season_id": to_int(str(form.get("season_id", "")).strip() or None),
        "episode_id": to_int(str(form.get("episode_id", "")).strip() or None),
        "status": str(form.get("status", "active")).strip(),
    }

    try:
        CodeService(db).update_code(current_admin.id, code_id, payload)
    except Exception as exc:
        db.rollback()
        return _render_error(
            "code_form.html",
            request,
            current_admin,
            str(exc),
            page_title=f"Редактировать код #{code_id}",
            titles=media_service.list_titles(),
            seasons=media_service.list_seasons(),
            episodes=media_service.list_episodes(),
            values=payload,
            action_url=f"/admin/codes/{code_id}/edit",
            submit_label="Сохранить изменения",
        )

    return redirect_to("/admin/codes")


@router.post("/admin/codes/{code_id}/deactivate")
def admin_code_deactivate(code_id: int, request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = get_admin_or_redirect(request, db)
    if redirect:
        return redirect
    CodeService(db).deactivate_code(current_admin.id, code_id)
    return redirect_to("/admin/codes")


@router.post("/admin/codes/{code_id}/delete")
def admin_code_delete(code_id: int, request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = get_admin_or_redirect(request, db)
    if redirect:
        return redirect
    CodeService(db).delete_code(current_admin.id, code_id)
    return redirect_to("/admin/codes")


@router.get("/admin/lookup-test")
def admin_lookup_test(request: Request, db: Session = Depends(get_db_session), code: str | None = None):
    current_admin, redirect = get_admin_or_redirect(request, db)
    if redirect:
        return redirect

    result = None
    error = None
    if code:
        try:
            result = PublicLookupService(db).lookup(code)
        except Exception as exc:
            db.rollback()
            error = str(exc)

    return render_template(
        "lookup_test.html",
        request,
        page_title="Тест lookup",
        current_admin=current_admin,
        code=code or "",
        result=result,
        error=error,
    )


@router.post("/admin/codes/{code_id}/activate")
def admin_code_activate(code_id: int, request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = get_admin_or_redirect(request, db)
    if redirect:
        return redirect
    CodeService(db).activate_code(current_admin.id, code_id)
    return redirect_to("/admin/codes")


@router.post("/admin/codes/bulk-action")
async def admin_codes_bulk_action(request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = get_admin_or_redirect(request, db)
    if redirect:
        return redirect

    form = await request.form()
    action = str(form.get("bulk_action", "")).strip()
    selected_values = form.getlist("selected_ids")

    if not action:
        return render_template(
            "codes_list.html",
            request,
            page_title="Коды",
            current_admin=current_admin,
            codes=CodeService(db).list_codes(),
            error="Не выбрано массовое действие.",
        )

    if not selected_values:
        return render_template(
            "codes_list.html",
            request,
            page_title="Коды",
            current_admin=current_admin,
            codes=CodeService(db).list_codes(),
            error="Не выбраны коды.",
        )

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
        return render_template(
            "codes_list.html",
            request,
            page_title="Коды",
            current_admin=current_admin,
            codes=CodeService(db).list_codes(),
            error=str(exc),
        )

    return redirect_to("/admin/codes")


@router.get("/admin/import-export")
def admin_import_export_page(request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = get_admin_or_redirect(request, db)
    if redirect:
        return redirect

    return render_template(
        "import_export.html",
        request,
        page_title="Импорт / экспорт",
        current_admin=current_admin,
        error=None,
        success=None,
    )


@router.get("/admin/import-jobs")
def admin_import_jobs_page(request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = get_admin_or_redirect(request, db)
    if redirect:
        return redirect

    jobs = ImportExportService(db).list_jobs()
    return render_template(
        "import_jobs_list.html",
        request,
        page_title="Import jobs",
        current_admin=current_admin,
        jobs=jobs,
    )


@router.get("/admin/export/titles.csv")
def admin_export_titles_csv(request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = get_admin_or_redirect(request, db)
    if redirect:
        return redirect
    content = ImportExportService(db).export_titles_csv()
    return Response(
        content=content,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=titles.csv"},
    )


@router.get("/admin/export/seasons.csv")
def admin_export_seasons_csv(request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = get_admin_or_redirect(request, db)
    if redirect:
        return redirect
    content = ImportExportService(db).export_seasons_csv()
    return Response(
        content=content,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=seasons.csv"},
    )


@router.get("/admin/export/episodes.csv")
def admin_export_episodes_csv(request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = get_admin_or_redirect(request, db)
    if redirect:
        return redirect
    content = ImportExportService(db).export_episodes_csv()
    return Response(
        content=content,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=episodes.csv"},
    )


@router.get("/admin/export/assets.csv")
def admin_export_assets_csv(request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = get_admin_or_redirect(request, db)
    if redirect:
        return redirect
    content = ImportExportService(db).export_assets_csv()
    return Response(
        content=content,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=assets.csv"},
    )


@router.get("/admin/export/codes.csv")
def admin_export_codes_csv(request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = get_admin_or_redirect(request, db)
    if redirect:
        return redirect
    content = ImportExportService(db).export_codes_csv()
    return Response(
        content=content,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=codes.csv"},
    )


@router.post("/admin/import/titles/csv")
async def admin_import_titles_csv(request: Request, file: UploadFile = File(...), db: Session = Depends(get_db_session)):
    current_admin, redirect = get_admin_or_redirect(request, db)
    if redirect:
        return redirect

    try:
        content = await file.read()
        job = ImportExportService(db).import_titles_csv(
            current_admin.id,
            file.filename or "titles.csv",
            content,
        )
        success = f"Импорт titles завершён. Успешно: {job.success_rows}, ошибок: {job.failed_rows}."
        return render_template(
            "import_export.html",
            request,
            page_title="Импорт / экспорт",
            current_admin=current_admin,
            error=None,
            success=success,
        )
    except Exception as exc:
        db.rollback()
        return render_template(
            "import_export.html",
            request,
            page_title="Импорт / экспорт",
            current_admin=current_admin,
            error=str(exc),
            success=None,
        )


@router.post("/admin/import/codes/csv")
async def admin_import_codes_csv(request: Request, file: UploadFile = File(...), db: Session = Depends(get_db_session)):
    current_admin, redirect = get_admin_or_redirect(request, db)
    if redirect:
        return redirect

    try:
        content = await file.read()
        job = ImportExportService(db).import_codes_csv(
            current_admin.id,
            file.filename or "codes.csv",
            content,
        )
        success = f"Импорт codes завершён. Успешно: {job.success_rows}, ошибок: {job.failed_rows}."
        return render_template(
            "import_export.html",
            request,
            page_title="Импорт / экспорт",
            current_admin=current_admin,
            error=None,
            success=success,
        )
    except Exception as exc:
        db.rollback()
        return render_template(
            "import_export.html",
            request,
            page_title="Импорт / экспорт",
            current_admin=current_admin,
            error=str(exc),
            success=None,
        )


@router.post("/admin/titles/bulk-delete")
async def admin_titles_bulk_delete(request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = get_admin_or_redirect(request, db)
    if redirect:
        return redirect

    form = await request.form()
    selected_ids = [int(item) for item in form.getlist("selected_ids")]
    media_service = MediaService(db)

    if not selected_ids:
        return render_template(
            "titles_list.html",
            request,
            page_title="Тайтлы",
            current_admin=current_admin,
            titles=media_service.list_titles(),
            error="Не выбраны тайтлы.",
        )

    try:
        for item_id in selected_ids:
            media_service.delete_title(current_admin.id, item_id)
    except Exception as exc:
        db.rollback()
        return render_template(
            "titles_list.html",
            request,
            page_title="Тайтлы",
            current_admin=current_admin,
            titles=media_service.list_titles(),
            error=str(exc),
        )

    return redirect_to("/admin/titles")


@router.post("/admin/seasons/bulk-delete")
async def admin_seasons_bulk_delete(request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = get_admin_or_redirect(request, db)
    if redirect:
        return redirect

    form = await request.form()
    selected_ids = [int(item) for item in form.getlist("selected_ids")]
    media_service = MediaService(db)

    if not selected_ids:
        return render_template(
            "seasons_list.html",
            request,
            page_title="Сезоны",
            current_admin=current_admin,
            seasons=media_service.list_seasons(),
            titles=media_service.list_titles(),
            selected_title_id=None,
            error="Не выбраны сезоны.",
        )

    try:
        for item_id in selected_ids:
            media_service.delete_season(current_admin.id, item_id)
    except Exception as exc:
        db.rollback()
        return render_template(
            "seasons_list.html",
            request,
            page_title="Сезоны",
            current_admin=current_admin,
            seasons=media_service.list_seasons(),
            titles=media_service.list_titles(),
            selected_title_id=None,
            error=str(exc),
        )

    return redirect_to("/admin/seasons")


@router.post("/admin/episodes/bulk-delete")
async def admin_episodes_bulk_delete(request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = get_admin_or_redirect(request, db)
    if redirect:
        return redirect

    form = await request.form()
    selected_ids = [int(item) for item in form.getlist("selected_ids")]
    media_service = MediaService(db)

    if not selected_ids:
        return render_template(
            "episodes_list.html",
            request,
            page_title="Эпизоды",
            current_admin=current_admin,
            episodes=media_service.list_episodes(),
            titles=media_service.list_titles(),
            seasons=media_service.list_seasons(),
            selected_title_id=None,
            selected_season_id=None,
            error="Не выбраны серии.",
        )

    try:
        for item_id in selected_ids:
            media_service.delete_episode(current_admin.id, item_id)
    except Exception as exc:
        db.rollback()
        return render_template(
            "episodes_list.html",
            request,
            page_title="Эпизоды",
            current_admin=current_admin,
            episodes=media_service.list_episodes(),
            titles=media_service.list_titles(),
            seasons=media_service.list_seasons(),
            selected_title_id=None,
            selected_season_id=None,
            error=str(exc),
        )

    return redirect_to("/admin/episodes")


@router.post("/admin/assets/bulk-delete")
async def admin_assets_bulk_delete(request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = get_admin_or_redirect(request, db)
    if redirect:
        return redirect

    form = await request.form()
    selected_ids = [int(item) for item in form.getlist("selected_ids")]
    asset_service = AssetService(db)

    if not selected_ids:
        return render_template(
            "assets_list.html",
            request,
            page_title="Ассеты",
            current_admin=current_admin,
            assets=asset_service.list_assets(),
            error="Не выбраны ассеты.",
        )

    try:
        for item_id in selected_ids:
            asset_service.delete_asset(current_admin.id, item_id)
    except Exception as exc:
        db.rollback()
        return render_template(
            "assets_list.html",
            request,
            page_title="Ассеты",
            current_admin=current_admin,
            assets=asset_service.list_assets(),
            error=str(exc),
        )

    return redirect_to("/admin/assets")


def _render_media_cards(request: Request, current_admin, db: Session, error: str | None = None):
    cards = MediaCardService(db).list_cards()
    return render_template(
        "media_cards_list.html",
        request,
        page_title="Медиа",
        current_admin=current_admin,
        cards=cards,
        error=error,
    )


@router.get("/admin/media")
def admin_media_cards(request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = get_admin_or_redirect(request, db)
    if redirect:
        return redirect
    return _render_media_cards(request, current_admin, db)


@router.post("/admin/media/bulk-delete")
async def admin_media_bulk_delete(request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = get_admin_or_redirect(request, db)
    if redirect:
        return redirect

    form = await request.form()
    selected_ids = [int(item) for item in form.getlist("selected_ids")]
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
    current_admin, redirect = get_admin_or_redirect(request, db)
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
        "external_url": card["asset"].external_url if card["asset"] else "",
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
        values={"generate_code": True, "status": "active", "asset_type": "image", "genre": "anime"},
        result=None,
        action_url="/admin/card-builder",
        submit_label="Создать карточку",
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
            values={"generate_code": True, "status": "active", "asset_type": "image", "genre": "anime"},
            result=result,
            action_url="/admin/card-builder",
            submit_label="Создать карточку",
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
        )