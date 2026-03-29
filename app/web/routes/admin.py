from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from starlette.responses import RedirectResponse

from app.core.database import get_db_session
from app.core.exceptions import AuthenticationError
from app.schemas.auth import LoginRequest
from app.services.asset_service import AssetService
from app.services.auth_service import AuthService
from app.services.code_service import CodeService
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

    titles = media_service.list_titles()
    seasons = media_service.list_seasons()
    episodes = media_service.list_episodes()
    assets = asset_service.list_assets()
    codes = code_service.list_codes()

    return render_template(
        "dashboard.html",
        request,
        page_title="Панель",
        current_admin=current_admin,
        counts={
            "titles": len(titles),
            "seasons": len(seasons),
            "episodes": len(episodes),
            "assets": len(assets),
            "codes": len(codes),
        },
    )


@router.get("/admin/titles")
def admin_titles(request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = get_admin_or_redirect(request, db)
    if redirect:
        return redirect

    titles = MediaService(db).list_titles()
    return render_template(
        "titles_list.html",
        request,
        page_title="Тайтлы",
        current_admin=current_admin,
        titles=titles,
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
        return render_template(
            "title_form.html",
            request,
            page_title="Новый тайтл",
            current_admin=current_admin,
            error=str(exc),
            values=payload,
        )

    return redirect_to("/admin/titles")


@router.get("/admin/seasons")
def admin_seasons(request: Request, db: Session = Depends(get_db_session), title_id: int | None = None):
    current_admin, redirect = get_admin_or_redirect(request, db)
    if redirect:
        return redirect

    media_service = MediaService(db)
    seasons = media_service.list_seasons(title_id=title_id)
    titles = media_service.list_titles()

    return render_template(
        "seasons_list.html",
        request,
        page_title="Сезоны",
        current_admin=current_admin,
        seasons=seasons,
        titles=titles,
        selected_title_id=title_id,
    )


@router.get("/admin/seasons/new")
def admin_season_new_page(request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = get_admin_or_redirect(request, db)
    if redirect:
        return redirect

    titles = MediaService(db).list_titles()
    return render_template(
        "season_form.html",
        request,
        page_title="Новый сезон",
        current_admin=current_admin,
        titles=titles,
        error=None,
        values={},
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
        return render_template(
            "season_form.html",
            request,
            page_title="Новый сезон",
            current_admin=current_admin,
            titles=titles,
            error=str(exc),
            values=payload,
        )

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
    episodes = media_service.list_episodes(title_id=title_id, season_id=season_id)
    titles = media_service.list_titles()
    seasons = media_service.list_seasons(title_id=title_id)

    return render_template(
        "episodes_list.html",
        request,
        page_title="Эпизоды",
        current_admin=current_admin,
        episodes=episodes,
        titles=titles,
        seasons=seasons,
        selected_title_id=title_id,
        selected_season_id=season_id,
    )


@router.get("/admin/episodes/new")
def admin_episode_new_page(request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = get_admin_or_redirect(request, db)
    if redirect:
        return redirect

    media_service = MediaService(db)
    titles = media_service.list_titles()
    seasons = media_service.list_seasons()
    return render_template(
        "episode_form.html",
        request,
        page_title="Новый эпизод",
        current_admin=current_admin,
        titles=titles,
        seasons=seasons,
        error=None,
        values={},
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
        return render_template(
            "episode_form.html",
            request,
            page_title="Новый эпизод",
            current_admin=current_admin,
            titles=titles,
            seasons=seasons,
            error=str(exc),
            values=payload,
        )

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

    media_service = MediaService(db)
    asset_service = AssetService(db)
    assets = asset_service.list_assets(title_id=title_id, season_id=season_id, episode_id=episode_id)
    titles = media_service.list_titles()
    seasons = media_service.list_seasons()
    episodes = media_service.list_episodes()

    return render_template(
        "assets_list.html",
        request,
        page_title="Ассеты",
        current_admin=current_admin,
        assets=assets,
        titles=titles,
        seasons=seasons,
        episodes=episodes,
    )


@router.get("/admin/assets/new")
def admin_asset_new_page(request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = get_admin_or_redirect(request, db)
    if redirect:
        return redirect

    media_service = MediaService(db)
    return render_template(
        "asset_form.html",
        request,
        page_title="Новый ассет",
        current_admin=current_admin,
        titles=media_service.list_titles(),
        seasons=media_service.list_seasons(),
        episodes=media_service.list_episodes(),
        error=None,
        values={},
    )


@router.post("/admin/assets/new")
async def admin_asset_new_submit(request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = get_admin_or_redirect(request, db)
    if redirect:
        return redirect

    media_service = MediaService(db)
    titles = media_service.list_titles()
    seasons = media_service.list_seasons()
    episodes = media_service.list_episodes()

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
        return render_template(
            "asset_form.html",
            request,
            page_title="Новый ассет",
            current_admin=current_admin,
            titles=titles,
            seasons=seasons,
            episodes=episodes,
            error=str(exc),
            values=payload,
        )

    return redirect_to("/admin/assets")


@router.get("/admin/codes")
def admin_codes(request: Request, db: Session = Depends(get_db_session)):
    current_admin, redirect = get_admin_or_redirect(request, db)
    if redirect:
        return redirect

    codes = CodeService(db).list_codes()
    return render_template(
        "codes_list.html",
        request,
        page_title="Коды",
        current_admin=current_admin,
        codes=codes,
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
        return render_template(
            "code_generate.html",
            request,
            page_title="Генерация кодов",
            current_admin=current_admin,
            titles=titles,
            seasons=seasons,
            episodes=episodes,
            error=str(exc),
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
