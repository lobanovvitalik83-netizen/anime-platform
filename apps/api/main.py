from contextlib import asynccontextmanager

from fastapi import FastAPI

from api import auth_router, permissions_router, roles_router, users_router
from config import settings
from db import Base, SessionLocal, engine
import models  # noqa: F401
from services.init_data import init_database


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        init_database(db)
    finally:
        db.close()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.APP_DEBUG,
    lifespan=lifespan,
)

app.include_router(auth_router, prefix="/api/v1")
app.include_router(users_router, prefix="/api/v1")
app.include_router(roles_router, prefix="/api/v1")
app.include_router(permissions_router, prefix="/api/v1")


@app.get("/")
def root():
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "env": settings.APP_ENV,
    }


@app.get("/health")
def health():
    return {"status": "healthy"}
