from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.routes.access_codes import router as access_codes_router
from app.api.routes.auth import router as auth_router
from app.api.routes.health import router as health_router
from app.api.routes.media_assets import router as media_assets_router
from app.api.routes.media_episodes import router as media_episodes_router
from app.api.routes.media_seasons import router as media_seasons_router
from app.api.routes.media_titles import router as media_titles_router
from app.api.routes.public_lookup import router as public_lookup_router
from app.bot.dispatcher import start_bot_polling, stop_bot_polling
from app.core.config import settings
from app.core.database import init_database
from app.core.logging import configure_logging, get_logger
from app.services.bootstrap_service import ensure_default_admin_exists
from app.web.routes.admin import router as admin_web_router

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
    app = FastAPI(title=settings.app_name, debug=settings.is_development, lifespan=lifespan)
    settings.public_upload_dir.mkdir(parents=True, exist_ok=True)
    app.mount("/uploads", StaticFiles(directory=str(settings.public_upload_dir)), name="uploads")

    app.include_router(health_router)
    app.include_router(auth_router)
    app.include_router(media_titles_router)
    app.include_router(media_seasons_router)
    app.include_router(media_episodes_router)
    app.include_router(media_assets_router)
    app.include_router(access_codes_router)
    app.include_router(public_lookup_router)
    app.include_router(admin_web_router)
    return app
