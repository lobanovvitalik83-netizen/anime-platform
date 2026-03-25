from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.db import Base, SessionLocal, engine
from app.routers import analytics, auth, content, permissions, roles, settings_api, users
from app.schemas import HealthResponse
from app.seed import seed_database

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup_event():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()


@app.get("/", response_model=HealthResponse)
@app.get("/health", response_model=HealthResponse)
def health_check():
    return HealthResponse(status="healthy", app=settings.app_name, env=settings.app_env)


app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
app.include_router(roles.router, prefix="/api/v1/roles", tags=["roles"])
app.include_router(permissions.router, prefix="/api/v1/permissions", tags=["permissions"])
app.include_router(content.router, prefix="/api/v1/content", tags=["content"])
app.include_router(settings_api.router, prefix="/api/v1/settings", tags=["settings"])
app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["analytics"])
