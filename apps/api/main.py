from fastapi import FastAPI
from config import settings

app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.APP_DEBUG,
)

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
