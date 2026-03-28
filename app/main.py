from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes.access_codes import router as access_codes_router
from app.api.routes.auth import router as auth_router
from app.api.routes.health import router as health_router
from app.api.routes.media_titles import router as media_titles_router
from app.core.config import settings
from app.core.database import init_database
from app.core.logging import configure_logging, get_logger

configure_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_database()
    logger.info("Application startup completed")
    yield
    logger.info("Application shutdown completed")


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        debug=settings.is_development,
        lifespan=lifespan,
    )
    app.include_router(health_router)
    app.include_router(auth_router)
    app.include_router(media_titles_router)
    app.include_router(access_codes_router)
    return app
