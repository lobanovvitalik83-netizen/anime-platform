import uvicorn

from app.core.config import settings


if __name__ == "__main__":
    uvicorn.run(
        "app.main:create_app",
        host=settings.app_host,
        port=settings.app_port,
        factory=True,
        reload=settings.is_development,
    )
