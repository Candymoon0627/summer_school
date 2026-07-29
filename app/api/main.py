from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import admin, health, line
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.core.sentry import init_sentry

configure_logging()
init_sentry()

settings = get_settings()
app = FastAPI(title=settings.app_name, version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        origin.strip()
        for origin in settings.cors_allow_origins.split(",")
        if origin.strip()
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(line.router, prefix="/line", tags=["line"])
app.include_router(admin.router, prefix="/admin", tags=["admin"])
