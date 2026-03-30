from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.routes.access_codes import router as access_codes_router
from app.api.routes.auth import router as auth_router
from app.api.routes.health import router as health_router
from app.api.routes.media_assets import router as media_assets_router
from app.api.routes.media_episodes import router as media_episodes_router
from app.api.routes.media_proxy import router as media_proxy_router
from app.api.routes.media_seasons import router as media_seasons_router
from app.api.routes.media_titles import router as media_titles_router
from app.api.routes.public_lookup import router as public_lookup_router
from app.bot.dispatcher import start_bot_polling, stop_bot_polling
from app.core.config import settings
from app.core.database import init_database
from app.core.logging import configure_logging, get_logger
from app.services.bootstrap_service import ensure_default_admin_exists
from app.web.routes.admin import router as admin_web_router
from app.web.routes.private_docs import router as private_docs_router
from app.web.routes.stage24 import router as stage24_web_router
from app.web.routes.stage26 import router as stage26_web_router

configure_logging()
logger = get_logger(__name__)

@asynccontextmanager
async def lifespan(_: FastAPI):
    init_database()
    ensure_default_admin_exists()
    await start_bot_polling()
    logger.info("Application startup completed")
    yield
    await stop_bot_polling()
    logger.info("Application shutdown completed")

def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        debug=settings.is_development,
        lifespan=lifespan,
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )
    settings.public_upload_dir.mkdir(parents=True, exist_ok=True)
    app.mount("/uploads", StaticFiles(directory=str(settings.public_upload_dir)), name="uploads")
    app.include_router(health_router)
    app.include_router(auth_router)
    app.include_router(media_titles_router)
    app.include_router(media_proxy_router)
    app.include_router(media_seasons_router)
    app.include_router(media_episodes_router)
    app.include_router(media_assets_router)
    app.include_router(access_codes_router)
    app.include_router(public_lookup_router)
    app.include_router(admin_web_router)
    app.include_router(stage24_web_router)
    app.include_router(stage26_web_router)
    app.include_router(private_docs_router)
    return app

app = create_app()
